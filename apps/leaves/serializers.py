from decimal import Decimal

from rest_framework import serializers

from .models import (LeaveRequest,LeaveStatus,)

class LeaveRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeaveRequest

        fields = [
            "id",
            "employee",
            "leave_type",
            "start_date",
            "end_date",
            "total_days",
            "reason",
            "approver",
            "approver_comment",
            "manager_submitted_at",
            "cancellation_reason",
            "employee_cancelled_at",
            "status",
            "employee_submitted_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "employee",
            "total_days",
            "approver",
            "approver_comment",
            "manager_submitted_at",
            "cancellation_reason",
            "employee_cancelled_at",
            "status",
            "employee_submitted_at",
            "updated_at",
        ]

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date > end_date:
            raise serializers.ValidationError({
                "end_date": "End date cannot be before start date."
            })

        return attrs

    def create(self, validated_data):
        request = self.context["request"]

        user = request.user

        # Employee → Manager
        if user.role == "EMPLOYEE":

            approver = user.manager

            if approver is None:
                raise serializers.ValidationError({
                    "employee": "You are not assigned to a manager."
                })

        # Manager → Main Manager
        elif user.role == "MANAGER":

            approver = user.manager

            if approver is None:
                raise serializers.ValidationError({
                    "manager": "You are not assigned to a main manager."
                })

        # Main Manager cannot submit
        elif user.role == "MAIN_MANAGER":

            raise serializers.ValidationError({
                "role": "Main manager cannot submit a leave request."
            })

        else:

            raise serializers.ValidationError({
                "role": "Invalid user role."
            })

        start_date = validated_data["start_date"]
        end_date = validated_data["end_date"]

        total_days = Decimal(
            (end_date - start_date).days + 1
        )

        leave_request = LeaveRequest.objects.create(
            employee=user,
            leave_type=validated_data["leave_type"],
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=validated_data["reason"],
            approver=approver,
            status=LeaveStatus.PENDING,
        )

        return leave_request
    

class LeaveRequestActionSerializer(serializers.Serializer):

    action = serializers.ChoiceField(
        choices=["APPROVE", "REJECT"]
    )

    comment = serializers.CharField(
        required=False,
        allow_blank=True
    )

    def validate(self, attrs):

        action = attrs.get("action")
        comment = attrs.get("comment", "").strip()

        # Comment is required when rejecting
        if action == "REJECT" and not comment:
            raise serializers.ValidationError(
                {
                    "comment": "Comment is required when rejecting a leave request."
                }
            )

        attrs["comment"] = comment

        return attrs
