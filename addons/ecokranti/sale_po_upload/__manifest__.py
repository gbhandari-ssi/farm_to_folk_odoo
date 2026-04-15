{
    'name': 'Sale Order PO Upload',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Upload Purchase Order before creating invoices',
    'description': """
        This module requires users to upload a Purchase Order document 
        on a confirmed Sales Order before they are allowed to create an invoice.
    """,
    'depends': ['sale', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}