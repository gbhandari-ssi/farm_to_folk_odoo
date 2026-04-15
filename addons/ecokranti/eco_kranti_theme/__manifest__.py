{
    'name': 'Eco Kranti Theme',
    'version': '1.0',
    'summary': 'Changes Odoo default purple to Eco Kranti Green',
    'description': 'Overrides the core bootstrap and Odoo brand variables to match the Eco Kranti website branding.',
    'category': 'Theme/Backend',
    'author': 'Eco Kranti',
    'depends': ['web'],
    'assets': {
        'web._assets_primary_variables': [
            'eco_kranti_theme/static/src/scss/primary_variables.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}