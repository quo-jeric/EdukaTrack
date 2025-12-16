/**
 * EdukaTrack Teacher Dashboard JavaScript
 * 
 * This module handles the teacher dashboard functionality including:
 * - Class management and student viewing
 * - Grade assignment and management
 * - Attendance tracking
 * - Assignment creation and grading
 * - Subject preference selection
 * 
 * Data Structures Used:
 * - Arrays: allClasses for storing class data, used for filtering/searching
 * - Dynamic rendering: All tables use map/join for efficient DOM updates
 */

const token = localStorage.getItem('session_token');
const API_BASE = '';
let currentClassId = null;
let currentAssignmentId = null;
let allClasses = [];

// Sorting state for tables
let sortState = {
    classes: { column: null, ascending: true },
    grades: { column: null, ascending: true },
    attendanceHistory: { column: null, ascending: true }
};

// Store data for sorting
let allGradesData = [];
let allAttendanceHistoryData = [];

// Day name mapping - converts abbreviations to full names
const DAY_MAP = {
    'MWF': 'Monday, Wednesday, Friday',
    'TTh': 'Tuesday, Thursday',
    'MW': 'Monday, Wednesday',
    'TF': 'Tuesday, Friday',
    'M': 'Monday',
    'T': 'Tuesday',
    'W': 'Wednesday',
    'Th': 'Thursday',
    'F': 'Friday',
    'S': 'Saturday',
    'Su': 'Sunday'
};

/**
 * Converts day abbreviations to full day names
 * @param {string} day - Day abbreviation (e.g., 'MWF', 'TTh')
 * @returns {string} Full day name(s)
 */
function formatDayName(day) {
    if (!day) return 'N/A';
    return DAY_MAP[day] || day;
}

/**
 * Sorts an array of objects by a specified key
 * @param {Array} array - Array to sort
 * @param {string} key - Object key to sort by
 * @param {boolean} ascending - Sort direction
 * @returns {Array} Sorted array
 */
function sortArray(array, key, ascending = true) {
    return [...array].sort((a, b) => {
        let valA = a[key];
        let valB = b[key];
        
        if (valA == null) valA = '';
        if (valB == null) valB = '';
        
        if (typeof valA === 'number' && typeof valB === 'number') {
            return ascending ? valA - valB : valB - valA;
        }
        
        valA = String(valA).toLowerCase();
        valB = String(valB).toLowerCase();
        
        if (valA < valB) return ascending ? -1 : 1;
        if (valA > valB) return ascending ? 1 : -1;
        return 0;
    });
}

/**
 * Handles column header click for sorting
 * @param {string} tableType - Type of table
 * @param {string} column - Column key to sort by
 */
function handleSort(tableType, column) {
    const state = sortState[tableType];
    
    if (state.column === column) {
        state.ascending = !state.ascending;
    } else {
        state.column = column;
        state.ascending = true;
    }
    
    if (tableType === 'classes') {
        renderClasses(sortArray(allClasses, column, state.ascending));
    } else if (tableType === 'grades') {
        renderGradesTable(sortArray(allGradesData, column, state.ascending));
    } else if (tableType === 'attendanceHistory') {
        renderAttendanceHistoryTable(sortArray(allAttendanceHistoryData, column, state.ascending));
    }
}

/**
 * Sets up click handlers for sortable table headers
 */
function setupSortableHeaders() {
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => {
            const tableType = th.dataset.table;
            const column = th.dataset.sort;
            handleSort(tableType, column);
        });
    });
}

// Redirect to login if no token
if (!token) {
    window.location.href = '/';
}

/**
 * Authentication check on page load
 * Verifies session token and initializes dashboard if valid
 */
(async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/api/verify-session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, role: 'teacher' })
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('teacherName').textContent = data.user || 'Teacher';
            document.getElementById('userName').textContent = data.user || 'Teacher';
            initializeDashboard();
        } else {
            throw new Error('Invalid Session');
        }
    } catch (err) {
        localStorage.clear();
        window.location.href = '/';
    }
})();

/**
 * Initializes the dashboard by loading all required data
 */
function initializeDashboard() {
    loadProfile();
    loadClasses();
    loadActivities();
    loadSubjects();
    setupEventListeners();
    setupSortableHeaders();
    document.getElementById('attendanceDate').valueAsDate = new Date();
}

