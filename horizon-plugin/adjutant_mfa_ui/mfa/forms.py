# Copyright (c) 2016 Catalyst IT Ltd.
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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import ValidationError  # noqa
from django import http
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils

from adjutant_mfa_ui.api import adjutant


class AddMFAForm(forms.SelfHandlingForm):
    token_id = forms.Field()
    token_id.widget = forms.HiddenInput()
    details = forms.Field(widget=forms.HiddenInput())

    provisioning_url = forms.Field(widget=forms.HiddenInput(),
                                   help_text=_(
                                   "Scan this qrcode with "
                                   "a compatible 2 factor authentication app "
                                   " on your phone."))
    passcode = forms.CharField(
        label=_("Enter Passcode"))

    no_autocomplete = True

    @sensitive_variables('data')
    def handle(self, request, data):
        user_has_mfa = adjutant.user_has_mfa(request)

        if not user_has_mfa:
            try:
                submit_response = adjutant.token_submit(
                    request, data.pop('token_id'), data)
                if submit_response.status_code == 200:
                    response = http.HttpResponseRedirect(settings.LOGOUT_URL)
                    msg = _("MFA Setup. Please log in again to continue.")
                    utils.add_logout_reason(request, response, msg)
                    return response
                else:
                    messages.error(request,
                                   _('Unable to setup MFA. Your passcode '
                                     'may be incorrect.'))
            except Exception:
                exceptions.handle(request,
                                  _('Unable to setup MFA.'))
        else:
            messages.error(request, _('MFA already setup for this account.'))

        return False


class RemoveMFAForm(forms.SelfHandlingForm):
    passcode = forms.CharField(
        label=_("Enter Passcode"))
    no_autocomplete = True

    @sensitive_variables('data')
    def handle(self, request, data):
        user_has_mfa = adjutant.user_has_mfa(request)

        if user_has_mfa:
            try:
                submit_response = adjutant.remove_user_mfa(request,
                                                           data['passcode'])
                if submit_response.status_code == 200:
                    response = http.HttpResponseRedirect(settings.LOGOUT_URL)
                    msg = _("MFA Removed. Please log in again to continue.")
                    utils.add_logout_reason(request, response, msg)
                    return response
                elif submit_response.status_code == 400:
                    messages.error(request,
                                   _('Unable to remove MFA. This may be '
                                     'due to an incorrectly entered '
                                     'passcode.'))
                else:
                    messages.error(request,
                                   _('Unable to remove MFA.'))
            except Exception:
                exceptions.handle(request,
                                  _('Unable to remove MFA.'))
        else:
            messages.error(request, _('MFA not setup on this account.'))

        return http.HttpResponseRedirect(reverse("horizon:settings:mfa:index"))
