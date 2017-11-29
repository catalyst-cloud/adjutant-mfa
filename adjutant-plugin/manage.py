import os
import sys
from adjutant import test_settings
from django.core.management import execute_from_command_line

test_settings.ADDITIONAL_APPS.append("mfa_actions")
test_settings.ADDITIONAL_APPS.append("mfa_views")

test_settings.ACTIVE_TASKVIEWS.append("EditMFA")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adjutant.settings")

execute_from_command_line(sys.argv)
