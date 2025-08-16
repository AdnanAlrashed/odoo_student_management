from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class StudentProfile(models.TransientModel):
    _name = 'student_management.student.profile'
    _description = 'Student Profile Editor'

    # حقل لتخزين مرجع لسجل الطالب الأصلي
    student_id_ref = fields.Many2one('student_management.student', string='Student Record', readonly=True)

    # الحقول القابلة للتعديل
    phone = fields.Char(string='Phone')
    address = fields.Text(string='Address')
    date_of_birth = fields.Date(string='Date of Birth')
    profile_pic = fields.Binary(string='Profile Picture', attachment=True)

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        """Validate the date of birth."""
        for record in self:
            if record.date_of_birth and record.date_of_birth > date.today():
                raise ValidationError(_("The date of birth cannot be in the future."))

    def action_save_student_profile(self):
        """Saves the modified values back to the original student record."""
        self.ensure_one()
        if self.student_id_ref:
            self.student_id_ref.write({
                'phone': self.phone,
                'address': self.address,
                'date_of_birth': self.date_of_birth,
                'profile_pic': self.profile_pic,
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Your profile has been updated successfully.'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
