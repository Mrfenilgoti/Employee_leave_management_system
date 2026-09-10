from django.utils import timezone
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import (
    LeaveRequest,
    LeaveStatus,
)

from .serializers import (
    LeaveRequestSerializer,
    LeaveRequestActionSerializer,
)


class LeaveRequestCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:

            serializer = LeaveRequestSerializer(
                data=request.data,
                context={
                    "request": request
                }
            )

            serializer.is_valid(
                raise_exception=True
            )

            leave_request = serializer.save()

            return Response(
                {
                    "message": "Leave request submitted successfully.",
                    "data": LeaveRequestSerializer(
                        leave_request
                    ).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:

            return Response(
                {
                    "message": "Failed to submit leave request.",
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class AllLeaveRequestView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:

            user = request.user

            # ==========================================
            # 1. Check user role
            # ==========================================

            if user.role not in [
                "MANAGER",
                "MAIN_MANAGER",
            ]:

                return Response(
                    {
                        "message": (
                            "You do not have permission to "
                            "view leave requests."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # ==========================================
            # 2. MANAGER
            # ==========================================

            if user.role == "MANAGER":

                # Get only employees assigned to
                # the logged-in manager
                employee_leaves = (
                    LeaveRequest.objects
                    .filter(
                        employee__role="EMPLOYEE",
                        employee__manager=user,
                    )
                    .select_related(
                        "employee",
                        "approver",
                    )
                    .order_by(
                        "-employee_submitted_at"
                    )
                )

                employee_serializer = LeaveRequestSerializer(
                    employee_leaves,
                    many=True
                )

                return Response(
                    {
                        "message": (
                            "Assigned employee leave "
                            "requests fetched successfully."
                        ),

                        "employee_leaves": {
                            "count": employee_leaves.count(),
                            "data": employee_serializer.data,
                        },
                    },
                    status=status.HTTP_200_OK,
                )

            # ==========================================
            # 3. MAIN MANAGER
            # ==========================================

            if user.role == "MAIN_MANAGER":

                # All employee leaves
                employee_leaves = (
                    LeaveRequest.objects
                    .filter(
                        employee__role="EMPLOYEE"
                    )
                    .select_related(
                        "employee",
                        "approver",
                    )
                    .order_by(
                        "-employee_submitted_at"
                    )
                )

                # All manager leaves
                manager_leaves = (
                    LeaveRequest.objects
                    .filter(
                        employee__role="MANAGER"
                    )
                    .select_related(
                        "employee",
                        "approver",
                    )
                    .order_by(
                        "-employee_submitted_at"
                    )
                )

                employee_serializer = LeaveRequestSerializer(
                    employee_leaves,
                    many=True
                )

                manager_serializer = LeaveRequestSerializer(
                    manager_leaves,
                    many=True
                )

                return Response(
                    {
                        "message": (
                            "Leave requests fetched successfully."
                        ),

                        "employee_leaves": {
                            "count": employee_leaves.count(),
                            "data": employee_serializer.data,
                        },

                        "manager_leaves": {
                            "count": manager_leaves.count(),
                            "data": manager_serializer.data,
                        },
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as exc:

            return Response(
                {
                    "message": (
                        "Failed to fetch leave requests."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )



class LeaveRequestActionView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, leave_id):

        try:

            user = request.user

            # ==========================================
            # 1. Check user role
            # ==========================================

            if user.role not in [
                "MANAGER",
                "MAIN_MANAGER",
            ]:

                return Response(
                    {
                        "message": (
                            "You do not have permission to "
                            "approve or reject a leave request."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # ==========================================
            # 2. Get leave request
            # ==========================================

            try:

                leave_request = (
                    LeaveRequest.objects
                    .select_related(
                        "employee",
                        "approver",
                    )
                    .get(
                        id=leave_id
                    )
                )

            except LeaveRequest.DoesNotExist:

                return Response(
                    {
                        "message": "Leave request not found."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # ==========================================
            # 3. Check pending status
            # ==========================================

            if leave_request.status != LeaveStatus.PENDING:

                return Response(
                    {
                        "message": (
                            "Only pending leave requests "
                            "can be approved or rejected."
                        ),
                        "current_status": leave_request.status,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ==========================================
            # 4. Check assigned approver
            # ==========================================

            if leave_request.approver != user:

                return Response(
                    {
                        "message": (
                            "You are not the assigned approver "
                            "for this leave request."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # ==========================================
            # 5. Validate request body
            # ==========================================

            serializer = LeaveRequestActionSerializer(
                data=request.data
            )

            serializer.is_valid(
                raise_exception=True
            )

            # ==========================================
            # 6. Get validated data
            # ==========================================

            action = request.data.get("action")
            comment = request.data.get("comment", "")
            if comment is None:
                 comment = ""
                 comment = str(comment).strip()

            # ==========================================
            # 7. Approve / Reject
            # ==========================================

            if action == "APPROVE":

                leave_request.status = (
                    LeaveStatus.APPROVED
                )

                message = (
                    "Leave request approved successfully."
                )

            elif action == "REJECT":

                leave_request.status = (
                    LeaveStatus.REJECTED
                )

                message = (
                    "Leave request rejected successfully."
                )

            # ==========================================
            # 8. Save decision
            # ==========================================

            leave_request.approver_comment = comment

            leave_request.manager_submitted_at = (
                timezone.now()
            )

            leave_request.save(
                update_fields=[
                    "status",
                    "approver_comment",
                    "manager_submitted_at",
                    "updated_at",
                ]
            )

            # ==========================================
            # 9. Response
            # ==========================================

            return Response(
                {
                    "message": message,
                    "data": LeaveRequestSerializer(
                        leave_request
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            return Response(
                {
                    "message": (
                        "Failed to process leave request."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class OwnLeaveRequestView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:

            user = request.user

            status_filter = request.data.get("status")

            if not status_filter:

                return Response(
                    {
                        "message": "Status is required."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            status_filter = str(status_filter).upper().strip()

            # Allowed filters
            allowed_statuses = [
                "PENDING",
                "APPROVED",
                "REJECTED",
                "CANCELLED",
                "HISTORY",
            ]

            if status_filter not in allowed_statuses:

                return Response(
                    {
                        "message": "Invalid status.",
                        "allowed_values": allowed_statuses,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get only logged-in user's leaves
            leave_requests = (
                LeaveRequest.objects
                .filter(
                    employee=user
                )
                .select_related(
                    "employee",
                    "approver",
                )
                .order_by(
                    "-employee_submitted_at"
                )
            )

            # HISTORY → return all leaves
            if status_filter != "HISTORY":

                leave_requests = leave_requests.filter(
                    status=status_filter
                )

            serializer = LeaveRequestSerializer(
                leave_requests,
                many=True
            )

            return Response(
                {
                    "message": "Leave requests fetched successfully.",
                    "filter": status_filter,
                    "count": leave_requests.count(),
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            return Response(
                {
                    "message": "Failed to fetch leave requests.",
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

# ============================================================
# 5. OWN LEAVE BALANCE
# ============================================================

class OwnLeaveBalanceView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:

            user = request.user

            # =================================================
            # Only EMPLOYEE and MANAGER
            # =================================================

            if user.role not in [
                "EMPLOYEE",
                "MANAGER",
            ]:

                return Response(
                    {
                        "message": (
                            "Only employees and managers "
                            "can view their leave balance."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            # =================================================
            # Total leave balance
            # =================================================

            total_leaves = Decimal("4")

            # =================================================
            # Get approved leaves
            # =================================================

            approved_leaves = (
                LeaveRequest.objects
                .filter(
                    employee=user,
                    status=LeaveStatus.APPROVED,
                )
            )

            # =================================================
            # Calculate used leaves
            # =================================================

            used_leaves = Decimal("0")

            for leave in approved_leaves:

                used_leaves += leave.total_days

            # =================================================
            # Calculate remaining leaves
            # =================================================

            remaining_leaves = (
                total_leaves - used_leaves
            )

            # =================================================
            # Prevent negative balance
            # =================================================

            if remaining_leaves < Decimal("0"):

                remaining_leaves = Decimal("0")

            # =================================================
            # Response
            # =================================================

            return Response(
                {
                    "message": (
                        "Leave balance fetched successfully."
                    ),

                    "data": {
                        "user_id": user.id,
                        "email": user.email,
                        "role": user.role,
                        "total_leaves": total_leaves,
                        "remaining_leaves ": used_leaves,
                        "used_leaves": remaining_leaves,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            return Response(
                {
                    "message": (
                        "Failed to fetch leave balance."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )