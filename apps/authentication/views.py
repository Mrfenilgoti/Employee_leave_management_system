from django.contrib.sites import managers
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from typing import cast

from apps.authentication.models import UserRole
from apps.authentication.permission import IsManager
from .models import User, UserRole

from .serializers import (
    ChangePasswordSerializer,
    EmployeeSerializer,
    LoginSerializer,
    LogoutSerializer,
    UserRegistrationSerializer,
    AssignEmployeesToManagerSerializer,
    ManagerRegistrationSerializer,
)

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(
                data=request.data
            )

            serializer.is_valid(
                raise_exception=True
            )

            serializer.save()

            return Response(
                {
                    "message": "User registered successfully."
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            return Response(
                {
                    "message": "Registration failed.",
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class ManagerRegistrationView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:

            if request.user.role != UserRole.MAIN_MANAGER:

                return Response(
                    {
                        "message": (
                            "Only main manager can "
                            "register a manager."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = ManagerRegistrationSerializer(
                data=request.data
            )

            serializer.is_valid(
                raise_exception=True
            )

            serializer.save()

            manager_email = request.data.get("email")

            manager = User.objects.get(
                email=manager_email
            )

            return Response(
                {
                    "message": "Manager registered successfully.",
                    "manager": {
                        "id": int(manager.pk),
                        "email": manager_email,
                        "role": UserRole.MANAGER,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:

            return Response(
                {
                    "message": "Failed to register manager.",
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify that the provided credentials belong to the authenticated user
        user = authenticate(email=email, password=password)
        if user is None or user != request.user:
            return Response(
                {"error": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Blacklist all outstanding tokens for this user automatically
        try:
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass  # Fallthrough if token_blacklist model is not used

        return Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        assert isinstance(data, dict)  # Informs Pylance that data is a non-null dict

        email = data["email"]
        old_password = data["old_password"]
        new_password = data["new_password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"message": "Invalid email or old password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not check_password(old_password, user.password):
            return Response(
                {"message": "Invalid email or old password."},
                status=status.HTTP_401_UNAUTHORIZED,    
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )

class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        user = request.user

        # If Main Manager: Return both employees and managers
        if user.is_main_manager:
            employees = User.objects.filter(role=UserRole.EMPLOYEE)
            managers = User.objects.filter(role=UserRole.MANAGER)

            return Response(
                {
                    "employee_count": employees.count(),
                    "manager_count": managers.count(),
                    "employees": EmployeeSerializer(employees, many=True).data,
                    "managers": EmployeeSerializer(managers, many=True).data,
                },
                status=status.HTTP_200_OK,
            )

        # If Manager: Return only employees
        employees = User.objects.filter(role=UserRole.EMPLOYEE)
        return Response(
            {
                "employee_count": employees.count(),
                "employees": EmployeeSerializer(employees, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

class AssignEmployeesToManagerView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request):

        try:

            # =================================================
            # Logged-in user
            # =================================================

            user = request.user

            # =================================================
            # Only MAIN_MANAGER can access
            # =================================================

            if user.role != UserRole.MAIN_MANAGER:

                return Response(
                    {
                        "message": (
                            "Only main manager can assign "
                            "employees to a manager."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # =================================================
            # Validate request data
            # =================================================

            serializer = AssignEmployeesToManagerSerializer(
                data=request.data
            )

            serializer.is_valid(
                raise_exception=True
            )

            # =================================================
            # Get values from request
            # =================================================

            manager_id = request.data.get(
                "manager_id"
            )

            employee_ids = request.data.get(
                "employee_ids"
            )

            # =================================================
            # Convert manager ID
            # =================================================

            manager_id = int(
                manager_id
            )

            # =================================================
            # Get manager
            # =================================================

            manager = User.objects.get(
                id=manager_id,
                role=UserRole.MANAGER,
            )

            # =================================================
            # Assign employees
            # =================================================

            updated_count = User.objects.filter(
                id__in=employee_ids,
                role=UserRole.EMPLOYEE,
            ).update(
                manager_id=manager_id
            )

            # =================================================
            # Get assigned employees
            # =================================================

            employees = User.objects.filter(
                id__in=employee_ids,
                role=UserRole.EMPLOYEE,
                manager_id=manager_id,
            ).values(
                "id",
                "email",
                "role",
                "manager_id",
            )

            # =================================================
            # Response
            # =================================================

            return Response(
                {
                    "message": (
                        "Employees assigned to manager "
                        "successfully."
                    ),

                    "manager": {
                        "id": manager_id,
                        "email": manager.email,
                        "role": UserRole.MANAGER,
                    },

                    "assigned_employee_count": (
                        updated_count
                    ),

                    "employees": list(
                        employees
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            return Response(
                {
                    "message": (
                        "Failed to assign employees "
                        "to manager."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class ManagerEmployeeListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:

            # =========================
            # Only MAIN_MANAGER
            # =========================

            if request.user.role != UserRole.MAIN_MANAGER:

                return Response(
                    {
                        "message": (
                            "Only main manager can view "
                            "manager and employee assignments."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # =========================
            # Get all managers
            # =========================

            manager_records = User.objects.filter(
    role=UserRole.MANAGER
).values(
    "id",
    "email",
    "role",
)

            manager_data = []

            # =========================
            # Get employees of each manager
            # =========================

            for manager in manager_records:

                manager_id = manager["id"]
                manager_email = manager["email"]
                manager_role = manager["role"]

                employees = User.objects.filter(
                    role=UserRole.EMPLOYEE,
                    manager_id=manager_id,
                ).values(
                    "id",
                    "email",
                    "role",
                )

                manager_data.append(
                    {
                        "manager_id": manager_id,
                        "manager_email": manager_email,
                        "manager_role": manager_role,
                        "employees": list(employees),
                    }
                )

            # =========================
            # Response
            # =========================

            return Response(
                {
                    "manager_count": manager_records.count(),
                    "managers": manager_data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            return Response(
                {
                    "message": (
                        "Failed to fetch manager "
                        "employee assignments."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )