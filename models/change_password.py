from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessDenied
from odoo.http import request # <-- استيراد request للحصول على بيئة المستخدم

class ChangePasswordWizard(models.TransientModel ):
    _name = 'student_management.change.password.wizard'
    _description = 'Change Password Wizard'

    current_password = fields.Char(string='Current Password', required=True)
    new_password = fields.Char(string='New Password', required=True)
    confirm_password = fields.Char(string='Confirm New Password', required=True)

    @api.constrains('new_password', 'confirm_password')
    def _check_passwords_match(self):
        """Ensures that the new password and confirmation match."""
        if self.new_password and self.confirm_password and self.new_password != self.confirm_password:
            raise ValidationError(_("The new password and confirmation do not match."))

    def action_change_password(self):
        self.ensure_one()
        user = self.env.user

        try:
            # الطريقة الصحيحة: إنشاء قاموس يحتوي على نوع وكلمة المرور
            credentials = {
                'type': 'password',
                'password': self.current_password,
            }
            user_agent_env = request.httprequest.environ
            user.with_user(user)._check_credentials(credentials, user_agent_env)
            
        except AccessDenied as e:
            raise UserError(_("The current password you entered is incorrect. Please try again.")) from e

        user.password = self.new_password

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Your password has been changed successfully.'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }



