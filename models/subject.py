from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Subject(models.Model):
    _name = 'student_management.subject'
    _description = 'Academic Subject'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'subject_name'
    _rec_name = 'subject_name'

    subject_name = fields.Char(
        string='Subject Name',
        required=True,
        help='Name of the academic subject'
    )
    subject_code = fields.Char(
        string='Subject Code',
        help='Unique code for the subject'
    )
    description = fields.Text(
        string='Description',
        help='Detailed description of the subject'
    )
    credits = fields.Integer(
        string='Credits',
        default=3,
        help='Number of credits for this subject'
    )
    course_id = fields.Many2one(
        'student_management.course',
        string='Course',
        required=True,
        ondelete='cascade',
        help='Course to which this subject belongs'
    )
    staff_id = fields.Many2one(
        'student_management.staff',
        string='Assigned Staff',
        required=True,
        ondelete='cascade',
        help='Staff member assigned to teach this subject'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Set to false to archive the subject'
    )

    student_count = fields.Integer(
        string='Student Count',
        compute='_compute_student_count'
    )

    student_ids = fields.Many2many(
        'student_management.student',
        'subject_student_rel',
        'subject_id',
        'student_id',
        string='Students'
    )
    
    # Related fields for statistics
    attendance_count = fields.Integer(
        string='Attendance Record Count',
        compute='_compute_attendance_count'
    )
    result_count = fields.Integer(
        string='Student Results Count',
        compute='_compute_result_count'
    )
    
    # One2many relationships
    attendance_ids = fields.One2many(
        'student_management.attendance',
        'subject_id',
        string='Attendance Records'
    )
    result_ids = fields.One2many(
        'student_management.student_result',
        'subject_id',
        string='Student Results'
    )
    
    attendance_report_ids = fields.One2many(
        'student_management.attendance_report',
        'subject_id',
        string='Attendance Reports'
    )

    def _compute_attendance_count(self):
        """Compute attendance count efficiently"""
        for subject in self:
            subject.attendance_count = len(subject.attendance_ids)

    def _compute_result_count(self):
        """Compute result count efficiently"""
        for subject in self:
            subject.result_count = len(subject.result_ids)

    def _compute_student_count(self):
        """Compute student count efficiently"""
        for subject in self:
            subject.student_count = len(subject.student_ids)

    @api.constrains('subject_name', 'course_id')
    def _check_subject_name_unique_per_course(self):
        """Check subject name uniqueness per course"""
        for subject in self:
            if subject.subject_name and subject.course_id:
                existing = self.search([
                    ('id', '!=', subject.id),
                    ('subject_name', '=', subject.subject_name),
                    ('course_id', '=', subject.course_id.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        f"Subject '{subject.subject_name}' already exists in course '{subject.course_id.course_name}'."
                    )

    @api.constrains('subject_code')
    def _check_subject_code_unique(self):
        """Check subject code uniqueness"""
        for subject in self:
            if subject.subject_code:
                existing = self.search([
                    ('id', '!=', subject.id),
                    ('subject_code', '=', subject.subject_code)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        f"Subject code '{subject.subject_code}' already exists."
                    )

    @api.constrains('credits')
    def _check_credits(self):
        """Validate credits value"""
        for subject in self:
            if subject.credits and subject.credits <= 0:
                raise ValidationError("Subject credits must be greater than 0.")

    def action_view_attendance(self):
        """Action to view attendance records for this subject"""
        self.ensure_one()
        return {
            'name': f'Attendance - {self.subject_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.attendance',
            'view_mode': 'tree,form',
            'domain': [('subject_id', '=', self.id)],
            'context': {
                'default_subject_id': self.id,
                'default_course_id': self.course_id.id,
            },
        }

    def action_view_results(self):
        """Action to view student results for this subject"""
        self.ensure_one()
        return {
            'name': f'Results - {self.subject_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.student_result',
            'view_mode': 'tree,form',
            'domain': [('subject_id', '=', self.id)],
            'context': {
                'default_subject_id': self.id,
                'default_course_id': self.course_id.id,
            },
        }

    def action_take_attendance(self):
        """Action to take attendance for this subject"""
        self.ensure_one()
        return {
            'name': f'Take Attendance - {self.subject_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.attendance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_subject_id': self.id,
                'default_course_id': self.course_id.id,
            },
        }

    def name_get(self):
        """Custom display name with subject code and course"""
        result = []
        for subject in self:
            name_parts = []
            if subject.subject_code:
                name_parts.append(f"[{subject.subject_code}]")
            name_parts.append(subject.subject_name)
            if subject.course_id:
                name_parts.append(f"({subject.course_id.course_name})")
            result.append((subject.id, " ".join(name_parts)))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced name search to include subject code and course name"""
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', 
                     ('subject_name', operator, name),
                     ('subject_code', operator, name),
                     ('course_id.course_name', operator, name)]
            if operator in ('=', 'ilike', '=like', 'like'):
                domain = ['|', '|', 
                         ('subject_name', operator, name),
                         ('subject_code', operator, name),
                         ('course_id.course_name', operator, name)]
        
        subjects = self.search(domain + args, limit=limit)
        return subjects.name_get()

    def action_activate(self):
        """Activate subject"""
        for subject in self:
            subject.write({'active': True})
        return True

    def action_deactivate(self):
        """Deactivate subject"""
        for subject in self:
            subject.write({'active': False})
        return True

    def read(self, fields=None, load='_classic_read'):
        """Optimize read performance for large datasets"""
        if fields and 'student_ids' in fields and len(self) > 50:
            fields = [f for f in fields if f != 'student_ids']
        return super().read(fields=fields, load=load)

    def copy(self, default=None):
        """Override copy method to handle unique constraints"""
        default = default or {}
        if 'subject_code' not in default:
            default['subject_code'] = f"{self.subject_code}_COPY"
        if 'subject_name' not in default:
            default['subject_name'] = f"{self.subject_name} (Copy)"
        return super().copy(default)

