import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError, UserError
_logger = logging.getLogger(__name__)

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
            if not record.active:
                continue
                
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
        staff_group = self.env.ref('odoo_student_management.group_student_management_staff', raise_if_not_found=False)
        
        if self.env.context.get('staff_profile_editing'):
            existing = self.search([('user_id', '=', self.env.uid)], limit=1)
            if existing:
                return existing
            raise UserError(_("You cannot create a new profile from here. Please contact administrator."))
        
        if staff_group:
            user_ids = [s.user_id.id for s in staffs if s.user_id]
            if user_ids:
                staff_group.users = [(4, uid) for uid in user_ids]
        return staffs

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('staff_profile_editing'):
            staff = self.search([('user_id', '=', self.env.uid)], limit=1)
            if staff:
                for field in fields:
                    if field in self._fields:
                        field_type = self._fields[field]
                        if field_type.type == 'many2one':
                            res[field] = staff[field].id
                        else:
                            res[field] = staff[field]
                res['id'] = staff.id
        return res

    

     # This function is correct and should remain as is
    def action_open_my_profile_wizard(self):
        """
        This function creates a new 'staff.profile' wizard record,
        populates it with current data, and returns an action to open it in a popup.
        """
        self.ensure_one() # تأكد من أننا نعمل على سجل واحد

        # إنشاء سجل جديد في النموذج الوكيل مع القيم الحالية
        wizard = self.env['student_management.staff.profile'].create({
            'staff_id': self.id,
            'phone': self.phone,
            'address': self.address,
            'date_of_birth': self.date_of_birth,
            'gender': self.gender,
            'qualification': self.qualification,
            'experience_years': self.experience_years,
            'profile_pic': self.profile_pic,
        })

        # إرجاع إجراء لفتح هذا السجل في نافذة منبثقة
        return {
            'name': _('Edit My Profile'),
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.staff.profile',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new', # 'new' يفتحها كنافذة منبثقة
        }
    # =================================================================
    #           THIS IS THE FINAL, SECURE WRITE METHOD
    # =================================================================
    def write(self, vals):
        # إذا كان المستخدم الحالي ليس مديرًا، قم بتطبيق قواعد صارمة
        if not self.env.user.has_group('odoo_student_management.group_student_management_admin'):
            # قائمة بيضاء بالحقول المسموح للموظف بتعديلها
            allowed_fields = [
                'phone', 'address', 'date_of_birth', 'gender', 
                'qualification', 'experience_years', 'profile_pic'
            ]
            
            # إنشاء قاموس جديد يحتوي فقط على الحقول المسموح بها من vals
            filtered_vals = {key: vals[key] for key in vals if key in allowed_fields}

            # إذا لم يتبق شيء للتعديل، فلا تفعل شيئًا
            if not filtered_vals:
                return True
            
            # استدعاء الدالة الأصلية بالبيانات المصفاة فقط
            return super(Staff, self).write(filtered_vals)
        
        # إذا كان المستخدم مديرًا، اسمح له بتعديل كل شيء
        return super(Staff, self).write(vals)



    def get_formview_id(self, access_uid=None):
        """ Override to ensure correct record is loaded in form view """
        if self.env.context.get('staff_profile_editing'):
            staff = self.search([('user_id', '=', self.env.uid)], limit=1)
            if staff:
                return staff.id
        return super().get_formview_id(access_uid=access_uid)

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