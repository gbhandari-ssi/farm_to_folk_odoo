{
    'name': 'GRN Upload',
    'version': '1.0',
    'summary': 'Require GRN upload with Smart Button for outgoing deliveries.',
    'description': 'Adds a wizard and smart button to upload and view GRNs on Deliveries, mirroring the PO upload workflow.',
    'category': 'Inventory',
    'author': 'Eco Kranti',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}