/**
 * Loads teacher profile information
 */
async function loadProfile() {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/profile?token=${token}`);
        const profile = await res.json();
        document.getElementById('profileId').textContent = profile.id;
        document.getElementById('profileName').textContent = profile.name;
        document.getElementById('profileEmail').textContent = profile.email;
        document.getElementById('profilePhone').textContent = profile.phone || '-';
        document.getElementById('profileDepartment').textContent = profile.department;
        document.getElementById('profileSpecialization').textContent = profile.specialization;
        document.getElementById('profileOffice').textContent = profile.office_location || '-';
        document.getElementById('profileHours').textContent = profile.office_hours || '-';
        document.getElementById('profileAddress').textContent = profile.address || '-';
    } catch (e) {
        console.error('Error loading profile:', e);
    }
}

/**
 * Loads recent activity feed for teacher
 */
async function loadActivities() {
    try {
        const res = await fetch(`${API_BASE}/api/activities?token=${token}&role=teacher&limit=10`);
        const activities = await res.json();
        const container = document.getElementById('recentActivities');
        
        if (activities.length === 0) {
            container.innerHTML = '<p class="empty-state">No recent activities</p>';
            return;
        }
        
        const iconMap = {
            'system': 'fas fa-cog',
            'assignment': 'fas fa-tasks',
            'enrollment': 'fas fa-user-plus',
            'grade': 'fas fa-star',
            'announcement': 'fas fa-bullhorn',
            'preference': 'fas fa-heart'
        };
        
        container.innerHTML = activities.map(a => `
            <div class="activity-item">
                <div class="activity-icon">
                    <i class="${iconMap[a.type] || 'fas fa-info-circle'}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-description">${a.description}</div>
                    <div class="activity-meta">${a.user} - ${a.time}</div>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Error loading activities:', e);
        document.getElementById('recentActivities').innerHTML = '<p class="loading-text">Unable to load activities</p>';
    }
}

/**
 * Loads available subjects for preference selection
 */
async function loadSubjects() {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/available_subjects?token=${token}`);
        const subjects = await res.json();
        const container = document.getElementById('subjectsList');
        
        if (subjects.length === 0) {
            container.innerHTML = '<p class="empty-state">No subjects available</p>';
            return;
        }
        
        container.innerHTML = subjects.map(s => `
            <div class="subject-card ${s.selected ? 'selected' : ''}" onclick="toggleSubjectPreference(${s.id}, this)">
                ${s.selected ? '<i class="fas fa-check-circle check-icon"></i>' : ''}
                <div class="subject-code">${s.code}</div>
                <div class="subject-name">${s.name}</div>
                <div class="subject-units">${s.units} units</div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Error loading subjects:', e);
        document.getElementById('subjectsList').innerHTML = '<p class="loading-text">Unable to load subjects</p>';
    }
}

/**
 * Toggles subject teaching preference
 * @param {number} subjectId - Subject ID to toggle
 * @param {HTMLElement} element - DOM element that was clicked
 */
async function toggleSubjectPreference(subjectId, element) {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/select_subject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, subject_id: subjectId })
        });
        
        if (res.ok) {
            element.classList.toggle('selected');
            if (element.classList.contains('selected')) {
                element.innerHTML = '<i class="fas fa-check-circle check-icon"></i>' + element.innerHTML;
            } else {
                const checkIcon = element.querySelector('.check-icon');
                if (checkIcon) checkIcon.remove();
            }
            showAlert('Subject preference updated', 'success');
        }
    } catch (e) {
        showAlert('Error updating preference', 'error');
    }
}

/**
 * Loads all classes assigned to the teacher
 */
