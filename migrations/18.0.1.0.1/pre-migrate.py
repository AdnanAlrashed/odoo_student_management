from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Course = env['student_management.course']
    
    # Update existing records to set name = course_name
    for course in Course.search([]):
        course.write({'name': course.course_name or 'Default Course Name'})