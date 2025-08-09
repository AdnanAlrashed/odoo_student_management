import json
import logging
import base64
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class StudentManagementAdminController(http.Controller):
    """Admin controller for Student Management System HOD/Admin operations"""

    def _check_admin_access(self):
        """Check if current user has admin access"""
        if not request.env.user.has_group('student_management_django_odoo.group_student_management_admin'):
            raise AccessError("Access denied. Admin privileges required.")

    @http.route('/student_management/admin/dashboard', type='http', auth='user', methods=['GET'])
    def admin_dashboard(self, **kwargs):
        """Admin dashboard page"""
        try:
            self._check_admin_access()
            return request.render('student_management_django_odoo.admin_dashboard_template')
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== STAFF MANAGEMENT ====================

    @http.route('/student_management/admin/staff/add', type='http', auth='user', methods=['GET', 'POST'])
    def add_staff(self, **kwargs):
        """Add new staff member"""
        try:
            self._check_admin_access()
            
            if request.httprequest.method == 'GET':
                return request.render('student_management_django_odoo.add_staff_template')
            
            # Handle POST request
            first_name = kwargs.get('first_name')
            last_name = kwargs.get('last_name')
            username = kwargs.get('username')
            email = kwargs.get('email')
            password = kwargs.get('password')
            address = kwargs.get('address')
            
            if not all([first_name, last_name, username, email, password]):
                return request.render('student_management_django_odoo.add_staff_template', {
                    'error': 'All fields are required'
                })
            
            try:
                # Create user
                user_vals = {
                    'name': f"{first_name} {last_name}",
                    'login': email,
                    'email': email,
                    'password': password,
                    'groups_id': [(6, 0, [request.env.ref('student_management_django_odoo.group_student_management_staff').id])]
                }
                user = request.env['res.users'].sudo().create(user_vals)
                
                # Create staff record
                staff_vals = {
                    'user_id': user.id,
                    'name': f"{first_name} {last_name}",
                    'email': email,
                    'address': address,
                }
                request.env['student_management.staff'].sudo().create(staff_vals)
                
                return request.render('student_management_django_odoo.add_staff_template', {
                    'success': 'Staff member added successfully'
                })
            except Exception as e:
                _logger.error(f"Error adding staff: {str(e)}")
                return request.render('student_management_django_odoo.add_staff_template', {
                    'error': 'Failed to add staff member'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/admin/staff/manage', type='http', auth='user', methods=['GET'])
    def manage_staff(self, **kwargs):
        """Manage staff members"""
        try:
            self._check_admin_access()
            staffs = request.env['student_management.staff'].search([])
            return request.render('student_management_django_odoo.manage_staff_template', {
                'staffs': staffs
            })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/admin/staff/edit/<int:staff_id>', type='http', auth='user', methods=['GET', 'POST'])
    def edit_staff(self, staff_id, **kwargs):
        """Edit staff member"""
        try:
            self._check_admin_access()
            staff = request.env['student_management.staff'].sudo().browse(staff_id)
            
            if not staff.exists():
                return request.redirect('/student_management/admin/staff/manage')
            
            if request.httprequest.method == 'GET':
                return request.render('student_management_django_odoo.edit_staff_template', {
                    'staff': staff
                })
            
            # Handle POST request
            first_name = kwargs.get('first_name')
            last_name = kwargs.get('last_name')
            email = kwargs.get('email')
            address = kwargs.get('address')
            
            try:
                # Update user
                staff.user_id.sudo().write({
                    'name': f"{first_name} {last_name}",
                    'email': email,
                })
                
                # Update staff
                staff.sudo().write({
                    'name': f"{first_name} {last_name}",
                    'email': email,
                    'address': address,
                })
                
                return request.render('student_management_django_odoo.edit_staff_template', {
                    'staff': staff,
                    'success': 'Staff member updated successfully'
                })
            except Exception as e:
                _logger.error(f"Error updating staff: {str(e)}")
                return request.render('student_management_django_odoo.edit_staff_template', {
                    'staff': staff,
                    'error': 'Failed to update staff member'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== STUDENT MANAGEMENT ====================

    @http.route('/student_management/admin/student/add', type='http', auth='user', methods=['GET', 'POST'])
    def add_student(self, **kwargs):
        """Add new student"""
        try:
            self._check_admin_access()
            
            if request.httprequest.method == 'GET':
                courses = request.env['student_management.course'].search([])
                session_years = request.env['student_management.session_year'].search([])
                return request.render('student_management_django_odoo.add_student_template', {
                    'courses': courses,
                    'session_years': session_years
                })
            
            # Handle POST request
            first_name = kwargs.get('first_name')
            last_name = kwargs.get('last_name')
            username = kwargs.get('username')
            email = kwargs.get('email')
            password = kwargs.get('password')
            address = kwargs.get('address')
            course_id = kwargs.get('course_id')
            session_year_id = kwargs.get('session_year_id')
            gender = kwargs.get('gender')
            profile_pic = request.httprequest.files.get('profile_pic')
            
            if not all([first_name, last_name, username, email, password, course_id, session_year_id]):
                courses = request.env['student_management.course'].search([])
                session_years = request.env['student_management.session_year'].search([])
                return request.render('student_management_django_odoo.add_student_template', {
                    'courses': courses,
                    'session_years': session_years,
                    'error': 'All required fields must be filled'
                })
            
            try:
                # Create user
                user_vals = {
                    'name': f"{first_name} {last_name}",
                    'login': email,
                    'email': email,
                    'password': password,
                    'groups_id': [(6, 0, [request.env.ref('student_management_django_odoo.group_student_management_student').id])]
                }
                user = request.env['res.users'].sudo().create(user_vals)
                
                # Handle profile picture
                profile_pic_data = None
                if profile_pic:
                    profile_pic_data = base64.b64encode(profile_pic.read())
                
                # Create student record
                student_vals = {
                    'user_id': user.id,
                    'name': f"{first_name} {last_name}",
                    'email': email,
                    'address': address,
                    'course_id': int(course_id),
                    'session_year_id': int(session_year_id),
                    'gender': gender,
                    'profile_pic': profile_pic_data,
                }
                request.env['student_management.student'].sudo().create(student_vals)
                
                courses = request.env['student_management.course'].search([])
                session_years = request.env['student_management.session_year'].search([])
                return request.render('student_management_django_odoo.add_student_template', {
                    'courses': courses,
                    'session_years': session_years,
                    'success': 'Student added successfully'
                })
            except Exception as e:
                _logger.error(f"Error adding student: {str(e)}")
                courses = request.env['student_management.course'].search([])
                session_years = request.env['student_management.session_year'].search([])
                return request.render('student_management_django_odoo.add_student_template', {
                    'courses': courses,
                    'session_years': session_years,
                    'error': 'Failed to add student'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/admin/student/manage', type='http', auth='user', methods=['GET'])
    def manage_student(self, **kwargs):
        """Manage students"""
        try:
            self._check_admin_access()
            students = request.env['student_management.student'].search([])
            return request.render('student_management_django_odoo.manage_student_template', {
                'students': students
            })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/admin/student/edit/<int:student_id>', type='http', auth='user', methods=['GET', 'POST'])
    def edit_student(self, student_id, **kwargs):
        """Edit student"""
        try:
            self._check_admin_access()
            student = request.env['student_management.student'].sudo().browse(student_id)
            
            if not student.exists():
                return request.redirect('/student_management/admin/student/manage')
            
            if request.httprequest.method == 'GET':
                courses = request.env['student_management.course'].search([])
                session_years = request.env['student_management.session_year'].search([])
                return request.render('student_management_django_odoo.edit_student_template', {
                    'student': student,
                    'courses': courses,
                    'session_years': session_years
                })
            
            # Handle POST request
            first_name = kwargs.get('first_name')
            last_name = kwargs.get('last_name')
            email = kwargs.get('email')
            address = kwargs.get('address')
            course_id = kwargs.get('course_id')
            session_year_id = kwargs.get('session_year_id')
            gender = kwargs.get('gender')
            profile_pic = request.httprequest.files.get('profile_pic')
            
            try:
                # Update user
                student.user_id.sudo().write({
                    'name': f"{first_name} {last_name}",
                    'email': email,
                })
                
                # Handle profile picture
                update_vals = {
                    'name': f"{first_name} {last_name}",
                    'email': email,
                    'address': address,
                    'course_id': int(course_id),
                    'session_year_id': int(session_year_id),
                    'gender': gender,
                }
                
                if profile_pic:
                    update_vals['profile_pic'] = base64.b64encode(profile_pic.read())
                
                # Update student
                student.sudo().write(update_vals)
                
                courses = request.env['student_management.course'].search([])
                session_years = request.env['student_management.session_year'].search([])
                return request.render('student_management_django_odoo.edit_student_template', {
                    'student': student,
                    'courses': courses,
                    'session_years': session_years,
                    'success': 'Student updated successfully'
                })
            except Exception as e:
                _logger.error(f"Error updating student: {str(e)}")
                courses = request.env['student_management.course'].search([])
                session_years = request.env['student_management.session_year'].search([])
                return request.render('student_management_django_odoo.edit_student_template', {
                    'student': student,
                    'courses': courses,
                    'session_years': session_years,
                    'error': 'Failed to update student'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== COURSE MANAGEMENT ====================

    @http.route('/student_management/admin/course/add', type='http', auth='user', methods=['GET', 'POST'])
    def add_course(self, **kwargs):
        """Add new course"""
        try:
            self._check_admin_access()
            
            if request.httprequest.method == 'GET':
                return request.render('student_management_django_odoo.add_course_template')
            
            # Handle POST request
            course_name = kwargs.get('course_name')
            
            if not course_name:
                return request.render('student_management_django_odoo.add_course_template', {
                    'error': 'Course name is required'
                })
            
            try:
                request.env['student_management.course'].sudo().create({
                    'course_name': course_name
                })
                
                return request.render('student_management_django_odoo.add_course_template', {
                    'success': 'Course added successfully'
                })
            except Exception as e:
                _logger.error(f"Error adding course: {str(e)}")
                return request.render('student_management_django_odoo.add_course_template', {
                    'error': 'Failed to add course'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/admin/course/manage', type='http', auth='user', methods=['GET'])
    def manage_course(self, **kwargs):
        """Manage courses"""
        try:
            self._check_admin_access()
            courses = request.env['student_management.course'].search([])
            return request.render('student_management_django_odoo.manage_course_template', {
                'courses': courses
            })
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== SUBJECT MANAGEMENT ====================

    @http.route('/student_management/admin/subject/add', type='http', auth='user', methods=['GET', 'POST'])
    def add_subject(self, **kwargs):
        """Add new subject"""
        try:
            self._check_admin_access()
            
            if request.httprequest.method == 'GET':
                courses = request.env['student_management.course'].search([])
                staffs = request.env['student_management.staff'].search([])
                return request.render('student_management_django_odoo.add_subject_template', {
                    'courses': courses,
                    'staffs': staffs
                })
            
            # Handle POST request
            subject_name = kwargs.get('subject_name')
            course_id = kwargs.get('course_id')
            staff_id = kwargs.get('staff_id')
            
            if not all([subject_name, course_id, staff_id]):
                courses = request.env['student_management.course'].search([])
                staffs = request.env['student_management.staff'].search([])
                return request.render('student_management_django_odoo.add_subject_template', {
                    'courses': courses,
                    'staffs': staffs,
                    'error': 'All fields are required'
                })
            
            try:
                request.env['student_management.subject'].sudo().create({
                    'subject_name': subject_name,
                    'course_id': int(course_id),
                    'staff_id': int(staff_id)
                })
                
                courses = request.env['student_management.course'].search([])
                staffs = request.env['student_management.staff'].search([])
                return request.render('student_management_django_odoo.add_subject_template', {
                    'courses': courses,
                    'staffs': staffs,
                    'success': 'Subject added successfully'
                })
            except Exception as e:
                _logger.error(f"Error adding subject: {str(e)}")
                courses = request.env['student_management.course'].search([])
                staffs = request.env['student_management.staff'].search([])
                return request.render('student_management_django_odoo.add_subject_template', {
                    'courses': courses,
                    'staffs': staffs,
                    'error': 'Failed to add subject'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/admin/subject/manage', type='http', auth='user', methods=['GET'])
    def manage_subject(self, **kwargs):
        """Manage subjects"""
        try:
            self._check_admin_access()
            subjects = request.env['student_management.subject'].search([])
            return request.render('student_management_django_odoo.manage_subject_template', {
                'subjects': subjects
            })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/admin/subject/edit/<int:subject_id>', type='http', auth='user', methods=['GET', 'POST'])
    def edit_subject(self, subject_id, **kwargs):
        """Edit subject"""
        try:
            self._check_admin_access()
            subject = request.env['student_management.subject'].browse(subject_id)

            if request.httprequest.method == 'GET':
                courses = request.env['student_management.course'].search([])
                staffs = request.env['student_management.staff'].search([])
                return request.render('student_management_django_odoo.edit_subject_template', {
                    'subject': subject,
                    'courses': courses,
                    'staffs': staffs
                })

            # Handle POST request
            subject_name = kwargs.get('subject_name')
            course_id = kwargs.get('course_id')
            staff_id = kwargs.get('staff_id')

            if not all([subject_name, course_id, staff_id]):
                courses = request.env['student_management.course'].search([])
                staffs = request.env['student_management.staff'].search([])
                return request.render('student_management_django_odoo.edit_subject_template', {
                    'subject': subject,
                    'courses': courses,
                    'staffs': staffs,
                    'error': 'All fields are required'
                })

            try:
                subject.sudo().write({
                    'subject_name': subject_name,
                    'course_id': int(course_id),
                    'staff_id': int(staff_id)
                })

                courses = request.env['student_management.course'].search([])
                staffs = request.env['student_management.staff'].search([])
                return request.render('student_management_django_odoo.edit_subject_template', {
                    'subject': subject,
                    'courses': courses,
                    'staffs': staffs,
                    'success': 'Subject updated successfully'
                })
            except Exception as e:
                _logger.error(f"Error updating subject: {str(e)}")
                courses = request.env['student_management.course'].search([])
                staffs = request.env['student_management.staff'].search([])
                return request.render('student_management_django_odoo.edit_subject_template', {
                    'subject': subject,
                    'courses': courses,
                    'staffs': staffs,
                    'error': 'Failed to update subject'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/admin/subject/delete/<int:subject_id>', type='http', auth='user', methods=['POST'])
    def delete_subject(self, subject_id, **kwargs):
        """Delete subject"""
        try:
            self._check_admin_access()
            subject = request.env['student_management.subject'].browse(subject_id)
            subject.sudo().unlink()
            return request.redirect('/student_management/admin/subject/manage')
        except AccessError:
            return request.redirect('/student_management/login')