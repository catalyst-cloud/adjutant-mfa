# Copyright (c) 2017 Catalyst IT Ltd.
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
from adjutant_mfa_ui import api
from adjutant_mfa_ui.mfa import forms as mfa_forms

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import views
from horizon.utils import memoized

from openstack_auth import utils

from openstack_dashboard.dashboards.project.api_access import views as a_views

import logging

from six.moves.urllib import parse
LOG = logging.getLogger(__name__)


def update_mfa_router(request, *args, **kwargs):
    """Routes requests to the correct view, based on submission parameters."""
    try:
        user_has_mfa = api.adjutant.user_has_mfa(request)
    except Exception:
        return ErrorMFAView.as_view()(request, *args, **kwargs)

    if user_has_mfa:
        return RemoveMFAView.as_view()(request, *args, **kwargs)
    else:
        return AddMFAView.as_view()(request, *args, **kwargs)


def download_rc_file_mfa(request):
    template = 'mfa/openrc_v3_mfa.sh.template'
    context = a_views._get_openrc_credentials(request)

    # make v3 specific changes
    context['user_domain_name'] = request.user.user_domain_name
    try:
        project_domain_id = request.user.token.project['domain_id']
    except KeyError:
        project_domain_id = ''
    context['project_domain_id'] = project_domain_id
    # sanity fix for removing v2.0 from the url if present
    context['auth_url'], _ = utils.fix_auth_url_version_prefix(
        context['auth_url'])
    context['os_identity_api_version'] = 3
    context['os_auth_version'] = 3
    return a_views._download_rc_file_for_template(request, context, template)


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
            details = parse.parse_qs(
                parse.urlparse(task['otpauth']).query)
            data = {'provisioning_url': task['otpauth'],
                    'token_id': task['token_id'],
                    'details': details,
                    }
            return data


class ErrorMFAView(views.HorizonTemplateView):
    page_title = _("Cannot access MFA details")
    template_name = 'settings/mfa/error.html'
