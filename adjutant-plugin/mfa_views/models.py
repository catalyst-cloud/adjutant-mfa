
from adjutant.api.v1.models import register_taskview_class

from mfa_views import views

register_taskview_class(r'^openstack/edit-mfa/?$', views.EditMFA)
