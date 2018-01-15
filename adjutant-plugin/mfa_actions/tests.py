# Copyright (C) 2015 Catalyst IT Ltd
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
import mock
import os


from adjutant.api.models import Task
from adjutant.common.tests.fake_clients import (FakeManager,
                                                setup_identity_cache)
from adjutant.common.tests import fake_clients
from adjutant.common.tests.utils import AdjutantTestCase

from mfa_actions.models import EditMFAAction
from mfa_actions.utils import generate_totp_passcode


@mock.patch('adjutant.common.user_store.IdentityManager',
            FakeManager)
class MFAActionTests(AdjutantTestCase):

    def test_add_mfa(self):
        """
        Existing user, valid tenant, correct passcode, mfa not previously
        setup
        """

        user = fake_clients.FakeUser(
            name="test@example.com", password="test_password",
            email="test@example.com")

        setup_identity_cache(users=[user])

        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={
                'roles': ['admin', 'project_mod'],
                'project_id': 'test_project_id',
                'project_domain_id': 'default',
                'id': user.id
            })

        data = {
            'user_id': user.id,
            'delete': False
        }

        action = EditMFAAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEqual(action.valid, True)

        action.post_approve()
        self.assertEqual(action.valid, True)

        manager = FakeManager()

        user_cred = manager.list_credentials

        self.assertEqual(len(user_cred(user.id, 'totp-draft')), 1)

        secret = user_cred(user.id, 'totp-draft')[0].blob

        passcode = generate_totp_passcode(secret)
        token_data = {'passcode': passcode}
        action.submit(token_data)
        self.assertEqual(action.valid, True)

        self.assertEqual(len(user_cred(user.id, 'totp')), 1)
        self.assertEqual(len(user_cred(user.id, 'totp-draft')), 0)

    def test_add_mfa_draft_removed(self):
        """
        Existing user, valid tenant, correct passcode, however the draft-totp
        code is removed between post_approve and token
        """

        user = fake_clients.FakeUser(
            name="test@example.com", password="test_password",
            email="test@example.com")

        setup_identity_cache(users=[user])

        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={
                'roles': ['admin', 'project_mod'],
                'project_id': 'test_project_id',
                'project_domain_id': 'default',
                'id': user.id
            })

        data = {
            'user_id': user.id,
            'delete': False
        }

        action = EditMFAAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEqual(action.valid, True)

        action.post_approve()
        self.assertEqual(action.valid, True)

        manager = FakeManager()

        user_draft = manager.list_credentials(
            user_id=user.id, cred_type='totp-draft')
        self.assertEqual(len(user_draft), 1)

        secret = user_draft[0].blob
        manager.clear_credential_type(user_id=user.id, cred_type='totp-draft')

        passcode = generate_totp_passcode(secret)
        token_data = {'passcode': passcode}
        return_data = action.submit(token_data)
        self.assertEqual(action.valid, False)

        self.assertEqual(return_data.get('errors'), 'TOTP Secret Removed')
        user_draft = manager.list_credentials(
            user_id=user.id, cred_type='totp-draft')
        self.assertEqual(len(user_draft), 0)

    def test_add_mfa_incorrect_passcode(self):

        user = fake_clients.FakeUser(
            name="test@example.com", password="test_password",
            email="test@example.com")

        setup_identity_cache(users=[user])

        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={
                'roles': ['admin', 'project_mod'],
                'project_id': 'test_project_id',
                'project_domain_id': 'default',
                'id': user.id
            })

        data = {
            'user_id': user.id,
            'delete': False
        }

        action = EditMFAAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEqual(action.valid, True)

        action.post_approve()
        self.assertEqual(action.valid, True)

        manager = FakeManager()

        user_draft = manager.list_credentials(
            user_id=user.id, cred_type='totp-draft')
        self.assertEqual(len(user_draft), 1)

        passcode = generate_totp_passcode(
            base64.b32encode(os.urandom(20)).decode('utf-8'))
        token_data = {'passcode': passcode}
        action.submit(token_data)
        self.assertEqual(action.valid, False)

        # Should not have updated the credentials
        user_totp = manager.list_credentials(user_id=user.id, cred_type='totp')
        self.assertEqual(len(user_totp), 0)

        user_draft = manager.list_credentials(
            user_id=user.id, cred_type='totp-draft')
        self.assertEqual(len(user_draft), 1)

    def test_remove_mfa(self):
        """
        Existing user, valid tenant, correct passcode, mfa setup
        """

        user = fake_clients.FakeUser(
            name="test@example.com", password="test_password",
            email="test@example.com")

        cred = fake_clients.FakeCredential(
            blob=base64.b32encode(os.urandom(20)).decode('utf-8'),
            cred_type='totp', user_id=user.id)

        setup_identity_cache(users=[user], credentials=[cred])

        task = Task.objects.create(
            ip_address="0.0.0.0",
            keystone_user={
                'roles': ['admin', 'project_mod'],
                'project_id': 'test_project_id',
                'project_domain_id': 'default',
                'id': user.id
            })

        data = {
            'user_id': user.id,
            'delete': True
        }

        action = EditMFAAction(data, task=task, order=1)

        action.pre_approve()
        self.assertEqual(action.valid, True)

        action.post_approve()
        self.assertEqual(action.valid, True)

        token_data = {'passcode': generate_totp_passcode(cred.blob)}
        action.submit(token_data)
        self.assertEqual(action.valid, True)

        manager = FakeManager()
        # Check for no creds
        user_totp = manager.list_credentials(user_id=user.id, cred_type='totp')
        self.assertEqual(len(user_totp), 0)

        user_draft = manager.list_credentials(
            user_id=user.id, cred_type='totp-draft')
        self.assertEqual(len(user_draft), 0)
