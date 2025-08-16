from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Course(models.Model):
    _name = 'student_management.course'
    _description = 'Academic Course'
    _order = 'course_name'
    _rec_name = 'course_name'
    
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Technical field to satisfy database constraint',
        default=lambda self: self._default_name()
    )
    
    def _default_name(self):
        return "Temp Name"
    
    _inherit = [
        'mail.thread.cc',              # لتتبع التغييرات عبر الشات
        'mail.activity.mixin',         # لدعم الأنشطة المجدولة
        'mail.tracking.duration.mixin',# لتتبع مدة المراحل
        'ir.attachment',               # لربط المرفقات مباشرة بالنموذج
    ]

    course_name = fields.Char(
        string='Course Name',
        required=True,
        help='Name of the academic course'
    )
    course_code = fields.Char(
        string='Course Code',
        help='Unique code for the course'
    )
    description = fields.Text(
        string='Description',
        help='Detailed description of the course'
    )
    duration_years = fields.Integer(
        string='Duration (Years)',
        default=4,
        help='Duration of the course in years'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to archive the course'
    )
    fcm_token = fields.Text(
        string='FCM Token',
        help='Firebase Cloud Messaging token for notifications'
    )
    
    # Related fields for statistics
    subject_count = fields.Integer(
        string='Number of Subjects',
        compute='_compute_subject_count'
    )
    student_count = fields.Integer(
        string='Number of Students',
        compute='_compute_student_count'
    )
    staff_count = fields.Integer(
        string='Number of Staff',
        compute='_compute_staff_count'
    )
    active_students = fields.Integer(
        string='Active Students',
        compute='_compute_active_counts'
    )
    active_subjects = fields.Integer(
        string='Active Subjects',
        compute='_compute_active_counts'
    )
    
    # One2many relationships
    subject_ids = fields.One2many(
        'student_management.subject',
        'course_id',
        string='Subjects'
    )
    student_ids = fields.One2many(
        'student_management.student',
        'course_id',
        string='Students'
    )

    @api.depends('course_name')
    def _compute_name(self):
        for record in self:
            record.name = record.course_name

    def _compute_subject_count(self):
        for record in self:
            record.subject_count = len(record.subject_ids)

    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.student_ids)

    def _compute_active_counts(self):
        for record in self:
            record.active_students = len(record.student_ids.filtered(lambda s: s.active))
            record.active_subjects = len(record.subject_ids.filtered(lambda s: s.active))

    def _compute_staff_count(self):
        for record in self:
            # Count unique staff members teaching subjects in this course
            staff_ids = record.subject_ids.mapped('staff_id')
            record.staff_count = len(staff_ids)

    @api.constrains('course_name')
    def _check_course_name_unique(self):
        for record in self:
            if record.course_name:
                existing = self.search([
                    ('id', '!=', record.id),
                    ('course_name', '=', record.course_name)
                ])
                if existing:
                    raise ValidationError(
                        f"Course name '{record.course_name}' already exists."
                    )

    @api.constrains('course_code')
    def _check_course_code_unique(self):
        for record in self:
            if record.course_code:
                existing = self.search([
                    ('id', '!=', record.id),
                    ('course_code', '=', record.course_code)
                ])
                if existing:
                    raise ValidationError(
                        f"Course code '{record.course_code}' already exists."
                    )

    @api.constrains('duration_years')
    def _check_duration_years(self):
        for record in self:
            if record.duration_years and record.duration_years <= 0:
                raise ValidationError(
                    "Course duration must be greater than 0 years."
                )

    def action_view_subjects(self):
        """Action to view subjects related to this course"""
        return {
            'name': f'Subjects - {self.course_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.subject',
            'view_mode': 'tree,form',
            'domain': [('course_id', '=', self.id)],
            'context': {'default_course_id': self.id},
        }

    def action_view_students(self):
        """Action to view students enrolled in this course"""
        return {
            'name': f'Students - {self.course_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.student',
            'view_mode': 'tree,form',
            'domain': [('course_id', '=', self.id)],
            'context': {'default_course_id': self.id},
        }

    def name_get(self):
        result = []
        for record in self:
            name = record.course_name
            if record.course_code:
                name = f"[{record.course_code}] {name}"
            result.append((record.id, name))
        return result

     # دالة جديدة لفتح المواد الخاصة بالطالب في دورة معينة
    
    
    def action_view_my_subjects_in_course(self):
        self.ensure_one()
        # هذا الإجراء سيفتح عرض شجري للمواد
        # وسيتم تصفيته ليظهر فقط المواد المرتبطة بدورة الطالب
        return {
            'name': _('Subjects in %s') % (self.course_id.course_name),
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.subject',
            'view_mode': 'list,form', # يمكن استخدام kanban أيضًا
            'domain': [('course_id', '=', self.course_id.id)],
            'target': 'current', # يفتح في نفس النافذة
        }

    
