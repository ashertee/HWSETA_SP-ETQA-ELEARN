{
    "name": "SETA person management",
    "description": """person stuff.""",
    "category": "SETA",
    "version": "16.0",
    "author": "HWSETA SYSTEMS DEPT",
    "website": "",
    "depends": [
        "base",
        "mail",
        "seta_base",
        "seta_lookup",
        "seta_compliance",
        # "seta_hide_action_archive_button",
        # "seta_sdf",
    ],
    "data": [
        "data/sequence_data.xml",
        # "data/cron.xml",
        "data/notifications.xml",
        "security/security.xml",
        "security/rules.xml",
        "security/ir.model.access.csv",
"wizard/person_wizard.xml",
        "wizard/person_disable_wizard.xml",
        "wizard/person_re_enable_wizard.xml",
        "views/person.xml",
        "views/users.xml",
        "views/person_transaction.xml",
        "views/person_disable_transaction.xml",
        "views/person_re_enable_transaction.xml",

    ],
    "demo": [
        "demo/person_demo_data.xml"
    ]
}
