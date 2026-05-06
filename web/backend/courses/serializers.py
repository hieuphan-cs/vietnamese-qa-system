from rest_framework import serializers
from .models import Course, Enrollment

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'code', 'name', 'teachers']

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'course', 'grade', 'date_enrolled']
    
class ExcelImportSerializer(serializers.Serializer):
    file = serializers.FileField(help_text="Upload file Excel (.xlsx, .xls)")