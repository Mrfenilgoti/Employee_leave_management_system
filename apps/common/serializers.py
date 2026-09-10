from rest_framework import serializers

from .models import EmployeeProfile


class EmployeeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = [
            "id",
            "user",
            "employee_id",
            "first_name",
            "last_name",
            "phone",
            "designation",
            "joining_date",
            "manager",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
        ]