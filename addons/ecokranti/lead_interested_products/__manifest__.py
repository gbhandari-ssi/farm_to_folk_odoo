{
    'name': 'Interested Products Tracking',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Tracks interested products on CRM leads',
    'depends': ['crm', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/interested_product_views.xml',
    ],
    'installable': True,
    'application': False,
}