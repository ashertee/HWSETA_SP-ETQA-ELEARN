{
    'name': 'SETA base',
    'description': '''a place to keep all root menu items, all other root stuf. this helps us avoid circular dependencies''',
    'category': 'SETA',
    'version': '17.0',
    'author': 'HWSETA SYSTEMS DEPT',
    'website': '',
    'depends': [
        'base',
        'mail',
        'password_security',
                ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/application_requirements.xml',
        # 'data/notifications.xml',
        'wizard/confirm_application_wizard.xml',
        'wizard/update_message_wizard.xml',
        'views/seta_base.xml',
	    'views/webclient_templates.xml',
        'templates/template.xml',
        'menu_items.xml',

    ],
'assets': {
    'web.assets_backend': [
        'seta_base/static/src/scss/chatter_hide_activities.scss',
        'seta_base/static/src/scss/chatter_hide_attachment.scss',
        'seta_base/static/src/scss/chatter_hide_follow.scss',
        'seta_base/static/src/scss/chatter_hide_log_note.scss',
        'seta_base/static/src/scss/chatter_hide_email.scss',
        'seta_base/static/src/scss/chatter_hide_fullcomposer.scss',

    ],
},
}
