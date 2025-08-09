# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check if user_type column exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='res_users' AND column_name='user_type'
    """)
    if not cr.fetchone():
        # Add the column if it doesn't exist
        cr.execute("""
            ALTER TABLE res_users 
            ADD COLUMN user_type VARCHAR
        """)
        cr.execute("""
            COMMENT ON COLUMN res_users.user_type 
            IS 'Type of user in the student management system'
        """)