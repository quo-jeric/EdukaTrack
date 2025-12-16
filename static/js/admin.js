/**
 * EdukaTrack Admin Dashboard JavaScript
 * 
 * This module handles the admin dashboard functionality including:
 * - Student, teacher, and schedule management
 * - Enrollment and update request processing
 * - Data sorting and filtering
 * - CRUD operations for all entities
 * 
 * Data Structures Used:
 * - Arrays: allStudents, allTeachers, allSchedules for storing fetched data
 * - Objects: dropdownData for caching dropdown options
 * - HashMap pattern: Used for quick lookups in dropdown population
 */

const token = localStorage.getItem('session_token');
const API_BASE = '';
let allStudents = [];
let allTeachers = [];
let allSchedules = [];
let dropdownData = {};

// Sorting state tracking for each table
let sortState = {
    students: { column: null, ascending: true },
    teachers: { column: null, ascending: true },
    schedules: { column: null, ascending: true }
};

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
            body: JSON.stringify({ token, role: 'admin' })
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('adminName').textContent = data.user || 'Admin';
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
 * Uses parallel API calls for efficiency
 */
function initializeDashboard() {
    loadStats();
    loadStudents();
    loadTeachers();
    loadSchedules();
    loadEnrollmentRequests();
    loadUpdateRequests();
    loadDropdowns();
    loadActivities();
    setupEventListeners();
}

/**
 * Loads dashboard statistics (counts)
 * Displays total students, teachers, schedules, and pending requests
 */
async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/stats?token=${token}`);
        const data = await res.json();
        document.getElementById('totalStudents').textContent = data.students || 0;
        document.getElementById('totalTeachers').textContent = data.teachers || 0;
        document.getElementById('totalSchedules').textContent = data.schedules || 0;
        document.getElementById('pendingRequests').textContent = data.pending_requests || 0;
    } catch (e) {
        console.error('Error loading stats:', e);
    }
}

/**
 * Loads recent activity feed
 * Displays admin-relevant activities with icons
 */
async function loadActivities() {
    try {
        const res = await fetch(`${API_BASE}/api/activities?token=${token}&role=admin&limit=10`);
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
            'edit': 'fas fa-edit',
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
 * Loads all student records from the API
 * Stores data in allStudents array for filtering/sorting
 */
async function loadStudents() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/students?token=${token}`);
        allStudents = await res.json();
        renderStudents(allStudents);
    } catch (e) {
        console.error('Error loading students:', e);
    }
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
        
        // Handle null/undefined values
        if (valA == null) valA = '';
        if (valB == null) valB = '';
        
        // Handle numeric values
        if (typeof valA === 'number' && typeof valB === 'number') {
            return ascending ? valA - valB : valB - valA;
        }
        
        // Handle string values (case-insensitive)
        valA = String(valA).toLowerCase();
        valB = String(valB).toLowerCase();
        
        if (valA < valB) return ascending ? -1 : 1;
        if (valA > valB) return ascending ? 1 : -1;
        return 0;
    });
}

/**
 * Handles column header click for sorting
 * @param {string} tableType - Type of table (students, teachers, schedules)
 * @param {string} column - Column key to sort by
 */
function handleSort(tableType, column) {
    const state = sortState[tableType];
    
    // Toggle direction if same column, otherwise reset to ascending
    if (state.column === column) {
        state.ascending = !state.ascending;
    } else {
        state.column = column;
        state.ascending = true;
    }
    
    // Re-render the appropriate table
    switch (tableType) {
        case 'students':
            renderStudents(sortArray(allStudents, column, state.ascending));
            break;
        case 'teachers':
            renderTeachers(sortArray(allTeachers, column, state.ascending));
            break;
        case 'schedules':
            renderSchedules(sortArray(allSchedules, column, state.ascending));
            break;
    }
    
    // Update sort indicators in header
    updateSortIndicators(tableType, column, state.ascending);
}

