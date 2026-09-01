# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'school_admin', 'School Admin'
        TEACHER = 'teacher', 'Teacher'
        STUDENT = 'student', 'Student'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

class SchoolAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='school_admin')
    employee_id = models.CharField(max_length=20, unique=True)

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)
    specialization = models.CharField(max_length=255)
    qualifications = models.TextField()
    employment_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='Active')
    office_location = models.CharField(max_length=100)
    office_hours = models.CharField(max_length=100)
    hire_date = models.DateField()
    
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    student_id = models.CharField(max_length=20, unique=True)
    program = models.ForeignKey('Program', on_delete=models.SET_NULL, null=True)
    year_level = models.IntegerField()
    term = models.CharField(max_length=20)
    section = models.CharField(max_length=50)
    admission_date = models.DateField()
    status = models.CharField(max_length=50)

class Department(models.Model):
    dept_code = models.CharField(max_length=20, unique=True)
    dept_name = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.dept_code} - {self.dept_name}"
    
class Program(models.Model):
    program_code = models.CharField(max_length=20, unique=True)
    program_name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.program_code} - {self.program_name}"

    