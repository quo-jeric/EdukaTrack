/**
 * EdukaTrack Student Dashboard JavaScript
 * 
 * This module handles the student dashboard functionality including:
 * - Schedule viewing with formatted day names
 * - Grade tracking and display
 * - Attendance monitoring
 * - Assignment submission
 * - Class enrollment requests
 * - Profile update requests
 * 
 * Data Structures Used:
 * - Arrays: allSchedule, allAssignments, allClasses for storing fetched data
 * - Dynamic rendering: All tables use map/join for efficient DOM updates
 * - Queue pattern: Update requests processed in FIFO order by admin
 */

const token = localStorage.getItem('session_token');
const API_BASE = '';
let allSchedule = [];
let allAssignments = [];
let allClasses = [];

// Sorting state for tables
let sortState = {
    schedule: { column: null, ascending: true },
    assignments: { column: null, ascending: true },
    classes: { column: null, ascending: true }
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
            body: JSON.stringify({ token, role: 'student' })
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('studentName').textContent = data.user || 'Student';
            document.getElementById('userName').textContent = data.user || 'Student';
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
    loadSchedule();
    loadGrades();
    loadAttendance();
    loadAssignments();
    loadAvailableClasses();
    loadActivities();
    setupEventListeners();
    setupSortableHeaders();
}

/**
 * Loads student profile information
 */
async function loadProfile() {
    try {
        const res = await fetch(`${API_BASE}/api/student/profile?token=${token}`);
        const profile = await res.json();
        document.getElementById('profileId').textContent = profile.id;
        document.getElementById('profileName').textContent = profile.name;
        document.getElementById('profileEmail').textContent = profile.email;
        document.getElementById('profilePhone').textContent = profile.phone || '-';
        document.getElementById('profileProgram').textContent = profile.program;
        document.getElementById('profileYear').textContent = profile.year;
        document.getElementById('profileTerm').textContent = profile.term || '-';
        document.getElementById('profileSection').textContent = profile.section || '-';
        document.getElementById('profileAddress').textContent = profile.address || '-';
        document.getElementById('profileStatus').textContent = profile.status;
    } catch (e) {
        console.error('Error loading profile:', e);
    }
}

/**
 * Loads recent activity feed for student
 */