/**
 * Updates visual sort indicators on table headers
 * @param {string} tableType - Type of table
 * @param {string} activeColumn - Currently sorted column
 * @param {boolean} ascending - Sort direction
 */
function updateSortIndicators(tableType, activeColumn, ascending) {
    const tableId = tableType + 'TableBody';
    const table = document.getElementById(tableId)?.closest('table');
    if (!table) return;
    
    // Remove existing indicators
    table.querySelectorAll('th .sort-indicator').forEach(el => el.remove());
    
    // Add indicator to active column
    const headers = table.querySelectorAll('th[data-sort]');
    headers.forEach(th => {
        if (th.dataset.sort === activeColumn) {
            const indicator = document.createElement('i');
            indicator.className = `fas fa-sort-${ascending ? 'up' : 'down'} sort-indicator`;
            indicator.style.marginLeft = '5px';
            th.appendChild(indicator);
        }
    });
}

/**
 * Renders student table rows
 * @param {Array} students - Array of student objects
 */
function renderStudents(students) {
    const tbody = document.getElementById('studentsTableBody');
    tbody.innerHTML = students.map(s => `
        <tr>
            <td>${s.school_id}</td>
            <td>${s.name}</td>
            <td>${s.program}</td>
            <td>${s.year}</td>
            <td><span class="status-badge status-active">${s.status}</span></td>
            <td>
                <button class="btn btn-small btn-primary" onclick="openEditStudentModal(${s.id})"><i class="fas fa-edit"></i> Edit</button>
                <button class="btn btn-small btn-danger" onclick="deleteStudent(${s.id})"><i class="fas fa-trash"></i> Delete</button>
            </td>
        </tr>
    `).join('');
}

/**
 * Loads all teacher records from the API
 */
async function loadTeachers() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/teachers?token=${token}`);
        allTeachers = await res.json();
        renderTeachers(allTeachers);
    } catch (e) {
        console.error('Error loading teachers:', e);
    }
}

/**
 * Renders teacher table rows
 * @param {Array} teachers - Array of teacher objects
 */
function renderTeachers(teachers) {
    const tbody = document.getElementById('teachersTableBody');
    tbody.innerHTML = teachers.map(t => `
        <tr>
            <td>${t.school_id}</td>
            <td>${t.name}</td>
            <td>${t.department}</td>
            <td>${t.specialization}</td>
            <td>
                <button class="btn btn-small btn-primary" onclick="openEditTeacherModal(${t.id})"><i class="fas fa-edit"></i> Edit</button>
                <button class="btn btn-small btn-danger" onclick="deleteTeacher(${t.id})"><i class="fas fa-trash"></i> Delete</button>
            </td>
        </tr>
    `).join('');
}

/**
 * Loads all schedule records from the API
 */
async function loadSchedules() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/schedules?token=${token}`);
        allSchedules = await res.json();
        renderSchedules(allSchedules);
    } catch (e) {
        console.error('Error loading schedules:', e);
    }
}

/**
 * Renders schedule table rows with formatted day names
 * @param {Array} schedules - Array of schedule objects
 */
function renderSchedules(schedules) {
    const tbody = document.getElementById('schedulesTableBody');
    tbody.innerHTML = schedules.map(s => `
        <tr>
            <td>${s.id}</td>
            <td>${s.subject}</td>
            <td>${s.teacher}</td>
            <td>${formatDayName(s.day)}</td>
            <td>${s.time}</td>
            <td>${s.room}</td>
            <td>
                <button class="btn btn-small btn-primary" onclick="openEditScheduleModal(${s.id})"><i class="fas fa-edit"></i> Edit</button>
                <button class="btn btn-small btn-danger" onclick="deleteSchedule(${s.id})"><i class="fas fa-trash"></i> Delete</button>
            </td>
        </tr>
    `).join('');
}

/**
 * Loads pending enrollment requests
 */
