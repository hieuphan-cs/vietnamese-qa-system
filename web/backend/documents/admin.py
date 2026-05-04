from django.contrib import admin
from .models import Document # Đảm bảo tên class trong models.py của bạn là Document

admin.site.register(Document)