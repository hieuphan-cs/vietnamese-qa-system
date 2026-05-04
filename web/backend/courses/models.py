from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()
class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    
    teachers = models.ManyToManyField(User, related_name='teaching_courses',limit_choices_to={'role': User.Role.TEACHER})
    
    students = models.ManyToManyField(User, related_name='enrolled_courses',through='Enrollment',limit_choices_to={'role': User.Role.STUDENT})
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'})
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    date_enrolled = models.DateTimeField(auto_now_add=True)
    
    grade = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.email} học {self.course.code}"
