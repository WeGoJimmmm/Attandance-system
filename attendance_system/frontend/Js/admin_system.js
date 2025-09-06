// Admin System Settings JavaScript
const API_BASE = '/api/admin/system';

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadDropdownData();
    setupEventListeners();
});

function setupEventListeners() {
    // Admin settings form
    document.getElementById('adminSettingsForm').addEventListener('submit', handleAdminSettingsSubmit);
    
    // Teacher forms
    document.getElementById('removeTeacherForm').addEventListener('submit', handleRemoveTeacher);
    document.getElementById('updateTeacherForm').addEventListener('submit', handleUpdateTeacher);
    document.getElementById('changeTeacherPasswordForm').addEventListener('submit', handleChangeTeacherPassword);
    
    // Student forms
    document.getElementById('fetchStudentsForm').addEventListener('submit', handleFetchStudents);
    document.getElementById('blockAttendanceForm').addEventListener('submit', handleBlockAttendance);
    document.getElementById('changeStudentDetailsForm').addEventListener('submit', handleChangeStudentDetails);
    document.getElementById('removeStudentForm').addEventListener('submit', handleRemoveStudent);
}

// Tab switching functionality
function switchTab(tabName) {
    // Remove active class from all tabs and buttons
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active class to selected tab and button
    document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Load dropdown data
async function loadDropdownData() {
    try {
        const [branches] = await Promise.all([
            fetch('/api/admin/branches').then(res => res.ok ? res.json() : [])
        ]);
        
        populateDropdowns(branches);
    } catch (error) {
        console.error('Error loading dropdown data:', error);
        showNotification('Failed to load dropdown data', 'error');
    }
}

function populateDropdowns(branches) {
    // Get unique values
    const uniqueBranches = [...new Set(branches.map(b => b.branchName))];
    const uniqueYears = [...new Set(branches.map(b => b.year))].sort();
    const uniqueDivisions = [...new Set(branches.map(b => b.division))].sort();
    
    // Populate student fetch dropdowns
    populateSelect('studentBranch', uniqueBranches.map(name => ({value: name, text: name})));
    populateSelect('studentYear', uniqueYears.map(year => ({value: year, text: `Year ${year}`})));
    populateSelect('studentDivision', uniqueDivisions.map(div => ({value: div, text: `Division ${div}`})));
    
    // Populate student update dropdowns
    populateSelect('studentNewBranch', uniqueBranches.map(name => ({value: name, text: name})));
    populateSelect('studentNewYear', uniqueYears.map(year => ({value: year, text: `Year ${year}`})));
    populateSelect('studentNewDivision', uniqueDivisions.map(div => ({value: div, text: `Division ${div}`})));
}

function populateSelect(selectId, options) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    // Keep the first option (placeholder)
    const firstOption = select.querySelector('option');
    select.innerHTML = '';
    if (firstOption) select.appendChild(firstOption);
    
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option.value;
        optionElement.textContent = option.text;
        select.appendChild(optionElement);
    });
}