async function loadEnrollmentRequests() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/enrollment_requests?token=${token}`);
        const requests = await res.json();
        const tbody = document.getElementById('enrollmentRequestsBody');
        if (requests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No pending enrollment requests</td></tr>';
        } else {
            tbody.innerHTML = requests.map(r => `
                <tr>
                    <td>${r.id}</td>
                    <td>${r.student}</td>
                    <td>${r.subject}</td>
                    <td>${r.date}</td>
                    <td>
                        <button class="btn btn-small btn-success" onclick="handleEnrollment(${r.id}, 'approve')"><i class="fas fa-check"></i> Approve</button>
                        <button class="btn btn-small btn-danger" onclick="handleEnrollment(${r.id}, 'deny')"><i class="fas fa-times"></i> Deny</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        console.error('Error loading enrollment requests:', e);
    }
}

/**
 * Loads pending update requests
 * Displays type and details without redundancy
 */
async function loadUpdateRequests() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/update_requests?token=${token}`);
        const requests = await res.json();
        const tbody = document.getElementById('updateRequestsBody');
        if (requests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No pending update requests</td></tr>';
        } else {
            tbody.innerHTML = requests.map(r => `
                <tr>
                    <td>${r.id}</td>
                    <td>${r.user} <span style="color: var(--muted); font-size: 12px;">(${r.user_role || 'User'})</span></td>
                    <td><span class="status-badge status-pending">${r.type}</span></td>
                    <td style="max-width: 300px; word-wrap: break-word;">${r.details}</td>
                    <td>
                        <button class="btn btn-small btn-success" onclick="handleUpdate(${r.id}, 'approve')"><i class="fas fa-check"></i> Approve</button>
                        <button class="btn btn-small btn-danger" onclick="handleUpdate(${r.id}, 'deny')"><i class="fas fa-times"></i> Deny</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        console.error('Error loading update requests:', e);
    }
}

/**
 * Loads update request history (all processed requests)
 */
async function loadUpdateRequestHistory() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/update_request_history?token=${token}`);
        const requests = await res.json();
        const container = document.getElementById('updateHistoryContent');
        
        if (requests.length === 0) {
            container.innerHTML = '<p class="empty-state">No update request history</p>';
            return;
        }
        
        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>User</th>
                        <th>Type</th>
                        <th>Details</th>
                        <th>Status</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    ${requests.map(r => `
                        <tr>
                            <td>${r.id}</td>
                            <td>${r.user}</td>
                            <td>${r.type}</td>
                            <td style="max-width: 200px; word-wrap: break-word;">${r.details}</td>
                            <td><span class="status-badge status-${r.status === 'approved' ? 'active' : 'inactive'}">${r.status}</span></td>
                            <td>${r.date || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (e) {
        console.error('Error loading update history:', e);
        document.getElementById('updateHistoryContent').innerHTML = '<p class="empty-state">Error loading history</p>';
    }
}

/**
 * Opens the update request history modal
 */
function openUpdateHistory() {
    loadUpdateRequestHistory();
    openModal('updateHistoryModal');
}

/**
 * Loads dropdown data for forms (programs, departments, subjects, etc.)
 * Caches data for reuse across multiple forms
 */
