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
import six

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.twofactor.totp import TOTP

from django.conf import settings
from django.utils import timezone

from rest_framework.response import Response

from adjutant.api.models import Token, Task
from adjutant.api import utils
from adjutant.api.v1.openstack import UserList
from adjutant.api.v1.tasks import TaskView
from adjutant.api.v1.utils import add_task_id_for_roles
from adjutant.common import user_store


class EditMFA(TaskView):
    """
    A task for adding and removal of totp-based mfa from
    user accounts.
    """

    task_type = "edit_mfa"

    default_actions = ['EditMFAAction', ]

    cred_expiry = 15

    @utils.authenticated
    def get(self, request):
        user_id = request.keystone_user['user_id']
        id_manager = user_store.IdentityManager()
        user = id_manager.get_user(user_id)
        has_mfa = bool(id_manager.list_credentials(user_id, 'totp'))

        return Response({'username': user.name,
                         'has_mfa': has_mfa})

    def _reuse_existing_task(self, request, otpauth=True):
        class_conf = settings.TASK_SETTINGS.get(
            self.task_type, settings.DEFAULT_TASK_SETTINGS)

        expiry_time = timezone.now() - timedelta(
            minutes=int(
                class_conf.get('cred_expiry', self.cred_expiry)))

        project_mfa_tasks = Task.objects.filter(
            project_id=request.keystone_user['project_id'],
            keystone_user__icontains=request.keystone_user['user_id'],
            task_type=self.task_type,
            created_on__gt=expiry_time,
            completed=0,
            cancelled=0)

        if project_mfa_tasks.count() == 1:
            task = project_mfa_tasks[0]
            task_data = {}
            for action in task.actions:
                task_data.update(action.action_data)

            if task_data['delete'] == request.data['delete']:
                tokens = Token.objects.filter(task=task.uuid)
                if tokens.count() == 1:
                    token = tokens[0]
                    response_dict = {
                        'notes': 'Reusing existing task.',
                        'token_id': token.token}
                    if otpauth:
                        response_dict['otpauth'] = self.get_provisioning_uri(
                            request.data['user_id'])
                    return Response(response_dict, status=200)
        return None

    @utils.authenticated
    def post(self, request, format=None):
        """ Add MFA to an account """
        request.data['user_id'] = request.keystone_user['user_id']
        request.data['delete'] = False

        existing_task = self._reuse_existing_task(request)
        if existing_task is not None:
            self.logger.info(
                "(%s) - Existing EditMFA request." % timezone.now())
            return existing_task

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
        class_conf = settings.TASK_SETTINGS.get(self.task_type, {})

        id_manager = user_store.IdentityManager()
        creds = id_manager.list_credentials(user_id, cred_type)

        # NOTE(amelia): There will only be one as the action checks for
        #               other cases and marks them invalid
        secret = json.loads(creds[0].blob)['secret']

        user_name = id_manager.get_user(user_id).name

        if isinstance(secret, six.text_type):
            secret = secret.encode('utf-8')

        while len(secret) % 8 != 0:
            secret = secret + b'='

        decoded = base64.b32decode(secret)

        totp = TOTP(decoded, 6, SHA1(), 30, backend=default_backend())

        cloud_name = class_conf.get('cloud_name')
        return totp.get_provisioning_uri(user_name, cloud_name)

    @utils.authenticated
    def delete(self, request, format=None):
        """ Remove MFA from account """
        request.data['user_id'] = request.keystone_user['user_id']
        request.data['delete'] = True

        existing_task = self._reuse_existing_task(request, otpauth=False)
        if existing_task is not None:
            self.logger.info(
                "(%s) - Existing EditMFA request." % timezone.now())
            return existing_task

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
