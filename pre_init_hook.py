def pre_init_hook(cr):
    """Pre initialization hook to clean up existing data"""
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE module = 'odoo_student_management' 
        AND model = 'ir.actions.act_window'
    """)
    cr.execute("""
        DELETE FROM ir_actions 
        WHERE id IN (
            SELECT res_id FROM ir_model_data 
            WHERE module = 'odoo_student_management' 
            AND model = 'ir.actions.act_window'
        )
    """)