# -*- coding: utf-8 -*-
from . import models
from . import controllers

def post_init_hook(cr, registry):
    """Add user_type column if missing when module is installed"""
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='res_users' AND column_name='user_type'
    """)
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE res_users 
            ADD COLUMN user_type VARCHAR
        """)