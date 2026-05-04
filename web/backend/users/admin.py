from django.contrib import admin
from .models import User # Thay bằng tên class User thực tế của bạn (VD: CustomUser)

admin.site.register(User)