from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

class StaffProfile(models.TransientModel):
    _name = 'student_management.staff.profile'
    _description = 'Staff Profile Editor'

    # حقل لتخزين مرجع لسجل الموظف الأصلي
    staff_id = fields.Many2one('student_management.staff', string='Staff Record', readonly=True)

    # الحقول القابلة للتعديل - نسخة طبق الأصل من الحقول في staff.py
    phone = fields.Char(string='Phone')
    address = fields.Text(string='Address')
    date_of_birth = fields.Date(string='Date of Birth')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender')
    qualification = fields.Char(string='Qualification')
    experience_years = fields.Integer(string='Years of Experience')
    profile_pic = fields.Binary(string='Profile Picture', attachment=True)

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        """Validate the date of birth."""
        for record in self:
            if record.date_of_birth and record.date_of_birth > date.today():
                raise ValidationError(_("The date of birth cannot be in the future."))

    def action_save_profile(self):
        """
        This method saves the data, displays a success notification,
        and then closes the wizard.
        """
        self.ensure_one()
        if self.staff_id:
            # 1. كتابة البيانات إلى سجل الموظف الأصلي
            self.staff_id.write({
                'phone': self.phone,
                'address': self.address,
                'date_of_birth': self.date_of_birth,
                'gender': self.gender,
                'qualification': self.qualification,
                'experience_years': self.experience_years,
                'profile_pic': self.profile_pic,
            })
        
        # 2. إنشاء رسالة التأكيد
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Profile Updated'),
                'message': _('Your personal information has been saved successfully.'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}, # <-- هذا هو الجزء السحري
            }
        }
        
        return notification


