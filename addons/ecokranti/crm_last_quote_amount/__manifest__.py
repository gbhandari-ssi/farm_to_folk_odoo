{
    'name': 'CRM: Last Quote Amount',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Calculates and displays the amount of the most recent quotation on the lead.',
    'author': 'Smart Sight Innovations',
    'depends': ['crm', 'sale_crm'], 
    'data': [
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}