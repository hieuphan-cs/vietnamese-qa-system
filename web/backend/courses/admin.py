from django.contrib import admin
from .models import Course, Enrollment  # 1. Thêm Enrollment vào chỗ import này

class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',) 

admin.site.register(Course, CourseAdmin)
admin.site.register(Enrollment)  