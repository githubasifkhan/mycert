# -*- coding: utf-8 -*-
#############################################################################
#
#
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Property Maintenance',
    'category': 'Maintainence',
    'summary': "Property Maintenance",
    'author':'APPSGATE FZC LLC',
    'depends': ['mail','hr','stock','ag_property_maintainence'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/maintainence.xml',
        'views/maintain_menu.xml',
        'data/pro_data.xml'

    ],
    'demo': [
    ],
    'assets': {
        'web._assets_primary_variables': [
            # 'account/static/src/scss/variables.scss',
        ],
        'web.assets_backend': [
            'ag_maintainence/static/src/css/class.css',
        ],
        'web.assets_frontend': [
            # 'account/static/src/js/account_portal_sidebar.js',
        ],
        'web.assets_tests': [
            # 'account/static/tests/tours/**/*',
        ],
        'web.qunit_suite_tests': [
            # ('after', 'web/static/tests/legacy/views/kanban_tests.js', 'account/static/tests/account_payment_field_tests.js'),
            # ('after', 'web/static/tests/legacy/views/kanban_tests.js', 'account/static/tests/section_and_note_tests.js'),
        ],
        'web.assets_qweb': [
            # 'account/static/src/xml/**/*',
        ],
    },
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'auto_install': False,
}
