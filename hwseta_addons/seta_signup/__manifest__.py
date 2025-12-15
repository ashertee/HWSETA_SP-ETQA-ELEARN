{
    'name': 'SETA signup',
    'description': '''user signup stuff.''',
    'category': 'SETA',
    'version': '17.0',
    'author': 'HWSETA SYSTEMS DEPT',
    'website': '',
    'depends': [
        'auth_signup',
        'auth_signup_verify_email',
        'partner_autocomplete',
        'seta_base',
                ],
    # 'data': ['views/res_partner_view.xml', 'security/security_view.xml', 'security/ir.model.access.csv']
    'data': [
        # 'data/data.xml',
        'views/signup_login_templates.xml',
        # 'security/ir.model.access.csv',
             ]
}
