from flask import Blueprint, request, jsonify
from firebase_admin import firestore
import logging
from datetime import datetime

# Create blueprint
admin_system_bp = Blueprint('admin_system', __name__)

# Initialize logger
logger = logging.getLogger(__name__)

# Global app and db reference
app = None
db = None

def init_admin_system_routes(flask_app, firestore_db):
    """Initialize admin system routes with app and database"""
    global app, db
    app = flask_app
    db = firestore_db
    app.register_blueprint(admin_system_bp, url_prefix='/api/admin/system')

# --- Admin Settings Routes ---
@admin_system_bp.route('/admin/update', methods=['POST'])
def update_admin_settings():
    """Update admin settings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get current admin user (assuming there's a way to identify the current admin)
        # For now, we'll update the first admin found
        users_ref = db.collection('users')
        admin_query = users_ref.where('role', '==', 'Admin').limit(1)
        admin_docs = admin_query.get()
        
        if not admin_docs:
            return jsonify({"error": "Admin user not found"}), 404
        
        admin_doc = admin_docs[0]
        update_data = {'updatedAt': firestore.SERVER_TIMESTAMP}
        
        # Update fields if provided
        if data.get('phone'):
            update_data['phone'] = data['phone'].strip()
        if data.get('email'):
            update_data['email'] = data['email'].lower().strip()
        if data.get('newPassword'):
            update_data['password'] = data['newPassword']
        
        admin_doc.reference.update(update_data)
        
        return jsonify({"message": "Admin settings updated successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error updating admin settings: {str(e)}")
        return jsonify({"error": "Failed to update admin settings"}), 500

# --- Teacher Management Routes ---
@admin_system_bp.route('/teacher/remove', methods=['POST'])
def remove_teacher():
    """Remove a teacher"""
    try:
        data = request.get_json()
        
        if not data or not data.get('search') or not data.get('reason'):
            return jsonify({"error": "Search term and reason are required"}), 400
        
        search_term = data['search'].strip()
        
        # Search for teacher by name, email, or teacherId
        users_ref = db.collection('users')
        teacher_query = users_ref.where('role', '==', 'Teacher')
        teachers = teacher_query.get()
        
        teacher_to_remove = None
        for teacher in teachers:
            teacher_data = teacher.to_dict()
            if (search_term.lower() in teacher_data.get('name', '').lower() or
                search_term.lower() == teacher_data.get('email', '').lower() or
                search_term == teacher_data.get('teacherId', '')):
                teacher_to_remove = teacher
                break
        
        if not teacher_to_remove:
            return jsonify({"error": "Teacher not found"}), 404
        
        # Log the removal action
        removal_log = {
            'teacherId': teacher_to_remove.id,
            'teacherData': teacher_to_remove.to_dict(),
            'reason': data['reason'],
            'reasonText': data.get('reasonText', ''),
            'removedAt': firestore.SERVER_TIMESTAMP,
            'removedBy': 'admin'  # You might want to get the actual admin ID
        }
        
        # Save removal log
        db.collection('teacher_removals').document().set(removal_log)
        
        # Remove the teacher
        teacher_to_remove.reference.delete()
        
        return jsonify({"message": "Teacher removed successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error removing teacher: {str(e)}")
        return jsonify({"error": "Failed to remove teacher"}), 500

@admin_system_bp.route('/teacher/search', methods=['GET'])
def search_teacher():
    """Search for a teacher"""
    try:
        query = request.args.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Search query is required"}), 400
        
        users_ref = db.collection('users')
        teacher_query = users_ref.where('role', '==', 'Teacher')
        teachers = teacher_query.get()
        
        for teacher in teachers:
            teacher_data = teacher.to_dict()
            if (query.lower() == teacher_data.get('email', '').lower() or
                query == teacher_data.get('teacherId', '')):
                teacher_data['id'] = teacher.id
                return jsonify({"teacher": teacher_data}), 200
        
        return jsonify({"error": "Teacher not found"}), 404
        
    except Exception as e:
        logger.error(f"Error searching teacher: {str(e)}")
        return jsonify({"error": "Failed to search teacher"}), 500

@admin_system_bp.route('/teacher/update', methods=['POST'])
def update_teacher():
    """Update teacher details"""
    try:
        data = request.get_json()
        
        if not data or not data.get('search'):
            return jsonify({"error": "Search term is required"}), 400
        
        search_term = data['search'].strip()
        
        # Find the teacher
        users_ref = db.collection('users')
        teacher_query = users_ref.where('role', '==', 'Teacher')
        teachers = teacher_query.get()
        
        teacher_to_update = None
        for teacher in teachers:
            teacher_data = teacher.to_dict()
            if (search_term.lower() == teacher_data.get('email', '').lower() or
                search_term == teacher_data.get('teacherId', '')):
                teacher_to_update = teacher
                break
        
        if not teacher_to_update:
            return jsonify({"error": "Teacher not found"}), 404
        
        update_data = {'updatedAt': firestore.SERVER_TIMESTAMP}
        
        # Update fields if provided
        if data.get('name'):
            update_data['name'] = data['name'].strip()
        if data.get('email'):
            update_data['email'] = data['email'].lower().strip()
        if data.get('phone'):
            update_data['phone'] = data['phone'].strip()
        if data.get('bluetoothDeviceId'):
            update_data['bluetoothDeviceId'] = data['bluetoothDeviceId'].strip()
        
        teacher_to_update.reference.update(update_data)
        
        return jsonify({"message": "Teacher updated successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error updating teacher: {str(e)}")
        return jsonify({"error": "Failed to update teacher"}), 500

@admin_system_bp.route('/teacher/change-password', methods=['POST'])
def change_teacher_password():
    """Change teacher password"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('newPassword'):
            return jsonify({"error": "Email and new password are required"}), 400
        
        email = data['email'].lower().strip()
        
        # Find the teacher
        users_ref = db.collection('users')
        teacher_query = users_ref.where('role', '==', 'Teacher').where('email', '==', email).limit(1)
        teachers = teacher_query.get()
        
        if not teachers:
            return jsonify({"error": "Teacher not found"}), 404
        
        teacher = teachers[0]
        teacher.reference.update({
            'password': data['newPassword'],
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({"message": "Teacher password changed successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error changing teacher password: {str(e)}")
        return jsonify({"error": "Failed to change teacher password"}), 500

@admin_system_bp.route('/teacher/missing-bluetooth', methods=['GET'])
def get_teachers_without_bluetooth():
    """Get teachers without Bluetooth ID"""
    try:
        users_ref = db.collection('users')
        teacher_query = users_ref.where('role', '==', 'Teacher')
        teachers = teacher_query.get()
        
        teachers_without_bluetooth = []
        for teacher in teachers:
            teacher_data = teacher.to_dict()
            if not teacher_data.get('bluetoothDeviceId'):
                teacher_data['id'] = teacher.id
                teachers_without_bluetooth.append(teacher_data)
        
        return jsonify({"teachers": teachers_without_bluetooth}), 200
        
    except Exception as e:
        logger.error(f"Error getting teachers without bluetooth: {str(e)}")
        return jsonify({"error": "Failed to get teachers"}), 500

@admin_system_bp.route('/teacher/add-bluetooth', methods=['POST'])
def add_teacher_bluetooth():
    """Add Bluetooth ID to teacher"""
    try:
        data = request.get_json()
        
        if not data or not data.get('teacherId') or not data.get('bluetoothId'):
            return jsonify({"error": "Teacher ID and Bluetooth ID are required"}), 400
        
        teacher_ref = db.collection('users').document(data['teacherId'])
        teacher = teacher_ref.get()
        
        if not teacher.exists:
            return jsonify({"error": "Teacher not found"}), 404
        
        teacher_ref.update({
            'bluetoothDeviceId': data['bluetoothId'].strip(),
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({"message": "Bluetooth ID added successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error adding bluetooth ID: {str(e)}")
        return jsonify({"error": "Failed to add Bluetooth ID"}), 500

# --- Student Management Routes ---
@admin_system_bp.route('/student/fetch', methods=['GET'])
def fetch_students():
    """Fetch students by branch, year, division"""
    try:
        branch = request.args.get('branch')
        year = request.args.get('year')
        division = request.args.get('division')
        
        if not branch or not year or not division:
            return jsonify({"error": "Branch, year, and division are required"}), 400
        
        users_ref = db.collection('users')
        student_query = users_ref.where('role', '==', 'Student')
        students = student_query.get()
        
        filtered_students = []
        for student in students:
            student_data = student.to_dict()
            # Check if student matches the criteria
            if (student_data.get('year') == int(year) and
                student_data.get('division') == division):
                # Check branch name from branchId
                branch_id = student_data.get('branchId', '')
                if branch.upper() in branch_id.upper():
                    student_data['id'] = student.id
                    # TODO: Calculate actual attendance percentage
                    student_data['totalAttendance'] = 75  # Placeholder
                    filtered_students.append(student_data)
        
        return jsonify({"students": filtered_students}), 200
        
    except Exception as e:
        logger.error(f"Error fetching students: {str(e)}")
        return jsonify({"error": "Failed to fetch students"}), 500

@admin_system_bp.route('/student/block-attendance', methods=['POST'])
def block_student_attendance():
    """Block student attendance"""
    try:
        data = request.get_json()
        
        if not data or not data.get('studentSearch') or not data.get('blockUntilDate') or not data.get('reason'):
            return jsonify({"error": "Student search, block date, and reason are required"}), 400
        
        search_term = data['studentSearch'].strip()
        
        # Find the student
        users_ref = db.collection('users')
        student_query = users_ref.where('role', '==', 'Student')
        students = student_query.get()
        
        student_to_block = None
        for student in students:
            student_data = student.to_dict()
            if (search_term.lower() == student_data.get('email', '').lower() or
                search_term == student_data.get('studentId', '')):
                student_to_block = student
                break
        
        if not student_to_block:
            return jsonify({"error": "Student not found"}), 404
        
        # Create attendance block record
        block_data = {
            'studentId': student_to_block.id,
            'studentData': student_to_block.to_dict(),
            'blockUntilDate': data['blockUntilDate'],
            'reason': data['reason'],
            'reasonText': data.get('reasonText', ''),
            'blockedAt': firestore.SERVER_TIMESTAMP,
            'blockedBy': 'admin'  # You might want to get the actual admin ID
        }
        
        db.collection('attendance_blocks').document().set(block_data)
        
        # Update student record
        student_to_block.reference.update({
            'attendanceBlocked': True,
            'blockUntilDate': data['blockUntilDate'],
            'blockReason': data['reason'],
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({"message": "Student attendance blocked successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error blocking student attendance: {str(e)}")
        return jsonify({"error": "Failed to block student attendance"}), 500

@admin_system_bp.route('/student/search', methods=['GET'])
def search_student():
    """Search for a student"""
    try:
        query = request.args.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Search query is required"}), 400
        
        users_ref = db.collection('users')
        student_query = users_ref.where('role', '==', 'Student')
        students = student_query.get()
        
        for student in students:
            student_data = student.to_dict()
            if (query.lower() == student_data.get('email', '').lower() or
                query == student_data.get('studentId', '')):
                student_data['id'] = student.id
                # Extract branch name from branchId
                branch_id = student_data.get('branchId', '')
                if '_' in branch_id:
                    student_data['branchName'] = branch_id.split('_')[0]
                return jsonify({"student": student_data}), 200
        
        return jsonify({"error": "Student not found"}), 404
        
    except Exception as e:
        logger.error(f"Error searching student: {str(e)}")
        return jsonify({"error": "Failed to search student"}), 500

@admin_system_bp.route('/student/update', methods=['POST'])
def update_student():
    """Update student details"""
    try:
        data = request.get_json()
        
        if not data or not data.get('search'):
            return jsonify({"error": "Search term is required"}), 400
        
        search_term = data['search'].strip()
        
        # Find the student
        users_ref = db.collection('users')
        student_query = users_ref.where('role', '==', 'Student')
        students = student_query.get()
        
        student_to_update = None
        for student in students:
            student_data = student.to_dict()
            if (search_term.lower() == student_data.get('email', '').lower() or
                search_term == student_data.get('studentId', '')):
                student_to_update = student
                break
        
        if not student_to_update:
            return jsonify({"error": "Student not found"}), 404
        
        update_data = {'updatedAt': firestore.SERVER_TIMESTAMP}
        
        # Update fields if provided
        if data.get('newBranch') and data.get('newYear') and data.get('newDivision'):
            # Create new branchId
            new_branch_id = f"{data['newBranch']}_Y{data['newYear']}_{data['newDivision']}"
            update_data['branchId'] = new_branch_id
            update_data['year'] = int(data['newYear'])
            update_data['division'] = data['newDivision']
        
        if data.get('newPhone'):
            update_data['phone'] = data['newPhone'].strip()
        if data.get('newEmail'):
            update_data['email'] = data['newEmail'].lower().strip()
        if data.get('newPassword'):
            update_data['password'] = data['newPassword']
        
        student_to_update.reference.update(update_data)
        
        return jsonify({"message": "Student updated successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error updating student: {str(e)}")
        return jsonify({"error": "Failed to update student"}), 500

@admin_system_bp.route('/student/remove', methods=['POST'])
def remove_student():
    """Remove a student"""
    try:
        data = request.get_json()
        
        if not data or not data.get('studentSearch') or not data.get('reason'):
            return jsonify({"error": "Student search and reason are required"}), 400
        
        search_term = data['studentSearch'].strip()
        
        # Find the student
        users_ref = db.collection('users')
        student_query = users_ref.where('role', '==', 'Student')
        students = student_query.get()
        
        student_to_remove = None
        for student in students:
            student_data = student.to_dict()
            if (search_term.lower() == student_data.get('email', '').lower() or
                search_term == student_data.get('studentId', '')):
                student_to_remove = student
                break
        
        if not student_to_remove:
            return jsonify({"error": "Student not found"}), 404
        
        # Log the removal action
        removal_log = {
            'studentId': student_to_remove.id,
            'studentData': student_to_remove.to_dict(),
            'reason': data['reason'],
            'reasonText': data.get('reasonText', ''),
            'removedAt': firestore.SERVER_TIMESTAMP,
            'removedBy': 'admin'  # You might want to get the actual admin ID
        }
        
        # Save removal log
        db.collection('student_removals').document().set(removal_log)
        
        # Remove the student
        student_to_remove.reference.delete()
        
        return jsonify({"message": "Student removed successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error removing student: {str(e)}")
        return jsonify({"error": "Failed to remove student"}), 500