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
        for record in self:
            record.attendance_count = len(record.attendance_ids)

    def _compute_result_count(self):
        for record in self:
            record.result_count = len(record.result_ids)

    @api.constrains('subject_name', 'course_id')
    def _check_subject_name_unique_per_course(self):
        for record in self:
            if record.subject_name and record.course_id:
                existing = self.search([
                    ('id', '!=', record.id),
                    ('subject_name', '=', record.subject_name),
                    ('course_id', '=', record.course_id.id)
                ])
                if existing:
                    raise ValidationError(
                        f"Subject '{record.subject_name}' already exists in course '{record.course_id.course_name}'."
                    )

    @api.constrains('subject_code')
    def _check_subject_code_unique(self):
        for record in self:
            if record.subject_code:
                existing = self.search([
                    ('id', '!=', record.id),
                    ('subject_code', '=', record.subject_code)
                ])
                if existing:
                    raise ValidationError(
                        f"Subject code '{record.subject_code}' already exists."
                    )

    @api.constrains('credits')
    def _check_credits(self):
        for record in self:
            if record.credits and record.credits <= 0:
                raise ValidationError(
                    "Subject credits must be greater than 0."
                )

    def action_view_attendance(self):
        """Action to view attendance records for this subject"""
        return {
            'name': f'Attendance - {self.subject_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.attendance',
            'view_mode': 'tree,form',
            'domain': [('subject_id', '=', self.id)],
            'context': {'default_subject_id': self.id},
        }

    def action_view_results(self):
        """Action to view student results for this subject"""
        return {
            'name': f'Results - {self.subject_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.student_result',
            'view_mode': 'tree,form',
            'domain': [('subject_id', '=', self.id)],
            'context': {'default_subject_id': self.id},
        }

    def action_take_attendance(self):
        """Action to take attendance for this subject"""
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
        result = []
        for record in self:
            name = record.subject_name
            if record.subject_code:
                name = f"[{record.subject_code}] {name}"
            if record.course_id:
                name = f"{name} ({record.course_id.course_name})"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced name search to include subject code and course name"""
        args = args or []
        if name:
            domain = [
                '|', '|',
                ('subject_name', operator, name),
                ('subject_code', operator, name),
                ('course_id.course_name', operator, name)
            ]
            subjects = self.search(domain + args, limit=limit)
            return subjects.name_get()
        return super().name_search(name, args, operator, limit)

    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.student_ids)

    def action_activate(self):
        self.ensure_one()
        self.write({'active': True})
        return True

    def action_deactivate(self):
        self.ensure_one()
        self.write({'active': False})
        return True



