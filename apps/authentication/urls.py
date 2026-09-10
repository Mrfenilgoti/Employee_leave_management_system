from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.leaves.views import (LeaveRequestActionView, 
                               OwnLeaveRequestView,
                               OwnLeaveBalanceView,
                               LeaveRequestCreateView,
                               AllLeaveRequestView,)

from .views import (AssignEmployeesToManagerView,
                    ChangePasswordView,
                    EmployeeListView,
                    LoginView,
                    LogoutView,
                    ManagerRegistrationView,
                    UserRegistrationView,
                    ManagerEmployeeListView,)

urlpatterns = [
    # Authentication URLs
    path("register/",UserRegistrationView.as_view(),name="register",),
    path("managers/register/",ManagerRegistrationView.as_view(),name="manager-register",),
    path("login/",LoginView.as_view(),name="login",),
    path("token/refresh/",TokenRefreshView.as_view(),name="token-refresh",),
    path("logout/",LogoutView.as_view(),name="logout",),
    path("change-password/", ChangePasswordView.as_view(),name="change-password",),
    
    # Leave Requests
    path("leave-requests/",LeaveRequestCreateView.as_view(),name="leave-request-create",),
    # Manager / Main Manager can view all leave requests
    path("leave-requests/all/",AllLeaveRequestView.as_view(),name="all-leave-requests",),
    # Employee List View
    path("employees/", EmployeeListView.as_view(), name="employee-list"),
    # Manager / Main Manager approves or rejects
    path("leave-requests/<int:leave_id>/action/",LeaveRequestActionView.as_view(),name="leave-request-action",),
    # Own leaves
    path("leave-requests/my/",OwnLeaveRequestView.as_view(),name="own-leave-requests",),
    # Own leave balance
    path("leave-balance/",OwnLeaveBalanceView.as_view(),name="own-leave-balance",),
    # Manager can assign employees to themselves
    path("manager/assign-employees/", AssignEmployeesToManagerView.as_view(),name="assign-employees-to-manager",),
    # Manager can view their employees
    path("manager/employees/",ManagerEmployeeListView.as_view(),name="manager-employees",),
]