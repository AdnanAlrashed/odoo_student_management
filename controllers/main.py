import json
import logging
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class StudentManagementMainController(http.Controller):
    """Main controller for Student Management System authentication and common functions"""

    @http.route('/student_management/login', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def login_page(self, **kwargs):
        """Display login page or handle login request"""
        if request.httprequest.method == 'GET':
            return request.render('student_management_django_odoo.login_page_template')
        
        # Handle POST login request
        email = kwargs.get('email')
        password = kwargs.get('password')
        
        if not email or not password:
            return request.render('student_management_django_odoo.login_page_template', {
                'error': 'Email and password are required'
            })
        
        try:
            # Authenticate user
            uid = request.session.authenticate(request.session.db, email, password)
            if uid:
                user = request.env['res.users'].sudo().browse(uid)
                
                # Determine user type and redirect accordingly
                if user.has_group('student_management_django_odoo.group_student_management_admin'):
                    return request.redirect('/student_management/admin/dashboard')
                elif user.has_group('student_management_django_odoo.group_student_management_staff'):
                    return request.redirect('/student_management/staff/dashboard')
                elif user.has_group('student_management_django_odoo.group_student_management_student'):
                    return request.redirect('/student_management/student/dashboard')
                else:
                    return request.render('student_management_django_odoo.login_page_template', {
                        'error': 'User does not have access to Student Management System'
                    })
            else:
                return request.render('student_management_django_odoo.login_page_template', {
                    'error': 'Invalid email or password'
                })
        except Exception as e:
            _logger.error(f"Login error: {str(e)}")
            return request.render('student_management_django_odoo.login_page_template', {
                'error': 'Login failed. Please try again.'
            })

    @http.route('/student_management/logout', type='http', auth='user', methods=['GET'])
    def logout(self, **kwargs):
        """Logout user and redirect to login page"""
        request.session.logout()
        return request.redirect('/student_management/login')

    @http.route('/student_management/user_details', type='json', auth='user', methods=['POST'])
    def get_user_details(self, **kwargs):
        """Get current user details"""
        try:
            user = request.env.user
            user_type = 'unknown'
            
            if user.has_group('student_management_django_odoo.group_student_management_admin'):
                user_type = 'admin'
            elif user.has_group('student_management_django_odoo.group_student_management_staff'):
                user_type = 'staff'
            elif user.has_group('student_management_django_odoo.group_student_management_student'):
                user_type = 'student'
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'user_type': user_type,
                }
            }
        except Exception as e:
            _logger.error(f"Error getting user details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/student_management/dashboard_stats', type='json', auth='user', methods=['POST'])
    def get_dashboard_stats(self, **kwargs):
        """Get dashboard statistics for admin users"""
        try:
            # Check if user is admin
            if not request.env.user.has_group('student_management_django_odoo.group_student_management_admin'):
                raise AccessError("Access denied. Admin privileges required.")
            
            # Get basic counts
            student_count = request.env['student_management.student'].search_count([])
            staff_count = request.env['student_management.staff'].search_count([])
            course_count = request.env['student_management.course'].search_count([])
            subject_count = request.env['student_management.subject'].search_count([])
            
            # Get course statistics
            courses = request.env['student_management.course'].search([])
            course_stats = []
            for course in courses:
                course_stats.append({
                    'name': course.course_name,
                    'student_count': course.student_count,
                    'subject_count': course.subject_count,
                })
            
            # Get subject statistics
            subjects = request.env['student_management.subject'].search([])
            subject_stats = []
            for subject in subjects:
                subject_stats.append({
                    'name': subject.subject_name,
                    'course': subject.course_id.course_name,
                    'student_count': subject.student_count,
                })
            
            # Get staff attendance statistics
            staff_stats = []
            staffs = request.env['student_management.staff'].search([])
            for staff in staffs:
                # Count attendance records for subjects taught by this staff
                attendance_count = request.env['student_management.attendance'].search_count([
                    ('subject_id.staff_id', '=', staff.id),
                    ('status', '=', 'present')
                ])
                
                # Count leave requests
                leave_count = request.env['student_management.leave_report_staff'].search_count([
                    ('staff_id', '=', staff.id),
                    ('leave_status', '=', 'approved')
                ])
                
                staff_stats.append({
                    'name': staff.name,
                    'attendance_count': attendance_count,
                    'leave_count': leave_count,
                })
            
            # Get student attendance statistics
            student_stats = []
            students = request.env['student_management.student'].search([])
            for student in students:
                present_count = request.env['student_management.attendance'].search_count([
                    ('student_id', '=', student.id),
                    ('status', '=', 'present')
                ])
                
                absent_count = request.env['student_management.attendance'].search_count([
                    ('student_id', '=', student.id),
                    ('status', '=', 'absent')
                ])
                
                leave_count = request.env['student_management.leave_report_student'].search_count([
                    ('student_id', '=', student.id),
                    ('leave_status', '=', 'approved')
                ])
                
                student_stats.append({
                    'name': student.name,
                    'present_count': present_count,
                    'absent_count': absent_count + leave_count,
                })
            
            return {
                'success': True,
                'stats': {
                    'counts': {
                        'students': student_count,
                        'staff': staff_count,
                        'courses': course_count,
                        'subjects': subject_count,
                    },
                    'courses': course_stats,
                    'subjects': subject_stats,
                    'staff': staff_stats,
                    'students': student_stats,
                }
            }
        except Exception as e:
            _logger.error(f"Error getting dashboard stats: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/student_management/api/notifications', type='json', auth='user', methods=['POST'])
    def get_notifications(self, **kwargs):
        """Get notifications for current user"""
        try:
            user = request.env.user
            notifications = []
            
            if user.has_group('student_management_django_odoo.group_student_management_student'):
                # Get student notifications
                student = request.env['student_management.student'].search([('user_id', '=', user.id)], limit=1)
                if student:
                    student_notifications = request.env['student_management.notification_student'].search([
                        ('student_id', '=', student.id),
                        ('is_read', '=', False)
                    ], limit=10, order='create_date desc')
                    
                    for notif in student_notifications:
                        notifications.append({
                            'id': notif.id,
                            'title': notif.title,
                            'message': notif.message,
                            'type': notif.notification_type,
                            'priority': notif.priority,
                            'date': notif.create_date.strftime('%Y-%m-%d %H:%M:%S'),
                        })
            
            elif user.has_group('student_management_django_odoo.group_student_management_staff'):
                # Get staff notifications
                staff = request.env['student_management.staff'].search([('user_id', '=', user.id)], limit=1)
                if staff:
                    staff_notifications = request.env['student_management.notification_staff'].search([
                        ('staff_id', '=', staff.id),
                        ('is_read', '=', False)
                    ], limit=10, order='create_date desc')
                    
                    for notif in staff_notifications:
                        notifications.append({
                            'id': notif.id,
                            'title': notif.title,
                            'message': notif.message,
                            'type': notif.notification_type,
                            'priority': notif.priority,
                            'date': notif.create_date.strftime('%Y-%m-%d %H:%M:%S'),
                        })
            
            return {
                'success': True,
                'notifications': notifications
            }
        except Exception as e:
            _logger.error(f"Error getting notifications: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/student_management/api/mark_notification_read', type='json', auth='user', methods=['POST'])
    def mark_notification_read(self, notification_id, **kwargs):
        """Mark notification as read"""
        try:
            user = request.env.user
            
            if user.has_group('student_management_django_odoo.group_student_management_student'):
                notification = request.env['student_management.notification_student'].browse(notification_id)
                if notification.student_id.user_id.id == user.id:
                    notification.action_mark_as_read()
                    return {'success': True}
            
            elif user.has_group('student_management_django_odoo.group_student_management_staff'):
                notification = request.env['student_management.notification_staff'].browse(notification_id)
                if notification.staff_id.user_id.id == user.id:
                    notification.action_mark_as_read()
                    return {'success': True}
            
            return {
                'success': False,
                'error': 'Notification not found or access denied'
            }
        except Exception as e:
            _logger.error(f"Error marking notification as read: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
