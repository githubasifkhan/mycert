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
    'name': 'Property CRM Management',
    'category': 'crm',
    'summary': "Property CRM Management",
    'author':'Ziad-Monim',
    'depends': ['mail','crm','stock','ag_property_maintainence'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/create_booking.xml',
        'views/pro_crm.xml',
        # 'views/maintain_menu.xml',
        # 'data/pro_data.xml'

    ],
    'demo': [
    ],
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'auto_install': False,
}
