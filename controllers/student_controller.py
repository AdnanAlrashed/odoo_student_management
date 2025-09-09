import json
import logging
from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class StudentManagementStudentController(http.Controller):
    """Student controller for Student Management System student operations"""

    def _check_student_access(self):
        """Check if current user has student access"""
        if not request.env.user.has_group('odoo_student_management.group_student_management_student'):
            raise AccessError("Access denied. Student privileges required.")

    def _get_current_student(self):
        """Get current student record"""
        student = request.env['student_management.student'].search([('user_id', '=', request.env.user.id)], limit=1)
        if not student:
            raise UserError("Student record not found for current user")
        return student

    @http.route('/student_management/student/dashboard', type='http', auth='user', website=True, methods=['GET'])
    def student_dashboard(self, **kwargs):
        """Student dashboard page"""
        try:
            self._check_student_access()
            student = self._get_current_student()
            
            # Get attendance statistics
            total_attendance = request.env['student_management.attendance'].search_count([('student_id', '=', student.id)])
            present_attendance = request.env['student_management.attendance'].search_count([
                ('student_id', '=', student.id),
                ('status', '=', 'present')
            ])
            absent_attendance = request.env['student_management.attendance'].search_count([
                ('student_id', '=', student.id),
                ('status', '=', 'absent')
            ])
            
            # Get subjects count and course info with safe access
            subjects_count = 0
            course_name = "Not Available"
            session_name = "Not Available"
            
            try:
                # محاولة الوصول إلى بيانات المقرر بشكل آمن
                if student.course_id:
                    subjects_count = request.env['student_management.subject'].search_count([
                        ('course_id', '=', student.course_id.id)
                    ])
                    course_name = student.course_id.course_name
            except Exception as e:
                _logger.warning(f"Could not access course data for student {student.id}: {str(e)}")
                # إذا فشل الوصول، نحاول طريقة بديلة
                subjects_count = request.env['student_management.subject'].search_count([])
            
            try:
                if student.session_year_id:
                    session_name = student.session_year_id.session_name
            except Exception as e:
                _logger.warning(f"Could not access session data for student {student.id}: {str(e)}")
            
            # Get attendance data by subject
            subject_data = []
            try:
                subjects = request.env['student_management.subject'].search([])
                for subject in subjects:
                    try:
                        present_count = request.env['student_management.attendance'].search_count([
                            ('student_id', '=', student.id),
                            ('subject_id', '=', subject.id),
                            ('status', '=', 'present')
                        ])
                        absent_count = request.env['student_management.attendance'].search_count([
                            ('student_id', '=', student.id),
                            ('subject_id', '=', subject.id),
                            ('status', '=', 'absent')
                        ])
                        
                        # Only add subjects with attendance records
                        if present_count > 0 or absent_count > 0:
                            subject_data.append({
                                'name': subject.subject_name,
                                'present_count': present_count,
                                'absent_count': absent_count
                            })
                    except Exception as e:
                        _logger.warning(f"Could not get attendance for subject {subject.id}: {str(e)}")
                        continue
            except Exception as e:
                _logger.error(f"Error getting subject data: {str(e)}")
            
            return request.render('odoo_student_management.student_dashboard_template', {
                'total_attendance': total_attendance,
                'present_attendance': present_attendance,
                'absent_attendance': absent_attendance,
                'subjects_count': subjects_count,
                'subject_data': subject_data,
                'student': student,
                'course_name': course_name,
                'session_name': session_name
            })
        except AccessError:
            return request.redirect('/student_management/login')
        except Exception as e:
            _logger.error(f"Error in student dashboard: {str(e)}")
            return request.render('odoo_student_management.error_template', {
                'error_message': 'An error occurred while loading your dashboard.'
            })


    # ==================== ATTENDANCE VIEWING ====================

    @http.route('/student_management/student/attendance/view', type='http', auth='user', methods=['GET', 'POST'])
    def view_attendance(self, **kwargs):
        """View attendance page"""
        try:
            self._check_student_access()
            student = self._get_current_student()
            
            if request.httprequest.method == 'GET':
                subjects = request.env['student_management.subject'].search([('course_id', '=', student.course_id.id)])
                return request.render('odoo_student_management.student_view_attendance', {
                    'subjects': subjects
                })
            
            # Handle POST request - Filter attendance
            subject_id = kwargs.get('subject_id')
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            if not all([subject_id, start_date, end_date]):
                subjects = request.env['student_management.subject'].search([('course_id', '=', student.course_id.id)])
                return request.render('odoo_student_management.student_view_attendance', {
                    'subjects': subjects,
                    'error': 'All fields are required'
                })
            
            # Get attendance records for the specified period
            domain = [
                ('student_id', '=', student.id),
                ('subject_id', '=', int(subject_id)),
                ('attendance_date', '>=', start_date),
                ('attendance_date', '<=', end_date)
            ]
            attendance_records = request.env['student_management.attendance'].search(domain)
            
            subjects = request.env['student_management.subject'].search([('course_id', '=', student.course_id.id)])
            return request.render('odoo_student_management.student_attendance_data', {
                'attendance_records': attendance_records,
                'subjects': subjects,
                'selected_subject_id': int(subject_id),
                'start_date': start_date,
                'end_date': end_date
            })
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== LEAVE MANAGEMENT ====================

    @http.route('/student_management/student/leave/apply', type='http', auth='user', methods=['GET', 'POST'])
    def apply_leave(self, **kwargs):
        """Apply for leave"""
        try:
            self._check_student_access()
            student = self._get_current_student()
            
            if request.httprequest.method == 'GET':
                # Get existing leave requests
                leave_requests = request.env['student_management.leave_report_student'].search([('student_id', '=', student.id)])
                return request.render('odoo_student_management.student_apply_leave', {
                    'leave_requests': leave_requests
                })
            
            # Handle POST request
            leave_date = kwargs.get('leave_date')
            leave_message = kwargs.get('leave_message')
            
            if not all([leave_date, leave_message]):
                leave_requests = request.env['student_management.leave_report_student'].search([('student_id', '=', student.id)])
                return request.render('odoo_student_management.student_apply_leave', {
                    'leave_requests': leave_requests,
                    'error': 'All fields are required'
                })
            
            try:
                request.env['student_management.leave_report_student'].sudo().create({
                    'student_id': student.id,
                    'leave_date': leave_date,
                    'leave_message': leave_message,
                    'leave_status': 'pending',
                })
                
                leave_requests = request.env['student_management.leave_report_student'].search([('student_id', '=', student.id)])
                return request.render('odoo_student_management.student_apply_leave', {
                    'leave_requests': leave_requests,
                    'success': 'Leave application submitted successfully'
                })
            except Exception as e:
                _logger.error(f"Error applying for leave: {str(e)}")
                leave_requests = request.env['student_management.leave_report_student'].search([('student_id', '=', student.id)])
                return request.render('odoo_student_management.student_apply_leave', {
                    'leave_requests': leave_requests,
                    'error': 'Failed to submit leave application'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== FEEDBACK ====================

    @http.route('/student_management/student/feedback', type='http', auth='user', methods=['GET', 'POST'])
    def student_feedback(self, **kwargs):
        """Student feedback"""
        try:
            self._check_student_access()
            student = self._get_current_student()
            
            if request.httprequest.method == 'GET':
                # Get existing feedback
                feedback_records = request.env['student_management.feedback_student'].search([('student_id', '=', student.id)])
                return request.render('odoo_student_management.student_feedback', {
                    'feedback_records': feedback_records
                })
            
            # Handle POST request
            feedback_message = kwargs.get('feedback_message')
            category = kwargs.get('category', 'general')
            priority = kwargs.get('priority', 'medium')
            
            if not feedback_message:
                feedback_records = request.env['student_management.feedback_student'].search([('student_id', '=', student.id)])
                return request.render('odoo_student_management.student_feedback', {
                    'feedback_records': feedback_records,
                    'error': 'Feedback message is required'
                })
            
            try:
                request.env['student_management.feedback_student'].sudo().create({
                    'student_id': student.id,
                    'feedback_message': feedback_message,
                    'category': category,
                    'priority': priority,
                })
                
                feedback_records = request.env['student_management.feedback_student'].search([('student_id', '=', student.id)])
                return request.render('odoo_student_management.student_feedback', {
                    'feedback_records': feedback_records,
                    'success': 'Feedback submitted successfully'
                })
            except Exception as e:
                _logger.error(f"Error submitting feedback: {str(e)}")
                feedback_records = request.env['student_management.feedback_student'].search([('student_id', '=', student.id)])
                return request.render('odoo_student_management.student_feedback', {
                    'feedback_records': feedback_records,
                    'error': 'Failed to submit feedback'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== RESULTS VIEWING ====================

    @http.route('/student_management/student/results/view', type='http', auth='user', methods=['GET'])
    def view_results(self, **kwargs):
        """View student results"""
        try:
            self._check_student_access()
            student = self._get_current_student()
            
            # Get student results
            results = request.env['student_management.student_result'].search([('student_id', '=', student.id)])
            
            # Calculate overall statistics
            total_subjects = len(results)
            total_marks = sum(result.total_marks for result in results)
            average_marks = total_marks / total_subjects if total_subjects > 0 else 0
            
            # Group results by subject
            subject_results = {}
            for result in results:
                subject_name = result.subject_id.subject_name
                if subject_name not in subject_results:
                    subject_results[subject_name] = []
                subject_results[subject_name].append(result)
            
            return request.render('odoo_student_management.student_view_result', {
                'results': results,
                'subject_results': subject_results,
                'total_subjects': total_subjects,
                'total_marks': total_marks,
                'average_marks': average_marks,
                'student': student
            })
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== PROFILE MANAGEMENT ====================

    @http.route('/student_management/student/profile', type='http', auth='user', methods=['GET', 'POST'])
    def student_profile(self, **kwargs):
        """Student profile"""
        try:
            self._check_student_access()
            student = self._get_current_student()
            
            if request.httprequest.method == 'GET':
                return request.render('odoo_student_management.student_profile', {
                    'student': student
                })
            
            # Handle POST request - Update profile
            name = kwargs.get('name')
            email = kwargs.get('email')
            address = kwargs.get('address')
            password = kwargs.get('password')
            
            try:
                # Update user
                user_vals = {
                    'name': name,
                    'email': email,
                }
                if password:
                    user_vals['password'] = password
                
                student.user_id.sudo().write(user_vals)
                
                # Update student
                student.sudo().write({
                    'name': name,
                    'email': email,
                    'address': address,
                })
                
                return request.render('odoo_student_management.student_profile', {
                    'student': student,
                    'success': 'Profile updated successfully'
                })
            except Exception as e:
                _logger.error(f"Error updating profile: {str(e)}")
                return request.render('odoo_student_management.student_profile', {
                    'student': student,
                    'error': 'Failed to update profile'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== NOTIFICATIONS ====================

    @http.route('/student_management/student/notifications', type='http', auth='user', methods=['GET'])
    def view_notifications(self, **kwargs):
        """View student notifications"""
        try:
            self._check_student_access()
            student = self._get_current_student()
            
            # Get notifications for this student
            notifications = request.env['student_management.notification_student'].search([
                ('student_id', '=', student.id)
            ], order='create_date desc')
            
            # Mark notifications as read when viewed
            unread_notifications = notifications.filtered(lambda n: not n.is_read)
            if unread_notifications:
                unread_notifications.sudo().write({'is_read': True})
            
            return request.render('odoo_student_management.student_notifications', {
                'notifications': notifications,
                'student': student
            })
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== API ENDPOINTS ====================

    @http.route('/student_management/api/student/get_attendance_summary', type='json', auth='user', methods=['POST'])
    def get_attendance_summary(self, subject_id=None, **kwargs):
        """Get attendance summary for student"""
        try:
            self._check_student_access()
            student = self._get_current_student()
            
            domain = [('student_id', '=', student.id)]
            if subject_id:
                domain.append(('subject_id', '=', subject_id))
            attendances = request.env['student_management.attendance'].search(domain)
            attendance_summary = {}
            for attendance in attendances:
                subject_id = attendance.subject_id.id
                if subject_id not in attendance_summary:
                    attendance_summary[subject_id] = {
                        'subject_name': attendance.subject_id.name,
                        'total_classes': 0,
                        'attended_classes': 0
                    }
                attendance_summary[subject_id]['total_classes'] += 1
                if attendance.is_present:
                    attendance_summary[subject_id]['attended_classes'] += 1

            return {'status': 'success', 'data': attendance_summary}
        except AccessError:
            return {'status': 'error', 'message': 'Access denied'}
        except Exception as e:
            _logger.error(f"Error getting attendance summary: {str(e)}")
            return {'status': 'error', 'message': 'Failed to get attendance summary'}