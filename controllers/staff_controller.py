import json
import logging
from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class StudentManagementStaffController(http.Controller):
    """Staff controller for Student Management System staff operations"""

    def _check_staff_access(self):
        """Check if current user has staff access"""
        if not request.env.user.has_group('odoo_student_management.group_student_management_staff'):
            raise AccessError("Access denied. Staff privileges required.")

    def _get_current_staff(self):
        """Get current staff record"""
        staff = request.env['student_management.staff'].search([('user_id', '=', request.env.user.id)], limit=1)
        if not staff:
            raise UserError("Staff record not found for current user")
        return staff

    @http.route('/student_management/staff/dashboard', type='http', auth='user', website=True, methods=['GET'])
    def staff_dashboard(self, **kwargs):
        """Staff dashboard page"""
        try:
            self._check_staff_access()
            staff = self._get_current_staff()
            
            # Get subjects taught by this staff
            subjects = request.env['student_management.subject'].search([('staff_id', '=', staff.id)])

            # Get courses for these subjects
            course_ids = subjects.mapped('course_id.id')
            
            # Count students in these courses
            student_count = request.env['student_management.student'].search_count([('course_id', 'in', course_ids)])
            
            # Count attendance records for subjects taught by this staff
            attendance_count = request.env['student_management.attendance'].search_count([('subject_id', 'in', subjects.ids)])
            
            # Count approved leave requests for this staff
            leave_count = request.env['student_management.leave_report_staff'].search_count([
                ('staff_id', '=', staff.id),
                ('leave_status', '=', 'approved')
            ])
            
            subjects_count = len(subjects)
            
            # Get attendance data by subject
            subject_data = []
            for subject in subjects:
                attendance_count_subject = request.env['student_management.attendance'].search_count([('subject_id', '=', subject.id)])
                subject_data.append({
                    'name': subject.subject_name,
                    'attendance_count': attendance_count_subject
                })
            
            # Get student attendance data
            students = request.env['student_management.student'].search([('course_id', 'in', course_ids)])
            student_data = []
            for student in students:
                present_count = request.env['student_management.attendance'].search_count([
                    ('student_id', '=', student.id),
                    ('status', '=', 'present')
                ])
                absent_count = request.env['student_management.attendance'].search_count([
                    ('student_id', '=', student.id),
                    ('status', '=', 'absent')
                ])
                student_data.append({
                    'name': student.name,
                    'present_count': present_count,
                    'absent_count': absent_count
                })
            
            return request.render('odoo_student_management.staff_page_layout', {
                'student_count': student_count,
                'attendance_count': attendance_count,
                'leave_count': leave_count,
                'subjects_count': subjects_count,
                'subject_data': subject_data,
                'student_data': student_data,
                'staff': staff
            })
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== ATTENDANCE MANAGEMENT ====================

    @http.route('/student_management/staff/attendance/take', type='http', auth='user', methods=['GET'])
    def take_attendance(self, **kwargs):
        """Take attendance page"""
        try:
            self._check_staff_access()
            staff = self._get_current_staff()
            subjects = request.env['student_management.subject'].search([('staff_id', '=', staff.id)])
            session_years = request.env['student_management.session_year'].search([])

            return request.render('odoo_student_management.staff_take_attendance', {
                'subjects': subjects,
                'session_years': session_years
            })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/api/staff/get_students', type='json', auth='user', methods=['POST'])
    def get_students(self, subject_id, session_year_id, **kwargs):
        """Get students for a subject and session year"""
        try:
            self._check_staff_access()
            
            subject = request.env['student_management.subject'].browse(subject_id)
            session_year = request.env['student_management.session_year'].browse(session_year_id)
            
            students = request.env['student_management.student'].search([
                ('course_id', '=', subject.course_id.id),
                ('session_year_id', '=', session_year.id)
            ])
            
            student_data = []
            for student in students:
                student_data.append({
                    'id': student.id,
                    'name': student.name
                })
            
            return {
                'success': True,
                'students': student_data
            }
        except Exception as e:
            _logger.error(f"Error getting students: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/student_management/api/staff/save_attendance', type='json', auth='user', methods=['POST'])
    def save_attendance(self, subject_id, session_year_id, attendance_date, student_data, **kwargs):
        """Save attendance data"""
        try:
            self._check_staff_access()
            staff = self._get_current_staff()
            
            subject = request.env['student_management.subject'].browse(subject_id)
            session_year = request.env['student_management.session_year'].browse(session_year_id)
            
            # Check if staff teaches this subject
            if subject.staff_id.id != staff.id:
                raise AccessError("You are not authorized to take attendance for this subject")
            
            # Create attendance record
            attendance = request.env['student_management.attendance'].sudo().create({
                'subject_id': subject_id,
                'session_year_id': session_year_id,
                'attendance_date': attendance_date,
            })
            
            # Create attendance records for each student
            for student_info in student_data:
                student_id = student_info['id']
                status = student_info['status']

                request.env['student_management.attendance'].sudo().create({
                    'student_id': student_id,
                    'subject_id': subject_id,
                    'session_year_id': session_year_id,
                    'attendance_date': attendance_date,
                    'status': status,
                })
            
            return {
                'success': True,
                'message': 'Attendance saved successfully'
            }
        except Exception as e:
            _logger.error(f"Error saving attendance: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/student_management/staff/attendance/update', type='http', auth='user', methods=['GET'])
    def update_attendance(self, **kwargs):
        """Update attendance page"""
        try:
            self._check_staff_access()
            staff = self._get_current_staff()

            subjects = request.env['student_management.subject'].search([('staff_id', '=', staff.id)])
            session_years = request.env['student_management.session_year'].search([])

            return request.render('odoo_student_management.staff_update_attendance', {
                'subjects': subjects,
                'session_years': session_years
            })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/api/staff/get_attendance_dates', type='json', auth='user', methods=['POST'])
    def get_attendance_dates(self, subject_id, session_year_id, **kwargs):
        """Get attendance dates for a subject and session year"""
        try:
            self._check_staff_access()

            attendances = request.env['student_management.attendance'].search([
                ('subject_id', '=', subject_id),
                ('session_year_id', '=', session_year_id)
            ])
            
            # Group by date
            attendance_dates = {}
            for attendance in attendances:
                date_str = attendance.attendance_date.strftime('%Y-%m-%d')
                if date_str not in attendance_dates:
                    attendance_dates[date_str] = {
                        'date': date_str,
                        'attendance_ids': []
                    }
                attendance_dates[date_str]['attendance_ids'].append(attendance.id)
            
            return {
                'success': True,
                'attendance_dates': list(attendance_dates.values())
            }
        except Exception as e:
            _logger.error(f"Error getting attendance dates: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/student_management/api/staff/get_attendance_students', type='json', auth='user', methods=['POST'])
    def get_attendance_students(self, attendance_date, subject_id, session_year_id, **kwargs):
        """Get students attendance for a specific date"""
        try:
            self._check_staff_access()

            attendances = request.env['student_management.attendance'].search([
                ('subject_id', '=', subject_id),
                ('session_year_id', '=', session_year_id),
                ('attendance_date', '=', attendance_date)
            ])
            
            student_data = []
            for attendance in attendances:
                if attendance.student_id:
                    student_data.append({
                        'id': attendance.student_id.id,
                        'name': attendance.student_id.name,
                        'status': attendance.status,
                        'attendance_id': attendance.id
                    })
            
            return {
                'success': True,
                'students': student_data
            }
        except Exception as e:
            _logger.error(f"Error getting attendance students: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/student_management/api/staff/update_attendance', type='json', auth='user', methods=['POST'])
    def update_attendance_data(self, student_data, **kwargs):
        """Update attendance data"""
        try:
            self._check_staff_access()
            
            for student_info in student_data:
                attendance_id = student_info['attendance_id']
                status = student_info['status']

                attendance = request.env['student_management.attendance'].browse(attendance_id)
                attendance.sudo().write({'status': status})
            
            return {
                'success': True,
                'message': 'Attendance updated successfully'
            }
        except Exception as e:
            _logger.error(f"Error updating attendance: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== STUDENT RESULTS ====================

    @http.route('/student_management/staff/results/add', type='http', auth='user', methods=['GET', 'POST'])
    def add_student_result(self, **kwargs):
        """Add student result"""
        try:
            self._check_staff_access()
            staff = self._get_current_staff()
            
            if request.httprequest.method == 'GET':
                subjects = request.env['student_management.subject'].search([('staff_id', '=', staff.id)])
                return request.render('odoo_student_management.staff_add_result', {
                    'subjects': subjects
                })
            
            # Handle POST request
            student_id = kwargs.get('student_id')
            subject_id = kwargs.get('subject_id')
            total_marks = kwargs.get('total_marks')
            remarks = kwargs.get('remarks', '')
            
            if not all([student_id, subject_id, total_marks]):
                subjects = request.env['student_management.subject'].search([('staff_id', '=', staff.id)])
                return request.render('odoo_student_management.staff_add_result', {
                    'subjects': subjects,
                    'error': 'All required fields must be filled'
                })
            
            try:
                # Check if staff teaches this subject
                subject = request.env['student_management.subject'].browse(int(subject_id))
                if subject.staff_id.id != staff.id:
                    raise AccessError("You are not authorized to add results for this subject")
                
                request.env['student_management.student_result'].sudo().create({
                    'student_id': int(student_id),
                    'subject_id': int(subject_id),
                    'total_marks': float(total_marks),
                    'remarks': remarks,
                })
                
                subjects = request.env['student_management.subject'].search([('staff_id', '=', staff.id)])
                return request.render('odoo_student_management.staff_add_result', {
                    'subjects': subjects,
                    'success': 'Student result added successfully'
                })
            except Exception as e:
                _logger.error(f"Error adding student result: {str(e)}")
                subjects = request.env['student_management.subject'].search([('staff_id', '=', staff.id)])
                return request.render('odoo_student_management.staff_add_result', {
                    'subjects': subjects,
                    'error': 'Failed to add student result'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== LEAVE MANAGEMENT ====================

    @http.route('/student_management/staff/leave/apply', type='http', auth='user', methods=['GET', 'POST'])
    def apply_leave(self, **kwargs):
        """Apply for leave"""
        try:
            self._check_staff_access()
            staff = self._get_current_staff()
            
            if request.httprequest.method == 'GET':
                return request.render('odoo_student_management.staff_apply_leave')

            # Handle POST request
            leave_date = kwargs.get('leave_date')
            leave_message = kwargs.get('leave_message')
            
            if not all([leave_date, leave_message]):
                return request.render('odoo_student_management.staff_apply_leave', {
                    'error': 'All fields are required'
                })
            
            try:
                request.env['student_management.leave_report_staff'].sudo().create({
                    'staff_id': staff.id,
                    'leave_date': leave_date,
                    'leave_message': leave_message,
                    'leave_status': 'pending',
                })
                return request.render('odoo_student_management.staff_apply_leave', {
                    'success': 'Leave applied successfully'
                })
            except Exception as e:
                _logger.error(f"Error applying leave: {str(e)}")
                return request.render('odoo_student_management.staff_apply_leave', {
                    'error': 'Failed to apply leave'
                })
        except AccessError:
            return request.redirect('/student_management/login')


    @http.route(
    ['/student_management/staff/logout'],
    type='http', auth='public', methods=['GET', 'POST'], csrf=False, website=True
)
    def staff_logout(self, **kwargs):
        """Logout route dedicated for Staff dashboard button with correct redirect."""
        # احفظ اسم قاعدة البيانات قبل الـ logout
        current_db = request.env.cr.dbname

        try:
            request.session.logout()
        except Exception as e:
            _logger.warning("Staff logout called but session not active or other issue: %s", e)

        # لو ما أُرسل redirect، نحدده لصفحة الدخول ومعها redirect إلى check_user_type + db الصحيح
        target = kwargs.get('redirect')
        if not target:
            target = f"/web/login?redirect=/student_management/check_user_type&db={current_db}"

        return request.redirect(target)