{
    'name': 'Lead Mandatory Phone',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Enforces a mandatory phone number on the CRM Lead/Opportunity UI.',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}