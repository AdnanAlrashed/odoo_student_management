{
    'name': 'Student Management System',
    'icon': '/odoo_student_management/static/img/academy.png',
    'version': '18.0.1.0.1',
    'category': 'Education',
    'summary': 'Complete Student Management System ',
    'description': """
        Student Management System - Django Port to Odoo 18
        ==================================================
        
        This module is a complete port of a Django-based Student Management System to Odoo 18.
        It includes all the features and functionality of the original Django application:
        
        Features:
        ---------
        * Multi-user system with three user types: HOD (Admin), Staff, and Students
        * Course and Subject Management
        * Student Registration and Profile Management
        * Staff Management and Assignment to Subjects
        * Attendance Management System
        * Leave Request Management for both Students and Staff
        * Feedback System
        * Notification System
        * Student Results and Grading System
        * Session Year Management
        * Comprehensive Reporting
        
        User Roles:
        -----------
        * HOD/Admin: Full system access, user management, course/subject management
        * Staff: Subject teaching, attendance taking, student result entry, leave requests
        * Students: View attendance, apply for leave, provide feedback, view results
        
        This module maintains the same data structure and business logic as the original
        Django application while leveraging Odoo's powerful framework features.
    """,
    'author': 'Adnan Alrashed',
    'website': 'https://ittech-ye.net',
    'depends': ['base', 'web', 'mail', 'documents', 'website'],
    'data': [
        # Security
        'security/groups.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/session_year_data.xml',
        'data/course_data.xml',
        
        
        # Views
        'views/session_year_views.xml',
        'views/odoo_course_views.xml',
        'views/subject_views.xml',
        'views/staff_views.xml',
        'views/student_views.xml',
        'views/attendance_views.xml',
        'views/leave_views.xml',
        'views/feedback_views.xml',
        'views/notification_views.xml',
        'views/res_users_views.xml',
        'views/student_result_views.xml',
        'views/change_password_views.xml',
        'views/staff_profile_views.xml',
        'views/profile/student_profile_views.xml',
        'views/menu.xml',
        'views/menu_actions.xml',

         # =======================================================
        #           ADD THE NEW TEMPLATE FILES HERE
        # =======================================================
        'templates/menus.xml',
        'templates/layout.xml',
        'templates/admin_templates.xml',
        'templates/staff_dashboard_template.xml',
        'templates/edit_staff_template.xml',
        'templates/student_templates.xml',

        'reports/attendance_report.xml'
    ],
    'assets': {
        'web.assets_backend': [
            # 'odoo_student_management/static/src/css/student_management.css',
            # 'odoo_student_management/static/src/js/student_management.js',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license':'LGPL-3',
    'sequence': 10,
}