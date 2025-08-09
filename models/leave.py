from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LeaveReportStudent(models.Model):
    _name = 'student_management.leave_report_student'
    _description = 'Student Leave Request'
    _order = 'leave_date desc, create_date desc'
    _rec_name = 'display_name'

    student_id = fields.Many2one(
        'student_management.student',
        string='Student',
        required=True,
        ondelete='cascade',
        help='Student requesting leave'
    )
    leave_date = fields.Date(
        string='Leave Date',
        required=True,
        help='Date for which leave is requested'
    )
    leave_end_date = fields.Date(
        string='Leave End Date',
        help='End date for multiple day leave (optional)'
    )
    leave_message = fields.Text(
        string='Leave Message',
        required=True,
        help='Reason for leave request'
    )
    leave_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', required=True)
    
    admin_reply = fields.Text(
        string='Admin Reply',
        help='Reply from administrator regarding the leave request'
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        help='Administrator who approved/rejected the request'
    )
    approval_date = fields.Datetime(
        string='Approval Date',
        help='Date when the request was approved/rejected'
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
        related='student_id.course_id',
        store=True,
        readonly=True
    )
    session_year_id = fields.Many2one(
        'student_management.session_year',
        string='Session Year',
        related='student_id.session_year_id',
        store=True,
        readonly=True
    )
    
    # Computed fields
    leave_duration = fields.Integer(
        string='Leave Duration (Days)',
        compute='_compute_leave_duration',
        store=True
    )

    @api.depends('student_id', 'leave_date', 'leave_status')
    def _compute_display_name(self):
        for record in self:
            if record.student_id and record.leave_date:
                status_text = dict(record._fields['leave_status'].selection)[record.leave_status]
                record.display_name = f"{record.student_id.name} - {record.leave_date} ({status_text})"
            else:
                record.display_name = "New Leave Request"

    @api.depends('leave_date', 'leave_end_date')
    def _compute_leave_duration(self):
        for record in self:
            if record.leave_date:
                if record.leave_end_date:
                    delta = record.leave_end_date - record.leave_date
                    record.leave_duration = delta.days + 1
                else:
                    record.leave_duration = 1
            else:
                record.leave_duration = 0

    @api.constrains('leave_date', 'leave_end_date')
    def _check_leave_dates(self):
        for record in self:
            if record.leave_end_date and record.leave_date:
                if record.leave_end_date < record.leave_date:
                    raise ValidationError(
                        "Leave end date cannot be before leave start date."
                    )

    def action_approve(self):
        """Approve the leave request"""
        for record in self:
            record.write({
                'leave_status': 'approved',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now()
            })

    def action_reject(self):
        """Reject the leave request"""
        for record in self:
            record.write({
                'leave_status': 'rejected',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now()
            })

    def action_reset_to_pending(self):
        """Reset the leave request to pending status"""
        for record in self:
            record.write({
                'leave_status': 'pending',
                'approved_by': False,
                'approval_date': False,
                'admin_reply': ''
            })


class LeaveReportStaff(models.Model):
    _name = 'student_management.leave_report_staff'
    _description = 'Staff Leave Request'
    _order = 'leave_date desc, create_date desc'
    _rec_name = 'display_name'

    staff_id = fields.Many2one(
        'student_management.staff',
        string='Staff',
        required=True,
        ondelete='cascade',
        help='Staff member requesting leave'
    )
    leave_date = fields.Date(
        string='Leave Date',
        required=True,
        help='Date for which leave is requested'
    )
    leave_end_date = fields.Date(
        string='Leave End Date',
        help='End date for multiple day leave (optional)'
    )
    leave_message = fields.Text(
        string='Leave Message',
        required=True,
        help='Reason for leave request'
    )
    leave_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', required=True)
    
    admin_reply = fields.Text(
        string='Admin Reply',
        help='Reply from administrator regarding the leave request'
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        help='Administrator who approved/rejected the request'
    )
    approval_date = fields.Datetime(
        string='Approval Date',
        help='Date when the request was approved/rejected'
    )
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    # Computed fields
    leave_duration = fields.Integer(
        string='Leave Duration (Days)',
        compute='_compute_leave_duration',
        store=True
    )

    @api.depends('staff_id', 'leave_date', 'leave_status')
    def _compute_display_name(self):
        for record in self:
            if record.staff_id and record.leave_date:
                status_text = dict(record._fields['leave_status'].selection)[record.leave_status]
                record.display_name = f"{record.staff_id.name} - {record.leave_date} ({status_text})"
            else:
                record.display_name = "New Leave Request"

    @api.depends('leave_date', 'leave_end_date')
    def _compute_leave_duration(self):
        for record in self:
            if record.leave_date:
                if record.leave_end_date:
                    delta = record.leave_end_date - record.leave_date
                    record.leave_duration = delta.days + 1
                else:
                    record.leave_duration = 1
            else:
                record.leave_duration = 0

    @api.constrains('leave_date', 'leave_end_date')
    def _check_leave_dates(self):
        for record in self:
            if record.leave_end_date and record.leave_date:
                if record.leave_end_date < record.leave_date:
                    raise ValidationError(
                        "Leave end date cannot be before leave start date."
                    )

    def action_approve(self):
        """Approve the leave request"""
        for record in self:
            record.write({
                'leave_status': 'approved',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now()
            })

    def action_reject(self):
        """Reject the leave request"""
        for record in self:
            record.write({
                'leave_status': 'rejected',
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now()
            })

    def action_reset_to_pending(self):
        """Reset the leave request to pending status"""
        for record in self:
            record.write({
                'leave_status': 'pending',
                'approved_by': False,
                'approval_date': False,
                'admin_reply': ''
            })

    @api.model
    def get_staff_leave_summary(self, staff_id, date_from=None, date_to=None):
        """Get leave summary for a staff member"""
        domain = [('staff_id', '=', staff_id)]
        
        if date_from:
            domain.append(('leave_date', '>=', date_from))
        if date_to:
            domain.append(('leave_date', '<=', date_to))
        
        leaves = self.search(domain)
        
        summary = {
            'total_requests': len(leaves),
            'pending': len(leaves.filtered(lambda l: l.leave_status == 'pending')),
            'approved': len(leaves.filtered(lambda l: l.leave_status == 'approved')),
            'rejected': len(leaves.filtered(lambda l: l.leave_status == 'rejected')),
            'total_days_requested': sum(leaves.mapped('leave_duration')),
            'approved_days': sum(leaves.filtered(lambda l: l.leave_status == 'approved').mapped('leave_duration'))
        }
        
        return summary
