{
    'name' : 'HWSETA Persons',
    # 'version' : '1.1',
    'author' : 'SMART ICT System',
    'category' : 'HWSETA departments',
    'description' : """
HWSETA PERSONS module covers.
====================================
    Maintains Fields information regarding Employer, Provider, Employer Department, SDF, Assessors and Moderators. 
    """,
    'website': 'https://www.odoo.com/page/billing',
    'depends' : ['base','hr'],
    'data': [
              'security/ir.model.access.csv',
              'views/person_view.xml',
              'views/web_master.xml',
             ],
    'qweb' : [],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}