from adjutant.actions.v1.serializers import BaseUserIdSerializer
from rest_framework import serializers


class EditMFASerializer(BaseUserIdSerializer):
    delete = serializers.BooleanField(default=False)
