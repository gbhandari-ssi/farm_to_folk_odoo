{
    'name': 'Payment Proof',
    'version': '1.0',
    'summary': 'Adds an optional payment proof upload to the Register Payment wizard.',
    'description': 'Allows users to upload NEFT screenshots/receipts directly in the payment wizard, attaching them automatically to both the Payment and the Invoice.',
    'category': 'Accounting',
    'author': 'Eco Kranti',
    'depends': ['account'],
    'data': [
        'views/account_payment_register_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}