async function loadDropdowns() {
    try {
        const [programs, departments, subjects, rooms, teachers] = await Promise.all([
            fetch(`${API_BASE}/api/admin/programs?token=${token}`).then(r => r.json()),
            fetch(`${API_BASE}/api/admin/departments?token=${token}`).then(r => r.json()),
            fetch(`${API_BASE}/api/admin/subjects?token=${token}`).then(r => r.json()),
            fetch(`${API_BASE}/api/admin/rooms?token=${token}`).then(r => r.json()),
            fetch(`${API_BASE}/api/admin/teachers?token=${token}`).then(r => r.json())
        ]);

        dropdownData = { programs, departments, subjects, rooms, teachers };

        document.getElementById('studentProgramSelect').innerHTML = programs.map(p => 
            `<option value="${p.id}">${p.code} - ${p.name}</option>`
        ).join('');

        document.getElementById('teacherDeptSelect').innerHTML = departments.map(d => 
            `<option value="${d.id}">${d.code} - ${d.name}</option>`
        ).join('');

        document.getElementById('scheduleSubjectSelect').innerHTML = subjects.map(s => 
            `<option value="${s.id}">${s.code} - ${s.name}</option>`
        ).join('');

        document.getElementById('scheduleRoomSelect').innerHTML = rooms.map(r => 
            `<option value="${r.id}">${r.name}</option>`
        ).join('');

        document.getElementById('scheduleTeacherSelect').innerHTML = teachers.map(t => 
            `<option value="${t.id}">${t.name}</option>`
        ).join('');

        document.getElementById('editStudentProgram').innerHTML = programs.map(p => 
            `<option value="${p.id}">${p.code} - ${p.name}</option>`
        ).join('');

        document.getElementById('editTeacherDept').innerHTML = departments.map(d => 
            `<option value="${d.id}">${d.code} - ${d.name}</option>`
        ).join('');

        document.getElementById('editScheduleSubject').innerHTML = subjects.map(s => 
            `<option value="${s.id}">${s.code} - ${s.name}</option>`
        ).join('');

        document.getElementById('editScheduleTeacher').innerHTML = teachers.map(t => 
            `<option value="${t.id}">${t.name}</option>`
        ).join('');

        document.getElementById('editScheduleRoom').innerHTML = rooms.map(r => 
            `<option value="${r.id}">${r.name}</option>`
        ).join('');
    } catch (e) {
        console.error('Error loading dropdowns:', e);
    }
}

/**
 * Opens edit student modal and populates with current data
 * @param {number} userId - User ID of student to edit
 */
async function openEditStudentModal(userId) {
    try {
        const res = await fetch(`${API_BASE}/api/admin/get_student/${userId}?token=${token}`);
        const student = await res.json();
        
        document.getElementById('editStudentId').value = student.user_id;
        document.getElementById('editStudentFirstName').value = student.first_name;
        document.getElementById('editStudentLastName').value = student.last_name;
        document.getElementById('editStudentEmail').value = student.email;
        document.getElementById('editStudentPhone').value = student.phone_number || '';
        document.getElementById('editStudentStreet').value = student.street_address || '';
        document.getElementById('editStudentBarangay').value = student.baranggay || '';
        document.getElementById('editStudentCity').value = student.city || '';
        document.getElementById('editStudentProvince').value = student.province || '';
        document.getElementById('editStudentZipCode').value = student.zip_code || '';
        document.getElementById('editStudentProgram').value = student.program_id;
        document.getElementById('editStudentYear').value = student.year_level;
        document.getElementById('editStudentTerm').value = student.term || '1st Semester';
        document.getElementById('editStudentSection').value = student.section || '';
        document.getElementById('editStudentStatus').value = student.status;
        
        openModal('editStudentModal');
    } catch (e) {
        showAlert('Error loading student details', 'error');
    }
}

/**
 * Opens edit teacher modal and populates with current data
 * @param {number} userId - User ID of teacher to edit
 */
async function openEditTeacherModal(userId) {
    try {
        const res = await fetch(`${API_BASE}/api/admin/get_teacher/${userId}?token=${token}`);
        const teacher = await res.json();
        
        document.getElementById('editTeacherId').value = teacher.user_id;
        document.getElementById('editTeacherFirstName').value = teacher.first_name;
        document.getElementById('editTeacherLastName').value = teacher.last_name;
        document.getElementById('editTeacherEmail').value = teacher.email;
        document.getElementById('editTeacherPhone').value = teacher.phone_number || '';
        document.getElementById('editTeacherStreet').value = teacher.street_address || '';
        document.getElementById('editTeacherBarangay').value = teacher.baranggay || '';
        document.getElementById('editTeacherCity').value = teacher.city || '';
        document.getElementById('editTeacherProvince').value = teacher.province || '';
        document.getElementById('editTeacherZipCode').value = teacher.zip_code || '';
        document.getElementById('editTeacherDept').value = teacher.department_id;
        document.getElementById('editTeacherSpec').value = teacher.specialization;
        document.getElementById('editTeacherOffice').value = teacher.office_location || '';
        document.getElementById('editTeacherHours').value = teacher.office_hours || '';
        document.getElementById('editTeacherStatus').value = teacher.status;
        
        openModal('editTeacherModal');
    } catch (e) {
        showAlert('Error loading teacher details', 'error');
    }
}

