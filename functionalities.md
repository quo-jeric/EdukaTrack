# EdukaTrack - Functionality Summary

## 🎓 **Core Platform**
- **Role-based access**: Admin, Teacher, Student portals with JWT authentication
- **Real-time dashboard** with stats, recent activities, and quick actions
- **Responsive UI** with sortable/searchable tables, modals, and notifications

---

## 👨‍💼 **Admin Features**

| Area | Capabilities |
|------|--------------|
| **User Management** | Create/edit/delete students & teachers; auto-generates IDs (S-XXXXX/T-XXXXX) & strong passwords |
| **Academic Setup** | Manage departments, programs, subjects, rooms, prerequisites |
| **Scheduling** | Create/edit/delete class schedules with **conflict detection** (room/teacher/time) |
| **Enrollment Requests** | Review/approve/deny student enrollment requests (FIFO queue) |
| **Profile Updates** | Process student/teacher profile change requests (email, phone, address) |
| **Bulk Operations** | CSV/JSON bulk student import |
| **Search & Audit** | Global search across students/teachers/schedules; activity log |

---

## 👨‍🏫 **Teacher Features**

| Area | Capabilities |
|------|--------------|
| **Class Overview** | View assigned classes with student counts |
| **Grade Management** | View calculated grades (from assignments); add remarks; auto-remarks based on score |
| **Attendance** | Mark daily attendance (Present/Absent/Late/Excused) with remarks; view history |
| **Assignments** | Create/edit/delete assignments with due dates; view/grade submissions |
| **Profile** | View profile; request updates (email, phone, office) |

---

## 🎒 **Student Features**

| Area | Capabilities |
|------|--------------|
| **Schedule** | View enrolled classes (subject, teacher, day, time, room) |
| **Grades** | View per-subject grades with status (Passed/Failed/Pending) + calculated average |
| **Attendance** | Summary stats + detailed records per subject |
| **Assignments** | View pending/submitted assignments; submit work (text/links); see grades |
| **Enrollment** | Browse available classes; submit enrollment requests (queued for admin) |
| **Profile** | View profile; request updates (email, phone, address) |

---