async function loadClasses() {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/classes?token=${token}`);
        allClasses = await res.json();
        
        document.getElementById('totalClasses').textContent = allClasses.length;
        let totalStudents = 0;
        allClasses.forEach(c => totalStudents += c.students);
        document.getElementById('totalStudents').textContent = totalStudents;
        
        renderClasses(allClasses);

        const classOptions = allClasses.map(c => `<option value="${c.id}">${c.subject} (${formatDayName(c.day)})</option>`).join('');
        document.getElementById('gradeClassSelect').innerHTML = '<option value="">Select a class</option>' + classOptions;
        document.getElementById('attendanceClassSelect').innerHTML = '<option value="">Select a class</option>' + classOptions;
        document.getElementById('assignmentClassSelect').innerHTML = '<option value="">Select a class</option>' + classOptions;
    } catch (e) {
        console.error('Error loading classes:', e);
    }
}

/**
 * Renders class table with formatted day names
 * @param {Array} classes - Array of class objects
 */
function renderClasses(classes) {
    const tbody = document.getElementById('classesTableBody');
    if (classes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No classes found</td></tr>';
        return;
    }
    tbody.innerHTML = classes.map(c => `
        <tr>
            <td>${c.subject}</td>
            <td>${formatDayName(c.day)}</td>
            <td>${c.time}</td>
            <td>${c.room}</td>
            <td>${c.students}</td>
            <td>
                <button class="btn btn-small btn-primary" onclick="viewClassStudents(${c.id})"><i class="fas fa-users"></i> View Students</button>
            </td>
        </tr>
    `).join('');
}

/**
 * Navigates to view students in a specific class
 * @param {number} classId - Class schedule ID
 */
async function viewClassStudents(classId) {
    currentClassId = classId;
    document.getElementById('gradeClassSelect').value = classId;
    loadClassStudentsForGrades(classId);
    document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
    document.querySelector('[data-tab="grades"]').classList.add('active');
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById('gradesTab').classList.add('active');
}

/**
 * Loads students for grading view
 * Uses DynamicArray pattern for grade management
 * @param {number} classId - Class schedule ID
 */
async function loadClassStudentsForGrades(classId) {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/class/${classId}/students?token=${token}`);
        const students = await res.json();
        
        if (students.length === 0) {
            const tbody = document.getElementById('gradesTableBody');
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No students enrolled</td></tr>';
            return;
        }
        
        allGradesData = students;
        renderGradesTable(students);
        
        document.getElementById('pendingGrades').textContent = students.filter(s => s.grade === null).length;
    } catch (e) {
        console.error('Error loading students:', e);
    }
}

function renderGradesTable(students) {
    const tbody = document.getElementById('gradesTableBody');
    tbody.innerHTML = students.map(s => `
        <tr>
            <td>${s.school_id}</td>
            <td>${s.name}</td>
            <td>${s.grade !== null && s.grade !== undefined ? s.grade : '-'}</td>
            <td>${getAutoRemarks(s.grade)}</td>
            <td>
                <span style="color: var(--muted); font-style: italic;">Grade from assignments</span>
            </td>
        </tr>
    `).join('');
}

/**
 * Loads students for attendance tracking
 * @param {number} classId - Class schedule ID
 */
async function loadClassStudentsForAttendance(classId) {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/class/${classId}/students?token=${token}`);
        const students = await res.json();
        const tbody = document.getElementById('attendanceTableBody');
        
        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No students enrolled</td></tr>';
            return;
        }
        
        tbody.innerHTML = students.map(s => `
            <tr>
                <td>${s.school_id}</td>
                <td>${s.name}</td>
                <td>
                    <select class="attendance-status" data-student-id="${s.id}">
                        <option value="Present">Present</option>
                        <option value="Absent">Absent</option>
                        <option value="Late">Late</option>
                        <option value="Excused">Excused</option>
                    </select>
                </td>
                <td>
                    <input type="text" class="attendance-remarks" data-student-id="${s.id}" placeholder="Add remarks..." style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                </td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Error loading students:', e);
    }
}

/**
 * Loads attendance history for a class
 * @param {number} classId - Class schedule ID
 */