/**
 * Opens edit schedule modal and populates with current data
 * @param {number} scheduleId - Schedule ID to edit
 */
async function openEditScheduleModal(scheduleId) {
    try {
        const res = await fetch(`${API_BASE}/api/admin/get_schedule/${scheduleId}?token=${token}`);
        const schedule = await res.json();
        
        document.getElementById('editScheduleId').value = schedule.id;
        document.getElementById('editScheduleSubject').value = schedule.subject_id;
        document.getElementById('editScheduleTeacher').value = schedule.teacher_id;
        document.getElementById('editScheduleRoom').value = schedule.room_id;
        document.getElementById('editScheduleSection').value = schedule.section || '';
        document.getElementById('editScheduleDay').value = schedule.day;
        document.getElementById('editScheduleStart').value = schedule.start_time;
        document.getElementById('editScheduleEnd').value = schedule.end_time;
        
        openModal('editScheduleModal');
    } catch (e) {
        showAlert('Error loading schedule details', 'error');
    }
}

/**
 * Sets up all event listeners for the dashboard
 * Includes menu navigation, form submissions, and search filters
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

    // Modal open buttons
    document.getElementById('addStudentBtn').addEventListener('click', () => openModal('addStudentModal'));
    document.getElementById('addTeacherBtn').addEventListener('click', () => openModal('addTeacherModal'));
    document.getElementById('addScheduleBtn').addEventListener('click', () => openModal('addScheduleModal'));

    // Add Student Form
    document.getElementById('addStudentForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        data.token = token;

        try {
            const res = await fetch(`${API_BASE}/api/admin/add_student`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await res.json();
            if (res.ok) {
                closeModal('addStudentModal');
                document.getElementById('newSchoolId').value = result.id;
                document.getElementById('newPassword').value = result.password;
                openModal('credentialsModal');
                loadStudents();
                loadStats();
                e.target.reset();
                showAlert('Student added successfully!', 'success');
            } else {
                showAlert(result.message || 'Error adding student', 'error');
            }
        } catch (err) {
            showAlert('Error adding student', 'error');
        }
    });

    // Edit Student Form
    document.getElementById('editStudentForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const studentId = document.getElementById('editStudentId').value;
        
        const data = {
            token,
            first_name: document.getElementById('editStudentFirstName').value,
            last_name: document.getElementById('editStudentLastName').value,
            email: document.getElementById('editStudentEmail').value,
            phone_number: document.getElementById('editStudentPhone').value,
            street_address: document.getElementById('editStudentStreet').value,
            baranggay: document.getElementById('editStudentBarangay').value,
            city: document.getElementById('editStudentCity').value,
            province: document.getElementById('editStudentProvince').value,
            zip_code: document.getElementById('editStudentZipCode').value,
            program_id: parseInt(document.getElementById('editStudentProgram').value),
            year_level: parseInt(document.getElementById('editStudentYear').value),
            term: document.getElementById('editStudentTerm').value,
            section: document.getElementById('editStudentSection').value,
            status: document.getElementById('editStudentStatus').value
        };

        try {
            const res = await fetch(`${API_BASE}/api/admin/edit_student/${studentId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                closeModal('editStudentModal');
                loadStudents();
                showAlert('Student updated successfully!', 'success');
            } else {
                showAlert('Error updating student', 'error');
            }
        } catch (err) {
            showAlert('Error updating student', 'error');
        }
    });

    // Add Teacher Form
    document.getElementById('addTeacherForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        data.token = token;

        try {
            const res = await fetch(`${API_BASE}/api/admin/add_teacher`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await res.json();
            if (res.ok) {
                closeModal('addTeacherModal');
                document.getElementById('newSchoolId').value = result.id;
                document.getElementById('newPassword').value = result.password;
                openModal('credentialsModal');
                loadTeachers();
                loadStats();
                loadDropdowns();
                e.target.reset();
                showAlert('Teacher added successfully!', 'success');
            } else {
                showAlert(result.message || 'Error adding teacher', 'error');
            }
        } catch (err) {
            showAlert('Error adding teacher', 'error');
        }
    });

    // Edit Teacher Form
    document.getElementById('editTeacherForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const teacherId = document.getElementById('editTeacherId').value;
        
        const data = {
            token,
            first_name: document.getElementById('editTeacherFirstName').value,
            last_name: document.getElementById('editTeacherLastName').value,
            email: document.getElementById('editTeacherEmail').value,
            phone_number: document.getElementById('editTeacherPhone').value,
            street_address: document.getElementById('editTeacherStreet').value,
            baranggay: document.getElementById('editTeacherBarangay').value,
            city: document.getElementById('editTeacherCity').value,
            province: document.getElementById('editTeacherProvince').value,
            zip_code: document.getElementById('editTeacherZipCode').value,
            department_id: parseInt(document.getElementById('editTeacherDept').value),
            specialization: document.getElementById('editTeacherSpec').value,
            office_location: document.getElementById('editTeacherOffice').value,
            office_hours: document.getElementById('editTeacherHours').value,
            status: document.getElementById('editTeacherStatus').value
        };

        try {
            const res = await fetch(`${API_BASE}/api/admin/edit_teacher/${teacherId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                closeModal('editTeacherModal');
                loadTeachers();
                showAlert('Teacher updated successfully!', 'success');
            } else {
                showAlert('Error updating teacher', 'error');
            }
        } catch (err) {
            showAlert('Error updating teacher', 'error');
        }
    });

    // Add Schedule Form
    document.getElementById('addScheduleForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        data.token = token;

        try {
            const res = await fetch(`${API_BASE}/api/admin/add_schedule`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await res.json();
            if (res.ok) {
                closeModal('addScheduleModal');
                loadSchedules();
                loadStats();
                e.target.reset();
                showAlert('Schedule added successfully!', 'success');
            } else {
                showAlert(result.message || 'Error adding schedule', 'error');
            }
        } catch (err) {
            showAlert('Error adding schedule', 'error');
        }
    });

    // Edit Schedule Form
    document.getElementById('editScheduleForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const scheduleId = document.getElementById('editScheduleId').value;
        
        const data = {
            token,
            subject_id: parseInt(document.getElementById('editScheduleSubject').value),
            teacher_id: parseInt(document.getElementById('editScheduleTeacher').value),
            room_id: parseInt(document.getElementById('editScheduleRoom').value),
            section: document.getElementById('editScheduleSection').value,
            day: document.getElementById('editScheduleDay').value,
            start_time: document.getElementById('editScheduleStart').value,
            end_time: document.getElementById('editScheduleEnd').value
        };

        try {
            const res = await fetch(`${API_BASE}/api/admin/edit_schedule/${scheduleId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                closeModal('editScheduleModal');
                loadSchedules();
                showAlert('Schedule updated successfully!', 'success');
            } else {
                showAlert('Error updating schedule', 'error');
            }
        } catch (err) {
            showAlert('Error updating schedule', 'error');
        }
    });

    // Search filters
    document.getElementById('studentSearch').addEventListener('input', (e) => {
        const search = e.target.value.toLowerCase();
        const filtered = allStudents.filter(s => 
            s.school_id.toLowerCase().includes(search) || 
            s.name.toLowerCase().includes(search) ||
            s.program.toLowerCase().includes(search)
        );
        renderStudents(filtered);
    });

    document.getElementById('teacherSearch').addEventListener('input', (e) => {
        const search = e.target.value.toLowerCase();
        const filtered = allTeachers.filter(t => 
            t.school_id.toLowerCase().includes(search) || 
            t.name.toLowerCase().includes(search) ||
            t.department.toLowerCase().includes(search)
        );
        renderTeachers(filtered);
    });

    document.getElementById('scheduleSearch').addEventListener('input', (e) => {
        const search = e.target.value.toLowerCase();
        const filtered = allSchedules.filter(s => 
            s.subject.toLowerCase().includes(search) || 
            s.teacher.toLowerCase().includes(search) ||
            s.room.toLowerCase().includes(search)
        );
        renderSchedules(filtered);
    });
    
    // Setup sortable headers
    setupSortableHeaders();
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

/**
 * Deletes a student record
 * @param {number} id - Student ID to delete
 */
