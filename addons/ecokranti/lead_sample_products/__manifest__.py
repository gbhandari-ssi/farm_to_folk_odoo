{
    'name': 'CRM Sample Products',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Track physical sample kits provided to CRM Opportunities.',
    'depends': ['crm', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/sample_product_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}