from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Attendance(models.Model):
    _name = 'student_management.attendance'
    _description = 'Attendance Session'
    _order = 'attendance_date desc, subject_id'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    student_id = fields.Many2one(
        'student_management.student',
        string='Student',
        required=True,
        ondelete='cascade',
        help='Student attendance record'
    )
    subject_id = fields.Many2one(
        'student_management.subject',
        string='Subject',
        required=True,
        ondelete='restrict',
        help='Subject for which attendance is being taken'
    )
    attendance_date = fields.Date(
        string='Attendance Date',
        required=True,
        default=fields.Date.today,
        help='Date when attendance was taken'
    )
    session_year_id = fields.Many2one(
        'student_management.session_year',
        string='Session Year',
        required=True,
        ondelete='cascade',
        help='Academic session year'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    # Related fields
    course_id = fields.Many2one(
        'student_management.course',
        string='Course',
        related='subject_id.course_id',
        store=True,
        readonly=True
    )
    staff_id = fields.Many2one(
        'student_management.staff',
        string='Staff',
        related='subject_id.staff_id',
        store=True,
        readonly=True
    )
    
    # Statistics
    total_students = fields.Integer(
        string='Total Students',
        compute='_compute_attendance_stats'
    )
    present_students = fields.Integer(
        string='Present Students',
        compute='_compute_attendance_stats'
    )
    absent_students = fields.Integer(
        string='Absent Students',
        compute='_compute_attendance_stats'
    )
    attendance_percentage = fields.Float(
        string='Attendance Percentage',
        compute='_compute_attendance_stats'
    )
    
    # One2many relationships
    attendance_report_ids = fields.One2many(
        'student_management.attendance_report',
        'attendance_id',
        string='Attendance Reports'
    )

    status = fields.Selection(
        [('present', 'Present'),
         ('absent', 'Absent')],
        string='Status',
        required=True,
        default='present'
    )
    remarks = fields.Text(
        string='Remarks',
        help='Additional notes about the attendance'
    )

    @api.depends('subject_id', 'attendance_date')
    def _compute_display_name(self):
        for record in self:
            if record.subject_id and record.attendance_date:
                record.display_name = f"{record.subject_id.subject_name} - {record.attendance_date}"
            else:
                record.display_name = "New Attendance"

    def _compute_attendance_stats(self):
        for record in self:
            reports = record.attendance_report_ids
            record.total_students = len(reports)
            record.present_students = len(reports.filtered('status'))
            record.absent_students = record.total_students - record.present_students
            if record.total_students > 0:
                record.attendance_percentage = (record.present_students / record.total_students) * 100
            else:
                record.attendance_percentage = 0.0

    @api.constrains('subject_id', 'attendance_date', 'session_year_id')
    def _check_unique_attendance(self):
        for record in self:
            existing = self.search([
                ('id', '!=', record.id),
                ('subject_id', '=', record.subject_id.id),
                ('attendance_date', '=', record.attendance_date),
                ('session_year_id', '=', record.session_year_id.id)
            ])
            if existing:
                raise ValidationError(
                    f"Attendance for {record.subject_id.subject_name} on {record.attendance_date} already exists."
                )

    def action_view_reports(self):
        """Action to view attendance reports for this session"""
        return {
            'name': f'Attendance Reports - {self.display_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.attendance_report',
            'view_mode': 'tree,form',
            'domain': [('attendance_id', '=', self.id)],
            'context': {'default_attendance_id': self.id},
        }

    def action_take_attendance(self):
        """Action to take/update attendance for this session"""
        return {
            'name': f'Take Attendance - {self.display_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.attendance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_attendance_id': self.id,
                'default_subject_id': self.subject_id.id,
                'default_attendance_date': self.attendance_date,
                'default_session_year_id': self.session_year_id.id,
            },
        }

    @api.model
    def create_attendance_reports(self, attendance_id):
        """Create attendance reports for all students in the course"""
        attendance = self.browse(attendance_id)
        if not attendance.attendance_report_ids:
            # Get all students in the course for this session year
            students = self.env['student_management.student'].search([
                ('course_id', '=', attendance.course_id.id),
                ('session_year_id', '=', attendance.session_year_id.id),
                ('active', '=', True)
            ])
            
            # Create attendance reports for each student
            for student in students:
                self.env['student_management.attendance_report'].create({
                    'student_id': student.id,
                    'attendance_id': attendance.id,
                    'status': False,  # Default to absent
                })