// Admin Settings Functions
async function handleAdminSettingsSubmit(event) {
    event.preventDefault();
    
    const formData = {
        phone: document.getElementById('adminPhone').value,
        email: document.getElementById('adminEmail').value,
        newPassword: document.getElementById('adminNewPassword').value,
        confirmPassword: document.getElementById('adminConfirmPassword').value
    };
    
    if (formData.newPassword && formData.newPassword !== formData.confirmPassword) {
        showNotification('Passwords do not match', 'error');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/admin/update`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Admin settings updated successfully', 'success');
            document.getElementById('adminSettingsForm').reset();
        } else {
            showNotification(result.error || 'Failed to update admin settings', 'error');
        }
    } catch (error) {
        console.error('Error updating admin settings:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

// Teacher Management Functions
async function handleRemoveTeacher(event) {
    event.preventDefault();
    
    const formData = {
        search: document.getElementById('teacherSearch').value,
        reason: document.getElementById('removeReason').value,
        reasonText: document.getElementById('removeReasonText').value
    };
    
    if (!formData.search || !formData.reason) {
        showNotification('Please fill in all required fields', 'warning');
        return;
    }
    
    if (!confirm('Are you sure you want to remove this teacher? This action cannot be undone.')) {
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/teacher/remove`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Teacher removed successfully', 'success');
            document.getElementById('removeTeacherForm').reset();
        } else {
            showNotification(result.error || 'Failed to remove teacher', 'error');
        }
    } catch (error) {
        console.error('Error removing teacher:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

async function searchTeacher() {
    const searchValue = document.getElementById('updateTeacherSearch').value;
    if (!searchValue) {
        showNotification('Please enter email or teacher ID', 'warning');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/teacher/search?query=${encodeURIComponent(searchValue)}`);
        const result = await response.json();
        
        if (response.ok && result.teacher) {
            const teacher = result.teacher;
            document.getElementById('teacherName').value = teacher.name || '';
            document.getElementById('teacherEmail').value = teacher.email || '';
            document.getElementById('teacherPhone').value = teacher.phone || '';
            document.getElementById('teacherBluetoothId').value = teacher.bluetoothDeviceId || '';
            document.getElementById('teacherUpdateFields').style.display = 'block';
        } else {
            showNotification(result.error || 'Teacher not found', 'error');
            document.getElementById('teacherUpdateFields').style.display = 'none';
        }
    } catch (error) {
        console.error('Error searching teacher:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

async function handleUpdateTeacher(event) {
    event.preventDefault();
    
    const formData = {
        search: document.getElementById('updateTeacherSearch').value,
        name: document.getElementById('teacherName').value,
        email: document.getElementById('teacherEmail').value,
        phone: document.getElementById('teacherPhone').value,
        bluetoothDeviceId: document.getElementById('teacherBluetoothId').value
    };
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/teacher/update`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Teacher updated successfully', 'success');
        } else {
            showNotification(result.error || 'Failed to update teacher', 'error');
        }
    } catch (error) {
        console.error('Error updating teacher:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

async function handleChangeTeacherPassword(event) {
    event.preventDefault();
    
    const formData = {
        email: document.getElementById('teacherEmailPassword').value,
        newPassword: document.getElementById('teacherNewPassword').value
    };
    
    if (!formData.email || !formData.newPassword) {
        showNotification('Please fill in all fields', 'warning');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/teacher/change-password`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Teacher password changed successfully', 'success');
            document.getElementById('changeTeacherPasswordForm').reset();
        } else {
            showNotification(result.error || 'Failed to change password', 'error');
        }
    } catch (error) {
        console.error('Error changing teacher password:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

async function loadTeachersWithoutBluetooth() {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/teacher/missing-bluetooth`);
        const result = await response.json();
        
        if (response.ok) {
            displayTeachersWithoutBluetooth(result.teachers);
        } else {
            showNotification(result.error || 'Failed to load teachers', 'error');
        }
    } catch (error) {
        console.error('Error loading teachers without bluetooth:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

function displayTeachersWithoutBluetooth(teachers) {
    const container = document.getElementById('teachersWithoutBluetooth');
    
    if (teachers.length === 0) {
        container.innerHTML = '<p>All teachers have Bluetooth IDs assigned.</p>';
        return;
    }
    
    container.innerHTML = teachers.map(teacher => `
        <div class="teacher-item">
            <div class="teacher-info">
                <h4>${teacher.name}</h4>
                <p>${teacher.email} | ${teacher.teacherId}</p>
            </div>
            <div>
                <span class="bluetooth-status bluetooth-missing">Missing Bluetooth ID</span>
                <button class="btn btn-primary btn-sm" onclick="addBluetoothId('${teacher.id}')">Add Bluetooth ID</button>
            </div>
        </div>
    `).join('');
}

async function addBluetoothId(teacherId) {
    const bluetoothId = prompt('Enter Bluetooth Device ID:');
    if (!bluetoothId) return;
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/teacher/add-bluetooth`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ teacherId, bluetoothId })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Bluetooth ID added successfully', 'success');
            loadTeachersWithoutBluetooth(); // Refresh the list
        } else {
            showNotification(result.error || 'Failed to add Bluetooth ID', 'error');
        }
    } catch (error) {
        console.error('Error adding Bluetooth ID:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

// Student Management Functions
async function handleFetchStudents(event) {
    event.preventDefault();
    
    const branch = document.getElementById('studentBranch').value;
    const year = document.getElementById('studentYear').value;
    const division = document.getElementById('studentDivision').value;
    
    if (!branch || !year || !division) {
        showNotification('Please select branch, year, and division', 'warning');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/student/fetch?branch=${encodeURIComponent(branch)}&year=${year}&division=${encodeURIComponent(division)}`);
        const result = await response.json();
        
        if (response.ok) {
            displayStudents(result.students);
        } else {
            showNotification(result.error || 'Failed to fetch students', 'error');
        }
    } catch (error) {
        console.error('Error fetching students:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

function displayStudents(students) {
    const container = document.getElementById('studentsList');
    
    if (students.length === 0) {
        container.innerHTML = '<p>No students found for the selected criteria.</p>';
        return;
    }
    
    container.innerHTML = students.map(student => {
        const attendancePercentage = student.totalAttendance || 0;
        let attendanceClass = 'attendance-good';
        if (attendancePercentage < 60) attendanceClass = 'attendance-danger';
        else if (attendancePercentage < 75) attendanceClass = 'attendance-warning';
        
        return `
            <div class="student-item">
                <div class="student-info">
                    <h4>${student.name}</h4>
                    <p>${student.email} | ${student.studentId}</p>
                </div>
                <div>
                    <span class="attendance-badge ${attendanceClass}">${attendancePercentage}%</span>
                </div>
            </div>
        `;
    }).join('');
}

async function handleBlockAttendance(event) {
    event.preventDefault();
    
    const formData = {
        studentSearch: document.getElementById('blockStudentSearch').value,
        blockUntilDate: document.getElementById('blockUntilDate').value,
        reason: document.getElementById('blockReason').value,
        reasonText: document.getElementById('blockReasonText').value
    };
    
    if (!formData.studentSearch || !formData.blockUntilDate || !formData.reason) {
        showNotification('Please fill in all required fields', 'warning');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/student/block-attendance`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Student attendance blocked successfully', 'success');
            document.getElementById('blockAttendanceForm').reset();
        } else {
            showNotification(result.error || 'Failed to block attendance', 'error');
        }
    } catch (error) {
        console.error('Error blocking attendance:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

async function searchStudent() {
    const searchValue = document.getElementById('changeStudentSearch').value;
    if (!searchValue) {
        showNotification('Please enter email or student ID', 'warning');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/student/search?query=${encodeURIComponent(searchValue)}`);
        const result = await response.json();
        
        if (response.ok && result.student) {
            const student = result.student;
            document.getElementById('studentNewBranch').value = student.branchName || '';
            document.getElementById('studentNewYear').value = student.year || '';
            document.getElementById('studentNewDivision').value = student.division || '';
            document.getElementById('studentNewPhone').value = student.phone || '';
            document.getElementById('studentNewEmail').value = student.email || '';
            document.getElementById('studentUpdateFields').style.display = 'block';
        } else {
            showNotification(result.error || 'Student not found', 'error');
            document.getElementById('studentUpdateFields').style.display = 'none';
        }
    } catch (error) {
        console.error('Error searching student:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

async function handleChangeStudentDetails(event) {
    event.preventDefault();
    
    const formData = {
        search: document.getElementById('changeStudentSearch').value,
        newBranch: document.getElementById('studentNewBranch').value,
        newYear: document.getElementById('studentNewYear').value,
        newDivision: document.getElementById('studentNewDivision').value,
        newPhone: document.getElementById('studentNewPhone').value,
        newEmail: document.getElementById('studentNewEmail').value,
        newPassword: document.getElementById('studentNewPassword').value
    };
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/student/update`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Student details updated successfully', 'success');
        } else {
            showNotification(result.error || 'Failed to update student', 'error');
        }
    } catch (error) {
        console.error('Error updating student:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

async function handleRemoveStudent(event) {
    event.preventDefault();
    
    const formData = {
        studentSearch: document.getElementById('removeStudentSearch').value,
        reason: document.getElementById('removeStudentReason').value,
        reasonText: document.getElementById('removeStudentReasonText').value
    };
    
    if (!formData.studentSearch || !formData.reason) {
        showNotification('Please fill in all required fields', 'warning');
        return;
    }
    
    if (!confirm('Are you sure you want to remove this student? This action cannot be undone.')) {
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/student/remove`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Student removed successfully', 'success');
            document.getElementById('removeStudentForm').reset();
        } else {
            showNotification(result.error || 'Failed to remove student', 'error');
        }
    } catch (error) {
        console.error('Error removing student:', error);
        showNotification('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

// Utility Functions
function showNotification(message, type = 'info') {
    // Remove any existing notifications first
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
}

function showLoading(show) {
    let overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        overlay.innerHTML = `
            <div style="background: white; padding: 20px; border-radius: 8px; display: flex; align-items: center;">
                <i class="fas fa-spinner fa-spin" style="margin-right: 10px;"></i>
                <span>Processing...</span>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    
    overlay.style.display = show ? 'flex' : 'none';
}

// Make functions available globally
window.switchTab = switchTab;
window.searchTeacher = searchTeacher;
window.searchStudent = searchStudent;
window.loadTeachersWithoutBluetooth = loadTeachersWithoutBluetooth;
window.addBluetoothId = addBluetoothId;