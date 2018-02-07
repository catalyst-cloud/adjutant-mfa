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

from adjutant_mfa_ui.api import adjutant

from adjutant_ui.content.project_users import tables as user_tables
from adjutant_ui.content.project_users import views as user_views

from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.dashboards.project.api_access import tables
from openstack_dashboard.dashboards.project.api_access import views

from horizon import exceptions
from horizon.tables import Column
from horizon.tables import LinkAction


class DownloadOpenRCMFA(LinkAction):
    name = "download_openrc_mfa"
    verbose_name = _("OpenStack RC File (Identity API v3, MFA Enabled)")
    verbose_name_plural = _("OpenStack RC File (Identity API v3, MFA Enabled)")
    icon = "download"
    url = reverse_lazy("horizon:settings:mfa:openrc")


class MFAEndpointsTable(tables.EndpointsTable):
    class Meta(tables.EndpointsTable.Meta):
        table_actions_menu = tables.EndpointsTable.Meta.table_actions_menu \
            + (DownloadOpenRCMFA, )


views.IndexView.table_class = MFAEndpointsTable


class MFAUserTable(user_tables.UsersTable):
    has_mfa = Column('has_mfa', verbose_name=_('MFA Enabled'))

    class Meta(object):
        name = 'users'
        row_class = user_tables.UpdateUserRow
        verbose_name = _('Users')
        columns = ('id', 'name', 'email', 'roles', 'inherited_roles', 'status',
                   'cohort', 'has_mfa')
        table_actions = (user_tables.CohortFilter, user_tables.InviteUser,
                         user_tables.RevokeUser)
        row_actions = (user_tables.UpdateUser, user_tables.ResendInvitation,
                       user_tables.RevokeUser)
        multi_select = True


def get_mfa_user_data(self):
    try:
        return adjutant.user_list_mfa(self.request)
    except Exception:
        exceptions.handle(self.request, _('Failed to list users.'))
        return []


if getattr(settings, "SHOW_MFA_ENABLED_IN_USER_LIST", False):
    user_views.UsersView.table_class = MFAUserTable
    user_views.UsersView.get_data = get_mfa_user_data
