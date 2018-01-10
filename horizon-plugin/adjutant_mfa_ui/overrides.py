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

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.dashboards.project.api_access import tables
from openstack_dashboard.dashboards.project.api_access import views

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