async function loadAttendanceHistory(classId) {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/class/${classId}/attendance?token=${token}`);
        const data = await res.json();
        const container = document.getElementById('attendanceHistoryContent');
        
        if (data.length === 0) {
            container.innerHTML = '<p class="empty-state">No attendance records yet</p>';
            return;
        }
        
        // Flatten attendance data for sorting
        allAttendanceHistoryData = [];
        data.forEach(student => {
            student.attendance.forEach(att => {
                allAttendanceHistoryData.push({
                    student_name: student.student_name,
                    date: att.date,
                    status: att.status,
                    remarks: att.remarks || '-'
                });
            });
        });
        
        renderAttendanceHistoryTable(allAttendanceHistoryData);
    } catch (e) {
        console.error('Error loading attendance history:', e);
    }
}

function renderAttendanceHistoryTable(records) {
    const container = document.getElementById('attendanceHistoryContent');
    let html = `<table class="data-table"><thead><tr>
        <th data-sort="student_name" data-table="attendanceHistory" style="cursor: pointer;">Student <i class="fas fa-sort" style="opacity: 0.5;"></i></th>
        <th data-sort="date" data-table="attendanceHistory" style="cursor: pointer;">Date <i class="fas fa-sort" style="opacity: 0.5;"></i></th>
        <th data-sort="status" data-table="attendanceHistory" style="cursor: pointer;">Status <i class="fas fa-sort" style="opacity: 0.5;"></i></th>
        <th>Remarks</th>
    </tr></thead><tbody>`;
    records.forEach(r => {
        html += `<tr><td>${r.student_name}</td><td>${r.date}</td><td><span class="status-badge status-${r.status.toLowerCase()}">${r.status}</span></td><td>${r.remarks}</td></tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
    
    // Re-setup sortable headers for dynamically added table
    container.querySelectorAll('th[data-sort]').forEach(th => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', () => {
            const tableType = th.dataset.table;
            const column = th.dataset.sort;
            handleSort(tableType, column);
        });
    });
}

/**
 * Loads assignments for a class
 * @param {number} classId - Class schedule ID
 */
async function loadAssignments(classId) {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/assignments/${classId}?token=${token}`);
        const assignments = await res.json();
        const tbody = document.getElementById('assignmentsTableBody');
        
        if (assignments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No assignments yet</td></tr>';
            return;
        }
        
        tbody.innerHTML = assignments.map(a => `
            <tr>
                <td>
                    <div style="font-weight: 500;">${a.name}</div>
                    ${a.description ? `<div style="font-size: 12px; color: var(--muted); margin-top: 4px;">${a.description.substring(0, 60)}${a.description.length > 60 ? '...' : ''}</div>` : ''}
                </td>
                <td>${a.due_date || '-'}</td>
                <td><span class="status-badge status-active">${a.submissions}</span></td>
                <td>
                    <button class="btn btn-small btn-primary" onclick="viewSubmissions(${a.id}, '${a.name.replace(/'/g, "\\'")}')"><i class="fas fa-file-alt"></i> Submissions</button>
                    <button class="btn btn-small btn-warning" onclick="openEditAssignmentModal(${a.id})" title="Edit"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-small btn-danger" onclick="deleteAssignment(${a.id})" title="Delete"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Error loading assignments:', e);
    }
}

/**
 * Views submissions for an assignment
 * @param {number} assignmentId - Assignment ID
 * @param {string} assignmentName - Assignment name for display
 */
