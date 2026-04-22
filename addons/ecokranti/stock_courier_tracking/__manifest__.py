{
    'name': 'Inventory: Courier Tracking',
    'version': '1.0',
    'category': 'Inventory/Delivery',
    'summary': 'Adds Courier Tracking details directly to the Transfer (Pick/Ship) forms.',
    'author': 'Smart Sight Innovations',
    'depends': ['stock'], 
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}