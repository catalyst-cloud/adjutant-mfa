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

from rest_framework.response import Response


from adjutant.api.models import Token
from adjutant.api import utils
from adjutant.api.v1.openstack import UserList
from adjutant.api.v1.tasks import TaskView
from adjutant.api.v1.utils import add_task_id_for_roles
from adjutant.common import user_store

from django.utils import timezone

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.twofactor.totp import TOTP

import base64
from django.conf import settings
import six


class EditMFA(TaskView):
    """
    A task for adding and removal of totp-based mfa from
    user accounts.
    """

    task_type = "edit_mfa"

    default_actions = ['EditMFAAction', ]

    @utils.authenticated
    def get(self, request):
        user_id = request.keystone_user['user_id']
        id_manager = user_store.IdentityManager()
        user = id_manager.get_user(user_id)
        has_mfa = bool(id_manager.list_credentials(user_id, 'totp'))

        return Response({'username': user.name,
                         'has_mfa': has_mfa})

    @utils.authenticated
    def post(self, request, format=None):
        """ Add MFA to an account """
        request.data['user_id'] = request.keystone_user['user_id']
        request.data['delete'] = False

        self.logger.info("(%s) - New EditMFA request." % timezone.now())
        processed, status = self.process_actions(request)

        errors = processed.get('errors', None)
        if errors:
            self.logger.info("(%s) - Validation errors with task." %
                             timezone.now())
            return Response(errors, status=status)

        token = Token.objects.filter(task=processed.get('task'))[0]
        response_dict = {
            'notes': processed.get('notes'),
            'otpauth': self.get_provisioning_uri(request.data['user_id']),
            'token_id': token.token}
        add_task_id_for_roles(request, processed, response_dict, ['admin'])

        return Response(response_dict, status=status)

    def get_provisioning_uri(self, user_id, cred_type='totp-draft'):
        id_manager = user_store.IdentityManager()
        secret = id_manager.get_credential_blob(user_id,
                                                'totp-draft')
        user_name = id_manager.get_user(user_id).name

        if isinstance(secret, six.text_type):
            secret = secret.encode('utf-8')

        while len(secret) % 8 != 0:
            secret = secret + b'='

        decoded = base64.b32decode(secret)

        totp = TOTP(decoded, 6, SHA1(), 30, backend=default_backend())
        try:
            company_name = settings.COMPANY_NAME
        except AttributeError:
            company_name = ""
        return totp.get_provisioning_uri(user_name, company_name)

    @utils.authenticated
    def delete(self, request, format=None):
        """ Remove MFA from account """
        request.data['user_id'] = request.keystone_user['user_id']
        request.data['delete'] = True

        self.logger.info("(%s) - New EditMFA request." % timezone.now())
        processed, status = self.process_actions(request)

        errors = processed.get('errors', None)
        if errors:
            self.logger.info("(%s) - Validation errors with task." %
                             timezone.now())
            return Response(errors, status=status)

        token = Token.objects.filter(task=processed.get('task'))[0]

        response_dict = {'notes': processed.get('notes'),
                         'token_id': token.token}

        add_task_id_for_roles(request, processed, response_dict, ['admin'])

        return Response(response_dict, status=status)


class UserListMFA(UserList):
    """Overrides User list to include an additional has_mfa field"""

    @utils.mod_or_admin
    def get(self, request):
        # TODO(amelia): Pick more finetuned way of dealing with this
        #               while we only want users who have persmissions
        #               to find users this way we also dont want to be
        #               making a million requests for this to keystone
        #               either.
        #               It may be faster to get all TOTP keystone
        #               credentials and to sort through them to get
        #               the relevant ones.

        response = super(UserListMFA, self).get(request)
        id_manager = user_store.IdentityManager()
        credentials = id_manager.list_credentials(None, 'totp')
        credential_dict = {}

        for credential in credentials:
            credential_dict[credential.user_id] = True

        for user in response.data['users']:
            if user.get('status') != 'Active':
                user['has_mfa'] = 'N/A'
            elif user.get('cohort') != 'Inherited':
                user['has_mfa'] = credential_dict.get(user['id'], False)
            else:
                user['has_mfa'] = ''

        return response
