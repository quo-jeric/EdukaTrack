from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'school_admin', 'School Admin'
        TEACHER = 'teacher', 'Teacher'
        STUDENT = 'student', 'Student'
    
    # Primary identifier of the user. Cannot be changed. Used for login authentication.
    school_id = models.CharField(
        max_length=50,
        unique=True,
        # editable=False,
        primary_key=True,
        help_text="Unique institutional identifier (e.g. S-0001)"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    # Additional name fields (first_name and last_name is already defined in AbstractUser class).
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    suffix = models.CharField(max_length=20, blank=True, null=True)

    gender = models.CharField(max_length=20, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)

    # Contact information 
    email = models.EmailField(max_length=125, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Address 
    street_address = models.CharField(max_length=255, blank=True, null=True)
    barangay = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)

    # Audit tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Removes the username field from AbstractUser. 
    username = None

    # Set the username field to be the same as the school_id field. 
    USERNAME_FIELD = 'school_id'
    # Required fields
    REQUIRED_FIELDS = ['email']

    # Add a method to get the full name of the user.
    def get_full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name, self.suffix]
        return " ".join(p for p in parts if p)

class SchoolAdmin(models.Model):
    class AdminType(models.TextChoices):
        PRINCIPAL = 'principal', 'Principal'
        STAFF = 'staff', 'Staff'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='school_admin')
    admin_type = models.CharField(max_length=20, choices=AdminType.choices, default=AdminType.STAFF)
    position_title = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['admin_type'],
                condition=models.Q(admin_type='principal'),
                name='unique_principal'
            )
        ]

    def clean(self):
        if self.admin_type == self.admin_type.PRINCIPAL:
            existing = SchoolAdmin.objects.filter(
                admin_type=self.AdminType.PRINCIPAL
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError('Only one principal is allowed.')
    
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)
    specialization = models.CharField(max_length=255)
    qualifications = models.TextField()
    employment_type = models.CharField(max_length=50)
    office_location = models.CharField(max_length=100)
    office_hours = models.CharField(max_length=100)
    hire_date = models.DateField()
    
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    program = models.ForeignKey('Program', on_delete=models.SET_NULL, null=True)
    admission_date = models.DateField()

class Enrollment(models.Model):
    class Term(models.TextChoices):
        FIRST = '1st_semester', '1st Semester'
        SECOND = '2nd_semester', '2nd Semester'
        SUMMER = 'summer_term', 'Summer Term'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ENROLLED = 'enrolled', 'Enrolled'
        DENIED = 'denied', 'Denied'
        DROPPED = 'dropped', 'Dropped'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.CharField(max_length=9, help_text="e.g. 2026-2027") 
    term = models.CharField(max_length=20, choices=Term.choices)
    year_level = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    section = models.CharField(max_length=50)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True) # When they requested enrollment
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevents a student from enrolling twice in the exact same term & year
        constraints = [
            models.UniqueConstraint(
                fields=["student", "academic_year", "term"],
                name="unique_student_enrollment"
            )
        ]

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

    