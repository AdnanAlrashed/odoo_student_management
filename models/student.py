from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Student(models.Model):
    _name = 'student_management.student'
    _description = 'Student'
    _order = 'name'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Information
    user_id = fields.Many2one(
        'res.users',
        string='User Account',
        required=True,
        ondelete='cascade',
        help='Linked user account for login'
    )
    name = fields.Char(
        string='Name',
        related='user_id.name',
        store=True,
        readonly=True
    )
    email = fields.Char(
        string='Email',
        related='user_id.email',
        store=True,
        readonly=True
    )
    phone = fields.Char(
        string='Phone',
        related='user_id.phone',
        store=True
    )
    
    # Student-specific Information
    student_id = fields.Char(
        string='Student ID',
        help='Unique student identification number'
    )
    address = fields.Text(
        string='Address',
        help='Home address of the student'
    )
    date_of_birth = fields.Date(
        string='Date of Birth'
    )
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender')
    profile_pic = fields.Binary(
        string='Profile Picture',
        attachment=True
    )
    
    # Academic Information
    course_id = fields.Many2one(
        'student_management.course',
        string='Course',
        required=True,
        ondelete='restrict',
        help='Course in which the student is enrolled'
    )
    session_year_id = fields.Many2one(
        'student_management.session_year',
        string='Session Year',
        required=True,
        ondelete='cascade',
        help='Academic session year of enrollment'
    )
    admission_date = fields.Date(
        string='Admission Date',
        default=fields.Date.today
    )
    current_semester = fields.Integer(
        string='Current Semester',
        default=1
    )
    
    # Status and Notifications
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to archive the student'
    )
    fcm_token = fields.Text(
        string='FCM Token',
        help='Firebase Cloud Messaging token for notifications'
    )
    
    # Related fields for statistics
    attendance_percentage = fields.Float(
        string='Overall Attendance %',
        compute='_compute_attendance_percentage',
        store=True
    )
    leave_count = fields.Integer(
        string='Leave Requests',
        compute='_compute_leave_count'
    )
    feedback_count = fields.Integer(
        string='Feedback Messages',
        compute='_compute_feedback_count'
    )
    notification_count = fields.Integer(
        string='Notifications',
        compute='_compute_notification_count'
    )
    result_count = fields.Integer(
        string='Results',
        compute='_compute_result_count'
    )
    
    # One2many relationships
    attendance_report_ids = fields.One2many(
        'student_management.attendance_report',
        'student_id',
        string='Attendance Reports'
    )
    leave_ids = fields.One2many(
        'student_management.leave_report_student',
        'student_id',
        string='Leave Requests'
    )
    feedback_ids = fields.One2many(
        'student_management.feedback_student',
        'student_id',
        string='Feedback Messages'
    )
    notification_ids = fields.One2many(
        'student_management.notification_student',
        'student_id',
        string='Notifications'
    )
    result_ids = fields.One2many(
        'student_management.student_result',
        'student_id',
        string='Academic Results'
    )
    subject_ids = fields.One2many(
        'student_management.subject',
        'course_id',
        string='Subjects',
        compute='_compute_subject_ids',
    )

    # Computed fields
    subject_count = fields.Integer(
        string='Subject Count',
        compute='_compute_subject_count'
    )
    overall_grade = fields.Float(
        string='Overall Grade',
        compute='_compute_overall_grade'
    )

    def _compute_attendance_percentage(self):
        for record in self:
            total_attendance = len(record.attendance_report_ids)
            if total_attendance > 0:
                present_count = len(record.attendance_report_ids.filtered('status'))
                record.attendance_percentage = (present_count / total_attendance) * 100
            else:
                record.attendance_percentage = 0.0

    def _compute_leave_count(self):
        for record in self:
            record.leave_count = len(record.leave_ids)

    def _compute_feedback_count(self):
        for record in self:
            record.feedback_count = len(record.feedback_ids)

    def _compute_notification_count(self):
        for record in self:
            record.notification_count = len(record.notification_ids)

    def _compute_result_count(self):
        for record in self:
            record.result_count = len(record.result_ids)

    @api.constrains('student_id')
    def _check_student_id_unique(self):
        for record in self:
            if record.student_id:
                existing = self.search([
                    ('id', '!=', record.id),
                    ('student_id', '=', record.student_id)
                ])
                if existing:
                    raise ValidationError(
                        f"Student ID '{record.student_id}' already exists."
                    )

    @api.constrains('user_id')
    def _check_user_id_unique(self):
        for record in self:
            if record.user_id:
                existing = self.search([
                    ('id', '!=', record.id),
                    ('user_id', '=', record.user_id.id)
                ])
                if existing:
                    raise ValidationError(
                        f"User account is already linked to another student."
                    )

    @api.constrains('current_semester')
    def _check_current_semester(self):
        for record in self:
            if record.current_semester and record.current_semester <= 0:
                raise ValidationError(
                    "Current semester must be greater than 0."
                    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure users are assigned to student group"""
        students = super().create(vals_list)
        student_group = self.env.ref('odoo_student_management.group_student_management_student', raise_if_not_found=False)
        if student_group:
            user_ids = [s.user_id.id for s in students if s.user_id]
            if user_ids:
                student_group.users = [(4, uid) for uid in user_ids]
        return students

    def write(self, vals):
        """Override write to handle user group changes"""
        result = super().write(vals)
        if 'user_id' in vals:
            for student in self:
                if student.user_id:
                    # Add user to student group
                    student_group = self.env.ref('odoo_student_management.group_student_management_student', raise_if_not_found=False)
                    if student_group:
                        student_group.users = [(4, student.user_id.id)]
        return result

    def action_view_attendance(self):
        """Action to view attendance records of this student"""
        return {
            'name': f'Attendance - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.attendance_report',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_view_leaves(self):
        """Action to view leave requests of this student"""
        return {
            'name': f'Leave Requests - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.leave_report_student',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_view_feedback(self):
        """Action to view feedback messages of this student"""
        return {
            'name': f'Feedback - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.feedback_student',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_view_results(self):
        """Action to view academic results of this student"""
        return {
            'name': f'Results - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.student_result',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_apply_leave(self):
        """Action to apply for leave"""
        return {
            'name': 'Apply for Leave',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.leave_report_student',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_student_id': self.id},
        }

    def action_send_feedback(self):
        """Action to send feedback"""
        return {
            'name': 'Send Feedback',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.feedback_student',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_student_id': self.id},
        }

    def name_get(self):
        result = []
        for record in self:
            name = record.name or 'New Student'
            if record.student_id:
                name = f"[{record.student_id}] {name}"
            if record.course_id:
                name = f"{name} ({record.course_id.course_name})"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced name search to include student ID and course name"""
        args = args or []
        if name:
            domain = [
                '|', '|', '|',
                ('name', operator, name),
                ('student_id', operator, name),
                ('course_id.course_name', operator, name),
                ('email', operator, name)
            ]
            students = self.search(domain + args, limit=limit)
            return students.name_get()
        return super().name_search(name, args, operator, limit)

    def _compute_subject_ids(self):
        for record in self:
            record.subject_ids = self.env['student_management.subject'].search([
                ('course_id', '=', record.course_id.id)
            ])

    def _compute_subject_count(self):
        for record in self:
            record.subject_count = len(record.subject_ids)

    def _compute_overall_grade(self):
        for record in self:
            if record.result_ids:
                record.overall_grade = sum(
                    r.total_marks for r in record.result_ids
                ) / len(record.result_ids)
            else:
                record.overall_grade = 0.0

    def action_create_user(self):
        """Create a user account for the student"""
        self.ensure_one()
        # Implementation would go here
        return True

    def action_activate(self):
        """Activate the student record"""
        self.ensure_one()
        self.write({'active': True})
        return True

    def action_deactivate(self):
        """Deactivate the student record"""
        self.ensure_one()
        self.write({'active': False})
        return True

# student Profile
    def action_open_student_profile_wizard(self):
        """
        Creates and opens the student profile editing wizard.
        """
        self.ensure_one()
        wizard = self.env['student_management.student.profile'].create({
            'student_id_ref': self.id,
            'phone': self.phone,
            'address': self.address,
            'date_of_birth': self.date_of_birth,
            'profile_pic': self.profile_pic,
        })

        return {
            'name': 'Edit My Profile',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.student.profile',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }

    @api.model_create_multi
    def create(self, vals_list):
        students = super().create(vals_list)
        for student in students:
            if student.course_id:
                subjects = self.env['student_management.subject'].search([
                    ('course_id', '=', student.course_id.id)
                ])
                student.write({'subject_ids': [(6, 0, subjects.ids)]})
        return students