async function deleteStudent(id) {
    if (!confirm('Are you sure you want to delete this student?')) return;
    try {
        const res = await fetch(`${API_BASE}/api/admin/delete_student/${id}?token=${token}`, { method: 'DELETE' });
        if (res.ok) {
            loadStudents();
            loadStats();
            showAlert('Student deleted successfully', 'success');
        } else {
            showAlert('Error deleting student', 'error');
        }
    } catch (e) {
        showAlert('Error deleting student', 'error');
    }
}

/**
 * Deletes a teacher record
 * @param {number} id - Teacher ID to delete
 */
async function deleteTeacher(id) {
    if (!confirm('Are you sure you want to delete this teacher?')) return;
    try {
        const res = await fetch(`${API_BASE}/api/admin/delete_teacher/${id}?token=${token}`, { method: 'DELETE' });
        if (res.ok) {
            loadTeachers();
            loadStats();
            showAlert('Teacher deleted successfully', 'success');
        } else {
            showAlert('Error deleting teacher', 'error');
        }
    } catch (e) {
        showAlert('Error deleting teacher', 'error');
    }
}

/**
 * Deletes a schedule record
 * @param {number} id - Schedule ID to delete
 */
async function deleteSchedule(id) {
    if (!confirm('Are you sure you want to delete this schedule?')) return;
    try {
        const res = await fetch(`${API_BASE}/api/admin/delete_schedule/${id}?token=${token}`, { method: 'DELETE' });
        if (res.ok) {
            loadSchedules();
            loadStats();
            showAlert('Schedule deleted successfully', 'success');
        } else {
            showAlert('Error deleting schedule', 'error');
        }
    } catch (e) {
        showAlert('Error deleting schedule', 'error');
    }
}

/**
 * Handles enrollment request approval/denial
 * @param {number} id - Request ID
 * @param {string} action - 'approve' or 'deny'
 */
async function handleEnrollment(id, action) {
    try {
        const res = await fetch(`${API_BASE}/api/admin/handle_enrollment_request/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, action })
        });
        if (res.ok) {
            loadEnrollmentRequests();
            loadStats();
            const actionText = action === 'approve' ? 'approved' : 'denied';
            showAlert(`Enrollment request ${actionText}`, 'success');
        } else {
            showAlert('Error handling request', 'error');
        }
    } catch (e) {
        showAlert('Error handling request', 'error');
    }
}

/**
 * Handles update request approval/denial
 * @param {number} id - Request ID
 * @param {string} action - 'approve' or 'deny'
 */
async function handleUpdate(id, action) {
    try {
        const res = await fetch(`${API_BASE}/api/admin/handle_update_request/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, action })
        });
        if (res.ok) {
            loadUpdateRequests();
            const actionText = action === 'approve' ? 'approved' : 'denied';
            showAlert(`Update request ${actionText}`, 'success');
        } else {
            showAlert('Error handling request', 'error');
        }
    } catch (e) {
        showAlert('Error handling request', 'error');
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
