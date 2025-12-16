from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    dept_code = db.Column(db.String(10), unique=True, nullable=False)
    dept_name = db.Column(db.String(255), nullable=False)
    dept_head_id = db.Column(db.Integer, db.ForeignKey('teachers.user_id', name='fk_department_head', use_alter=True))

class Program(db.Model):
    __tablename__ = 'programs'
    id = db.Column(db.Integer, primary_key=True)
    program_code = db.Column(db.String(20), unique=True, nullable=False)
    program_name = db.Column(db.String(255), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(125), unique=True, nullable=False)
    phone_number = db.Column(db.String(125))
    user_type = db.Column(db.String(20))
    street_address = db.Column(db.String(255))
    baranggay = db.Column(db.String(255))
    city = db.Column(db.String(100))
    province = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }

class Admin(User):
    __tablename__ = 'admins'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    admin_level = db.Column(db.String(50))
    
    __mapper_args__ = {'polymorphic_identity': 'admin'}

class Teacher(User):
    __tablename__ = 'teachers'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    specialization = db.Column(db.String(255))
    qualifications = db.Column(db.Text)
    employment_type = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Active')
    office_location = db.Column(db.String(100))
    office_hours = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    
    __mapper_args__ = {'polymorphic_identity': 'teacher'}

class Student(User):
    __tablename__ = 'students'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'))
    year_level = db.Column(db.Integer)
    term = db.Column(db.String(20))
    section = db.Column(db.String(50))
    admission_date = db.Column(db.Date)
    status = db.Column(db.String(50))
    
    __mapper_args__ = {'polymorphic_identity': 'student'}

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(20), unique=True, nullable=False)
    subject_name = db.Column(db.String(255), nullable=False)
    units = db.Column(db.Integer)
    description = db.Column(db.Text)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'))

class Prerequisite(db.Model):
    __tablename__ = 'prerequisites'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    prereq_subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(50), nullable=False)
    building = db.Column(db.String(100))
    floor = db.Column(db.Integer)
    capacity = db.Column(db.Integer)

class ClassSchedule(db.Model):
    __tablename__ = 'class_schedules'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.user_id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    day = db.Column(db.String(20))
    time_start = db.Column(db.String(20))
    time_end = db.Column(db.String(20))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    section = db.Column(db.String(10))
    semester = db.Column(db.String(50))
    school_year = db.Column(db.String(20))
    
    subject = db.relationship('Subject', backref='schedules')
    professor = db.relationship('Teacher', foreign_keys=[teacher_id])
    room_obj = db.relationship('Room', foreign_keys=[room_id])

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    schedule_id = db.Column(db.Integer, db.ForeignKey('class_schedules.id'))
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    semester = db.Column(db.String(50))
    school_year = db.Column(db.String(20))
    status = db.Column(db.String(50), default='Pending')

    student = db.relationship('User', foreign_keys=[student_id], backref='student_enrollments')
    schedule = db.relationship('ClassSchedule', backref='enrollments')

class EnrollmentRequest(db.Model):
    __tablename__ = 'enrollment_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.user_id'))
    class_sched_id = db.Column(db.Integer, db.ForeignKey('class_schedules.id'))
    request_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(50), default='pending')

class Grade(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'))
    assessment_name = db.Column(db.String(100))
    score = db.Column(db.Numeric(5, 2))
    remarks = db.Column(db.String(255))
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=True)

    enrollment = db.relationship('Enrollment', backref='grades')

class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('class_schedules.id'))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    max_points = db.Column(db.Integer, default=100)
    weight = db.Column(db.Numeric(5, 2), default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    schedule = db.relationship('ClassSchedule', backref='assignments')
    creator = db.relationship('User', foreign_keys=[created_by])

class TaskSubmission(db.Model):
    __tablename__ = 'task_submissions'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('assignments.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('students.user_id'))
    submission_date = db.Column(db.Date)
    content = db.Column(db.Text)
    grade = db.Column(db.Numeric(5, 2))

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'))
    date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(50))
    remarks = db.Column(db.String(255))
    
    enrollment = db.relationship('Enrollment', backref='attendances')

class UpdateRequest(db.Model):
    __tablename__ = 'update_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    request_type = db.Column(db.String(50))
    details = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    related_id = db.Column(db.Integer, nullable=True)
    related_type = db.Column(db.String(50), nullable=True)
    target_roles = db.Column(db.String(100), default='all')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='activities')

class TeacherSubjectPreference(db.Model):
    __tablename__ = 'teacher_subject_preferences'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.user_id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    teacher = db.relationship('Teacher', foreign_keys=[teacher_id])
    subject = db.relationship('Subject', backref='teacher_preferences')
