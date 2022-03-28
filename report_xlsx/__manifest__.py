# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Base report xlsx",
    "summary": "Base module to create xlsx report",
    "author": "ACSONE SA/NV," "Creu Blanca," "Odoo Community Association (OCA)",
    "website": "https://github.com/oca/reporting-engine",
    "category": "Reporting",
    "version": "13.0.1.0.1",
    "license": "AGPL-3",
    "external_dependencies": {"python": ["xlsxwriter", "xlrd"]},
    'assets': {
        'web._assets_primary_variables': [
            # 'account/static/src/scss/variables.scss',
        ],
        'web.assets_backend': [
            'report_xlsx/static/src/js/report/action_manager_report.js',
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
    "depends": ["base", "web"],
    "data": ["views/webclient_templates.xml"],
    "demo": ["demo/report.xml"],
    "installable": True,
}