async function loadActivities() {
    try {
        const res = await fetch(`${API_BASE}/api/activities?token=${token}&role=student&limit=10`);
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
            'announcement': 'fas fa-bullhorn'
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
 * Loads student's class schedule
 */
async function loadSchedule() {
    try {
        const res = await fetch(`${API_BASE}/api/student/schedule?token=${token}`);
        allSchedule = await res.json();
        
        document.getElementById('enrolledCourses').textContent = allSchedule.length;
        renderSchedule(allSchedule);
    } catch (e) {
        console.error('Error loading schedule:', e);
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
    
    switch (tableType) {
        case 'schedule':
            renderSchedule(sortArray(allSchedule, column, state.ascending));
            break;
        case 'assignments':
            renderAssignments(sortArray(allAssignments, column, state.ascending));
            break;
        case 'classes':
            renderAvailableClasses(sortArray(allClasses, column, state.ascending));
            break;
    }
}

/**
 * Renders schedule table with formatted day names
 * @param {Array} schedule - Array of schedule objects
 */
function renderSchedule(schedule) {
    const tbody = document.getElementById('scheduleTableBody');
    if (schedule.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No classes enrolled yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = schedule.map(s => `
        <tr>
            <td>${s.subject}</td>
            <td>${s.teacher}</td>
            <td>${formatDayName(s.day)}</td>
            <td>${s.time}</td>
            <td>${s.room}</td>
        </tr>
    `).join('');
}

/**
 * Loads student grades with calculated average
 * Uses DynamicArray pattern from backend for sorting
 */
async function loadGrades() {
    try {
        const res = await fetch(`${API_BASE}/api/student/grades?token=${token}`);
        const data = await res.json();
        
        document.getElementById('avgGrade').textContent = data.average || '-';
        document.getElementById('gradesAverage').textContent = data.average || '-';
        
        const grid = document.getElementById('gradesGrid');
        if (data.grades.length === 0) {
            grid.innerHTML = '<div class="empty-state">No grades yet</div>';
            return;
        }
        
        grid.innerHTML = data.grades.map(g => {
            let gradeClass = 'average';
            if (g.score >= 85) gradeClass = 'good';
            else if (g.score !== null && g.score < 75) gradeClass = 'poor';
            
            return `
                <div class="grade-card">
                    <div class="grade-subject">${g.subject}</div>
                    <div class="grade-value ${gradeClass}">${g.score !== null && g.score !== undefined ? g.score : '-'}</div>
                    <span class="status-badge status-${g.status.toLowerCase()}">${g.status}</span>
                    <div class="grade-remarks" style="font-size: 12px; color: #666; margin-top: 5px;">Remarks: ${getAutoRemarks(g.score)}</div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Error loading grades:', e);
    }
}

/**
 * Loads student attendance records
 * Displays summary statistics and detailed records per subject
 */
async function loadAttendance() {
    try {
        const res = await fetch(`${API_BASE}/api/student/attendance?token=${token}`);
        const data = await res.json();
        
        const summaryDiv = document.getElementById('attendanceSummary');
        const detailsDiv = document.getElementById('attendanceDetails');
        
        if (data.length === 0) {
            summaryDiv.innerHTML = '<div class="empty-state">No attendance records yet</div>';
            detailsDiv.innerHTML = '';
            return;
        }
        
        // Calculate totals across all subjects
        let totalPresent = 0, totalAbsent = 0, totalLate = 0, totalExcused = 0;
        data.forEach(d => {
            totalPresent += d.present;
            totalAbsent += d.absent;
            totalLate += d.late;
            totalExcused += d.excused;
        });
        
        summaryDiv.innerHTML = `
            <div class="stats-grid" style="margin-bottom: 20px;">
                <div class="stat-card" style="background: linear-gradient(135deg, #10b981, #059669);">
                    <div class="stat-icon"><i class="fas fa-check"></i></div>
                    <div class="stat-label" style="color: rgba(255,255,255,0.9);">Present</div>
                    <div class="stat-value" style="color: #fff;">${totalPresent}</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #ef4444, #dc2626);">
                    <div class="stat-icon"><i class="fas fa-times"></i></div>
                    <div class="stat-label" style="color: rgba(255,255,255,0.9);">Absent</div>
                    <div class="stat-value" style="color: #fff;">${totalAbsent}</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #f59e0b, #d97706);">
                    <div class="stat-icon"><i class="fas fa-clock"></i></div>
                    <div class="stat-label" style="color: rgba(255,255,255,0.9);">Late</div>
                    <div class="stat-value" style="color: #fff;">${totalLate}</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #3b82f6, #2563eb);">
                    <div class="stat-icon"><i class="fas fa-file-medical"></i></div>
                    <div class="stat-label" style="color: rgba(255,255,255,0.9);">Excused</div>
                    <div class="stat-value" style="color: #fff;">${totalExcused}</div>
                </div>
            </div>
        `;
        
        // Render detailed records per subject
        let detailsHtml = '';
        data.forEach(subject => {
            detailsHtml += `
                <div class="content-section" style="margin-bottom: 20px;">
                    <h3><i class="fas fa-book"></i> ${subject.subject}</h3>
                    <p style="margin-bottom: 10px;">Present: ${subject.present} | Absent: ${subject.absent} | Late: ${subject.late} | Excused: ${subject.excused}</p>
                    ${subject.records.length > 0 ? `
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Status</th>
                                    <th>Remarks</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${subject.records.map(r => `
                                    <tr>
                                        <td>${r.date}</td>
                                        <td><span class="status-badge status-${r.status.toLowerCase()}">${r.status}</span></td>
                                        <td>${r.remarks || '-'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    ` : '<p class="empty-state">No records for this subject</p>'}
                </div>
            `;
        });
        detailsDiv.innerHTML = detailsHtml;
    } catch (e) {
        console.error('Error loading attendance:', e);
    }
}

/**
 * Loads assignments for the student
 */
async function loadAssignments() {
    try {
        const res = await fetch(`${API_BASE}/api/student/assignments?token=${token}`);
        allAssignments = await res.json();
        
        const pending = allAssignments.filter(a => !a.submitted).length;
        document.getElementById('pendingAssignments').textContent = pending;
        renderAssignments(allAssignments);
    } catch (e) {
        console.error('Error loading assignments:', e);
    }
}

/**
 * Renders assignments table
 * @param {Array} assignments - Array of assignment objects
 */
function renderAssignments(assignments) {
    const tbody = document.getElementById('assignmentsTableBody');
    if (assignments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No assignments yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = assignments.map(a => `
        <tr>
            <td>
                <div style="font-weight: 500;">${a.name}</div>
                ${a.description ? `<div style="font-size: 12px; color: var(--muted); margin-top: 4px;">${a.description.substring(0, 50)}${a.description.length > 50 ? '...' : ''}</div>` : ''}
            </td>
            <td>${a.subject}</td>
            <td><i class="fas fa-user-tie" style="color: var(--primary); margin-right: 5px;"></i>${a.teacher || 'N/A'}</td>
            <td>${a.due_date || '-'}</td>
            <td><span class="status-badge ${a.submitted ? 'status-active' : 'status-pending'}">${a.submitted ? 'Submitted' : 'Pending'}</span></td>
            <td>${a.grade !== null && a.grade !== undefined ? a.grade : '-'}</td>
            <td>
                ${!a.submitted ? `<button class="btn btn-small btn-primary" onclick="openSubmitModal(${a.id}, '${a.name.replace(/'/g, "\\'")}')"><i class="fas fa-paper-plane"></i> Submit</button>` : '<span style="color: var(--success);"><i class="fas fa-check"></i> Done</span>'}
            </td>
        </tr>
    `).join('');
}

/**
 * Loads available classes for enrollment
 */
async function loadAvailableClasses() {
    try {
        const res = await fetch(`${API_BASE}/api/student/available_classes?token=${token}`);
        allClasses = await res.json();
        renderAvailableClasses(allClasses);
    } catch (e) {
        console.error('Error loading available classes:', e);
    }
}

/**
 * Renders available classes table with formatted day names
 * @param {Array} classes - Array of class objects
 */
function renderAvailableClasses(classes) {
    const tbody = document.getElementById('availableClassesBody');
    if (classes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No available classes</td></tr>';
        return;
    }
    
    tbody.innerHTML = classes.map(c => `
        <tr>
            <td>${c.subject}</td>
            <td>${c.teacher}</td>
            <td>${formatDayName(c.day)}</td>
            <td>${c.time}</td>
            <td>${c.room}</td>
            <td>
                <button class="btn btn-small btn-success" onclick="requestEnrollment(${c.id})"><i class="fas fa-plus"></i> Enroll</button>
            </td>
        </tr>
    `).join('');
}

/**
 * Opens modal to submit an assignment
 * @param {number} taskId - Assignment ID
 * @param {string} taskName - Assignment name
 */
function openSubmitModal(taskId, taskName) {
    document.getElementById('submitTaskId').value = taskId;
    document.getElementById('submitTaskName').value = taskName;
    openModal('submitAssignmentModal');
}

/**
 * Requests enrollment in a class
 * Uses queue pattern - request is added to enrollment queue
 * @param {number} classId - Class schedule ID
 */
async function requestEnrollment(classId) {
    try {
        const res = await fetch(`${API_BASE}/api/student/request_enroll/${classId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token })
        });
        const data = await res.json();
        if (res.ok) {
            loadAvailableClasses();
            showAlert('Enrollment request submitted', 'success');
        } else {
            showAlert(data.message || 'Error requesting enrollment', 'error');
        }
    } catch (e) {
        showAlert('Error requesting enrollment', 'error');
    }
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

    // Schedule search filter
    document.getElementById('scheduleSearch').addEventListener('input', (e) => {
        const search = e.target.value.toLowerCase();
        const filtered = allSchedule.filter(s => 
            s.subject.toLowerCase().includes(search) || 
            s.teacher.toLowerCase().includes(search) ||
            s.room.toLowerCase().includes(search) ||
            s.day.toLowerCase().includes(search)
        );
        renderSchedule(filtered);
    });

    // Assignment search filter
    document.getElementById('assignmentSearch').addEventListener('input', (e) => {
        const search = e.target.value.toLowerCase();
        const filtered = allAssignments.filter(a => 
            a.name.toLowerCase().includes(search) || 
            a.subject.toLowerCase().includes(search)
        );
        renderAssignments(filtered);
    });

    // Classes search filter
    document.getElementById('classesSearch').addEventListener('input', (e) => {
        const search = e.target.value.toLowerCase();
        const filtered = allClasses.filter(c => 
            c.subject.toLowerCase().includes(search) || 
            c.teacher.toLowerCase().includes(search) ||
            c.room.toLowerCase().includes(search)
        );
        renderAvailableClasses(filtered);
    });

    // Submit assignment form
    document.getElementById('submitAssignmentForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const taskId = document.getElementById('submitTaskId').value;
        const content = e.target.querySelector('[name="content"]').value;

        try {
            const res = await fetch(`${API_BASE}/api/student/submit_task/${taskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, content })
            });
            if (res.ok) {
                closeModal('submitAssignmentModal');
                loadAssignments();
                e.target.reset();
                showAlert('Assignment submitted successfully', 'success');
            } else {
                showAlert('Error submitting assignment', 'error');
            }
        } catch (err) {
            showAlert('Error submitting assignment', 'error');
        }
    });

    // Request update button
    document.getElementById('requestUpdateBtn').addEventListener('click', () => openModal('updateRequestModal'));

    // Update request form - adds to update request queue
    document.getElementById('updateRequestForm').addEventListener('submit', async (e) => {
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
                showAlert('Update request submitted', 'success');
            } else {
                showAlert('Error submitting request', 'error');
            }
        } catch (err) {
            showAlert('Error submitting request', 'error');
        }
    });
    
    // Setup sortable headers
    setupSortableHeaders();
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
