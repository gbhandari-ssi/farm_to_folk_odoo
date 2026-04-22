{
    'name': 'Sales: Payment Status on List View',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Adds a computed payment status badge to the Sales Order list view.',
    'author': 'Smart Sight Innovations',
    'depends': ['sale', 'account'], # We need 'account' because we are checking invoice states
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}