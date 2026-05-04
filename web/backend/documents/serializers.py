from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):

    uploader_name = serializers.ReadOnlyField(source='uploaded_by.username')
    
    course_id = serializers.IntegerField(source='course.id', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'file', 'file_size', 'file_type', 'course_id',
            'status', 'uploader_name', 'created_at'
        ]
        read_only_fields = ['id', 'file_size', 'file_type', 'status', 'course_id', 'uploader_name']