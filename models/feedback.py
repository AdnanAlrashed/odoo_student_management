from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FeedbackStudent(models.Model):
    _name = 'student_management.feedback_student'
    _description = 'Student Feedback'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    student_id = fields.Many2one(
        'student_management.student',
        string='Student',
        required=True,
        ondelete='cascade',
        help='Student providing feedback'
    )
    feedback = fields.Text(
        string='Feedback Message',
        required=True,
        help='Feedback message from student'
    )
    feedback_reply = fields.Text(
        string='Admin Reply',
        help='Reply from administrator to the feedback'
    )
    is_replied = fields.Boolean(
        string='Is Replied',
        default=False,
        help='Indicates if feedback has been replied to'
    )
    replied_by = fields.Many2one(
        'res.users',
        string='Replied By',
        help='Administrator who replied to the feedback'
    )
    reply_date = fields.Datetime(
        string='Reply Date',
        help='Date when the feedback was replied to'
    )
    
    # Priority and Category
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='medium')
    
    category = fields.Selection([
        ('academic', 'Academic'),
        ('administrative', 'Administrative'),
        ('facilities', 'Facilities'),
        ('technical', 'Technical'),
        ('other', 'Other')
    ], string='Category', default='other')
    
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

    @api.depends('student_id', 'category', 'is_replied')
    def _compute_display_name(self):
        for record in self:
            if record.student_id:
                status = "Replied" if record.is_replied else "Pending"
                category = dict(record._fields['category'].selection).get(record.category, 'Other')
                record.display_name = f"{record.student_id.name} - {category} ({status})"
            else:
                record.display_name = "New Feedback"

    def action_reply(self):
        """Action to reply to feedback"""
        return {
            'name': 'Reply to Feedback',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.feedback.reply.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_feedback_id': self.id,
                'default_feedback_type': 'student',
                'default_original_message': self.feedback,
            },
        }

    def mark_as_replied(self, reply_message):
        """Mark feedback as replied with the given message"""
        self.write({
            'feedback_reply': reply_message,
            'is_replied': True,
            'replied_by': self.env.user.id,
            'reply_date': fields.Datetime.now()
        })

    def mark_as_pending(self):
        """Mark feedback as pending (remove reply)"""
        self.write({
            'feedback_reply': '',
            'is_replied': False,
            'replied_by': False,
            'reply_date': False
        })


class FeedbackStaff(models.Model):
    _name = 'student_management.feedback_staff'
    _description = 'Staff Feedback'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    staff_id = fields.Many2one(
        'student_management.staff',
        string='Staff',
        required=True,
        ondelete='cascade',
        help='Staff member providing feedback'
    )
    feedback = fields.Text(
        string='Feedback Message',
        required=True,
        help='Feedback message from staff'
    )
    feedback_reply = fields.Text(
        string='Admin Reply',
        help='Reply from administrator to the feedback'
    )
    is_replied = fields.Boolean(
        string='Is Replied',
        default=False,
        help='Indicates if feedback has been replied to'
    )
    replied_by = fields.Many2one(
        'res.users',
        string='Replied By',
        help='Administrator who replied to the feedback'
    )
    reply_date = fields.Datetime(
        string='Reply Date',
        help='Date when the feedback was replied to'
    )
    
    # Priority and Category
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='medium')
    
    category = fields.Selection([
        ('academic', 'Academic'),
        ('administrative', 'Administrative'),
        ('facilities', 'Facilities'),
        ('technical', 'Technical'),
        ('hr', 'Human Resources'),
        ('other', 'Other')
    ], string='Category', default='other')
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('staff_id', 'category', 'is_replied')
    def _compute_display_name(self):
        for record in self:
            if record.staff_id:
                status = "Replied" if record.is_replied else "Pending"
                category = dict(record._fields['category'].selection).get(record.category, 'Other')
                record.display_name = f"{record.staff_id.name} - {category} ({status})"
            else:
                record.display_name = "New Feedback"

    def action_reply(self):
        """Action to reply to feedback"""
        return {
            'name': 'Reply to Feedback',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.feedback.reply.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_feedback_id': self.id,
                'default_feedback_type': 'staff',
                'default_original_message': self.feedback,
            },
        }

    def mark_as_replied(self, reply_message):
        """Mark feedback as replied with the given message"""
        self.write({
            'feedback_reply': reply_message,
            'is_replied': True,
            'replied_by': self.env.user.id,
            'reply_date': fields.Datetime.now()
        })

    def mark_as_pending(self):
        """Mark feedback as pending (remove reply)"""
        self.write({
            'feedback_reply': '',
            'is_replied': False,
            'replied_by': False,
            'reply_date': False
        })

    @api.model
    def get_feedback_summary(self, date_from=None, date_to=None):
        """Get feedback summary statistics"""
        domain = []
        
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))
        
        # Student feedback
        student_feedback = self.env['student_management.feedback_student'].search(domain)
        # Staff feedback
        staff_feedback = self.search(domain)
        
        summary = {
            'student_feedback': {
                'total': len(student_feedback),
                'pending': len(student_feedback.filtered(lambda f: not f.is_replied)),
                'replied': len(student_feedback.filtered('is_replied')),
                'by_category': {}
            },
            'staff_feedback': {
                'total': len(staff_feedback),
                'pending': len(staff_feedback.filtered(lambda f: not f.is_replied)),
                'replied': len(staff_feedback.filtered('is_replied')),
                'by_category': {}
            }
        }
        
        # Category breakdown for student feedback
        for category in ['academic', 'administrative', 'facilities', 'technical', 'other']:
            count = len(student_feedback.filtered(lambda f: f.category == category))
            summary['student_feedback']['by_category'][category] = count
        
        # Category breakdown for staff feedback
        for category in ['academic', 'administrative', 'facilities', 'technical', 'hr', 'other']:
            count = len(staff_feedback.filtered(lambda f: f.category == category))
            summary['staff_feedback']['by_category'][category] = count
        
        return summary
