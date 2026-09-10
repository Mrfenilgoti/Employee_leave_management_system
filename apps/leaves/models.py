from django.conf import settings
from django.db import models


class LeaveTypeChoice(models.TextChoices):
    CASUAL = "CASUAL", "Casual Leave"
    SICK = "SICK", "Sick Leave"
    PAID = "PAID", "Paid Leave"
    UNPAID = "UNPAID", "Unpaid Leave"


class LeaveStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"


class LeaveRequest(models.Model):

    # Employee who created the leave request
    # DB column: employee_id
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="leave_requests",
        limit_choices_to={
            "role": "EMPLOYEE",
        },
    )

    # Leave type
    leave_type = models.CharField(max_length=20,choices=LeaveTypeChoice.choices,default=LeaveTypeChoice.CASUAL,)
    start_date = models.DateField()
    end_date = models.DateField()

    # Calculated by backend
    total_days = models.DecimalField(max_digits=5,decimal_places=2,)

    # Employee's reason
    reason = models.TextField()

    # Employee's manager
    # Determined by backend
    # DB column: approver_id
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leave_requests",
    )

    # Manager's decision/comment
    approver_comment = models.TextField(blank=True,null=True,)

    # Set when manager approves/rejects
    manager_submitted_at = models.DateTimeField(blank=True,null=True,)

    # Set when employee cancels the request
    cancellation_reason = models.TextField(blank=True,null=True,)

    # Set when employee cancels the request
    employee_cancelled_at = models.DateTimeField(blank=True,null=True,)

    # Backend controlled
    status = models.CharField(max_length=20,choices=LeaveStatus.choices,default=LeaveStatus.PENDING,)

    # Automatically set when employee creates request
    employee_submitted_at = models.DateTimeField(auto_now_add=True,)

    # Automatically updated whenever record changes
    updated_at = models.DateTimeField(auto_now=True,
    )

    def __str__(self):
        return f"{self.employee.email} - {self.leave_type} ({self.status})"