from typing import Any, cast
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserRole


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            role=UserRole.EMPLOYEE,
            **validated_data,
        )

        return user
    
class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "is_active",
            "date_joined",
            "last_login",
        ]
        read_only_fields = fields
class LoginSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data: dict[str, Any] = super().validate(attrs)

        user = cast(User, self.user)

        data["user"] = {
            "id": user.pk,
            "email": user.email,
            "role": user.role,
        }

        return data

class LogoutSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

from rest_framework import serializers

from .models import User


class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    old_password = serializers.CharField(write_only=True, style={"input_type": "password"},)
    new_password = serializers.CharField(write_only=True,min_length=8,style={"input_type": "password"},)
    confirm_password = serializers.CharField(write_only=True,min_length=8,style={"input_type": "password"},)

    def validate(self, attrs):
        new_password = attrs["new_password"]
        confirm_password = attrs["confirm_password"]

        if new_password != confirm_password:
            raise serializers.ValidationError(
                {
                    "confirm_password": "New password and confirm password do not match."
                }
            )

        return attrs

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "role", "created_at", "updated_at"]

class AssignEmployeesToManagerSerializer(serializers.Serializer):

    manager_id = serializers.IntegerField()
    employee_ids = serializers.ListField(child=serializers.IntegerField(),allow_empty=False,)

    def validate_manager_id(self, value):

        try:

            manager = User.objects.get(id=value)

        except User.DoesNotExist:

            raise serializers.ValidationError("Manager does not exist.")

        if manager.role != UserRole.MANAGER:

            raise serializers.ValidationError("Selected user is not a manager.")

        return value

    def validate_employee_ids(self, value):

        if len(value) != len(set(value)):

            raise serializers.ValidationError("Duplicate employee IDs are not allowed.")

        employees = User.objects.filter(id__in=value)

        if employees.count() != len(value):

            raise serializers.ValidationError("One or more employee IDs do not exist.")

        non_employees = employees.exclude(role=UserRole.EMPLOYEE)

        if non_employees.exists():

            raise serializers.ValidationError("Only employees can be assigned to a manager.")

        return value

class ManagerRegistrationSerializer(serializers.Serializer):

    email = serializers.EmailField()

    password = serializers.CharField(write_only=True,min_length=8)

    def validate_email(self, value):

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")

        return value

    def create(self, validated_data):

        manager = User(email=validated_data["email"],role=UserRole.MANAGER,)
        manager.set_password(validated_data["password"])
        manager.save()

        return manager