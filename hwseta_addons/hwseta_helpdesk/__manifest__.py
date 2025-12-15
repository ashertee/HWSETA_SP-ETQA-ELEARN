{
    'name': 'HWSETA Helpdesk',
    'description': '''user helpdesk stuff.''',
    'category': 'SETA',
    'version': '17.0',
    'author': 'HWSETA SYSTEMS DEPT',
    'website': '',
    'depends': [
        "base",
        "mail",
        "helpdesk_mgmt",
        'auth_signup_verify_email',
	    'seta_signup',
        'seta_base',
                ],
    'data': [
        'data/helpdesk_data.xml',
        'data/sequence.xml',
        "security/security.xml",
        "security/ir.model.access.csv",
        "security/rules.xml",
        'wizard/helpdesk_ticket_wizard.xml',
        'views/helpdesk_view.xml',
        'views/it_helpdesk_view.xml',
        'views/it_helpdesk_dashboard_views.xml',
        'views/it_helpdesk_ticket_team_views.xml',
        'views/it_helpdesk_ticket_location_views.xml',
        'views/it_helpdesk_ticket_category_views.xml',
        'views/it_helpdesk_ticket_department_views.xml',
        'views/it_helpdesk_ticket_request_type_views.xml',

             ],

}
