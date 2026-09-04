from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from datetime import date

class User(AbstractUser):
    """
    Contains information about the user, such as their name, role, contact 
    information, and address.
    """

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

    class Meta:
        db_table = 'users'

class SchoolAdmin(models.Model):
    """
    Inherits from the User model.
    Contains information about the school admin, such as their admin type, position title, etc.
    """

    class AdminType(models.TextChoices):
        PRINCIPAL = 'principal', 'Principal'
        STAFF = 'staff', 'Staff'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='school_admin')
    admin_type = models.CharField(max_length=20, choices=AdminType.choices, default=AdminType.STAFF)
    position_title = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'school_admin'
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
    """
    Inherits from the User model.
    Contains additional information about the teacher.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)
    specialization = models.CharField(max_length=255)
    qualifications = models.TextField()
    employment_type = models.CharField(max_length=50)
    office_location = models.CharField(max_length=100)
    office_hours = models.CharField(max_length=100)
    hire_date = models.DateField()

    class Meta:
        db_table = 'teachers'
    
class Student(models.Model):
    """
    Inherits from the User model.
    Contains additional information about the student.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    program = models.ForeignKey('Program', on_delete=models.SET_NULL, null=True)
    admission_date = models.DateField()

    class Meta:
        db_table = 'students'

class Enrollment(models.Model):
    """
    Represents the enrollment of a student in a specific academic year and term.
    """
    
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
        db_table = 'enrollments'

        # Prevents a student from enrolling twice in the exact same term & year
        constraints = [
            models.UniqueConstraint(
                fields=["student", "academic_year", "term"],
                name="unique_student_enrollment"
            )
        ]

class Department(models.Model):
    """
    Represents a department in the school.
    """

    dept_code = models.CharField(max_length=20, unique=True)
    dept_name = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.dept_code} - {self.dept_name}"

    class Meta:
        db_table = 'departments'
    
class Program(models.Model):
    """
    Represents a program offered by the school.
    """

    program_code = models.CharField(max_length=20, unique=True)
    program_name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.program_code} - {self.program_name}"

    class Meta:
        db_table = 'programs'

class Subject(models.Model):
    """
    Represents a subject offered by the school.
    """

    subject_code = models.CharField(max_length=20, unique=True)
    subject_name = models.CharField(max_length=255)
    units = models.IntegerField()
    description = models.TextField()

    programs = models.ManyToManyField(Program, through='ProgramSubject', related_name='subjects')
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True)
    
    class Meta:
        db_table = 'subjects'

class ProgramSubject(models.Model):
    """
    Junction model representing subjects to a specific program.
    """
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    # Context specific for this program's curriculum
    year_level = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    term = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 3)])
    is_elective = models.BooleanField(default=False)

    class Meta:
        db_table = 'program_subjects'
        constraints = [
            # Ensures a subject is only mapped once per program-year-term combination.
            models.UniqueConstraint(
                fields=['program', 'subject'],
                name='unique_program_subject'
            )
        ]
    
class Assignment(models.Model):
    """
    Represents an assignment given to students.
    """

    schedule = models.ForeignKey('ClassSchedule', on_delete=models.CASCADE, related_name='assignments')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_assignments')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    max_points = models.PositiveIntegerField(default=100)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def compute_weight_percentage(self):
        return self.weight / 100

    class Meta:
        db_table = 'assignments'
        ordering = ['created_at']    

class TaskSubmission(models.Model):
    """
    Represents a student's submission for an assignment.
    """

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(null=True, blank=True) # Null = not yet submitted
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'task_submissions'
        constraints = [
            models.UniqueConstraint(
                fields=['assignment', 'student'],
                name='unique_task_submission'
            )
        ]

class Grade(models.Model):
    """
    Represents grade given for student for term. 
    """
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='grade')
    midterm_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # Midterm grades
    final_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # Final grades
    computed_final_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # Computed final grade
    remarks = models.CharField(max_length=255, null=True, blank=True) # Remarks for the grade

    def compute_final_grade(self):
        if self.midterm_grade and self.final_grade:
            self.computed_final_grade = (self.midterm_grade + self.final_grade) / 2
            if self.computed_final_grade >= 75:
                self.remarks = "Passed"
            else:
                self.remarks = "Failed"
    
    def save(self, *args, **kwargs):
        self.compute_final_grade()
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'grades'

class Room(models.Model):
    """
    Represents a room in the school.
    """
    room_name = models.CharField(max_length=50)
    building = models.CharField(max_length=100)
    floor = models.IntegerField()
    capacity = models.IntegerField()
    
    class Meta:
        db_table = 'rooms'

class ClassSchedule(models.Model):
    """
    Represents the class schedule for a specific subject and teacher.
    """
    class Day(models.IntegerChoices):
        MONDAY = 1, 'Monday'
        TUESDAY = 2, 'Tuesday'
        WEDNESDAY = 3, 'Wednesday'
        THURSDAY = 4, 'Thursday'
        FRIDAY = 5, 'Friday'
        SATURDAY = 6, 'Saturday'
        SUNDAY = 7, 'Sunday'

    class Semester(models.TextChoices):
        FIRST = '1st_semester', '1st Semester'
        SECOND = '2nd_semester', '2nd Semester'
        SUMMER = 'summer_term', 'Summer Term'

    teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    room = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True)
    day = models.IntegerField(choices=Day.choices)
    time_start = models.TimeField()   # ← Critical fix
    time_end = models.TimeField()     # ← Critical fix
    section = models.CharField(max_length=50)
    semester = models.CharField(max_length=50, choices=Semester.choices)
    school_year = models.CharField(max_length=20)  # e.g. "2025-2026"

    class Meta:
        db_table = 'class_schedules'
        ordering = ['day', 'time_start']
        constraints = [
            models.UniqueConstraint(
                fields=["teacher", "day", "time_start", "time_end"],
                name="unique_schedule_collision"
            )
        ]

class Attendance(models.Model):
    """
    Represents the attendance of a student for a specific class schedule.
    """
    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT = 'absent', 'Absent'
        LATE = 'late', 'Late'
        EXCUSED = 'excused', 'Excused'

    enrollment = models.ForeignKey('Enrollment', on_delete=models.CASCADE)
    date = models.DateField(default=date.today) 
    status = models.CharField(max_length=20, choices=Status.choices)  
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'attendances'

