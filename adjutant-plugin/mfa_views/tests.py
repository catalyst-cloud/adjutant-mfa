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

import mock
import base64
import os
from six.moves.urllib import parse as urlparse

from rest_framework import status
from rest_framework.test import APITestCase

from adjutant.common.tests import fake_clients
from adjutant.common.tests.fake_clients import (
    FakeManager, setup_identity_cache)


from mfa_actions.utils import generate_totp_passcode


@mock.patch('adjutant.common.user_store.IdentityManager',
            FakeManager)
class MfaAPITests(APITestCase):

    def test_remove_mfa(self):
        """
        Ensure the reset user workflow goes as expected.
        Create task + create token, submit token.
        """

        user = fake_clients.FakeUser(
            name="test@example.com", password="test_password",
            email="test@example.com")
        cred = fake_clients.FakeCredential(
            user_id=user.id, cred_type='totp',
            blob=base64.b32encode(os.urandom(20)).decode('utf-8'))

        setup_identity_cache(users=[user], credentials=[cred])

        headers = {
            'project_name': "test_project",
            'project_id': "test_project_id",
            'roles': "_member_",
            'username': "test@example.com",
            'user_id': user.id,
            'authenticated': True
        }
        url = "/v1/openstack/edit-mfa"
        data = {}
        response = self.client.delete(url, data,
                                      format='json', headers=headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data.get('token_id')
        self.assertNotEqual(token, None)

        code = generate_totp_passcode(cred.blob)

        url = "/v1/tokens/" + token
        data = {'passcode': code}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_mfa(self):
        """
        Attempts to add mfa to a user account
        """

        user = fake_clients.FakeUser(
            name="test@example.com", password="test_password",
            email="test@example.com")

        setup_identity_cache(users=[user])

        headers = {
            'project_name': "test_project",
            'project_id': "test_project_id",
            'roles': "_member_",
            'username': "test@example.com",
            'user_id': user.id,
            'authenticated': True
        }
        url = "/v1/openstack/edit-mfa"

        response = self.client.post(url, {}, format='json', headers=headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        provisoning_uri = response.data.get('otpauth')
        token = response.data.get('token_id')

        self.assertNotEqual(provisoning_uri, None)

        secret = urlparse.parse_qs(
            urlparse.urlsplit(provisoning_uri).query).get('secret')[0]

        manager = FakeManager()
        creds = manager.list_credentials(user.id, 'totp-draft')
        self.assertEqual(secret, creds[0].blob)
        self.assertNotEqual(token, None)

        code = generate_totp_passcode(secret)
        url = "/v1/tokens/" + token
        data = {'passcode': code}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
