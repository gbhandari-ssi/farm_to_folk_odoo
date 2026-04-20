{
    'name': 'CRM: Sample Products Sync',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Automatically copies Interested Products to the Sample Tab on lead conversion.',
    'author': 'Smart Sight Innovations',
    'depends': ['crm', 'lead_interested_products', 'lead_sample_products'], # Good practice to list your custom dependencies
    'data': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}