async function viewSubmissions(assignmentId, assignmentName) {
    currentAssignmentId = assignmentId;
    const container = document.getElementById('submissionsList');
    container.innerHTML = '<p class="loading-text">Loading submissions...</p>';
    openModal('viewSubmissionsModal');
    
    try {
        const res = await fetch(`${API_BASE}/api/teacher/assignment/${assignmentId}/submissions?token=${token}`);
        const submissions = await res.json();
        
        if (submissions.length === 0) {
            container.innerHTML = '<p class="empty-state">No submissions yet</p>';
            return;
        }
        
        container.innerHTML = submissions.map(s => `
            <div class="submission-item">
                <div class="submission-header">
                    <div class="submission-student"><i class="fas fa-user"></i> ${s.student_name} (${s.student_school_id})</div>
                    <div class="submission-date"><i class="fas fa-calendar"></i> ${s.submission_date}</div>
                </div>
                <div class="submission-content">${s.content}</div>
                <div class="submission-grade">
                    <span>Grade: ${s.grade !== null && s.grade !== undefined ? s.grade : 'Not graded'}</span>
                    <button class="btn btn-small btn-success" onclick="openGradeSubmissionModal(${s.id}, '${s.student_name}', '${s.content.replace(/'/g, "\\'")}', ${s.grade !== null && s.grade !== undefined ? s.grade : 'null'})"><i class="fas fa-star"></i> Grade</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p class="empty-state">Error loading submissions</p>';
    }
}

/**
 * Opens modal to grade a submission
 * @param {number} submissionId - Submission ID
 * @param {string} studentName - Student name
 * @param {string} content - Submission content
 * @param {number} currentGrade - Current grade value
 */
function openGradeSubmissionModal(submissionId, studentName, content, currentGrade) {
    document.getElementById('gradeSubmissionId').value = submissionId;
    document.getElementById('gradeSubStudentName').value = studentName;
    document.getElementById('gradeSubContent').value = content;
    document.getElementById('gradeSubScore').value = currentGrade !== null && currentGrade !== undefined && currentGrade !== '' ? currentGrade : '';
    closeModal('viewSubmissionsModal');
    openModal('gradeSubmissionModal');
}

function getAutoRemarks(grade) {
    if (grade === null || grade === undefined) return '-';
    const score = parseFloat(grade);
    if (isNaN(score)) return '-';
    if (score >= 95) return 'Excellent';
    if (score >= 90) return 'Very Good';
    if (score >= 85) return 'Good';
    if (score >= 80) return 'Satisfactory';
    if (score >= 75) return 'Needs Improvement';
    return 'Failed';
}

/**
 * Opens modal to edit a student's grade
 * @param {number} enrollmentId - Enrollment ID
 * @param {string} studentName - Student name
 * @param {number} currentGrade - Current grade value
 * @param {string} currentRemarks - Current remarks
 */
function openGradeModal(enrollmentId, studentName, currentGrade, currentRemarks) {
    document.getElementById('gradeEnrollmentId').value = enrollmentId;
    document.getElementById('gradeStudentName').value = studentName;
    document.getElementById('gradeScore').value = currentGrade !== null && currentGrade !== undefined ? currentGrade : '';
    openModal('gradeModal');
}

/**
 * Opens modal to add/edit remarks for a student
 * @param {number} enrollmentId - Enrollment ID
 * @param {string} studentName - Student name
 * @param {string} currentRemarks - Current remarks
 */
function openRemarksModal(enrollmentId, studentName, currentRemarks) {
    document.getElementById('remarksEnrollmentId').value = enrollmentId;
    document.getElementById('remarksStudentName').value = studentName;
    document.getElementById('remarksText').value = currentRemarks || '';
    openModal('remarksModal');
}

/**
 * Sets up all event listeners for the dashboard
 */
function setupEventListeners() {
    // Menu navigation
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
            item.classList.add('active');
            const tab = item.dataset.tab;
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`${tab}Tab`).classList.add('active');
        });
    });

    // Class search filter
    document.getElementById('classSearch').addEventListener('input', (e) => {
        const search = e.target.value.toLowerCase();
        const filtered = allClasses.filter(c => 
            c.subject.toLowerCase().includes(search) || 
            c.room.toLowerCase().includes(search) ||
            c.day.toLowerCase().includes(search)
        );
        renderClasses(filtered);
    });

    // Logout handler
    document.getElementById('logoutBtn').addEventListener('click', async () => {
        await fetch(`${API_BASE}/api/logout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token })
        });
        localStorage.clear();
        window.location.href = '/';
    });

    // Class selection for grades
    document.getElementById('gradeClassSelect').addEventListener('change', (e) => {
        if (e.target.value) {
            currentClassId = parseInt(e.target.value);
            loadClassStudentsForGrades(currentClassId);
        }
    });

    // Class selection for attendance
    document.getElementById('attendanceClassSelect').addEventListener('change', (e) => {
        if (e.target.value) {
            currentClassId = parseInt(e.target.value);
            loadClassStudentsForAttendance(currentClassId);
        }
    });

    // Class selection for assignments
    document.getElementById('assignmentClassSelect').addEventListener('change', (e) => {
        if (e.target.value) {
            currentClassId = parseInt(e.target.value);
            loadAssignments(currentClassId);
        }
    });

    // Grade form submission - updates grade and refreshes view
    document.getElementById('gradeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const enrollmentId = document.getElementById('gradeEnrollmentId').value;
        const score = document.getElementById('gradeScore').value;

        try {
            const res = await fetch(`${API_BASE}/api/teacher/grade`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, enrollment_id: enrollmentId, score })
            });
            if (res.ok) {
                closeModal('gradeModal');
                loadClassStudentsForGrades(currentClassId);
                showAlert('Grade saved successfully', 'success');
            } else {
                showAlert('Error saving grade', 'error');
            }
        } catch (err) {
            showAlert('Error saving grade', 'error');
        }
    });

    // Grade submission form
    document.getElementById('gradeSubmissionForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const submissionId = document.getElementById('gradeSubmissionId').value;
        const grade = document.getElementById('gradeSubScore').value;

        try {
            const res = await fetch(`${API_BASE}/api/teacher/grade_submission/${submissionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, grade: parseFloat(grade) })
            });
            if (res.ok) {
                closeModal('gradeSubmissionModal');
                showAlert('Submission graded successfully', 'success');
                if (currentAssignmentId) {
                    viewSubmissions(currentAssignmentId, '');
                }
            } else {
                showAlert('Error grading submission', 'error');
            }
        } catch (err) {
            showAlert('Error grading submission', 'error');
        }
    });

    // Save attendance
    document.getElementById('saveAttendanceBtn').addEventListener('click', async () => {
        const dateInput = document.getElementById('attendanceDate').value;
        const scheduleId = document.getElementById('attendanceClassSelect').value;
        
        if (!scheduleId || !dateInput) {
            showAlert('Please select a class and date', 'warning');
            return;
        }

        const records = [];
        document.querySelectorAll('.attendance-status').forEach(select => {
            const studentId = select.dataset.studentId;
            const remarksInput = document.querySelector(`.attendance-remarks[data-student-id="${studentId}"]`);
            records.push({
                student_id: parseInt(studentId),
                status: select.value,
                remarks: remarksInput ? remarksInput.value : ''
            });
        });

        try {
            const res = await fetch(`${API_BASE}/api/teacher/attendance`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, date: dateInput, schedule_id: scheduleId, records })
            });
            if (res.ok) {
                showAlert('Attendance saved successfully', 'success');
            } else {
                showAlert('Error saving attendance', 'error');
            }
        } catch (err) {
            showAlert('Error saving attendance', 'error');
        }
    });

    // Add assignment button
    document.getElementById('addAssignmentBtn').addEventListener('click', () => {
        if (!currentClassId) {
            showAlert('Please select a class first', 'warning');
            return;
        }
        openModal('addAssignmentModal');
    });

    // Add assignment form
    document.getElementById('addAssignmentForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        data.token = token;
        data.schedule_id = currentClassId;

        try {
            const res = await fetch(`${API_BASE}/api/teacher/add_assignment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                closeModal('addAssignmentModal');
                loadAssignments(currentClassId);
                e.target.reset();
                showAlert('Assignment added successfully', 'success');
            } else {
                showAlert('Error adding assignment', 'error');
            }
        } catch (err) {
            showAlert('Error adding assignment', 'error');
        }
    });

    // Edit assignment form
    document.getElementById('editAssignmentForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const assignmentId = document.getElementById('editAssignmentId').value;
        const data = {
            token,
            name: document.getElementById('editAssignmentName').value,
            description: document.getElementById('editAssignmentDescription').value,
            due_date: document.getElementById('editAssignmentDueDate').value,
            max_points: parseInt(document.getElementById('editAssignmentMaxPoints').value) || 100
        };

        try {
            const res = await fetch(`${API_BASE}/api/teacher/edit_assignment/${assignmentId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                closeModal('editAssignmentModal');
                loadAssignments(currentClassId);
                showAlert('Assignment updated successfully', 'success');
            } else {
                showAlert('Error updating assignment', 'error');
            }
        } catch (err) {
            showAlert('Error updating assignment', 'error');
        }
    });

    // Remarks form
    document.getElementById('remarksForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const enrollmentId = document.getElementById('remarksEnrollmentId').value;
        const remarks = document.getElementById('remarksText').value;

        try {
            const res = await fetch(`${API_BASE}/api/teacher/add_remarks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, enrollment_id: enrollmentId, remarks })
            });
            if (res.ok) {
                closeModal('remarksModal');
                loadClassStudentsForGrades(currentClassId);
                showAlert('Remarks saved successfully', 'success');
            } else {
                showAlert('Error saving remarks', 'error');
            }
        } catch (err) {
            showAlert('Error saving remarks', 'error');
        }
    });

    // View Attendance History button
    document.getElementById('viewAttendanceHistoryBtn')?.addEventListener('click', () => {
        const classId = document.getElementById('attendanceClassSelect').value;
        if (!classId) {
            showAlert('Please select a class first', 'warning');
            return;
        }
        const historyDiv = document.getElementById('attendanceHistory');
        if (historyDiv.style.display === 'none' || !historyDiv.style.display) {
            historyDiv.style.display = 'block';
            loadAttendanceHistory(parseInt(classId));
        } else {
            historyDiv.style.display = 'none';
        }
    });

    // Request Profile Update button
    document.getElementById('requestUpdateBtn')?.addEventListener('click', () => openModal('updateRequestModal'));

    // Update request form submission
    document.getElementById('updateRequestForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const field = formData.get('field');
        const value = formData.get('value');

        try {
            const res = await fetch(`${API_BASE}/api/request_update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    token, 
                    type: `update_${field}`, 
                    details: { [field]: value } 
                })
            });
            if (res.ok) {
                closeModal('updateRequestModal');
                e.target.reset();
                showAlert('Update request submitted successfully', 'success');
            } else {
                showAlert('Error submitting request', 'error');
            }
        } catch (err) {
            showAlert('Error submitting request', 'error');
        }
    });
}

/**
 * Opens assignment details view
 * @param {number} assignmentId - Assignment ID
 */
async function viewAssignmentDetails(assignmentId) {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/assignment/${assignmentId}?token=${token}`);
        const assignment = await res.json();
        
        const content = `
            <div class="assignment-details">
                <h3>${assignment.name}</h3>
                <p><strong>Description:</strong> ${assignment.description || 'No description'}</p>
                <p><strong>Due Date:</strong> ${assignment.due_date || 'No due date'}</p>
                <p><strong>Max Points:</strong> ${assignment.max_points || 100}</p>
                <p><strong>Submissions:</strong> ${assignment.submissions || 0}</p>
            </div>
        `;
        
        document.getElementById('assignmentDetailsContent').innerHTML = content;
        openModal('assignmentDetailsModal');
    } catch (e) {
        showAlert('Error loading assignment details', 'error');
    }
}

