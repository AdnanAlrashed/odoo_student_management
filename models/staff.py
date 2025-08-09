from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Staff(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'student_management.staff'
    _description = 'Staff Member'
    _order = 'name'
    _rec_name = 'name'

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
    
    # Staff-specific Information
    employee_id = fields.Char(
        string='Employee ID',
        help='Unique employee identification number'
    )
    address = fields.Text(
        string='Address',
        help='Home address of the staff member',
        store=True
    )
    date_of_birth = fields.Date(
        string='Date of Birth',
        store=True
    )
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', store=True)
    qualification = fields.Char(
        string='Qualification',
        help='Educational qualification of the staff member'
    )
    experience_years = fields.Integer(
        string='Years of Experience',
        default=0
    )
    joining_date = fields.Date(
        string='Joining Date',
        default=fields.Date.today
    )
    profile_pic = fields.Binary(
        string='Profile Picture',
        attachment=True,
        related='user_id.image_1920',
        store=True
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to archive the staff member'
    )
    
    # Related fields for statistics
    subject_count = fields.Integer(
        string='Subjects Teaching',
        compute='_compute_subject_count',
        store=True,
        index=True
    )
    leave_count = fields.Integer(
        string='Leave Requests',
        compute='_compute_leave_count',
        store=True,
        index=True
    )
    feedback_count = fields.Integer(
        string='Feedback Messages',
        compute='_compute_feedback_count',
        store=True,
        index=True
    )
    notification_count = fields.Integer(
        string='Notifications',
        compute='_compute_notification_count',
        store=True,
        index=True
    )
    
    # One2many relationships
    subject_ids = fields.One2many(
        'student_management.subject',
        'staff_id',
        string='Assigned Subjects'
    )
    leave_request_ids = fields.One2many(
        'student_management.leave_report_staff',
        'staff_id',
        string='Leave Requests'
    )
    feedback_ids = fields.One2many(
        'student_management.feedback_staff',
        'staff_id',
        string='Feedback Messages'
    )
    notification_ids = fields.One2many(
        'student_management.notification_staff',
        'staff_id',
        string='Notifications'
    )

    def _compute_subject_count(self):
        for record in self:
            record.subject_count = len(record.subject_ids)

    def _compute_leave_count(self):
        for record in self:
            record.leave_count = len(record.leave_request_ids)

    def _compute_feedback_count(self):
        for record in self:
            record.feedback_count = len(record.feedback_ids)

    def _compute_notification_count(self):
        for record in self:
            record.notification_count = len(record.notification_ids)

    @api.constrains('employee_id')
    def _check_employee_id_unique(self):
        for record in self:
            if record.employee_id:
                existing = self.search([
                    ('id', '!=', record.id),
                    ('employee_id', '=', record.employee_id)
                ])
                if existing:
                    raise ValidationError(
                        f"Employee ID '{record.employee_id}' already exists."
                    )

    @api.constrains('user_id', 'employee_id')
    def _check_unique_records(self):
        for record in self:
            # Skip check for archived records
            if not record.active:
                continue
                
            # Check for duplicate user_id
            if record.user_id:
                existing_user = self.search([
                    ('id', '!=', record.id),
                    ('user_id', '=', record.user_id.id),
                    ('active', '=', True)
                ], limit=1)
                if existing_user:
                    raise ValidationError(
                        "User account is already linked to active staff member: %s (ID: %s)" %
                        (existing_user.name, existing_user.id)
                    )
            
            # Check for duplicate employee_id
            if record.employee_id:
                existing_emp = self.search([
                    ('id', '!=', record.id),
                    ('employee_id', '=', record.employee_id),
                    ('active', '=', True)
                ], limit=1)
                if existing_emp:
                    raise ValidationError(
                        "Employee ID already exists for active staff member: %s (ID: %s)" %
                        (existing_emp.name, existing_emp.id)
                    )

    @api.constrains('experience_years')
    def _check_experience_years(self):
        for record in self:
            if record.experience_years and record.experience_years < 0:
                raise ValidationError(
                    "Years of experience cannot be negative."
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure users are assigned to staff group"""
        staffs = super().create(vals_list)
        staff_group = self.env.ref('student_management_django_odoo.group_student_management_staff', raise_if_not_found=False)
        if staff_group:
            user_ids = [s.user_id.id for s in staffs if s.user_id]
            if user_ids:
                staff_group.users = [(4, uid) for uid in user_ids]
        return staffs

    def write(self, vals):
        """Override write to handle user group changes"""
        result = super().write(vals)
        if 'user_id' in vals:
            for staff in self:
                if staff.user_id:
                    # Add user to staff group
                    staff_group = self.env.ref('student_management_django_odoo.group_student_management_staff', raise_if_not_found=False)
                    if staff_group:
                        staff_group.users = [(4, staff.user_id.id)]
        return result

    def action_view_subjects(self):
        """Action to view subjects assigned to this staff member"""
        return {
            'name': f'Subjects - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.subject',
            'view_mode': 'tree,form',
            'domain': [('staff_id', '=', self.id)],
            'context': {'default_staff_id': self.id},
        }

    def action_view_leaves(self):
        """Action to view leave requests of this staff member"""
        return {
            'name': f'Leave Requests - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.leave_report_staff',
            'view_mode': 'tree,form',
            'domain': [('staff_id', '=', self.id)],
            'context': {'default_staff_id': self.id},
        }

    def action_view_feedback(self):
        """Action to view feedback messages of this staff member"""
        return {
            'name': f'Feedback - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.feedback_staff',
            'view_mode': 'tree,form',
            'domain': [('staff_id', '=', self.id)],
            'context': {'default_staff_id': self.id},
        }

    def action_apply_leave(self):
        """Action to apply for leave"""
        return {
            'name': 'Apply for Leave',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.leave_report_staff',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_staff_id': self.id},
        }

    def action_send_feedback(self):
        """Action to send feedback"""
        return {
            'name': 'Send Feedback',
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.feedback_staff',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_staff_id': self.id},
        }

    def name_get(self):
        result = []
        for record in self:
            name = record.name or 'New Staff'
            if record.employee_id:
                name = f"[{record.employee_id}] {name}"
            result.append((record.id, name))
        return result

    def action_create_user(self):
        """Create a user account for the staff member"""
        self.ensure_one()
        user = self.env['res.users'].create({
            'name': self.name,
            'login': self.email,
            'groups_id': [(4, self.env.ref('student_management.group_staff').id)]
        })
        self.write({'user_id': user.id})
        return True

    def action_activate(self):
        """Activate the staff member"""
        self.write({'active': True})
        return True

    def action_deactivate(self):
        """Deactivate the staff member"""
        self.write({'active': False})
        return True




