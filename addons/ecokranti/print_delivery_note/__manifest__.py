{
    'name': 'Delivery Note',
    'version': '1.0',
    'summary': 'Adds Print Delivery Note button and changes PDF title for Transit locations',
    'description': """
        - Adds a direct "Print Delivery Note" button to the internal picking header.
        - Overrides the standard stock delivery report. If an internal transfer is destined 
          for a Transit location, the PDF title changes from "Internal Move" to "Delivery Note".
    """,
    'category': 'Inventory/Delivery',
    'depends': ['stock'],
    'data': [
        'reports/delivery_report_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}