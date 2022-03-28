# -*- coding: utf-8 -*-
# Copyright 2020 Openworx
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Property Portal Page',
    'summary': 'Metro Style Website User Portal Page',
    'version': '1.0',
    'category': 'Website',
    'summary': """Give Odoo website portal a Metro style look""",
    'author': "Ziad Monim",
    'website': 'https://www.apps-gate.net',
    'license': 'LGPL-3',
    'depends': [
	'website',
    ],
    'data': [
        'views/assets.xml',
        'views/portal.xml',
    ],
    'images': ['images/image.png'],
    'installable': True,
    'application': False,
}
