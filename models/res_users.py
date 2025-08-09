from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    user_type = fields.Selection([
        ('admin', 'HOD/Admin'),
        ('staff', 'Staff'),
        ('student', 'Student')
    ], string='User Type', help='Type of user in the student management system')
    
    # Related fields for easy access
    staff_id = fields.Many2one(
        'student_management.staff',
        string='Staff Profile',
        help='Related staff profile if user is a staff member'
    )
    student_id = fields.Many2one(
        'student_management.student',
        string='Student Profile',
        help='Related student profile if user is a student'
    )
    
    # Computed fields to check user type
    is_student_management_admin = fields.Boolean(
        string='Is Student Management Admin',
        compute='_compute_user_roles'
    )
    is_student_management_staff = fields.Boolean(
        string='Is Student Management Staff',
        compute='_compute_user_roles'
    )
    is_student_management_student = fields.Boolean(
        string='Is Student Management Student',
        compute='_compute_user_roles'
    )

    def _compute_user_roles(self):
        """Compute user roles based on groups"""
        admin_group = self.env.ref('student_management_django_odoo.group_student_management_admin', raise_if_not_found=False)
        staff_group = self.env.ref('student_management_django_odoo.group_student_management_staff', raise_if_not_found=False)
        student_group = self.env.ref('student_management_django_odoo.group_student_management_student', raise_if_not_found=False)
        
        for user in self:
            user.is_student_management_admin = admin_group and admin_group in user.groups_id
            user.is_student_management_staff = staff_group and staff_group in user.groups_id
            user.is_student_management_student = student_group and student_group in user.groups_id

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle user type and profile creation"""
        users = super().create(vals_list)
        
        # Set user type based on groups if not explicitly set
        for user in users:
            if not any(vals.get('user_type') for vals in vals_list if vals.get('id') == user.id):
                user._set_user_type_from_groups()
        
        return users

    def write(self, vals):
        """Override write to handle user type changes"""
        result = super().write(vals)
        
        # Update user type if groups changed
        if 'groups_id' in vals:
            for user in self:
                user._set_user_type_from_groups()
        
        return result

    def _set_user_type_from_groups(self):
        """Set user type based on assigned groups"""
        admin_group = self.env.ref('student_management_django_odoo.group_student_management_admin', raise_if_not_found=False)
        staff_group = self.env.ref('student_management_django_odoo.group_student_management_staff', raise_if_not_found=False)
        student_group = self.env.ref('student_management_django_odoo.group_student_management_student', raise_if_not_found=False)
        
        for user in self:
            if admin_group and admin_group in user.groups_id:
                user.user_type = 'admin'
            elif staff_group and staff_group in user.groups_id:
                user.user_type = 'staff'
            elif student_group and student_group in user.groups_id:
                user.user_type = 'student'

    def action_create_staff_profile(self):
        """Create staff profile for this user"""
        self.ensure_one()
        if self.staff_id:
            raise ValidationError("Staff profile already exists for this user.")
        
        staff = self.env['student_management.staff'].create({
            'user_id': self.id,
            'address': '',
        })
        
        self.staff_id = staff.id
        
        # Add user to staff group
        staff_group = self.env.ref('student_management_django_odoo.group_student_management_staff', raise_if_not_found=False)
        if staff_group:
            self.groups_id = [(4, staff_group.id)]
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.staff',
            'res_id': staff.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_student_profile(self):
        """Create student profile for this user"""
        self.ensure_one()
        if self.student_id:
            raise ValidationError("Student profile already exists for this user.")
        
        # Get default course and session year
        default_course = self.env['student_management.course'].search([], limit=1)
        default_session = self.env['student_management.session_year'].search([('active', '=', True)], limit=1)
        
        if not default_course:
            raise ValidationError("Please create at least one course before creating student profiles.")
        if not default_session:
            raise ValidationError("Please create at least one active session year before creating student profiles.")
        
        student = self.env['student_management.student'].create({
            'user_id': self.id,
            'course_id': default_course.id,
            'session_year_id': default_session.id,
            'address': '',
            'gender': 'male',  # Default value
        })
        
        self.student_id = student.id
        
        # Add user to student group
        student_group = self.env.ref('student_management_django_odoo.group_student_management_student', raise_if_not_found=False)
        if student_group:
            self.groups_id = [(4, student_group.id)]
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.student',
            'res_id': student.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_staff_profile(self):
        """View staff profile"""
        self.ensure_one()
        if not self.staff_id:
            raise ValidationError("No staff profile exists for this user.")
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.staff',
            'res_id': self.staff_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_student_profile(self):
        """View student profile"""
        self.ensure_one()
        if not self.student_id:
            raise ValidationError("No student profile exists for this user.")
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'student_management.student',
            'res_id': self.student_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def create_user_with_profile(self, user_vals, profile_type, profile_vals=None):
        """Create user with associated profile (staff or student)"""
        if profile_vals is None:
            profile_vals = {}
        
        # Create user first
        user = self.create(user_vals)
        
        # Create associated profile
        if profile_type == 'staff':
            profile_vals.update({'user_id': user.id})
            staff = self.env['student_management.staff'].create(profile_vals)
            user.staff_id = staff.id
            
            # Add to staff group
            staff_group = self.env.ref('student_management_django_odoo.group_student_management_staff', raise_if_not_found=False)
            if staff_group:
                user.groups_id = [(4, staff_group.id)]
                
        elif profile_type == 'student':
            # Ensure required fields for student
            if 'course_id' not in profile_vals:
                default_course = self.env['student_management.course'].search([], limit=1)
                if not default_course:
                    raise ValidationError("Please create at least one course before creating students.")
                profile_vals['course_id'] = default_course.id
            
            if 'session_year_id' not in profile_vals:
                default_session = self.env['student_management.session_year'].search([('active', '=', True)], limit=1)
                if not default_session:
                    raise ValidationError("Please create at least one active session year before creating students.")
                profile_vals['session_year_id'] = default_session.id
            
            profile_vals.update({'user_id': user.id})
            student = self.env['student_management.student'].create(profile_vals)
            user.student_id = student.id
            
            # Add to student group
            student_group = self.env.ref('student_management_django_odoo.group_student_management_student', raise_if_not_found=False)
            if student_group:
                user.groups_id = [(4, student_group.id)]
        
        return user

    @api.constrains('staff_id', 'student_id')
    def _check_single_profile(self):
        """Ensure user has only one profile type"""
        for user in self:
            if user.staff_id and user.student_id:
                raise ValidationError("User cannot have both staff and student profiles.")

    def unlink(self):
        """Override unlink to handle profile deletion"""
        for user in self:
            # Delete associated profiles
            if user.staff_id:
                user.staff_id.unlink()
            if user.student_id:
                user.student_id.unlink()
        
        return super().unlink()



