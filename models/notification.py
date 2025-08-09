from odoo import models, fields, api
from odoo.exceptions import ValidationError


class NotificationStudent(models.Model):
    _name = 'student_management.notification_student'
    _description = 'Student Notification'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    student_id = fields.Many2one(
        'student_management.student',
        string='Student',
        required=True,
        ondelete='cascade',
        help='Student receiving the notification'
    )
    message = fields.Text(
        string='Message',
        required=True,
        help='Notification message content'
    )
    title = fields.Char(
        string='Title',
        help='Notification title/subject'
    )
    notification_type = fields.Selection([
        ('general', 'General'),
        ('academic', 'Academic'),
        ('attendance', 'Attendance'),
        ('leave', 'Leave'),
        ('result', 'Result'),
        ('fee', 'Fee'),
        ('event', 'Event'),
        ('urgent', 'Urgent')
    ], string='Type', default='general', required=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='medium')
    
    is_read = fields.Boolean(
        string='Is Read',
        default=False,
        help='Indicates if the notification has been read by the student'
    )
    read_date = fields.Datetime(
        string='Read Date',
        help='Date when the notification was read'
    )
    
    sent_by = fields.Many2one(
        'res.users',
        string='Sent By',
        default=lambda self: self.env.user,
        help='User who sent the notification'
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

    @api.depends('student_id', 'title', 'notification_type', 'is_read')
    def _compute_display_name(self):
        for record in self:
            if record.student_id:
                status = "Read" if record.is_read else "Unread"
                title = record.title or record.message[:50] + "..." if len(record.message) > 50 else record.message
                type_text = dict(record._fields['notification_type'].selection).get(record.notification_type, 'General')
                record.display_name = f"{record.student_id.name} - {title} ({type_text}) [{status}]"
            else:
                record.display_name = "New Notification"

    def action_mark_as_read(self):
        """Mark notification as read"""
        for record in self:
            if not record.is_read:
                record.write({
                    'is_read': True,
                    'read_date': fields.Datetime.now()
                })

    def action_mark_as_unread(self):
        """Mark notification as unread"""
        for record in self:
            record.write({
                'is_read': False,
                'read_date': False
            })

    @api.model
    def send_notification_to_student(self, student_id, message, title=None, notification_type='general', priority='medium'):
        """Send a notification to a specific student"""
        return self.create({
            'student_id': student_id,
            'message': message,
            'title': title,
            'notification_type': notification_type,
            'priority': priority,
            'sent_by': self.env.user.id
        })

    @api.model
    def send_notification_to_course(self, course_id, message, title=None, notification_type='general', priority='medium', session_year_id=None):
        """Send notification to all students in a course"""
        domain = [('course_id', '=', course_id), ('active', '=', True)]
        if session_year_id:
            domain.append(('session_year_id', '=', session_year_id))
        
        students = self.env['student_management.student'].search(domain)
        notifications = []
        
        for student in students:
            notification = self.create({
                'student_id': student.id,
                'message': message,
                'title': title,
                'notification_type': notification_type,
                'priority': priority,
                'sent_by': self.env.user.id
            })
            notifications.append(notification)
        
        return notifications


class NotificationStaff(models.Model):
    _name = 'student_management.notification_staff'
    _description = 'Staff Notification'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    staff_id = fields.Many2one(
        'student_management.staff',
        string='Staff',
        required=True,
        ondelete='cascade',
        help='Staff member receiving the notification'
    )
    message = fields.Text(
        string='Message',
        required=True,
        help='Notification message content'
    )
    title = fields.Char(
        string='Title',
        help='Notification title/subject'
    )
    notification_type = fields.Selection([
        ('general', 'General'),
        ('academic', 'Academic'),
        ('administrative', 'Administrative'),
        ('leave', 'Leave'),
        ('meeting', 'Meeting'),
        ('policy', 'Policy'),
        ('urgent', 'Urgent')
    ], string='Type', default='general', required=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='medium')
    
    is_read = fields.Boolean(
        string='Is Read',
        default=False,
        help='Indicates if the notification has been read by the staff member'
    )
    read_date = fields.Datetime(
        string='Read Date',
        help='Date when the notification was read'
    )
    
    sent_by = fields.Many2one(
        'res.users',
        string='Sent By',
        default=lambda self: self.env.user,
        help='User who sent the notification'
    )
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('staff_id', 'title', 'notification_type', 'is_read')
    def _compute_display_name(self):
        for record in self:
            if record.staff_id:
                status = "Read" if record.is_read else "Unread"
                title = record.title or record.message[:50] + "..." if len(record.message) > 50 else record.message
                type_text = dict(record._fields['notification_type'].selection).get(record.notification_type, 'General')
                record.display_name = f"{record.staff_id.name} - {title} ({type_text}) [{status}]"
            else:
                record.display_name = "New Notification"

    def action_mark_as_read(self):
        """Mark notification as read"""
        for record in self:
            if not record.is_read:
                record.write({
                    'is_read': True,
                    'read_date': fields.Datetime.now()
                })

    def action_mark_as_unread(self):
        """Mark notification as unread"""
        for record in self:
            record.write({
                'is_read': False,
                'read_date': False
            })

    @api.model
    def send_notification_to_staff(self, staff_id, message, title=None, notification_type='general', priority='medium'):
        """Send a notification to a specific staff member"""
        return self.create({
            'staff_id': staff_id,
            'message': message,
            'title': title,
            'notification_type': notification_type,
            'priority': priority,
            'sent_by': self.env.user.id
        })

    @api.model
    def send_notification_to_all_staff(self, message, title=None, notification_type='general', priority='medium'):
        """Send notification to all active staff members"""
        staff_members = self.env['student_management.staff'].search([('active', '=', True)])
        notifications = []
        
        for staff in staff_members:
            notification = self.create({
                'staff_id': staff.id,
                'message': message,
                'title': title,
                'notification_type': notification_type,
                'priority': priority,
                'sent_by': self.env.user.id
            })
            notifications.append(notification)
        
        return notifications

    @api.model
    def get_notification_summary(self, user_type='all', date_from=None, date_to=None):
        """Get notification summary statistics"""
        summary = {
            'student_notifications': {
                'total': 0,
                'read': 0,
                'unread': 0,
                'by_type': {},
                'by_priority': {}
            },
            'staff_notifications': {
                'total': 0,
                'read': 0,
                'unread': 0,
                'by_type': {},
                'by_priority': {}
            }
        }
        
        domain = []
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))
        
        if user_type in ['all', 'student']:
            student_notifications = self.env['student_management.notification_student'].search(domain)
            summary['student_notifications']['total'] = len(student_notifications)
            summary['student_notifications']['read'] = len(student_notifications.filtered('is_read'))
            summary['student_notifications']['unread'] = summary['student_notifications']['total'] - summary['student_notifications']['read']
            
            # By type
            for ntype in ['general', 'academic', 'attendance', 'leave', 'result', 'fee', 'event', 'urgent']:
                count = len(student_notifications.filtered(lambda n: n.notification_type == ntype))
                summary['student_notifications']['by_type'][ntype] = count
            
            # By priority
            for priority in ['low', 'medium', 'high', 'urgent']:
                count = len(student_notifications.filtered(lambda n: n.priority == priority))
                summary['student_notifications']['by_priority'][priority] = count
        
        if user_type in ['all', 'staff']:
            staff_notifications = self.search(domain)
            summary['staff_notifications']['total'] = len(staff_notifications)
            summary['staff_notifications']['read'] = len(staff_notifications.filtered('is_read'))
            summary['staff_notifications']['unread'] = summary['staff_notifications']['total'] - summary['staff_notifications']['read']
            
            # By type
            for ntype in ['general', 'academic', 'administrative', 'leave', 'meeting', 'policy', 'urgent']:
                count = len(staff_notifications.filtered(lambda n: n.notification_type == ntype))
                summary['staff_notifications']['by_type'][ntype] = count
            
            # By priority
            for priority in ['low', 'medium', 'high', 'urgent']:
                count = len(staff_notifications.filtered(lambda n: n.priority == priority))
                summary['staff_notifications']['by_priority'][priority] = count
        
        return summary
