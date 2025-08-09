from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SessionYear(models.Model):
    _name = 'student_management.session_year'
    _description = 'Academic Session Year'
    _order = 'session_start_year desc'
    _rec_name = 'display_name'
    
    # Override default 'name' field requirement
    name = fields.Char(required=False)
    _inherit = [
        'mail.thread.cc',              # لتتبع التغييرات عبر الشات
        'mail.activity.mixin',         # لدعم الأنشطة المجدولة
        'mail.tracking.duration.mixin',# لتتبع مدة المراحل
        'ir.attachment',               # لربط المرفقات مباشرة بالنموذج
    ]

    session_start_year = fields.Date(
        string='Session Start Year',
        required=True,
        help='Start date of the academic session'
    )
    session_end_year = fields.Date(
        string='Session End Year',
        required=True,
        help='End date of the academic session'
    )
    display_name = fields.Char(
        string='Session Name',
        compute='_compute_display_name',
        store=True
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to archive the session year'
    )
    
    # Related fields for statistics
    student_count = fields.Integer(
        string='Number of Students',
        compute='_compute_student_count'
    )
    course_count = fields.Integer(
        string='Number of Courses',
        compute='_compute_course_count'
    )

    @api.depends('session_start_year', 'session_end_year')
    def _compute_display_name(self):
        for record in self:
            if record.session_start_year and record.session_end_year:
                start_year = record.session_start_year.year
                end_year = record.session_end_year.year
                record.display_name = f"{start_year}-{end_year}"
            else:
                record.display_name = "New Session"

    def _compute_student_count(self):
        for record in self:
            record.student_count = self.env['student_management.student'].search_count([
                ('session_year_id', '=', record.id)
            ])

    # Relationships
    student_ids = fields.One2many(
        'student_management.student',
        'session_year_id',
        string='Students'
    )

    def _compute_course_count(self):
        for record in self:
            # Count unique courses for students in this session
            students = self.env['student_management.student'].search([
                ('session_year_id', '=', record.id)
            ])
            record.course_count = len(students.mapped('course_id'))

    @api.constrains('session_start_year', 'session_end_year')
    def _check_session_dates(self):
        for record in self:
            if record.session_start_year and record.session_end_year:
                if record.session_start_year >= record.session_end_year:
                    raise ValidationError(
                        "Session start year must be before session end year."
                    )

    @api.constrains('session_start_year', 'session_end_year')
    def _check_overlapping_sessions(self):
        for record in self:
            if record.session_start_year and record.session_end_year:
                # Allow same year if explicitly needed
                if record.session_start_year.year == record.session_end_year.year:
                    continue
                    
                overlapping = self.search([
                    ('id', '!=', record.id),
                    '|',
                    '&', ('session_start_year', '<', record.session_end_year),
                         ('session_end_year', '>', record.session_start_year),
                ])
                if overlapping:
                    raise ValidationError(
                        f"Session years cannot overlap with existing session: {overlapping[0].display_name}"
                    )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.display_name))
        return result
