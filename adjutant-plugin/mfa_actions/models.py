# Copyright (C) 2017 Catalyst IT Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import base64
from datetime import timedelta
import json
import os

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from adjutant.common import user_store
from adjutant.actions.v1.base import (
    UserIdAction, UserMixin, ProjectMixin)
from adjutant.actions.v1.models import register_action_class

from mfa_actions.utils import generate_totp_passcode
from mfa_actions import serializers


class EditMFAAction(UserIdAction, ProjectMixin, UserMixin):
    """
    A class for adding or removing MFA to a user account.
    """

    required = [
        'user_id',
        'delete'
    ]

    cred_expiry = 15  # in minutes

    def _validate_target_user(self):
        # Get target user
        user = self._get_target_user()
        if not user:
            self.add_note('No user present with user_id')
            return False

        return True

    def _validate_totp_enabled(self):
        id_manager = user_store.IdentityManager()
        if id_manager.list_credentials(user_id=self.user_id, cred_type='totp'):
            self.add_note('User has pre-exisiting totp credentials.')
            return self.delete
        self.add_note('User does not have pre-existing totp credentials.')
        return not self.delete

    def _validate(self):
        self.action.valid = (
            self._validate_target_user() and
            self._validate_totp_enabled()
        )
        self.action.save()

    def _pre_approve(self):
        self._validate()
        self.set_auto_approve()

        if self.valid and not self.delete:
            id_manager = user_store.IdentityManager()
            creds = id_manager.list_credentials(self.user_id, 'totp-draft')

            expiry_time = timezone.now() - timedelta(
                minutes=int(
                    self.settings.get('cred_expiry', self.cred_expiry)))

            valid_cred = None
            for cred in creds:
                if valid_cred:
                    id_manager.delete_credential(cred)
                    continue
                try:
                    cred_data = json.loads(cred.blob)
                    cred_time = parse_datetime(cred_data['created'])
                    if cred_time >= expiry_time:
                        valid_cred = True
                    else:
                        id_manager.delete_credential(cred)
                except (ValueError, KeyError):
                    id_manager.delete_credential(cred)

            if not valid_cred:
                # Generate a new secret
                secret = base64.b32encode(os.urandom(20)).decode('utf-8')
                blob = {
                    'secret': secret,
                    'created': str(timezone.now()),
                }
                id_manager.add_credential(
                    self.user_id, 'totp-draft', json.dumps(blob))

                self.add_note("Added new 'totp-draft' secret key.")
            else:
                self.add_note("There is already a valid 'totp-draft' key.")

    def _post_approve(self):
        self._validate()
        self.set_token_fields(['passcode'])
        self.action.need_token = True
        self.action.save()

    def _submit(self, token_data):
        self._validate()

        if not self.valid:
            return

        id_manager = user_store.IdentityManager()
        if self.delete:
            secret = self.get_credential_secret()

            if not secret:
                # TOTP already removed
                return

            if self.validate_passcode(secret, token_data.get('passcode')):
                id_manager.clear_credential_type(self.user_id, 'totp')
                self.add_note("TOTP secret key removed.")
                self.action.valid = True
            else:
                self.add_note("TOTP Passcode invalid, secret not removed.")
                self.action.valid = False

                return {'errors': 'Invalid TOTP passcode'}
        else:
            secret = self.get_credential_secret()

            if not secret:
                self.action.valid = False
                self.action.save()
                return {'errors': 'TOTP Secret Removed'}

            if self.validate_passcode(secret, token_data.get('passcode')):
                id_manager.clear_credential_type(self.user_id, 'totp-draft')
                id_manager.add_credential(self.user_id, 'totp', secret)

                self.action.valid = True
                self.add_note("New TOTP secret key enabled.")
            else:
                self.add_note("TOTP Passcode invalid")
                # Need some better way to provide this upwards
                self.action.valid = False
                return {'errors': 'Invalid TOTP passcode'}

    def get_credential_secret(self):
        id_manager = user_store.IdentityManager()
        cred_type = 'totp' if self.delete else 'totp-draft'
        credentials = id_manager.list_credentials(self.user_id, cred_type)

        if len(credentials) < 1:
            self.add_note("No Credentials found.")
            return False
        elif len(credentials) > 1:
            self.add_note("More than one credential found.")
            if cred_type == 'totp-draft':
                id_manager.clear_credential_type(self.user_id, 'totp-draft')
            return False

        if cred_type == 'totp':
            return credentials[0].blob

        try:
            return json.loads(credentials[0].blob)['secret']
        except (TypeError, ValueError, KeyError):
            self.add_note("Issues parsing credential.")
            return False

    def validate_passcode(self, secret, passcode):
        if not passcode or not secret:
            return False

        if generate_totp_passcode(secret) == str(passcode):
            return True
        else:
            return False


register_action_class(
    EditMFAAction, serializers.EditMFASerializer)
