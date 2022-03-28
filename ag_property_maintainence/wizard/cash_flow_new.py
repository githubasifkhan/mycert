from odoo import models, fields, api
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo import exceptions, _
from odoo.exceptions import Warning

class CashFlowNew(models.TransientModel):
    _name = 'cash.flow.new.wizard'
    _description = 'cash.flow.new.wizard'    

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    account_id = fields.Many2one('account.account',string="Account")
