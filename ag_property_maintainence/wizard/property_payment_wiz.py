from odoo import models, fields, api
from odoo.tools.translate import _

class PropertyContPaymentWiz(models.TransientModel):
    _name = 'property.cont.payment.wiz'
    _description = 'Payment Release'
    
    date_from = fields.Date(string="Date From",required=True)
    date_to = fields.Date(string="Date To",required=True)
    deposit = fields.Boolean('Deposit Only')
    
    def payment_release(self):
    	date_from = self.date_from 
    	date_to = self.date_to
    	payment_pool = self.env['property.cont.payment']
    	payment_recs = payment_pool.search([('date','>=',date_from),('date','<=',date_to),('move_id','=',False)])
    	for payment in payment_recs:
            if self.deposit:
                payment.bank_deposit()
            else:
                payment.payment_move()
