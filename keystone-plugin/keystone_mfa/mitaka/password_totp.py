# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Password and Time-based One-time Password (TOTP) Algorithm auth plugin.

The goal of this plugin is to combine username/password with a TOTP passcode
as a 2-factor solution when a TOTP credential is present for a given user.

This method works by replacing the password auth method, and using the password
field as a combination of <password>+<TOTP_passcode>.

TOTP is an algorithm that computes a one-time password from a shared secret
key and the current time.
TOTP is an implementation of a hash-based message authentication code (HMAC).
It combines a secret key with the current timestamp using a cryptographic hash
function to generate a one-time password. The timestamp typically increases in
30-second intervals, so passwords generated close together in time from the
same secret key will be equal.
"""

from oslo_log import log

from keystone import auth
from keystone.auth import plugins
from keystone.auth.plugins import totp
from keystone.common import dependency
from keystone import exception
from keystone.i18n import _


METHOD_NAME = 'password'

LOG = log.getLogger(__name__)

PASSCODE_LENGTH = 6


@dependency.requires('credential_api', 'identity_api')
class PasswordTOTP(auth.AuthMethodHandler):

    def authenticate(self, request, auth_payload, auth_context):
        """Try to authenticate against the identity backend and with TOTP."""
        user_info = plugins.UserAuthInfo.create(auth_payload, METHOD_NAME)

        # First we check if the given user_id has totp credentials
        credentials = self.credential_api.list_credentials_for_user(
            user_info.user_id, type='totp')

        if credentials:
            # If the user has credentials, strip passcode from password
            user_password = user_info.password[:-PASSCODE_LENGTH]
            auth_passcode = user_info.password[-PASSCODE_LENGTH:]
            valid_passcode = False
        else:
            # If the user has no TOTP credentials, skip TOTP.
            user_password = user_info.password
            valid_passcode = True

        try:
            self.identity_api.authenticate(
                request,
                user_id=user_info.user_id,
                password=user_password)
        except AssertionError:
            # authentication failed because of invalid username or password
            msg = _('Invalid username or password')
            raise exception.Unauthorized(msg)

        for credential in credentials:
            try:
                generated_passcode = totp._generate_totp_passcode(
                    credential['blob'])
                if auth_passcode == generated_passcode:
                    valid_passcode = True
                    break
            except (ValueError, KeyError):
                LOG.debug('No TOTP match; credential id: %s, user_id: %s',
                          credential['id'], user_info.user_id)
            except (TypeError):
                LOG.debug('Base32 decode failed for TOTP credential %s',
                          credential['id'])

        if not valid_passcode:
            # authentication failed because of invalid passcode
            msg = _('Invalid TOTP passcode')
            raise exception.Unauthorized(msg)

        auth_context['user_id'] = user_info.user_id
