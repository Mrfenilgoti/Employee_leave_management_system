from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserRole(models.TextChoices):
    EMPLOYEE = 'EMPLOYEE', 'Employee'
    MANAGER = 'MANAGER', 'Manager'
    MAIN_MANAGER = 'MAIN_MANAGER', 'Main Manager'


class CustomUserManager(BaseUserManager['User']):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.MAIN_MANAGER)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None

    email = models.EmailField('email address',unique=True)
    role = models.CharField(max_length=20,choices=UserRole.choices,default=UserRole.EMPLOYEE,)

    manager = models.ForeignKey('self',on_delete=models.SET_NULL,null=True,blank=True,related_name='employees',
                                limit_choices_to={
                                    'role': UserRole.MANAGER,
                                    },
                                )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()  # type: ignore

    @property
    def is_employee(self):
        return self.role == UserRole.EMPLOYEE

    @property
    def is_manager(self):
        return self.role == UserRole.MANAGER

    @property
    def is_main_manager(self):
        return self.role == UserRole.MAIN_MANAGER

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"  # type: ignore