class AttendanceReport(models.Model):
    _name = 'student_management.attendance_report'
    _description = 'Student Attendance Report'
    _order = 'attendance_id desc, student_id'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    total_attendance = fields.Integer(
        string='Total Attendance',
        compute='_compute_attendance_stats',
        store=True
    )
    attendance_percentage = fields.Float(
        string='Attendance Percentage',
        compute='_compute_attendance_stats',
        store=True
    )
    last_updated = fields.Datetime(
        string='Last Updated',
        default=fields.Datetime.now,
        readonly=True
    )
    
    subject_id = fields.Many2one(
        'student_management.subject',
        string='Subject',
        related='attendance_id.subject_id',
        store=True,
        readonly=False
    )

    student_id = fields.Many2one(
        'student_management.student',
        string='Student',
        required=True,
        ondelete='cascade',
        help='Student for whom attendance is recorded'
    )
    attendance_id = fields.Many2one(
        'student_management.attendance',
        string='Attendance Session',
        required=True,
        ondelete='cascade',
        help='Attendance session this report belongs to'
    )
    status = fields.Boolean(
        string='Present',
        default=False,
        help='True if student was present, False if absent'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    # Related fields for easy access
    subject_id = fields.Many2one(
        'student_management.subject',
        string='Subject',
        related='attendance_id.subject_id',
        store=True,
        readonly=True
    )
    attendance_date = fields.Date(
        string='Date',
        related='attendance_id.attendance_date',
        store=True,
        readonly=True
    )
    course_id = fields.Many2one(
        'student_management.course',
        string='Course',
        related='student_id.course_id',
        store=True,
        readonly=True
    )
    session_year_id = fields.Many2one(
        'student_management.session_year',
        string='Session Year',
        related='attendance_id.session_year_id',
        store=True,
        readonly=True
    )
    
    attendance_ids = fields.One2many(
        'student_management.attendance',
        'attendance_report_ids',
        string='Attendance Records',
        compute='_compute_attendance_records'
    )

    @api.depends('student_id', 'attendance_id', 'status')
    def _compute_display_name(self):
        for record in self:
            if record.student_id and record.attendance_id:
                status_text = "Present" if record.status else "Absent"
                record.display_name = f"{record.student_id.name} - {status_text}"
            else:
                record.display_name = "New Attendance Report"

    @api.depends('student_id', 'attendance_id')
    def _compute_attendance_stats(self):
        """Compute attendance statistics for the student"""
        for report in self:
            domain = [
                ('student_id', '=', report.student_id.id),
                ('subject_id', '=', report.subject_id.id)
            ]
            all_reports = self.search(domain)
            report.total_attendance = len(all_reports)
            present_reports = all_reports.filtered(lambda r: r.status)
            if report.total_attendance > 0:
                report.attendance_percentage = (len(present_reports) / report.total_attendance) * 100
            else:
                report.attendance_percentage = 0.0

    @api.constrains('student_id', 'attendance_id')
    def _check_unique_student_attendance(self):
        for record in self:
            existing = self.search([
                ('id', '!=', record.id),
                ('student_id', '=', record.student_id.id),
                ('attendance_id', '=', record.attendance_id.id)
            ])
            if existing:
                raise ValidationError(
                    f"Attendance report for {record.student_id.name} in this session already exists."
                )

    def toggle_status(self):
        """Toggle attendance status between present and absent"""
        for record in self:
            record.status = not record.status

    @api.model
    def _compute_attendance_records(self):
        """Compute related attendance records for this report"""
        for report in self:
            report.attendance_ids = self.env['student_management.attendance'].search([
                ('attendance_report_ids', 'in', report.id)
            ])

    def get_student_attendance_summary(self, student_id, subject_id=None, date_from=None, date_to=None):
        """Get attendance summary for a student"""
        domain = [('student_id', '=', student_id)]
        
        if subject_id:
            domain.append(('subject_id', '=', subject_id))
        if date_from:
            domain.append(('attendance_date', '>=', date_from))
        if date_to:
            domain.append(('attendance_date', '<=', date_to))
        
        reports = self.search(domain)
        total = len(reports)
        present = len(reports.filtered('status'))
        absent = total - present
        percentage = (present / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'present': present,
            'absent': absent,
            'percentage': percentage
        }



