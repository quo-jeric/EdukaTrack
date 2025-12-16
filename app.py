from dotenv import load_dotenv
load_dotenv()  # This loads the variables from .env
import os
import logging
import bcrypt
import json
from datetime import datetime, date
from collections import deque
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, User, Student, Subject, Program, Enrollment, Grade, ClassSchedule, Department, Assignment, Teacher, Room, Attendance, Prerequisite, TaskSubmission, UpdateRequest, EnrollmentRequest, Admin, Activity, TeacherSubjectPreference
from auth import auth_manager
from structures import EnrollmentQueue, DynamicArray, ConflictSet, HashMap, UniqueIDSet, StudentList
from id_generator import id_generator

logging.basicConfig(level=logging.DEBUG)

update_request_queue = deque()
enrollment_queue = EnrollmentQueue()
grade_array = DynamicArray()
conflict_set = ConflictSet()
active_sessions = {}
user_cache = HashMap()
student_id_set = UniqueIDSet()
student_list = StudentList()

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    session_secret = os.environ.get("SESSION_SECRET")
    if not session_secret:
        raise RuntimeError("SESSION_SECRET environment variable must be set")
    app.secret_key = session_secret
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    
    def load_queues():
        try:
            pending_updates = UpdateRequest.query.filter_by(status='pending').order_by(UpdateRequest.id).all()
            for req in pending_updates:
                update_request_queue.append(req.id)
            pending_enrs = EnrollmentRequest.query.filter_by(status='pending').order_by(EnrollmentRequest.id).all()
            for req in pending_enrs:
                enrollment_queue.enqueue(req.id)
        except Exception as e:
            logging.warning(f"Could not load queues: {e}")
    
    with app.app_context():
        db.create_all()
        load_queues()

    def verify_session_hybrid(token, required_role):
        try:
            payload = auth_manager.verify_token(token, required_role)
            return active_sessions.get(token), None
        except ValueError as e:
            return None, str(e)

    @app.route('/')
    def index():
        return render_template('login.html')
    
    @app.route('/pixelbook.gif')
    def serve_favicon():
        import os
        return send_from_directory(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pixelbook.gif')
    
    @app.route('/admin')
    def admin_dashboard():
        return render_template('admin/dashboard.html')
    
    @app.route('/teacher')
    def teacher_dashboard():
        return render_template('teacher/dashboard.html')
    
    @app.route('/student')
    def student_dashboard():
        return render_template('student/dashboard.html')

    @app.route('/api/status')
    def status():
        return jsonify({"status": "EdukaTrack Backend is running!"})

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.json
        school_id = data.get('schoolId', '').strip()
        password = data.get('password', '').encode('utf-8')
        role = data.get('role', '').lower()

        user = User.query.filter_by(school_id=school_id).first()

        if not user or user.user_type.lower() != role:
            return jsonify({"message": "Invalid credentials or role"}), 401
        
        if bcrypt.checkpw(password, user.password_hash.encode('utf-8')):
            token = auth_manager.create_token(user.school_id, user.user_type)
            active_sessions[token] = {
                "id": user.id,
                "role": user.user_type,
                "name": f"{user.first_name} {user.last_name}",
                "school_id": user.school_id
            }
            
            redirect_url = f"/{role}"
            
            return jsonify({
                "status": "success",
                "token": token,
                "name": f"{user.first_name} {user.last_name}",
                "redirect": redirect_url
            }), 200
        
        return jsonify({"message": "Invalid password"}), 401
    
    @app.route('/api/logout', methods=['POST'])
    def logout():
        data = request.json
        token = data.get('token')
        if auth_manager.logout(token):
            active_sessions.pop(token, None)
            return jsonify({"status": "success"}), 200
        return jsonify({"message": "Invalid token"}), 401

    @app.route('/api/verify-session', methods=['POST'])
    def verify_session():
        data = request.json
        token = data.get('token')
        required_role = data.get('role')
        try:
            payload = auth_manager.verify_token(token, required_role)
            session_data = active_sessions.get(token)
            if session_data:
                return jsonify({"status": "valid", "user": session_data['name'], "profile": {"school_id": session_data['school_id']}}), 200
            raise ValueError("Session not found")
        except ValueError as e:
            return jsonify({"message": str(e)}), 401

    @app.route('/api/admin/stats', methods=['GET'])
    def admin_stats():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        students_count = Student.query.count()
        teachers_count = Teacher.query.count()
        schedules_count = ClassSchedule.query.count()
        pending_requests = EnrollmentRequest.query.filter_by(status='pending').count()
        
        return jsonify({
            "students": students_count,
            "teachers": teachers_count,
            "schedules": schedules_count,
            "pending_requests": pending_requests
        }), 200

    @app.route('/api/admin/students', methods=['GET'])
    def get_students():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        students = Student.query.all()
        result = []
        for s in students:
            program = Program.query.get(s.program_id)
            result.append({
                "id": s.id,
                "school_id": s.school_id,
                "name": f"{s.first_name} {s.last_name}",
                "email": s.email,
                "program": program.program_code if program else "N/A",
                "year": s.year_level,
                "status": s.status or "Active"
            })
        return jsonify(result), 200

    @app.route('/api/admin/teachers', methods=['GET'])
    def get_teachers():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        teachers = Teacher.query.all()
        result = []
        for t in teachers:
            dept = Department.query.get(t.department_id)
            result.append({
                "id": t.id,
                "school_id": t.school_id,
                "name": f"{t.first_name} {t.last_name}",
                "email": t.email,
                "department": dept.dept_code if dept else "N/A",
                "specialization": t.specialization or "N/A",
                "status": "Active"
            })
        return jsonify(result), 200

    @app.route('/api/admin/schedules', methods=['GET'])
    def get_schedules():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        schedules = ClassSchedule.query.all()
        result = []
        for s in schedules:
            teacher = Teacher.query.filter_by(user_id=s.teacher_id).first()
            subject = Subject.query.get(s.subject_id)
            room = Room.query.get(s.room_id)
            result.append({
                "id": s.id,
                "teacher": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A",
                "teacher_id": s.teacher_id,
                "subject": subject.subject_name if subject else "N/A",
                "subject_id": s.subject_id,
                "day": s.day,
                "time": f"{s.time_start}-{s.time_end}",
                "room": room.room_name if room else "N/A",
                "room_id": s.room_id
            })
        return jsonify(result), 200

    @app.route('/api/admin/programs', methods=['GET'])
    def get_programs():
        token = request.args.get('token')
        programs = Program.query.all()
        return jsonify([{"id": p.id, "code": p.program_code, "name": p.program_name} for p in programs]), 200

    @app.route('/api/admin/departments', methods=['GET'])
    def get_departments():
        token = request.args.get('token')
        departments = Department.query.all()
        return jsonify([{"id": d.id, "code": d.dept_code, "name": d.dept_name} for d in departments]), 200

    @app.route('/api/admin/subjects', methods=['GET'])
    def get_subjects():
        token = request.args.get('token')
        subjects = Subject.query.all()
        return jsonify([{"id": s.id, "code": s.subject_code, "name": s.subject_name} for s in subjects]), 200

    @app.route('/api/admin/rooms', methods=['GET'])
    def get_rooms():
        token = request.args.get('token')
        rooms = Room.query.all()
        return jsonify([{"id": r.id, "name": r.room_name, "building": r.building} for r in rooms]), 200

    @app.route('/api/admin/add_student', methods=['POST'])
    def add_student():
        data = request.json
        token = data.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            school_id = id_generator.generate_unique_id('S')
            pwd = id_generator.generate_strong_password()
            hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            birthdate_str = data.get('birthdate', '2000-01-01')
            try:
                birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            except:
                birthdate = date(2000, 1, 1)
            
            student = Student(
                school_id=school_id,
                password_hash=hashed,
                first_name=data['first_name'],
                last_name=data['last_name'],
                gender=data.get('gender', 'Not Specified'),
                birthdate=birthdate,
                email=data['email'],
                phone_number=data.get('phone_number'),
                street_address=data.get('street_address'),
                baranggay=data.get('baranggay'),
                city=data.get('city'),
                province=data.get('province'),
                zip_code=data.get('zip_code'),
                user_type='student',
                program_id=data.get('program_id', 1),
                year_level=data.get('year_level', 1),
                term=data.get('term', '1st Semester'),
                section=data.get('section'),
                admission_date=date.today(),
                status='Active'
            )
            db.session.add(student)
            db.session.commit()
            return jsonify({'status': 'ok', 'id': school_id, 'password': pwd}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/admin/add_teacher', methods=['POST'])
    def add_teacher():
        data = request.json
        token = data.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            school_id = id_generator.generate_unique_id('T')
            pwd = id_generator.generate_strong_password()
            hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            birthdate_str = data.get('birthdate', '1980-01-01')
            try:
                birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            except:
                birthdate = date(1980, 1, 1)
            
            teacher = Teacher(
                school_id=school_id,
                password_hash=hashed,
                first_name=data['first_name'],
                last_name=data['last_name'],
                gender=data.get('gender', 'Not Specified'),
                birthdate=birthdate,
                email=data['email'],
                phone_number=data.get('phone_number'),
                street_address=data.get('street_address'),
                baranggay=data.get('baranggay'),
                city=data.get('city'),
                province=data.get('province'),
                zip_code=data.get('zip_code'),
                user_type='teacher',
                department_id=data.get('department_id', 1),
                specialization=data.get('specialization', ''),
                qualifications=data.get('qualifications', ''),
                employment_type=data.get('employment_type', 'Full-time'),
                office_location=data.get('office_location'),
                office_hours=data.get('office_hours'),
                hire_date=date.today()
            )
            db.session.add(teacher)
            db.session.commit()
            return jsonify({'status': 'ok', 'id': school_id, 'password': pwd}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/admin/delete_student/<int:student_id>', methods=['DELETE'])
    def delete_student(student_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            student = Student.query.filter_by(user_id=student_id).first()
            if not student:
                student = User.query.get(student_id)
            if student:
                db.session.delete(student)
                db.session.commit()
                return jsonify({'status': 'ok'}), 200
            return jsonify({'message': 'Student not found'}), 404
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/admin/delete_teacher/<int:teacher_id>', methods=['DELETE'])
    def delete_teacher(teacher_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            teacher = Teacher.query.filter_by(user_id=teacher_id).first()
            if not teacher:
                teacher = User.query.get(teacher_id)
            if teacher:
                db.session.delete(teacher)
                db.session.commit()
                return jsonify({'status': 'ok'}), 200
            return jsonify({'message': 'Teacher not found'}), 404
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/admin/add_schedule', methods=['POST'])
    def add_schedule():
        data = request.json
        token = data.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        day = data['day']
        time_range = f"{data['start_time']}-{data['end_time']}"

        if conflict_set.has_conflict(day, time_range):
            return jsonify({'message': 'Schedule conflict detected'}), 400

        try:
            sched = ClassSchedule(
                teacher_id=data['teacher_id'],
                subject_id=data['subject_id'],
                day=day,
                time_start=data['start_time'],
                time_end=data['end_time'],
                room_id=data['room_id'],
                section=data.get('section'),
                semester=data.get('semester', '1st Semester'),
                school_year=data.get('school_year', str(date.today().year))
            )
            db.session.add(sched)
            db.session.commit()
            conflict_set.add_schedule(day, time_range)
            return jsonify({'status': 'ok', 'id': sched.id}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/admin/delete_schedule/<int:schedule_id>', methods=['DELETE'])
    def delete_schedule(schedule_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            schedule = ClassSchedule.query.get(schedule_id)
            if schedule:
                conflict_set.remove_schedule(schedule.day, f"{schedule.time_start}-{schedule.time_end}")
                db.session.delete(schedule)
                db.session.commit()
                return jsonify({'status': 'ok'}), 200
            return jsonify({'message': 'Schedule not found'}), 404
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/admin/enrollment_requests', methods=['GET'])
    def get_enrollment_requests():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        requests = EnrollmentRequest.query.filter_by(status='pending').all()
        result = []
        for r in requests:
            student = Student.query.filter_by(user_id=r.student_id).first()
            schedule = ClassSchedule.query.get(r.class_sched_id)
            subject = Subject.query.get(schedule.subject_id) if schedule else None
            result.append({
                "id": r.id,
                "student": f"{student.first_name} {student.last_name}" if student else "N/A",
                "subject": subject.subject_name if subject else "N/A",
                "date": r.request_date.strftime('%Y-%m-%d') if r.request_date else "N/A"
            })
        return jsonify(result), 200

    @app.route('/api/admin/handle_enrollment_request/<int:request_id>', methods=['POST'])
    def handle_enrollment_request(request_id):
        data = request.json
        token = data.get('token')
        action = data['action']
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        req = EnrollmentRequest.query.get(request_id)
        if not req:
            return jsonify({'message': 'Request not found'}), 404

        if action == 'approve':
            try:
                enr = Enrollment(
                    student_id=req.student_id,
                    schedule_id=req.class_sched_id,
                    enrollment_date=datetime.now(),
                    semester='current',
                    school_year=str(date.today().year),
                    status='Enrolled'
                )
                db.session.add(enr)
                req.status = 'approved'
                db.session.commit()
                enrollment_queue.dequeue()
                return jsonify({'status': 'ok'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': str(e)}), 500
        else:
            req.status = 'denied'
            db.session.commit()
            return jsonify({'status': 'ok'}), 200

    @app.route('/api/admin/update_requests', methods=['GET'])
    def get_update_requests():
        """
        Retrieves all pending update requests for admin review.
        Uses a queue-based approach for FIFO processing of requests.
        
        Returns:
            JSON array of pending update requests with user info and details
        """
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        requests = UpdateRequest.query.filter_by(status='pending').all()
        result = []
        for r in requests:
            user = User.query.get(r.user_id)
            # Format the request type for display (e.g., 'update_phone_number' -> 'Phone Number')
            type_display = r.request_type.replace('update_', '').replace('_', ' ').title() if r.request_type else "Unknown"
            try:
                # Parse details JSON and format for display
                # Only show the values, not redundant field names
                details_json = json.loads(r.details) if r.details else {}
                details_display = ', '.join([str(v) for v in details_json.values()])
            except:
                details_display = r.details or ""
            result.append({
                "id": r.id,
                "user": f"{user.first_name} {user.last_name}" if user else "N/A",
                "user_role": user.user_type.title() if user else "Unknown",
                "type": type_display,
                "details": details_display
            })
        return jsonify(result), 200
    
    @app.route('/api/admin/update_request_history', methods=['GET'])
    def get_update_request_history():
        """
        Retrieves the history of all processed (approved/denied) update requests.
        Useful for audit trails and reviewing past request handling.
        
        Returns:
            JSON array of processed update requests with status and timestamps
        """
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        # Get all non-pending requests, ordered by most recent first
        requests = UpdateRequest.query.filter(
            UpdateRequest.status.in_(['approved', 'denied'])
        ).order_by(UpdateRequest.created_at.desc()).limit(100).all()
        
        result = []
        for r in requests:
            user = User.query.get(r.user_id)
            type_display = r.request_type.replace('update_', '').replace('_', ' ').title() if r.request_type else "Unknown"
            try:
                details_json = json.loads(r.details) if r.details else {}
                details_display = ', '.join([str(v) for v in details_json.values()])
            except:
                details_display = r.details or ""
            result.append({
                "id": r.id,
                "user": f"{user.first_name} {user.last_name}" if user else "N/A",
                "type": type_display,
                "details": details_display,
                "status": r.status,
                "date": r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else None
            })
        return jsonify(result), 200

    @app.route('/api/admin/handle_update_request/<int:request_id>', methods=['POST'])
    def handle_update_request(request_id):
        data = request.json
        token = data.get('token')
        action = data['action']
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        req = UpdateRequest.query.get(request_id)
        if not req:
            return jsonify({'message': 'Request not found'}), 404

        if action == 'approve':
            try:
                details = json.loads(req.details)
                user = User.query.get(req.user_id)
                for field, value in details.items():
                    if hasattr(user, field):
                        setattr(user, field, value)
                req.status = 'approved'
                db.session.commit()
                if update_request_queue:
                    update_request_queue.popleft()
                return jsonify({'status': 'ok'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': str(e)}), 500
        else:
            req.status = 'denied'
            db.session.commit()
            return jsonify({'status': 'ok'}), 200

    @app.route('/api/admin/bulk-import-students', methods=['POST'])
    def bulk_import_students():
        data = request.json
        token = data.get('token')
        students_list = data.get('students')
        
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        success_count = 0
        errors = []

        for row in students_list:
            try:
                sid = id_generator.generate_unique_id('S')
                pwd = id_generator.generate_strong_password()
                hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                if User.query.filter_by(email=row['email']).first():
                    errors.append(f"Email {row['email']} already exists")
                    continue
                
                prog_name = row.get('program', 'BSCS')
                prog = Program.query.filter(Program.program_code.like(f"%{prog_name}%")).first()
                pid = prog.id if prog else 1

                student = Student(
                    school_id=sid, 
                    password_hash=hashed, 
                    first_name=row['first_name'], 
                    last_name=row['last_name'], 
                    email=row['email'], 
                    phone_number=row.get('phone'), 
                    user_type='student',
                    gender='Not Specified', 
                    birthdate=date(2000, 1, 1),
                    program_id=pid,
                    year_level=row.get('year_level', 1),
                    status='Active'
                )
                db.session.add(student)
                db.session.commit()
                success_count += 1
            except Exception as e:
                db.session.rollback()
                errors.append(f"Row error: {str(e)}")

        return jsonify({'status': 'ok', 'imported': success_count, 'errors': errors}), 200

    @app.route('/api/teacher/profile', methods=['GET'])
    def teacher_profile():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        teacher = Teacher.query.filter_by(user_id=session_data['id']).first()
        if not teacher:
            teacher = User.query.get(session_data['id'])
        
        dept = Department.query.get(teacher.department_id) if hasattr(teacher, 'department_id') else None
        
        address_parts = [teacher.street_address, teacher.baranggay, teacher.city, teacher.province, teacher.zip_code]
        address = ', '.join([p for p in address_parts if p]) if any(address_parts) else 'N/A'
        
        return jsonify({
            "id": teacher.school_id,
            "name": f"{teacher.first_name} {teacher.last_name}",
            "email": teacher.email,
            "phone": teacher.phone_number if teacher.phone_number else "N/A",
            "department": dept.dept_name if dept else "N/A",
            "specialization": teacher.specialization if hasattr(teacher, 'specialization') else "N/A",
            "office_location": teacher.office_location if hasattr(teacher, 'office_location') else "N/A",
            "office_hours": teacher.office_hours if hasattr(teacher, 'office_hours') else "N/A",
            "address": address
        }), 200

    @app.route('/api/teacher/classes', methods=['GET'])
    def teacher_classes():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        schedules = ClassSchedule.query.filter_by(teacher_id=session_data['id']).all()
        result = []
        for s in schedules:
            subject = Subject.query.get(s.subject_id)
            room = Room.query.get(s.room_id)
            enrolled_count = Enrollment.query.filter_by(schedule_id=s.id).count()
            result.append({
                "id": s.id,
                "subject": subject.subject_name if subject else "N/A",
                "day": s.day,
                "time": f"{s.time_start}-{s.time_end}",
                "room": room.room_name if room else "N/A",
                "students": enrolled_count
            })
        return jsonify(result), 200

    @app.route('/api/teacher/class/<int:class_id>/students', methods=['GET'])
    def teacher_class_students(class_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        enrollments = Enrollment.query.filter_by(schedule_id=class_id).all()
        assignments = Assignment.query.filter_by(schedule_id=class_id).all()
        assignment_ids = [a.id for a in assignments]
        
        result = []
        for e in enrollments:
            student = User.query.get(e.student_id)
            
            calculated_grade = None
            if assignment_ids:
                submissions = TaskSubmission.query.filter(
                    TaskSubmission.task_id.in_(assignment_ids),
                    TaskSubmission.student_id == e.student_id
                ).all()
                
                graded_submissions = [s for s in submissions if s.grade is not None]
                if graded_submissions:
                    avg_grade = sum(float(s.grade) for s in graded_submissions) / len(graded_submissions)
                    calculated_grade = round(avg_grade, 2)
            
            if calculated_grade is None:
                legacy_grade = Grade.query.filter_by(enrollment_id=e.id).first()
                if legacy_grade and legacy_grade.score is not None:
                    calculated_grade = float(legacy_grade.score)
            
            result.append({
                "id": student.id,
                "enrollment_id": e.id,
                "school_id": student.school_id,
                "name": f"{student.first_name} {student.last_name}",
                "grade": calculated_grade
            })
        return jsonify(result), 200

    @app.route('/api/teacher/attendance', methods=['POST'])
    def teacher_attendance():
        data = request.json
        token = data['token']
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        date_str = data['date']
        records = data['records']
        schedule_id = data.get('schedule_id')

        try:
            att_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            for rec in records:
                enrollment = Enrollment.query.filter_by(student_id=rec['student_id'], schedule_id=schedule_id).first()
                if enrollment:
                    existing = Attendance.query.filter_by(enrollment_id=enrollment.id, date=att_date).first()
                    if existing:
                        existing.status = rec['status']
                        existing.remarks = rec.get('remarks', '')
                    else:
                        new_att = Attendance(
                            enrollment_id=enrollment.id, 
                            date=att_date, 
                            status=rec['status'],
                            remarks=rec.get('remarks', '')
                        )
                        db.session.add(new_att)
            
            db.session.commit()
            return jsonify({'status': 'ok', 'message': 'Attendance saved'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500
    
    @app.route('/api/teacher/class/<int:class_id>/attendance', methods=['GET'])
    def get_class_attendance(class_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        enrollments = Enrollment.query.filter_by(schedule_id=class_id).all()
        result = []
        for e in enrollments:
            student = User.query.get(e.student_id)
            attendance_records = Attendance.query.filter_by(enrollment_id=e.id).order_by(Attendance.date.desc()).all()
            att_list = []
            for a in attendance_records:
                att_list.append({
                    "id": a.id,
                    "date": a.date.strftime('%Y-%m-%d') if a.date else None,
                    "status": a.status,
                    "remarks": a.remarks or ""
                })
            result.append({
                "student_id": student.id,
                "student_name": f"{student.first_name} {student.last_name}",
                "school_id": student.school_id,
                "attendance": att_list
            })
        return jsonify(result), 200
    
    @app.route('/api/teacher/add_remarks', methods=['POST'])
    def add_remarks():
        data = request.json
        token = data['token']
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            grade_id = data.get('grade_id')
            enrollment_id = data.get('enrollment_id')
            remarks = data.get('remarks', '')
            
            if grade_id:
                grade = Grade.query.get(grade_id)
                if grade:
                    grade.remarks = remarks
            elif enrollment_id:
                grade = Grade.query.filter_by(enrollment_id=enrollment_id).first()
                if grade:
                    grade.remarks = remarks
                else:
                    grade = Grade(
                        enrollment_id=enrollment_id,
                        assessment_name='Remarks',
                        remarks=remarks
                    )
                    db.session.add(grade)
            
            db.session.commit()
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/teacher/grade', methods=['POST'])
    def teacher_grade():
        data = request.json
        token = data['token']
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            enrollment_id = data['enrollment_id']
            score = data['score']
            
            existing = Grade.query.filter_by(enrollment_id=enrollment_id).first()
            if existing:
                existing.score = score
            else:
                grade = Grade(
                    enrollment_id=enrollment_id,
                    assessment_name='Final Grade',
                    score=score
                )
                db.session.add(grade)
            
            db.session.commit()
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/teacher/assignments/<int:class_id>', methods=['GET'])
    def teacher_assignments(class_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        assignments = Assignment.query.filter_by(schedule_id=class_id).all()
        result = []
        for a in assignments:
            submissions = TaskSubmission.query.filter_by(task_id=a.id).count()
            result.append({
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "due_date": a.due_date.strftime('%Y-%m-%d') if a.due_date else None,
                "submissions": submissions
            })
        return jsonify(result), 200

    @app.route('/api/teacher/add_assignment', methods=['POST'])
    def add_assignment():
        data = request.json
        token = data['token']
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else None
            
            assignment = Assignment(
                schedule_id=data['schedule_id'],
                name=data['name'],
                description=data.get('description', ''),
                due_date=due_date,
                max_points=data.get('max_points', 100),
                created_by=session_data['id']
            )
            db.session.add(assignment)
            db.session.commit()
            
            try:
                schedule = ClassSchedule.query.get(data['schedule_id'])
                subject = Subject.query.get(schedule.subject_id) if schedule else None
                log_activity(
                    session_data['id'],
                    'create',
                    f"Created assignment '{data['name']}' for {subject.subject_name if subject else 'class'}",
                    assignment.id,
                    'assignment',
                    'student,teacher'
                )
            except Exception:
                pass
            
            return jsonify({'status': 'ok', 'id': assignment.id}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/student/profile', methods=['GET'])
    def student_profile():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'student')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        student = Student.query.filter_by(user_id=session_data['id']).first()
        if not student:
            student = User.query.get(session_data['id'])
        
        program = Program.query.get(student.program_id) if hasattr(student, 'program_id') else None
        
        address_parts = [student.street_address, student.baranggay, student.city, student.province, student.zip_code]
        address = ', '.join([p for p in address_parts if p]) if any(address_parts) else 'N/A'
        
        return jsonify({
            "id": student.school_id,
            "name": f"{student.first_name} {student.last_name}",
            "email": student.email,
            "phone": student.phone_number if student.phone_number else "N/A",
            "program": program.program_name if program else "N/A",
            "year": student.year_level if hasattr(student, 'year_level') else "N/A",
            "term": student.term if hasattr(student, 'term') else "N/A",
            "section": student.section if hasattr(student, 'section') else "N/A",
            "address": address,
            "status": student.status if hasattr(student, 'status') else "Active"
        }), 200

    @app.route('/api/student/schedule', methods=['GET'])
    def student_schedule():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'student')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        enrollments = Enrollment.query.filter_by(student_id=session_data['id']).all()
        result = []
        for e in enrollments:
            schedule = ClassSchedule.query.get(e.schedule_id)
            if schedule:
                subject = Subject.query.get(schedule.subject_id)
                teacher = Teacher.query.filter_by(user_id=schedule.teacher_id).first()
                room = Room.query.get(schedule.room_id)
                result.append({
                    "id": schedule.id,
                    "subject": subject.subject_name if subject else "N/A",
                    "teacher": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A",
                    "day": schedule.day,
                    "time": f"{schedule.time_start}-{schedule.time_end}",
                    "room": room.room_name if room else "N/A"
                })
        return jsonify(result), 200

    @app.route('/api/student/grades', methods=['GET'])
    def student_grades():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'student')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        enrollments = Enrollment.query.filter_by(student_id=session_data['id']).all()
        result = []
        grade_array.clear()
        
        for e in enrollments:
            schedule = ClassSchedule.query.get(e.schedule_id)
            if schedule:
                subject = Subject.query.get(schedule.subject_id)
                
                calculated_score = None
                assignments = Assignment.query.filter_by(schedule_id=e.schedule_id).all()
                assignment_ids = [a.id for a in assignments]
                
                if assignment_ids:
                    submissions = TaskSubmission.query.filter(
                        TaskSubmission.task_id.in_(assignment_ids),
                        TaskSubmission.student_id == session_data['id']
                    ).all()
                    
                    graded_submissions = [s for s in submissions if s.grade is not None]
                    if graded_submissions:
                        avg_grade = sum(float(s.grade) for s in graded_submissions) / len(graded_submissions)
                        calculated_score = round(avg_grade, 2)
                
                if calculated_score is None:
                    legacy_grade = Grade.query.filter_by(enrollment_id=e.id).first()
                    if legacy_grade and legacy_grade.score is not None:
                        calculated_score = float(legacy_grade.score)
                
                if calculated_score is not None:
                    status = "Passed" if calculated_score >= 75 else "Failed"
                else:
                    status = "Pending"
                
                grade_data = {
                    "subject": subject.subject_name if subject else "N/A",
                    "score": calculated_score,
                    "status": status,
                    "remarks": ""
                }
                result.append(grade_data)
                if calculated_score is not None:
                    grade_array.add({'score': calculated_score, 'subject': subject.subject_name if subject else "N/A"})
        
        grade_array.sort_by_grade(reverse=True)
        
        return jsonify({
            "grades": result,
            "average": grade_array.calculate_average()
        }), 200

    @app.route('/api/student/assignments', methods=['GET'])
    def student_assignments():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'student')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        enrollments = Enrollment.query.filter_by(student_id=session_data['id']).all()
        result = []
        
        for e in enrollments:
            assignments = Assignment.query.filter_by(schedule_id=e.schedule_id).all()
            for a in assignments:
                submission = TaskSubmission.query.filter_by(task_id=a.id, student_id=session_data['id']).first()
                schedule = ClassSchedule.query.get(e.schedule_id)
                subject = Subject.query.get(schedule.subject_id) if schedule else None
                teacher = Teacher.query.filter_by(user_id=schedule.teacher_id).first() if schedule else None
                result.append({
                    "id": a.id,
                    "name": a.name,
                    "subject": subject.subject_name if subject else "N/A",
                    "teacher": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A",
                    "description": a.description or "",
                    "due_date": a.due_date.strftime('%Y-%m-%d') if a.due_date else None,
                    "submitted": submission is not None,
                    "grade": float(submission.grade) if submission and submission.grade is not None else None
                })
        
        return jsonify(result), 200

    @app.route('/api/student/submit_task/<int:task_id>', methods=['POST'])
    def submit_task(task_id):
        data = request.json
        token = data['token']
        content = data['content']
        session_data, error = verify_session_hybrid(token, 'student')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            existing = TaskSubmission.query.filter_by(task_id=task_id, student_id=session_data['id']).first()
            if existing:
                existing.content = content
                existing.submission_date = date.today()
            else:
                sub = TaskSubmission(
                    task_id=task_id,
                    student_id=session_data['id'],
                    submission_date=date.today(),
                    content=content
                )
                db.session.add(sub)
            db.session.commit()
            
            try:
                assignment = Assignment.query.get(task_id)
                schedule = ClassSchedule.query.get(assignment.schedule_id) if assignment else None
                subject = Subject.query.get(schedule.subject_id) if schedule else None
                log_activity(
                    session_data['id'],
                    'submit',
                    f"Submitted assignment '{assignment.name if assignment else 'task'}' for {subject.subject_name if subject else 'class'}",
                    task_id,
                    'assignment',
                    'student,teacher'
                )
            except Exception:
                pass
            
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/student/available_classes', methods=['GET'])
    def available_classes():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'student')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        enrolled_schedules = [e.schedule_id for e in Enrollment.query.filter_by(student_id=session_data['id']).all()]
        pending_requests = [r.class_sched_id for r in EnrollmentRequest.query.filter_by(student_id=session_data['id'], status='pending').all()]
        
        schedules = ClassSchedule.query.all()
        result = []
        for s in schedules:
            if s.id not in enrolled_schedules and s.id not in pending_requests:
                subject = Subject.query.get(s.subject_id)
                teacher = Teacher.query.filter_by(user_id=s.teacher_id).first()
                room = Room.query.get(s.room_id)
                result.append({
                    "id": s.id,
                    "subject": subject.subject_name if subject else "N/A",
                    "teacher": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A",
                    "day": s.day,
                    "time": f"{s.time_start}-{s.time_end}",
                    "room": room.room_name if room else "N/A"
                })
        return jsonify(result), 200

    @app.route('/api/student/request_enroll/<int:class_id>', methods=['POST'])
    def student_request_enroll(class_id):
        data = request.json
        token = data['token']
        session_data, error = verify_session_hybrid(token, 'student')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            existing = EnrollmentRequest.query.filter_by(student_id=session_data['id'], class_sched_id=class_id).first()
            if existing:
                return jsonify({'message': 'Already requested'}), 400
            
            req = EnrollmentRequest(
                student_id=session_data['id'],
                class_sched_id=class_id,
                request_date=date.today(),
                status='pending'
            )
            db.session.add(req)
            db.session.commit()
            enrollment_queue.enqueue(req.id)
            
            try:
                schedule = ClassSchedule.query.get(class_id)
                subject = Subject.query.get(schedule.subject_id) if schedule else None
                log_activity(
                    session_data['id'],
                    'enroll',
                    f"Requested enrollment in {subject.subject_name if subject else 'class'}",
                    class_id,
                    'schedule',
                    'student,admin'
                )
            except Exception:
                pass
            
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/student/attendance', methods=['GET'])
    def student_attendance():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'student')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        enrollments = Enrollment.query.filter_by(student_id=session_data['id']).all()
        result = []
        
        for e in enrollments:
            schedule = ClassSchedule.query.get(e.schedule_id)
            if schedule:
                subject = Subject.query.get(schedule.subject_id)
                attendance_records = Attendance.query.filter_by(enrollment_id=e.id).order_by(Attendance.date.desc()).all()
                
                present_count = sum(1 for a in attendance_records if a.status == 'Present')
                absent_count = sum(1 for a in attendance_records if a.status == 'Absent')
                late_count = sum(1 for a in attendance_records if a.status == 'Late')
                excused_count = sum(1 for a in attendance_records if a.status == 'Excused')
                
                att_list = []
                for a in attendance_records:
                    att_list.append({
                        "date": a.date.strftime('%Y-%m-%d') if a.date else None,
                        "status": a.status,
                        "remarks": a.remarks or ""
                    })
                
                result.append({
                    "subject": subject.subject_name if subject else "N/A",
                    "present": present_count,
                    "absent": absent_count,
                    "late": late_count,
                    "excused": excused_count,
                    "total": len(attendance_records),
                    "records": att_list
                })
        
        return jsonify(result), 200

    @app.route('/api/request_update', methods=['POST'])
    def request_update():
        data = request.json
        token = data['token']
        request_type = data['type']
        details = json.dumps(data['details'])

        session_data = active_sessions.get(token)
        if not session_data:
            return jsonify({"message": "Invalid session"}), 401

        try:
            req = UpdateRequest(
                user_id=session_data['id'],
                request_type=request_type,
                details=details,
                status='pending'
            )
            db.session.add(req)
            db.session.commit()
            update_request_queue.append(req.id)
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/activities', methods=['GET'])
    def get_activities():
        token = request.args.get('token')
        role = request.args.get('role', 'all')
        limit = int(request.args.get('limit', 10))
        
        session_data = active_sessions.get(token)
        if not session_data:
            return jsonify({"message": "Invalid session"}), 401
        
        activities = Activity.query.filter(
            (Activity.target_roles.contains(role)) | (Activity.target_roles == 'all')
        ).order_by(Activity.created_at.desc()).limit(limit).all()
        
        result = []
        for a in activities:
            user = User.query.get(a.user_id) if a.user_id else None
            result.append({
                "id": a.id,
                "type": a.activity_type,
                "description": a.description,
                "user": f"{user.first_name} {user.last_name}" if user else "System",
                "time": a.created_at.strftime('%Y-%m-%d %H:%M') if a.created_at else None
            })
        return jsonify(result), 200

    def log_activity(user_id, activity_type, description, related_id=None, related_type=None, target_roles='all'):
        try:
            activity = Activity(
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                related_id=related_id,
                related_type=related_type,
                target_roles=target_roles
            )
            db.session.add(activity)
            db.session.commit()
        except Exception as e:
            logging.error(f"Error logging activity: {e}")

    @app.route('/api/admin/edit_student/<int:student_id>', methods=['PUT'])
    def edit_student(student_id):
        data = request.json
        token = data.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            student = Student.query.filter_by(user_id=student_id).first()
            if not student:
                student = User.query.get(student_id)
            if not student:
                return jsonify({'message': 'Student not found'}), 404
            
            if 'first_name' in data:
                student.first_name = data['first_name']
            if 'last_name' in data:
                student.last_name = data['last_name']
            if 'email' in data:
                student.email = data['email']
            if 'program_id' in data:
                student.program_id = data['program_id']
            if 'year_level' in data:
                student.year_level = data['year_level']
            if 'status' in data:
                student.status = data['status']
            if 'phone_number' in data:
                student.phone_number = data['phone_number']
            if 'street_address' in data:
                student.street_address = data['street_address']
            if 'baranggay' in data:
                student.baranggay = data['baranggay']
            if 'city' in data:
                student.city = data['city']
            if 'province' in data:
                student.province = data['province']
            if 'zip_code' in data:
                student.zip_code = data['zip_code']
            if 'term' in data:
                student.term = data['term']
            if 'section' in data:
                student.section = data['section']
            
            db.session.commit()
            log_activity(session_data['id'], 'edit', f"Updated student: {student.first_name} {student.last_name}", student_id, 'student', 'admin')
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/admin/edit_teacher/<int:teacher_id>', methods=['PUT'])
    def edit_teacher(teacher_id):
        data = request.json
        token = data.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            teacher = Teacher.query.filter_by(user_id=teacher_id).first()
            if not teacher:
                teacher = User.query.get(teacher_id)
            if not teacher:
                return jsonify({'message': 'Teacher not found'}), 404
            
            if 'first_name' in data:
                teacher.first_name = data['first_name']
            if 'last_name' in data:
                teacher.last_name = data['last_name']
            if 'email' in data:
                teacher.email = data['email']
            if 'department_id' in data:
                teacher.department_id = data['department_id']
            if 'specialization' in data:
                teacher.specialization = data['specialization']
            if 'phone_number' in data:
                teacher.phone_number = data['phone_number']
            if 'status' in data:
                teacher.status = data['status']
            if 'street_address' in data:
                teacher.street_address = data['street_address']
            if 'baranggay' in data:
                teacher.baranggay = data['baranggay']
            if 'city' in data:
                teacher.city = data['city']
            if 'province' in data:
                teacher.province = data['province']
            if 'zip_code' in data:
                teacher.zip_code = data['zip_code']
            if 'office_location' in data:
                teacher.office_location = data['office_location']
            if 'office_hours' in data:
                teacher.office_hours = data['office_hours']
            
            db.session.commit()
            log_activity(session_data['id'], 'edit', f"Updated teacher: {teacher.first_name} {teacher.last_name}", teacher_id, 'teacher', 'admin')
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/admin/edit_schedule/<int:schedule_id>', methods=['PUT'])
    def edit_schedule(schedule_id):
        data = request.json
        token = data.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            schedule = ClassSchedule.query.get(schedule_id)
            if not schedule:
                return jsonify({'message': 'Schedule not found'}), 404
            
            if 'teacher_id' in data:
                schedule.teacher_id = data['teacher_id']
            if 'subject_id' in data:
                schedule.subject_id = data['subject_id']
            if 'room_id' in data:
                schedule.room_id = data['room_id']
            if 'day' in data:
                schedule.day = data['day']
            if 'start_time' in data:
                schedule.time_start = data['start_time']
            if 'end_time' in data:
                schedule.time_end = data['end_time']
            if 'section' in data:
                schedule.section = data['section']
            
            db.session.commit()
            log_activity(session_data['id'], 'edit', f"Updated schedule ID: {schedule_id}", schedule_id, 'schedule', 'admin')
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/admin/get_student/<int:student_id>', methods=['GET'])
    def get_student_detail(student_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        student = Student.query.filter_by(user_id=student_id).first()
        if not student:
            return jsonify({'message': 'Student not found'}), 404
        
        program = Program.query.get(student.program_id)
        return jsonify({
            "id": student.id,
            "user_id": student.user_id,
            "school_id": student.school_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "email": student.email,
            "phone_number": student.phone_number or "",
            "street_address": student.street_address or "",
            "baranggay": student.baranggay or "",
            "city": student.city or "",
            "province": student.province or "",
            "zip_code": student.zip_code or "",
            "program_id": student.program_id,
            "program": program.program_code if program else "N/A",
            "year_level": student.year_level,
            "term": student.term or "1st Semester",
            "section": student.section or "",
            "status": student.status or "Active"
        }), 200

    @app.route('/api/admin/get_teacher/<int:teacher_id>', methods=['GET'])
    def get_teacher_detail(teacher_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        teacher = Teacher.query.filter_by(user_id=teacher_id).first()
        if not teacher:
            return jsonify({'message': 'Teacher not found'}), 404
        
        dept = Department.query.get(teacher.department_id)
        return jsonify({
            "id": teacher.id,
            "user_id": teacher.user_id,
            "school_id": teacher.school_id,
            "first_name": teacher.first_name,
            "last_name": teacher.last_name,
            "email": teacher.email,
            "phone_number": teacher.phone_number or "",
            "street_address": teacher.street_address or "",
            "baranggay": teacher.baranggay or "",
            "city": teacher.city or "",
            "province": teacher.province or "",
            "zip_code": teacher.zip_code or "",
            "department_id": teacher.department_id,
            "department": dept.dept_code if dept else "N/A",
            "specialization": teacher.specialization or "",
            "office_location": teacher.office_location or "",
            "office_hours": teacher.office_hours or "",
            "status": teacher.status or "Active"
        }), 200

    @app.route('/api/admin/get_schedule/<int:schedule_id>', methods=['GET'])
    def get_schedule_detail(schedule_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        schedule = ClassSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({'message': 'Schedule not found'}), 404
        
        return jsonify({
            "id": schedule.id,
            "teacher_id": schedule.teacher_id,
            "subject_id": schedule.subject_id,
            "room_id": schedule.room_id,
            "section": schedule.section or "",
            "day": schedule.day,
            "start_time": schedule.time_start,
            "end_time": schedule.time_end
        }), 200

    @app.route('/api/teacher/assignment/<int:assignment_id>/submissions', methods=['GET'])
    def get_assignment_submissions(assignment_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return jsonify({"message": "Assignment not found"}), 404
        
        submissions = TaskSubmission.query.filter_by(task_id=assignment_id).all()
        result = []
        for sub in submissions:
            student = Student.query.filter_by(user_id=sub.student_id).first()
            if not student:
                student = User.query.get(sub.student_id)
            result.append({
                "id": sub.id,
                "student_id": sub.student_id,
                "student_name": f"{student.first_name} {student.last_name}" if student else "Unknown",
                "student_school_id": student.school_id if student else "N/A",
                "submission_date": sub.submission_date.strftime('%Y-%m-%d') if sub.submission_date else None,
                "content": sub.content,
                "grade": float(sub.grade) if sub.grade is not None else None
            })
        return jsonify(result), 200

    @app.route('/api/teacher/grade_submission/<int:submission_id>', methods=['POST'])
    def grade_submission(submission_id):
        data = request.json
        token = data['token']
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            submission = TaskSubmission.query.get(submission_id)
            if not submission:
                return jsonify({'message': 'Submission not found'}), 404
            
            submission.grade = data.get('grade')
            db.session.commit()
            
            student = User.query.get(submission.student_id)
            assignment = Assignment.query.get(submission.task_id)
            log_activity(
                session_data['id'], 
                'grade', 
                f"Graded {student.first_name}'s submission for {assignment.name if assignment else 'assignment'}", 
                submission_id, 
                'submission', 
                'student,teacher'
            )
            
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/teacher/available_subjects', methods=['GET'])
    def get_available_subjects():
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        subjects = Subject.query.all()
        result = []
        for s in subjects:
            has_pref = TeacherSubjectPreference.query.filter_by(
                teacher_id=session_data['id'], 
                subject_id=s.id,
                status='active'
            ).first()
            result.append({
                "id": s.id,
                "code": s.subject_code,
                "name": s.subject_name,
                "units": s.units,
                "selected": has_pref is not None
            })
        return jsonify(result), 200

    @app.route('/api/teacher/select_subject', methods=['POST'])
    def select_subject():
        data = request.json
        token = data['token']
        subject_id = data['subject_id']
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            existing = TeacherSubjectPreference.query.filter_by(
                teacher_id=session_data['id'],
                subject_id=subject_id
            ).first()
            
            if existing:
                existing.status = 'active' if existing.status == 'inactive' else 'inactive'
            else:
                pref = TeacherSubjectPreference(
                    teacher_id=session_data['id'],
                    subject_id=subject_id,
                    status='active'
                )
                db.session.add(pref)
            
            db.session.commit()
            subject = Subject.query.get(subject_id)
            log_activity(
                session_data['id'],
                'preference',
                f"Updated teaching preference for {subject.subject_name if subject else 'subject'}",
                subject_id,
                'subject',
                'teacher,admin'
            )
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/teacher/assignment/<int:assignment_id>', methods=['GET'])
    def get_assignment_detail(assignment_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return jsonify({"message": "Assignment not found"}), 404
        
        schedule = ClassSchedule.query.get(assignment.schedule_id)
        subject = Subject.query.get(schedule.subject_id) if schedule else None
        
        return jsonify({
            "id": assignment.id,
            "name": assignment.name,
            "description": assignment.description or "",
            "due_date": assignment.due_date.strftime('%Y-%m-%d') if assignment.due_date else None,
            "max_points": assignment.max_points or 100,
            "subject": subject.subject_name if subject else "N/A",
            "schedule_id": assignment.schedule_id,
            "status": "active"
        }), 200

    @app.route('/api/teacher/assignment/<int:assignment_id>', methods=['PUT'])
    def update_assignment(assignment_id):
        data = request.json
        token = data.get('token')
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            assignment = Assignment.query.get(assignment_id)
            if not assignment:
                return jsonify({'message': 'Assignment not found'}), 404
            
            if 'name' in data:
                assignment.name = data['name']
            if 'description' in data:
                assignment.description = data['description']
            if 'due_date' in data:
                assignment.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            if 'max_points' in data:
                assignment.max_points = data['max_points']
            
            db.session.commit()
            log_activity(session_data['id'], 'edit', f"Updated assignment: {assignment.name}", assignment_id, 'assignment', 'student,teacher')
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/teacher/assignment/<int:assignment_id>', methods=['DELETE'])
    def delete_assignment(assignment_id):
        token = request.args.get('token')
        session_data, error = verify_session_hybrid(token, 'teacher')
        if error:
            return jsonify({"message": "Invalid session"}), 401

        try:
            assignment = Assignment.query.get(assignment_id)
            if not assignment:
                return jsonify({'message': 'Assignment not found'}), 404
            
            TaskSubmission.query.filter_by(task_id=assignment_id).delete()
            assignment_name = assignment.name
            db.session.delete(assignment)
            db.session.commit()
            log_activity(session_data['id'], 'delete', f"Deleted assignment: {assignment_name}", None, 'assignment', 'teacher')
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @app.route('/api/admin/search', methods=['GET'])
    def admin_search():
        token = request.args.get('token')
        query = request.args.get('q', '').lower()
        search_type = request.args.get('type', 'all')
        
        session_data, error = verify_session_hybrid(token, 'admin')
        if error:
            return jsonify({"message": "Invalid session"}), 401
        
        results = {"students": [], "teachers": [], "schedules": []}
        
        if search_type in ['all', 'students']:
            students = Student.query.filter(
                (Student.first_name.ilike(f'%{query}%')) |
                (Student.last_name.ilike(f'%{query}%')) |
                (Student.school_id.ilike(f'%{query}%')) |
                (Student.email.ilike(f'%{query}%'))
            ).all()
            for s in students:
                program = Program.query.get(s.program_id)
                results["students"].append({
                    "id": s.id,
                    "school_id": s.school_id,
                    "name": f"{s.first_name} {s.last_name}",
                    "program": program.program_code if program else "N/A"
                })
        
        if search_type in ['all', 'teachers']:
            teachers = Teacher.query.filter(
                (Teacher.first_name.ilike(f'%{query}%')) |
                (Teacher.last_name.ilike(f'%{query}%')) |
                (Teacher.school_id.ilike(f'%{query}%')) |
                (Teacher.email.ilike(f'%{query}%'))
            ).all()
            for t in teachers:
                dept = Department.query.get(t.department_id)
                results["teachers"].append({
                    "id": t.id,
                    "school_id": t.school_id,
                    "name": f"{t.first_name} {t.last_name}",
                    "department": dept.dept_code if dept else "N/A"
                })
        
        if search_type in ['all', 'schedules']:
            schedules = ClassSchedule.query.join(Subject).filter(
                Subject.subject_name.ilike(f'%{query}%')
            ).all()
            for s in schedules:
                subject = Subject.query.get(s.subject_id)
                teacher = Teacher.query.filter_by(user_id=s.teacher_id).first()
                results["schedules"].append({
                    "id": s.id,
                    "subject": subject.subject_name if subject else "N/A",
                    "teacher": f"{teacher.first_name} {teacher.last_name}" if teacher else "N/A"
                })
        
        return jsonify(results), 200

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
