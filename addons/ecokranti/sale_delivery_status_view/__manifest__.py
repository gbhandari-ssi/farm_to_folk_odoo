{
    'name': 'Sales: Delivery Status on List View',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Displays the native Delivery Status badge on the Sales Order list view next to Payment Status.',
    'author': 'Smart Sight Innovations',
    'depends': ['sale_stock', 'sale_payment_status'], 
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}