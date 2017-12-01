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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized

import logging

from adjutant_mfa_ui.mfa import forms as mfa_forms

from adjutant_mfa_ui import api

from six.moves.urllib import parse
LOG = logging.getLogger(__name__)


def update_mfa_router(request, *args, **kwargs):
    """Routes requests to the correct view, based on submission parameters.
    """
    user_has_mfa = api.adjutant.user_has_mfa(request)

    if user_has_mfa:
        return RemoveMFAView.as_view()(request, *args, **kwargs)
    else:
        return AddMFAView.as_view()(request, *args, **kwargs)


class RemoveMFAView(forms.ModalFormView):
    form_class = mfa_forms.RemoveMFAForm
    form_id = "add_mfa_view"
    modal_header = _("Remove MFA From your account")
    modal_id = "add_mfa_view"
    page_title = _("Remove MFA From your account")
    submit_label = _("Submit")
    submit_url = reverse_lazy("horizon:settings:mfa:index")
    template_name = 'mfa/remove.html'


class AddMFAView(forms.ModalFormView):
    form_class = mfa_forms.AddMFAForm
    form_id = "add_mfa_view"
    modal_header = _("Add MFA to your account")
    modal_id = "add_mfa_view"
    page_title = _("Add MFA to your account")
    submit_label = _("Submit")
    submit_url = reverse_lazy("horizon:settings:mfa:index")
    template_name = 'settings/mfa/add.html'
    _task = None

    @memoized.memoized_method
    def get_task(self):
        if self._task:
            return self._task
        try:
            self._task = api.adjutant.add_user_mfa(self.request).json()
            return self._task
        except Exception:
            msg = _('Unable to retrieve user.')
            url = reverse('horizon:settings:user:index')
            exceptions.handle(self.request, msg, redirect=url)

    def get_initial(self):
        # if initial information does not already exist
        if not self.request.POST.get('token_id'):
            task = self.get_task()
            secret = parse.parse_qs(
                parse.urlparse(task['otpauth']).query)['secret'][0]
            data = {'provisioning_url': task['otpauth'],
                    'token_id': task['token_id'],
                    'secret': secret,
                    }
            return data
