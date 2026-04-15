{
    'name': 'Delivery Note Labels',
    'version': '1.0',
    'category': 'Inventory/Delivery',
    'summary': 'Changes Internal Move to Delivery Note for 2-step Pick operations',
    'description': """
        Overrides the default QWeb report title for internal transfers. 
        If the internal transfer is a warehouse Pick stage, it prints 'Delivery Note' 
        for the delivery partner instead of 'Internal Move'.
    """,
    'author': 'Eco Kranti',
    'depends': ['stock'],
    'data': [
        'views/report_picking_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}