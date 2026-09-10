from django.conf import settings
from django.db import models


class EmployeeProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee_profile",)
    employee_id = models.CharField(max_length=50, unique=True,)
    first_name = models.CharField(max_length=150,)
    last_name = models.CharField(max_length=150,)
    phone = models.CharField(max_length=20,blank=True,)
    designation = models.CharField(max_length=150,blank=True,)
    joining_date = models.DateField(null=True,blank=True,)
    
    manager = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="team_members",
        limit_choices_to={
            "role": "MANAGER",
        },
    )

    created_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True,)

    
    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"