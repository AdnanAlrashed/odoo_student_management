import json
import logging
import base64
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class StudentManagementAdminController(http.Controller):
    """Admin controller for Student Management System HOD/Admin operations"""

    # ===== ثوابت المجموعات =====
    ADMIN_GROUP = 'odoo_student_management.group_student_management_admin'
    STAFF_GROUP = 'odoo_student_management.group_student_management_staff'
    STUDENT_GROUP = 'odoo_student_management.group_student_management_student'

    def _check_admin_access(self):
        """Check if current user has admin access"""
        if not request.env.user.has_group(self.ADMIN_GROUP):
            raise AccessError("Access denied. Admin privileges required.")

    # ===== دوال مساعدة للإحصائيات =====
    def _safe_count(self, model_names, domain=None):
        """يحاول العد على أول موديل متاح من القائمة (مع sudo)، وإلا يرجّع 0"""
        domain = domain or []
        for name in model_names:
            try:
                return request.env[name].sudo().search_count(domain)
            except Exception:
                continue
        return 0

    def _count_staff(self):
        """
        يحسب عدد الموظفين:
        1) إن وُجد موديل staff مخصص: student_management.staff
        2) وإلا: عدد مستخدمي res.users ضمن مجموعة الموظفين (fallback)
        """
        try:
            count_staff_model = request.env['student_management.staff'].sudo().search_count([])
            if count_staff_model:
                return count_staff_model
        except Exception:
            pass

        try:
            staff_group = request.env.ref(self.STAFF_GROUP)
            return request.env['res.users'].sudo().search_count([
                ('groups_id', 'in', [staff_group.id]),
                ('active', '=', True),
            ])
        except Exception:
            return 0

    def _count_status_any(self, model_names, field_candidates=('leave_status', 'state'), pending_values=('pending', 'to_approve', 'confirm')):
        """
        يحاول إيجاد حقل حالة صالح (leave_status أو state)، ثم يجمع القيم التي تُعد "قيد الموافقة".
        يجرّب الموديلات بالترتيب ويرجع أول نتيجة صالحة (حتى لو كانت 0).
        """
        for model in model_names:
            try:
                env_model = request.env[model].sudo()
            except Exception:
                continue
            # جرّب الحقول المحتملة
            for field in field_candidates:
                total = 0
                field_ok = False
                for val in pending_values:
                    try:
                        cnt = env_model.search_count([(field, '=', val)])
                        total += int(cnt)
                        field_ok = True
                    except Exception:
                        # هذا الحقل غير موجود أو القيمة غير صالحة للموديل الحالي
                        continue
                if field_ok:
                    return total
        return 0

    @http.route('/student_management/admin/dashboard', type='http', auth='user', website=True, methods=['GET'])
    def admin_dashboard(self, **kwargs):
        """Admin dashboard page"""
        try:
            self._check_admin_access()

            values = {
                # الأساسيات
                'total_students':  self._safe_count(['student_management.student',  'student.student']),
                'total_courses':   self._safe_count(['student_management.course',   'student.course']),
                'total_subjects':  self._safe_count(['student_management.subject',  'student.subject']),
                'total_staff':     self._count_staff(),

                # إحصائيات إضافية
                'total_sessions':  self._safe_count(['student_management.session_year', 'student.session_year']),
                'total_attendance': self._safe_count(['student_management.attendance', 'student.attendance']),

                # طلبات إجازة قيد الموافقة (موظفون/طلاب) — مرنة حسب حقول الحالة والموديلات
                'pending_staff_leaves': self._count_status_any(
                    ['student_management.leave_report_staff', 'hr.leave'],
                    field_candidates=('leave_status', 'state'),
                    pending_values=('pending', 'to_approve', 'confirm')
                ),
                'pending_student_leaves': self._count_status_any(
                    ['student_management.leave_report_student', 'student_management.leave_report', 'hr.leave'],
                    field_candidates=('leave_status', 'state'),
                    pending_values=('pending', 'to_approve', 'confirm')
                ),
            }
            return request.render('odoo_student_management.admin_dashboard_template', values)
        except AccessError:
            return request.redirect('/student_management/login')

    # ==================== STAFF MANAGEMENT ====================

    @http.route('/student_management/admin/staff/add', type='http', auth='user', website=True, methods=['GET', 'POST'] )
    def add_staff(self, **kwargs):
        """Add new staff member (link existing user OR create new) - Enhanced Version"""
        try:
            self._check_admin_access()
            Staff = request.env['student_management.staff'].sudo()
            Users = request.env['res.users'].sudo()

            # جلب مجموعة الموظفين
            try:
                staff_group = request.env.ref(self.STAFF_GROUP)
            except Exception as e:
                _logger.error("Could not find staff group '%s': %s", self.STAFF_GROUP, e)
                staff_group = None

            # ===== معالجة طلب GET (عرض النموذج) =====
            if request.httprequest.method == 'GET':
                # جلب المستخدمين الذين لديهم صلاحية موظف وغير مرتبطين بملف موظف آخر
                existing_staff_user_ids = Staff.search([('active', '=', True )]).mapped('user_id').ids
                
                domain = [
                    ('active', '=', True),
                    ('id', 'not in', existing_staff_user_ids),
                ]
                # فلترة المستخدمين حسب مجموعة الموظفين إذا كانت موجودة
                if staff_group:
                    domain.append(('groups_id', 'in', [staff_group.id]))

                available_users = Users.search(domain)
                
                return request.render('odoo_student_management.add_staff_template', {
                    'available_users': available_users,
                })

            # ===== معالجة طلب POST (حفظ البيانات) =====
            user = None
            
            # --- الحالة 1: ربط مستخدم موجود ---
            user_id = kwargs.get('user_id')
            if user_id:
                user = Users.browse(int(user_id))
                if not user.exists():
                    return request.render('odoo_student_management.add_staff_template', {'error': 'Selected user not found.'})
            
            # --- الحالة 2: إنشاء مستخدم جديد ---
            if not user:
                name = kwargs.get('name')
                email = kwargs.get('email')
                password = kwargs.get('password')
                phone = kwargs.get('phone') # إضافة حقل الهاتف

                if not all([name, email, password]):
                    return request.render('odoo_student_management.add_staff_template', {
                        'error': 'To create a new user, you must provide Name, Email, and Password.',
                    })
                
                try:
                    user_vals = {
                        'name': name,
                        'login': email,
                        'email': email,
                        'password': password,
                        'phone': phone,
                    }
                    # إضافة المستخدم لمجموعة الموظفين عند الإنشاء
                    if staff_group:
                        user_vals['groups_id'] = [(6, 0, [staff_group.id])]
                        
                    user = Users.create(user_vals)
                except Exception as e:
                    _logger.error("Error creating user for staff: %s", e, exc_info=True)
                    return request.render('odoo_student_management.add_staff_template', {'error': 'Failed to create user account. The email might already exist.'})

            # --- الخطوة النهائية: إنشاء سجل الموظف ---
            try:
                staff_vals = {
                    'user_id': user.id,
                    'employee_id': kwargs.get('employee_id'),
                    'address': kwargs.get('address'),
                    'gender': kwargs.get('gender'), # إضافة حقل الجنس
                }
                Staff.create(staff_vals)
            except Exception as e:
                _logger.error("Error creating staff record: %s", e, exc_info=True)
                return request.render('odoo_student_management.add_staff_template', {'error': 'Failed to create staff profile.'})

            # بعد النجاح، إعادة التوجيه إلى صفحة إدارة الموظفين
            return request.redirect('/student_management/admin/staff/manage')

        except AccessError:
            return request.redirect('/student_management/login')
        except Exception as e:
            # معالجة أي خطأ غير متوقع
            _logger.error("Unhandled error in add_staff: %s", e, exc_info=True)
            return request.render('odoo_student_management.add_staff_template', {
                'error': 'An unexpected system error occurred. Please contact the administrator.'
            })


    @http.route('/student_management/admin/staff/edit/<int:staff_id>', type='http', auth='user', methods=['GET', 'POST'])
    def edit_staff(self, staff_id, **kwargs):
        """Edit staff member"""
        try:
            self._check_admin_access()
            staff = request.env['student_management.staff'].sudo().browse(staff_id)
            
            if not staff.exists():
                return request.redirect('/student_management/admin/staff/manage')
            
            if request.httprequest.method == 'GET':
                return request.render('odoo_student_management.edit_staff_simple_template', {
                    'staff': staff
                })
            
            # Handle POST request
            email = kwargs.get('email')
            address = kwargs.get('address')
            phone = kwargs.get('phone')

            try:
                # Update user
                staff.user_id.sudo().write({
                    'email': email,
                    'phone': phone or False,
                })
                
                # Update staff
                staff.sudo().write({
                    'address': address or False,
                })
                
                # إرجاع رد JavaScript لإغلاق النافذة وتحديث الصفحة
                return "OK"
                    
            except Exception as e:
                _logger.error(f"Error updating staff: {str(e)}")
                return request.render('odoo_student_management.edit_staff_simple_template', {
                    'staff': staff,
                    'error': 'Failed to update staff member. Please try again.'
                })
                
        except AccessError:
            return request.redirect('/student_management/login')
  


    @http.route('/student_management/admin/staff/manage', type='http', auth='user', website=True, methods=['GET'])
    def manage_staff(self, **kwargs):
        """Manage staff members"""
        try:
            self._check_admin_access()  # تأكد من صلاحيات المدير
            staffs = request.env['student_management.staff'].sudo().search([])  # جلب الموظفين
            return request.render('odoo_student_management.manage_staff_template', {
                'staffs': staffs  # تم تمرير الموظفين للقالب
            })
        except AccessError:
            return request.redirect('/student_management/login')  # في حالة عدم صلاحية الوصول، إعادة التوجيه



        # ==================== STUDENT MANAGEMENT ====================

    @http.route('/student_management/admin/student/add', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def add_student(self, **kwargs):
        """Add new student (link existing user OR create new)"""
        try:
            self._check_admin_access()
            Student = request.env['student_management.student'].sudo()
            Users = request.env['res.users'].sudo()

            # مجموعة الطلاب
            try:
                student_group = request.env.ref(self.STUDENT_GROUP)
            except Exception as e:
                _logger.error("Could not find student group '%s': %s", self.STUDENT_GROUP, e)
                student_group = None

            if request.httprequest.method == 'GET':
                # جلب المستخدمين الذين لديهم صلاحية طالب وغير مرتبطين بملف طالب آخر
                existing_student_user_ids = Student.search([('active', '=', True )]).mapped('user_id').ids
                
                domain = [
                    ('active', '=', True),
                    ('id', 'not in', existing_student_user_ids),
                ]
                if student_group:
                    domain.append(('groups_id', 'in', [student_group.id]))

                available_users = Users.search(domain)
                
                courses = request.env['student_management.course'].sudo().search([])
                session_years = request.env['student_management.session_year'].sudo().search([])
                
                return request.render('odoo_student_management.add_student_template', {
                    'available_users': available_users,
                    'courses': courses,
                    'session_years': session_years,
                })

            # ====== POST ======
            user = None
            
            # 1) ربط مستخدم موجود
            user_id = kwargs.get('user_id')
            if user_id:
                user = Users.browse(int(user_id))
                if not user.exists():
                    # (يمكن إضافة رسالة خطأ هنا)
                    pass 
            
            # 2) أو إنشاء مستخدم جديد
            if not user:
                name = kwargs.get('name')
                email = kwargs.get('email')
                password = kwargs.get('password')
                phone = kwargs.get('phone')
                
                if not all([name, email, password]):
                     return request.render('odoo_student_management.add_student_template', {
                        'error': 'Select an existing user OR provide Name, Email, and Password to create one.',
                        # إعادة تمرير البيانات اللازمة للقالب
                        'courses': request.env['student_management.course'].sudo().search([]),
                        'session_years': request.env['student_management.session_year'].sudo().search([]),
                    })
                
                try:
                    user_vals = {
                        'name': name,
                        'login': email,
                        'email': email,
                        'password': password,
                        'phone': phone,
                    }
                    # إضافة المستخدم لمجموعة الطلاب عند الإنشاء
                    if student_group:
                        user_vals['groups_id'] = [(6, 0, [student_group.id])]
                    user = Users.create(user_vals)
                except Exception as e:
                    _logger.error("Error creating user for student: %s", e)
                    # (يمكن إضافة رسالة خطأ هنا)

            # 3) إنشاء سجل الطالب
            try:
                profile_pic_data = None
                if 'profile_pic' in request.httprequest.files:
                    profile_pic = request.httprequest.files.get('profile_pic' )
                    if profile_pic.filename:
                        profile_pic_data = base64.b64encode(profile_pic.read())

                student_vals = {
                    'user_id': user.id,
                    'student_id': kwargs.get('student_id'),
                    'address': kwargs.get('address'),
                    'date_of_birth': kwargs.get('date_of_birth') or None,
                    'gender': kwargs.get('gender'),
                    'course_id': int(kwargs.get('course_id')),
                    'session_year_id': int(kwargs.get('session_year_id')),
                    'profile_pic': profile_pic_data,
                }
                Student.create(student_vals)
            except Exception as e:
                _logger.error("Error creating student record: %s", e)
                # (يمكن إضافة رسالة خطأ هنا)

            # إعادة التوجيه إلى صفحة إدارة الطلاب بعد النجاح
            return request.redirect('/student_management/admin/student/manage')

        except AccessError:
            return request.redirect('/student_management/login')
        except Exception as e:
            _logger.error("Unhandled error in add_student: %s", e, exc_info=True)
            return request.render('odoo_student_management.add_student_template', {
                'error': 'An unexpected error occurred. Please check the logs.',
                'courses': request.env['student_management.course'].sudo().search([]),
                'session_years': request.env['student_management.session_year'].sudo().search([]),
            })



    @http.route('/student_management/admin/student/manage', type='http', auth='user', methods=['GET'])
    def manage_student(self, **kwargs):
        """Manage students"""
        try:
            self._check_admin_access()
            students = request.env['student_management.student'].sudo().search([])
            return request.render('odoo_student_management.manage_student_template', {
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
                courses = request.env['student_management.course'].sudo().search([])
                session_years = request.env['student_management.session_year'].sudo().search([])
                return request.render('odoo_student_management.edit_student_template', {
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
                
                courses = request.env['student_management.course'].sudo().search([])
                session_years = request.env['student_management.session_year'].sudo().search([])
                return request.render('odoo_student_management.edit_student_template', {
                    'student': student,
                    'courses': courses,
                    'session_years': session_years,
                    'success': 'Student updated successfully'
                })
            except Exception as e:
                _logger.error(f"Error updating student: {str(e)}")
                courses = request.env['student_management.course'].sudo().search([])
                session_years = request.env['student_management.session_year'].sudo().search([])
                return request.render('odoo_student_management.edit_student_template', {
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
                return request.render('odoo_student_management.add_course_template')
            
            # Handle POST request
            course_name = kwargs.get('course_name')
            
            if not course_name:
                return request.render('odoo_student_management.add_course_template', {
                    'error': 'Course name is required'
                })
            
            try:
                request.env['student_management.course'].sudo().create({
                    'course_name': course_name
                })
                
                return request.render('odoo_student_management.add_course_template', {
                    'success': 'Course added successfully'
                })
            except Exception as e:
                _logger.error(f"Error adding course: {str(e)}")
                return request.render('odoo_student_management.add_course_template', {
                    'error': 'Failed to add course'
                })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/admin/course/manage', type='http', auth='user', methods=['GET'])
    def manage_course(self, **kwargs):
        """Manage courses"""
        try:
            self._check_admin_access()
            courses = request.env['student_management.course'].sudo().search([])
            return request.render('odoo_student_management.manage_course_template', {
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
                courses = request.env['student_management.course'].sudo().search([])
                staffs = request.env['student_management.staff'].sudo().search([])
                return request.render('odoo_student_management.add_subject_template', {
                    'courses': courses,
                    'staffs': staffs
                })
            
            # Handle POST request
            subject_name = kwargs.get('subject_name')
            course_id = kwargs.get('course_id')
            staff_id = kwargs.get('staff_id')
            
            if not all([subject_name, course_id, staff_id]):
                courses = request.env['student_management.course'].sudo().search([])
                staffs = request.env['student_management.staff'].sudo().search([])
                return request.render('odoo_student_management.add_subject_template', {
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
                
                courses = request.env['student_management.course'].sudo().search([])
                staffs = request.env['student_management.staff'].sudo().search([])
                return request.render('odoo_student_management.add_subject_template', {
                    'courses': courses,
                    'staffs': staffs,
                    'success': 'Subject added successfully'
                })
            except Exception as e:
                _logger.error(f"Error adding subject: {str(e)}")
                courses = request.env['student_management.course'].sudo().search([])
                staffs = request.env['student_management.staff'].sudo().search([])
                return request.render('odoo_student_management.add_subject_template', {
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
            subjects = request.env['student_management.subject'].sudo().search([])
            return request.render('odoo_student_management.manage_subject_template', {
                'subjects': subjects
            })
        except AccessError:
            return request.redirect('/student_management/login')

    @http.route('/student_management/admin/subject/edit/<int:subject_id>', type='http', auth='user', methods=['GET', 'POST'])
    def edit_subject(self, subject_id, **kwargs):
        """Edit subject"""
        try:
            self._check_admin_access()
            subject = request.env['student_management.subject'].sudo().browse(subject_id)

            if request.httprequest.method == 'GET':
                courses = request.env['student_management.course'].sudo().search([])
                staffs = request.env['student_management.staff'].sudo().search([])
                return request.render('odoo_student_management.edit_subject_template', {
                    'subject': subject,
                    'courses': courses,
                    'staffs': staffs
                })

            # Handle POST request
            subject_name = kwargs.get('subject_name')
            course_id = kwargs.get('course_id')
            staff_id = kwargs.get('staff_id')

            if not all([subject_name, course_id, staff_id]):
                courses = request.env['student_management.course'].sudo().search([])
                staffs = request.env['student_management.staff'].sudo().search([])
                return request.render('odoo_student_management.edit_subject_template', {
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

                courses = request.env['student_management.course'].sudo().search([])
                staffs = request.env['student_management.staff'].sudo().search([])
                return request.render('odoo_student_management.edit_subject_template', {
                    'subject': subject,
                    'courses': courses,
                    'staffs': staffs,
                    'success': 'Subject updated successfully'
                })
            except Exception as e:
                _logger.error(f"Error updating subject: {str(e)}")
                courses = request.env['student_management.course'].sudo().search([])
                staffs = request.env['student_management.staff'].sudo().search([])
                return request.render('odoo_student_management.edit_subject_template', {
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
            subject = request.env['student_management.subject'].sudo().browse(subject_id)
            subject.sudo().unlink()
            return request.redirect('/student_management/admin/subject/manage')
        except AccessError:
            return request.redirect('/student_management/login')