{
    'name': 'CRM Interested Products',
    'version': '1.0',
    'depends': ['crm', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/interested_product_views.xml',
    ],
    'installable': True,
    'application': False,
}