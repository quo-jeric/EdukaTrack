from app import create_app
from models import db, Admin, Student, Program, Department, User, Subject, ClassSchedule, Enrollment, Grade, Teacher, Room, Prerequisite, Assignment, TaskSubmission, UpdateRequest, EnrollmentRequest, Attendance, Activity, TeacherSubjectPreference
import bcrypt
from datetime import date, datetime, timedelta
from id_generator import id_generator

app = create_app()

with app.app_context():
    from sqlalchemy import text
    
    tables = ['activities', 'teacher_subject_preferences', 'task_submissions', 'attendance', 'grades', 'assignments', 'enrollment_requests', 
              'enrollments', 'class_schedules', 'prerequisites', 'subjects', 'rooms', 
              'students', 'teachers', 'admins', 'users', 'programs', 'departments', 'update_requests']
    
    for table in tables:
        try:
            db.session.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
        except:
            pass
    db.session.commit()
    db.create_all()

    print("=" * 60)
    print("Starting database seeding for College of Computer Science...")
    print("=" * 60)

    departments_data = [
        ('CCS', 'College of Computer Science', None),
        ('CIT', 'College of Information Technology', None),
        ('CIS', 'College of Information Systems', None),
        ('CCE', 'College of Computer Engineering', None),
        ('CDT', 'College of Digital Technology', None),
        ('GED', 'General Education Department', None),
    ]
    
    departments = {}
    for code, name, head in departments_data:
        dept = Department(dept_code=code, dept_name=name, dept_head_id=head)
        db.session.add(dept)
        db.session.flush()
        departments[code] = dept
    print(f'Created {len(departments)} departments')

    programs_data = [
        ('BSCS', 'Bachelor of Science in Computer Science', 'CCS'),
        ('BSIT', 'Bachelor of Science in Information Technology', 'CIT'),
        ('BSIS', 'Bachelor of Science in Information Systems', 'CIS'),
        ('BSCE', 'Bachelor of Science in Computer Engineering', 'CCE'),
        ('BSDS', 'Bachelor of Science in Data Science', 'CCS'),
        ('BSAI', 'Bachelor of Science in Artificial Intelligence', 'CCS'),
        ('BSCY', 'Bachelor of Science in Cybersecurity', 'CIT'),
        ('BSGD', 'Bachelor of Science in Game Development', 'CDT'),
    ]
    
    programs = {}
    for code, name, dept_code in programs_data:
        prog = Program(program_code=code, program_name=name, department_id=departments[dept_code].id)
        db.session.add(prog)
        db.session.flush()
        programs[code] = prog
    print(f'Created {len(programs)} programs')

    rooms_data = [
        ('CL101', 'Science Building', 1, 40),
        ('CL102', 'Science Building', 1, 40),
        ('CL103', 'Science Building', 1, 35),
        ('CL201', 'Science Building', 2, 50),
        ('CL202', 'Science Building', 2, 45),
        ('LAB-A', 'Computer Lab Building', 1, 30),
        ('LAB-B', 'Computer Lab Building', 1, 30),
        ('LAB-C', 'Computer Lab Building', 2, 25),
        ('LAB-D', 'Computer Lab Building', 2, 25),
        ('LEC-1', 'Lecture Hall', 1, 100),
        ('LEC-2', 'Lecture Hall', 1, 80),
        ('RM-301', 'Main Building', 3, 40),
        ('RM-302', 'Main Building', 3, 40),
    ]
    
    rooms = {}
    for name, building, floor, capacity in rooms_data:
        room = Room(room_name=name, building=building, floor=floor, capacity=capacity)
        db.session.add(room)
        db.session.flush()
        rooms[name] = room
    print(f'Created {len(rooms)} rooms')

    subjects_data = [
        ('CS101', 'Introduction to Computer Science', 3, 'Fundamentals of computing and programming concepts', 'BSCS'),
        ('CS102', 'Programming Fundamentals', 3, 'Basic programming concepts using Python', 'BSCS'),
        ('CS201', 'Object-Oriented Programming', 3, 'OOP concepts using Java/C++', 'BSCS'),
        ('CS202', 'Data Structures and Algorithms', 3, 'Arrays, linked lists, trees, graphs, sorting, searching', 'BSCS'),
        ('CS301', 'Database Management Systems', 3, 'Relational databases, SQL, normalization', 'BSCS'),
        ('CS302', 'Operating Systems', 3, 'Process management, memory, file systems', 'BSCS'),
        ('CS303', 'Computer Networks', 3, 'Network protocols, TCP/IP, network security', 'BSCS'),
        ('CS304', 'Software Engineering', 3, 'SDLC, agile methodologies, software design patterns', 'BSCS'),
        ('CS305', 'Web Development', 3, 'HTML, CSS, JavaScript, frontend frameworks', 'BSCS'),
        ('CS306', 'Mobile App Development', 3, 'Android and iOS development', 'BSCS'),
        ('CS401', 'Artificial Intelligence', 3, 'Search algorithms, machine learning basics', 'BSCS'),
        ('CS402', 'Machine Learning', 3, 'Supervised and unsupervised learning algorithms', 'BSCS'),
        ('CS403', 'Computer Graphics', 3, 'Rendering, 3D modeling, graphics algorithms', 'BSCS'),
        ('CS404', 'Cybersecurity Fundamentals', 3, 'Security principles, cryptography, ethical hacking', 'BSCS'),
        ('CS405', 'Cloud Computing', 3, 'Cloud architecture, AWS, Azure, GCP', 'BSCS'),
        ('CS406', 'Distributed Systems', 3, 'Distributed computing concepts and frameworks', 'BSCS'),
        ('CS407', 'Compiler Design', 3, 'Lexical analysis, parsing, code generation', 'BSCS'),
        ('CS408', 'Computer Architecture', 3, 'CPU design, memory hierarchy, I/O systems', 'BSCS'),
        ('IT101', 'IT Fundamentals', 3, 'Basic IT concepts and terminology', 'BSIT'),
        ('IT201', 'System Administration', 3, 'Linux/Windows server administration', 'BSIT'),
        ('IT202', 'Network Administration', 3, 'Network setup and management', 'BSIT'),
        ('IT301', 'Information Security', 3, 'Security policies and implementation', 'BSIT'),
        ('IT302', 'IT Project Management', 3, 'Project planning and execution', 'BSIT'),
        ('GE101', 'English Communication', 3, 'Written and oral communication skills', 'BSCS'),
        ('GE102', 'Mathematics for Computing', 3, 'Discrete math, logic, set theory', 'BSCS'),
        ('GE103', 'Calculus', 3, 'Differential and integral calculus', 'BSCS'),
        ('GE104', 'Linear Algebra', 3, 'Vectors, matrices, linear transformations', 'BSCS'),
        ('GE105', 'Statistics and Probability', 3, 'Statistical methods and probability theory', 'BSCS'),
        ('GE106', 'Physics for Engineers', 3, 'Mechanics, thermodynamics, electromagnetism', 'BSCS'),
        ('GE107', 'Technical Writing', 3, 'Documentation and technical report writing', 'BSCS'),
    ]
    
    subjects = {}
    for code, name, units, desc, prog_code in subjects_data:
        subj = Subject(
            subject_code=code, 
            subject_name=name, 
            units=units, 
            description=desc, 
            program_id=programs[prog_code].id
        )
        db.session.add(subj)
        db.session.flush()
        subjects[code] = subj
    print(f'Created {len(subjects)} subjects')

    prerequisites_data = [
        ('CS201', 'CS102'),
        ('CS202', 'CS201'),
        ('CS301', 'CS202'),
        ('CS302', 'CS202'),
        ('CS303', 'CS302'),
        ('CS304', 'CS202'),
        ('CS305', 'CS102'),
        ('CS306', 'CS305'),
        ('CS401', 'CS202'),
        ('CS402', 'CS401'),
        ('CS403', 'CS201'),
        ('CS404', 'CS303'),
        ('CS405', 'CS303'),
        ('CS406', 'CS302'),
        ('CS407', 'CS202'),
        ('CS408', 'CS302'),
        ('IT201', 'IT101'),
        ('IT202', 'IT201'),
        ('IT301', 'IT202'),
        ('IT302', 'IT201'),
    ]
    
    for subj_code, prereq_code in prerequisites_data:
        if subj_code in subjects and prereq_code in subjects:
            prereq = Prerequisite(subject_id=subjects[subj_code].id, prereq_subject_id=subjects[prereq_code].id)
            db.session.add(prereq)
    db.session.commit()
    print(f'Created {len(prerequisites_data)} prerequisites')

    admin_school_id = id_generator.generate_unique_id('A')
    admin_pwd = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
    
    admin = Admin(
        school_id=admin_school_id,
        password_hash=admin_pwd,
        first_name='System',
        last_name='Administrator',
        gender='Male',
        birthdate=date(1985, 5, 15),
        email='admin@edukatrack.edu',
        user_type='admin',
        admin_level='Super'
    )
    db.session.add(admin)
    db.session.flush()
    print(f'Admin created: {admin_school_id} / admin123')

    teachers_data = [
        ('John', 'Smith', 'Male', 'john.smith@edukatrack.edu', 'CCS', 'Computer Science', 'PhD in Computer Science'),
        ('Jane', 'Doe', 'Female', 'jane.doe@edukatrack.edu', 'CCS', 'Software Engineering', 'MS in Software Engineering'),
        ('Robert', 'Johnson', 'Male', 'robert.johnson@edukatrack.edu', 'CIT', 'Network Security', 'MS in Cybersecurity'),
        ('Maria', 'Garcia', 'Female', 'maria.garcia@edukatrack.edu', 'CCS', 'Artificial Intelligence', 'PhD in AI'),
        ('Michael', 'Brown', 'Male', 'michael.brown@edukatrack.edu', 'CCS', 'Data Science', 'PhD in Data Science'),
        ('Sarah', 'Wilson', 'Female', 'sarah.wilson@edukatrack.edu', 'CIS', 'Information Systems', 'MS in Information Systems'),
        ('David', 'Lee', 'Male', 'david.lee@edukatrack.edu', 'CCE', 'Computer Engineering', 'PhD in Computer Engineering'),
        ('Emily', 'Martinez', 'Female', 'emily.martinez@edukatrack.edu', 'GED', 'Mathematics', 'MS in Mathematics'),
    ]
    
    teachers = {}
    for i, (fname, lname, gender, email, dept_code, spec, qual) in enumerate(teachers_data):
        tid = id_generator.generate_unique_id('T')
        tpwd = bcrypt.hashpw(b'teacher123', bcrypt.gensalt()).decode('utf-8')
        
        teacher = Teacher(
            school_id=tid,
            password_hash=tpwd,
            first_name=fname,
            last_name=lname,
            gender=gender,
            birthdate=date(1975 + i, 3 + i, 10 + i),
            email=email,
            user_type='teacher',
            department_id=departments[dept_code].id,
            specialization=spec,
            qualifications=qual,
            employment_type='Full-time',
            office_location=f'{dept_code} Building Room {101 + i}',
            hire_date=date(2010 + i, 8, 1)
        )
        db.session.add(teacher)
        db.session.flush()
        teachers[f'{fname}_{lname}'] = teacher
        print(f'Teacher created: {tid} / teacher123 ({fname} {lname})')

    students_data = [
        ('James', 'Wilson', 'Male', 'james.wilson@student.edu', 'BSCS', 2, 'BSCS-2A'),
        ('Emily', 'Brown', 'Female', 'emily.brown@student.edu', 'BSCS', 1, 'BSCS-1A'),
        ('Michael', 'Davis', 'Male', 'michael.davis@student.edu', 'BSIT', 2, 'BSIT-2A'),
        ('Sarah', 'Miller', 'Female', 'sarah.miller@student.edu', 'BSCS', 3, 'BSCS-3A'),
        ('David', 'Anderson', 'Male', 'david.anderson@student.edu', 'BSCS', 1, 'BSCS-1B'),
        ('Jessica', 'Taylor', 'Female', 'jessica.taylor@student.edu', 'BSIT', 1, 'BSIT-1A'),
        ('Christopher', 'Thomas', 'Male', 'chris.thomas@student.edu', 'BSDS', 2, 'BSDS-2A'),
        ('Amanda', 'Jackson', 'Female', 'amanda.jackson@student.edu', 'BSAI', 3, 'BSAI-3A'),
        ('Daniel', 'White', 'Male', 'daniel.white@student.edu', 'BSCE', 2, 'BSCE-2A'),
        ('Jennifer', 'Harris', 'Female', 'jennifer.harris@student.edu', 'BSCY', 1, 'BSCY-1A'),
    ]
    
    students = {}
    for i, (fname, lname, gender, email, prog_code, year, section) in enumerate(students_data):
        sid = id_generator.generate_unique_id('S')
        spwd = bcrypt.hashpw(b'student123', bcrypt.gensalt()).decode('utf-8')
        
        student = Student(
            school_id=sid,
            password_hash=spwd,
            first_name=fname,
            last_name=lname,
            gender=gender,
            birthdate=date(2000 + (i % 4), (i % 12) + 1, (i % 28) + 1),
            email=email,
            phone_number=f'+63 912 345 67{i:02d}',
            street_address=f'{100 + i} Sample Street',
            baranggay=f'Barangay {i + 1}',
            city='Davao City',
            province='Davao del Sur',
            zip_code='8000',
            user_type='student',
            program_id=programs[prog_code].id,
            year_level=year,
            term='1st Semester',
            section=section,
            admission_date=date(2022, 8, 15),
            status='Active'
        )
        db.session.add(student)
        db.session.flush()
        students[f'{fname}_{lname}'] = student
        print(f'Student created: {sid} / student123 ({fname} {lname})')

    schedules_data = [
        ('John_Smith', 'CS102', 'LAB-A', 'BSCS-1A', 'MWF', '08:00', '09:30'),
        ('John_Smith', 'CS202', 'LAB-A', 'BSCS-2A', 'TTh', '10:00', '11:30'),
        ('Jane_Doe', 'CS201', 'LAB-B', 'BSCS-2A', 'MWF', '10:00', '11:30'),
        ('Jane_Doe', 'CS304', 'CL101', 'BSCS-3A', 'TTh', '13:00', '14:30'),
        ('Robert_Johnson', 'CS303', 'CL102', 'BSCS-3A', 'MWF', '13:00', '14:30'),
        ('Maria_Garcia', 'CS401', 'LAB-C', 'BSCS-4A', 'TTh', '08:00', '09:30'),
        ('Maria_Garcia', 'CS402', 'LAB-C', 'BSCS-4A', 'MWF', '15:00', '16:30'),
        ('Michael_Brown', 'CS301', 'LAB-D', 'BSDS-2A', 'TTh', '15:00', '16:30'),
        ('Sarah_Wilson', 'IT101', 'CL201', 'BSIT-1A', 'MWF', '08:00', '09:30'),
        ('Emily_Martinez', 'GE102', 'LEC-1', 'BSCS-1A', 'TTh', '10:00', '11:30'),
        ('Emily_Martinez', 'GE103', 'LEC-1', 'BSCS-1B', 'MWF', '10:00', '11:30'),
    ]
    
    schedules = {}
    for teacher_key, subj_code, room_name, section, day, start, end in schedules_data:
        if teacher_key in teachers and subj_code in subjects and room_name in rooms:
            sched = ClassSchedule(
                teacher_id=teachers[teacher_key].user_id,
                subject_id=subjects[subj_code].id,
                room_id=rooms[room_name].id,
                section=section,
                day=day,
                time_start=start,
                time_end=end,
                semester='1st Semester',
                school_year=str(date.today().year)
            )
            db.session.add(sched)
            db.session.flush()
            schedules[f'{teacher_key}_{subj_code}'] = sched
    print(f'Created {len(schedules)} class schedules')

    enrollment_data = [
        ('James_Wilson', 'John_Smith_CS102'),
        ('James_Wilson', 'John_Smith_CS202'),
        ('James_Wilson', 'Jane_Doe_CS201'),
        ('Emily_Brown', 'John_Smith_CS102'),
        ('Emily_Brown', 'Emily_Martinez_GE102'),
        ('Michael_Davis', 'Sarah_Wilson_IT101'),
        ('Sarah_Miller', 'Jane_Doe_CS304'),
        ('Sarah_Miller', 'Maria_Garcia_CS401'),
        ('David_Anderson', 'John_Smith_CS102'),
        ('David_Anderson', 'Emily_Martinez_GE103'),
        ('Jessica_Taylor', 'Sarah_Wilson_IT101'),
        ('Christopher_Thomas', 'Michael_Brown_CS301'),
        ('Amanda_Jackson', 'Maria_Garcia_CS401'),
        ('Amanda_Jackson', 'Maria_Garcia_CS402'),
    ]
    
    enrollments = {}
    for student_key, sched_key in enrollment_data:
        if student_key in students and sched_key in schedules:
            enr = Enrollment(
                student_id=students[student_key].user_id,
                schedule_id=schedules[sched_key].id,
                semester='1st Semester',
                school_year=str(date.today().year),
                status='Enrolled'
            )
            db.session.add(enr)
            db.session.flush()
            enrollments[f'{student_key}_{sched_key}'] = enr
    print(f'Created {len(enrollments)} enrollments')

    for key, enr in enrollments.items():
        import random
        score = random.uniform(75, 98)
        remarks = ['Excellent work', 'Good performance', 'Shows improvement', 'Satisfactory', 'Keep it up'][random.randint(0, 4)]
        grade = Grade(
            enrollment_id=enr.id,
            assessment_name='Final Grade',
            score=round(score, 2),
            remarks=remarks
        )
        db.session.add(grade)
    print(f'Created grades for all enrollments')

    assignments_data = [
        ('John_Smith_CS102', 'Python Basics Quiz', 'Complete the quiz on Python fundamentals', 7),
        ('John_Smith_CS102', 'Control Structures Exercise', 'Practice if-else and loops', 14),
        ('John_Smith_CS202', 'Linked List Implementation', 'Implement a doubly linked list', 10),
        ('John_Smith_CS202', 'Binary Search Tree', 'Create a BST with insert and search', 21),
        ('Jane_Doe_CS201', 'OOP Concepts Project', 'Build a class hierarchy for a library system', 14),
        ('Jane_Doe_CS304', 'SDLC Documentation', 'Write requirements for a project', 7),
        ('Maria_Garcia_CS401', 'AI Search Algorithms', 'Implement BFS and DFS', 14),
        ('Michael_Brown_CS301', 'SQL Queries Assignment', 'Write complex SQL queries', 10),
        ('Sarah_Wilson_IT101', 'IT Basics Report', 'Research report on cloud computing', 7),
    ]
    
    assignments = {}
    for sched_key, name, desc, days_due in assignments_data:
        if sched_key in schedules:
            sched = schedules[sched_key]
            assign = Assignment(
                schedule_id=sched.id,
                name=name,
                description=desc,
                due_date=date.today() + timedelta(days=days_due),
                max_points=100,
                created_by=sched.teacher_id
            )
            db.session.add(assign)
            db.session.flush()
            assignments[f'{sched_key}_{name[:10]}'] = assign
    print(f'Created {len(assignments)} assignments')

    first_student = students['James_Wilson']
    first_assignment = list(assignments.values())[0] if assignments else None
    if first_assignment:
        submission = TaskSubmission(
            task_id=first_assignment.id,
            student_id=first_student.user_id,
            submission_date=date.today(),
            content='Here is my completed Python basics quiz. I have answered all questions to the best of my ability.',
            grade=None
        )
        db.session.add(submission)
        
        submission2 = TaskSubmission(
            task_id=first_assignment.id,
            student_id=students['Emily_Brown'].user_id,
            submission_date=date.today(),
            content='My Python quiz submission. Looking forward to feedback!',
            grade=None
        )
        db.session.add(submission2)
        print('Created sample task submissions')

    today = date.today()
    for key, enr in list(enrollments.items())[:5]:
        import random
        statuses = ['Present', 'Present', 'Present', 'Late', 'Absent', 'Excused']
        for days_ago in [14, 12, 10, 7, 5, 3, 1]:
            att = Attendance(
                enrollment_id=enr.id,
                date=today - timedelta(days=days_ago),
                status=random.choice(statuses),
                remarks=''
            )
            db.session.add(att)
    print('Created attendance records')

    activities_data = [
        ('system', 'System initialized - Welcome to EdukaTrack', None, None, 'all'),
        ('assignment', 'New assignment added: Python Basics Quiz', first_assignment.id if first_assignment else None, 'assignment', 'student,teacher'),
        ('enrollment', 'New student enrollment processed', None, 'enrollment', 'admin'),
        ('grade', 'Grades updated for Programming Fundamentals', None, 'grade', 'student'),
        ('announcement', 'Enrollment period for 2nd semester is now open', None, None, 'all'),
    ]
    
    for act_type, desc, rel_id, rel_type, targets in activities_data:
        activity = Activity(
            user_id=admin.user_id,
            activity_type=act_type,
            description=desc,
            related_id=rel_id,
            related_type=rel_type,
            target_roles=targets,
            created_at=datetime.now() - timedelta(hours=len(activities_data) - activities_data.index((act_type, desc, rel_id, rel_type, targets)))
        )
        db.session.add(activity)
    print('Created initial activities')

    db.session.commit()
    
    print("=" * 60)
    print("Seeding complete!")
    print("=" * 60)
    print("\nLogin Credentials:")
    print(f"  Admin: {admin_school_id} / admin123")
    print("\n  Teachers (all use password: teacher123):")
    for key, teacher in teachers.items():
        print(f"    {teacher.school_id} - {teacher.first_name} {teacher.last_name}")
    print("\n  Students (all use password: student123):")
    for key, student in students.items():
        print(f"    {student.school_id} - {student.first_name} {student.last_name}")
