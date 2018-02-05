# Copyright (c) 2016 Catalyst IT Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging

from adjutant_ui.api.adjutant import delete
from adjutant_ui.api.adjutant import get
from adjutant_ui.api.adjutant import post
from adjutant_ui.api.adjutant import token_submit

import collections

LOG = logging.getLogger(__name__)

USER = collections.namedtuple('User',
                              ['id', 'name', 'email', 'has_mfa',
                               'roles', 'inherited_roles', 'cohort', 'status'])


def user_has_mfa(request):
    headers = {"Content-Type": "application/json",
               'X-Auth-Token': request.user.token.id}

    data = get(request, 'openstack/edit-mfa', headers=headers).json()
    return bool(data['has_mfa'])


def add_user_mfa(request):
    headers = {"Content-Type": "application/json",
               'X-Auth-Token': request.user.token.id}

    return post(request, 'openstack/edit-mfa',
                data=json.dumps({}), headers=headers)


def remove_user_mfa(request, passcode):
    headers = {"Content-Type": "application/json",
               'X-Auth-Token': request.user.token.id}

    initail_response = delete(request, 'openstack/edit-mfa',
                              data=json.dumps({}), headers=headers)

    if initail_response.status_code != 200:
        return initail_response
    token = initail_response.json()['token_id']

    return token_submit(request, token, {'passcode': passcode})


def user_list_mfa(request):
    users = []
    try:
        headers = {'Content-Type': 'application/json',
                   'X-Auth-Token': request.user.token.id}
        resp = json.loads(get(request, 'openstack/users',
                              headers=headers).content)

        for user in resp['users']:
            # NOTE(adriant): Horizon doesn't like two objects with the
            # same id, so we make the id different since the 'Inherited'
            # cohort here will never need to be referenced by id.
            if user['cohort'] == "Inherited":
                user_id = user['id'] + user['cohort']
            else:
                user_id = user['id']
            users.append(
                USER(
                    id=user_id,
                    name=user['name'],
                    email=user['email'],
                    roles=user['roles'],
                    inherited_roles=user['inherited_roles'],
                    status=user['status'],
                    cohort=user['cohort'],
                    has_mfa=user.get('has_mfa', ''),
                )
            )
    except Exception as e:
        LOG.error(e)
        raise
    return users
