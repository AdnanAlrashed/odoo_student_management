import odoo

# Initialize Odoo environment
odoo.tools.config.parse_config(['-c', 'odoo.conf'])
odoo.cli.server.report_configuration()
odoo.service.server.start(preload=[], stop=True)
env = odoo.api.Environment(odoo.sql_db.db_connect('isms1'), odoo.SUPERUSER_ID, {})

# Reload the module
module = env['ir.module.module'].search([('name','=','odoo_student_management')])
module.button_immediate_upgrade()

print("Module reloaded successfully!")