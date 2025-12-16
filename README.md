# EdukaTrack

# EdukaTrack User Guide

## Overview

EdukaTrack is a comprehensive Student Management System designed for educational institutions. It provides separate portals for Administrators, Teachers, and Students to manage academic activities efficiently.

---

## System Requirements

### Software Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Web Browser**: Google Chrome (latest), Mozilla Firefox (latest), Microsoft Edge (latest), or Safari (latest)
- **Internet Connection**: Stable broadband connection recommended

### Hardware Requirements
- **CPU**: 1 GHz or faster processor
- **RAM**: 2 GB minimum (4 GB recommended)
- **Storage**: 100 MB available disk space for browser cache
- **Display**: 1280x720 resolution or higher

---

## Installation Instructions

### For End Users
1. Open your web browser
2. Navigate to the EdukaTrack URL provided by your institution
3. The login page will appear automatically

### For System Administrators
1. Clone the repository or download the source code
2. Ensure Python 3.11+ is installed
3. Install dependencies: `pip install -r requirements.txt`
4. Initialize the database: `python seed.py`
5. Run the application: `python app.py`
6. Access the system at `http://localhost:5000`

---

## How to Use the System

### Logging In
1. **Launch the Application**: Open your web browser and navigate to the EdukaTrack URL
2. **Select Your Role**: Choose from Administrator, Teacher, or Student
3. **Enter Credentials**: 
   - School ID: Your unique identifier (e.g., S-20250001 for students, T-20250001 for teachers)
   - Password: Your assigned password
4. **Click Sign In**: You will be redirected to your respective dashboard

### Administrator Portal

#### Dashboard Overview
- View total number of students, teachers, and schedules
- Monitor pending enrollment requests
- Access recent system activities

#### Student Management
1. Navigate to "Students" in the sidebar
2. **Add Student**: Click "Add Student" button, fill in details, submit
3. **Edit Student**: Click the edit icon next to a student
4. **Delete Student**: Click the delete icon (requires confirmation)
5. **Search**: Use the search box to find specific students

#### Teacher Management
1. Navigate to "Teachers" in the sidebar
2. **Add Teacher**: Click "Add Teacher" button, fill in details, submit
3. **Edit Teacher**: Click the edit icon next to a teacher
4. **Delete Teacher**: Click the delete icon (requires confirmation)

#### Schedule Management
1. Navigate to "Schedules" in the sidebar
2. **Add Schedule**: Click "Add Schedule" button
3. Fill in: Teacher, Subject, Day, Time, Room
4. The system automatically checks for scheduling conflicts

#### Enrollment Requests
1. Navigate to "Enrollment Requests" in the sidebar
2. View pending student enrollment requests
3. Click "Approve" or "Deny" for each request

#### Update Requests
1. Navigate to "Update Requests" in the sidebar
2. View requests from students/teachers to update their profiles
3. Approve or deny update requests

### Teacher Portal

#### Dashboard Overview
- View total classes assigned
- See total students across all classes
- Monitor pending grades

#### My Classes
1. Navigate to "My Classes" in the sidebar
2. View all assigned classes with schedule details
3. Click "View Students" to see enrolled students

#### Grade Management
1. Navigate to "Grades" in the sidebar
2. Select a class from the dropdown
3. View student list with their current grades
4. Grades are automatically calculated from assignment submissions
5. Remarks are automatically generated based on grade ranges:
   - 95-100: Excellent
   - 90-94: Very Good
   - 85-89: Good
   - 80-84: Satisfactory
   - 75-79: Needs Improvement
   - Below 75: Failed

#### Attendance Management
1. Navigate to "Attendance" in the sidebar
2. Select a class and date
3. Mark each student's status: Present, Absent, Late, or Excused
4. Add optional remarks
5. Click "Save Attendance"
6. Click "View History" to see past attendance records

#### Assignment Management
1. Navigate to "Assignments" in the sidebar
2. Select a class from the dropdown
3. **Add Assignment**: Click "Add Assignment", fill in title, description, due date
4. **View Submissions**: Click "Submissions" to see student work
5. **Grade Submissions**: Click "Grade" on a submission, enter score (0-100)
6. **Edit Assignment**: Click the edit icon
7. **Delete Assignment**: Click the delete icon

#### Subject Preferences
1. Navigate to "Subject Preferences" in the sidebar
2. Click on subjects you prefer to teach
3. Selected subjects show a checkmark

#### Profile
1. Navigate to "Profile" in the sidebar
2. View your personal and professional information
3. Click "Request Profile Update" to submit changes for admin approval

### Student Portal

#### Dashboard Overview
- View enrolled courses count
- See current average grade
- Monitor pending assignments

#### My Schedule
1. Navigate to "My Schedule" in the sidebar
2. View all enrolled classes with times and rooms
3. Use search to filter courses
4. Click column headers to sort

#### Grades
1. Navigate to "Grades" in the sidebar
2. View grades for each subject
3. Grades are calculated from your assignment submissions
4. See overall average at the top
5. Remarks indicate your performance level

#### Attendance
1. Navigate to "Attendance" in the sidebar
2. View attendance summary (Present, Absent, Late, Excused)
3. See detailed records per subject

#### Assignments
1. Navigate to "Assignments" in the sidebar
2. View all assigned work with due dates
3. Click "Submit" to submit an assignment
4. Enter your answer or paste a link
5. View your grade once the teacher grades it

#### Enroll in Classes
1. Navigate to "Enroll" in the sidebar
2. View available classes
3. Click "Enroll" to request enrollment
4. Wait for admin approval

#### Profile
1. Navigate to "Profile" in the sidebar
2. View your personal and academic information
3. Click "Request Profile Update" to submit changes

---

## Sample Use Case

### Scenario: Complete Assignment Workflow

1. **Administrator**: Adds a new schedule for "Data Structures" taught by Prof. Smith
2. **Student Maria**: 
   - Logs in and navigates to "Enroll"
   - Requests enrollment in Data Structures class
3. **Administrator**: 
   - Sees Maria's enrollment request
   - Clicks "Approve"
4. **Teacher Prof. Smith**:
   - Logs in and navigates to "Assignments"
   - Selects Data Structures class
   - Adds assignment "Linked List Implementation" with due date
5. **Student Maria**:
   - Logs in and sees new assignment under "Assignments"
   - Clicks "Submit", enters her solution
   - Submits the assignment
6. **Teacher Prof. Smith**:
   - Navigates to Assignments
   - Clicks "Submissions" for the assignment
   - Reviews Maria's submission
   - Clicks "Grade", enters 85
7. **Student Maria**:
   - Views grades in dashboard
   - Sees 85 for Data Structures with "Very Good" remarks

---

## Troubleshooting

### Cannot Log In
- **Verify credentials**: Check School ID and password
- **Correct role**: Ensure you selected the right role (Admin/Teacher/Student)
- **Caps Lock**: Check if Caps Lock is enabled
- **Contact admin**: Request password reset if needed

### Page Not Loading
- **Refresh**: Press F5 or click refresh
- **Clear cache**: Clear browser cache and cookies
- **Try another browser**: Test with different browser
- **Check internet**: Verify internet connection

### Grades Not Showing
- **Assignments submitted**: Ensure assignments have been submitted
- **Teacher graded**: Teacher needs to grade submissions first
- **Refresh page**: Reload to see latest grades

### Assignment Submission Failed
- **Check connection**: Ensure stable internet
- **Content required**: Make sure submission field is not empty
- **File size**: If pasting links, ensure URL is valid

### Attendance Not Saving
- **Select class**: Ensure a class is selected from dropdown
- **Select date**: Choose the attendance date
- **Try again**: Click "Save Attendance" again

---

## Contact Support

For technical issues or questions not covered in this guide:
- Dancel Mamansag (Siya lang po i-contact niyo)

---

## Version Information

- **Application**: EdukaTrack v1.0
- **Last Updated**: December 2025