/**
 * Opens edit assignment modal
 * @param {number} assignmentId - Assignment ID
 */
async function openEditAssignmentModal(assignmentId) {
    try {
        const res = await fetch(`${API_BASE}/api/teacher/assignment/${assignmentId}?token=${token}`);
        const assignment = await res.json();
        
        document.getElementById('editAssignmentId').value = assignment.id;
        document.getElementById('editAssignmentName').value = assignment.name;
        document.getElementById('editAssignmentDescription').value = assignment.description || '';
        document.getElementById('editAssignmentDueDate').value = assignment.due_date || '';
        document.getElementById('editAssignmentMaxPoints').value = assignment.max_points || 100;
        
        openModal('editAssignmentModal');
    } catch (e) {
        showAlert('Error loading assignment', 'error');
    }
}

/**
 * Deletes an assignment
 * @param {number} assignmentId - Assignment ID
 */
async function deleteAssignment(assignmentId) {
    if (!confirm('Are you sure you want to delete this assignment?')) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/teacher/delete_assignment/${assignmentId}?token=${token}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            loadAssignments(currentClassId);
            showAlert('Assignment deleted successfully', 'success');
        } else {
            showAlert('Error deleting assignment', 'error');
        }
    } catch (e) {
        showAlert('Error deleting assignment', 'error');
    }
}

/**
 * Opens a modal dialog
 * @param {string} id - Modal element ID
 */
function openModal(id) {
    document.getElementById(id).classList.add('show');
}

/**
 * Closes a modal dialog
 * @param {string} id - Modal element ID
 */
function closeModal(id) {
    document.getElementById(id).classList.remove('show');
}

/**
 * Displays an alert notification
 * @param {string} message - Alert message
 * @param {string} type - Alert type ('success', 'error', 'warning')
 */
function showAlert(message, type) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'exclamation-triangle'}"></i> ${message}`;
    document.getElementById('alertContainer').appendChild(alert);
    setTimeout(() => alert.remove(), 3000);
}
