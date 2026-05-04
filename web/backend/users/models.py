from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager

# Create your models here.

class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )

    name = models.CharField(max_length=255, blank=True)
    avatar = models.URLField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        # Nếu là tài khoản tạo từ Terminal (superuser), tự động phong thành ADMIN và cấp quyền staff
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.is_staff = True
        # Logic cũ của bạn cho những user bình thường
        elif self.role == self.Role.ADMIN:
            self.is_staff = True
        else:
            self.is_staff = False
            
        super().save(*args, **kwargs)
    user_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    def __str__(self):
        return self.email