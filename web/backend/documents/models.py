from django.db import models
from django.conf import settings
import os


# Create your models here.
class Document(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING'
        PROCESSING = 'PROCESSING'
        READY = 'READY'
        FAILED = 'FAILED'

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=10, blank=True)
    
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    
    #Liên kết với Course
    course = models.ForeignKey('courses.Course',on_delete=models.CASCADE,null=True, blank=True,related_name='documents')
    
    #Liên kết với User
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents')
    
    checksum = models.CharField(max_length=64, unique=True, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
