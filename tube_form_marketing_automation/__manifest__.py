{
    'name': 'Tube From Marketing Automation',
    'summary': 'Tube From Marketing Automation',
    'version': '16.0.0.0',
    'author': 'Silent Infotech Pvt. Ltd.',
    'website': 'https://silentinfotech.com',
    'license': 'LGPL-3',
    'depends': ['base','website','crm','contacts','mass_mailing','mail'],
    'data': [
        'data/completed_contact_us_form_template.xml',
        'data/completed_contact_us_form_after_week_template.xml',
        'data/completed_contact_us_email_mike_template.xml',
        'data/followup_1_tef_explained_email_template.xml',
        'data/followup_1_specifying_tube_bender_email_template.xml',
        'data/followup_2_tef_explained_email_template.xml',
        'data/followup_2_specifying_tube_bender_email_template.xml',
        'data/followup_3_tef_explained_email_template.xml',
        'data/completed_contact_us_form_cron.xml',
        'data/completed_mailing_contact_form_cron.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml'
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
