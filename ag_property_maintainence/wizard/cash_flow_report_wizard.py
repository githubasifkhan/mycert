from odoo import models, fields, api
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo import exceptions, _
from odoo.exceptions import Warning

class PropertyCashFlowReport(models.TransientModel):
    _name = 'property.cash.flow.report'
    _description = 'property.cash.flow.report'    

    property_id = fields.Many2one('property.master', string="Building")
    main_property_id = fields.Many2one('main.property', string="Property")


    def generate_cashflow(self):
        contract_cheque_obj = self.env['property.cont.payment'].search([])
        agree_cheque_obj = self.env['property.agree.payment'].search([])
        existing_ids = self.env['cashflow.analysis.master'].search([])
        existing_ids.unlink()
        if self.property_id and self.main_property_id:
            cond_ids = []
            agree_ids = []
            contract_ids =  self.env['property.contract'].search([('build_id','=',self.property_id.id),('main_property_id','=',self.main_property_id.id)])
            agreement_ids = self.env['property.agreement'].search([('build_id','=',self.property_id.id),('main_property_id','=',self.main_property_id.id)])
            for con in contract_ids:
                cond_ids.append(con.id)
            for agr in agreement_ids:
                agree_ids.append(agr.id)
                
            contract_cheque_obj = self.env['property.cont.payment'].search([('cont_id','in',cond_ids)])
            agree_cheque_obj = self.env['property.agree.payment'].search([('agree_id','in',agree_ids)])
        elif self.property_id and not self.main_property_id:
            cond_ids = []
            agree_ids = []
            contract_ids =  self.env['property.contract'].search([('build_id','=',self.property_id.id)])
            agreement_ids = self.env['property.agreement'].search([('build_id','=',self.property_id.id)])
            for con in contract_ids:
                cond_ids.append(con.id)
            for agr in agreement_ids:
                agree_ids.append(agr.id)
                
            contract_cheque_obj = self.env['property.cont.payment'].search([('cont_id','in',cond_ids)])
            agree_cheque_obj = self.env['property.agree.payment'].search([('agree_id','in',agree_ids)])
        elif not self.property_id and self.main_property_id:
            cond_ids = []
            agree_ids = []
            contract_ids =  self.env['property.contract'].search([('main_property_id','=',self.main_property_id.id)])
            agreement_ids = self.env['property.agreement'].search([('main_property_id','=',self.main_property_id.id)])
            for con in contract_ids:
                cond_ids.append(con.id)
            for agr in agreement_ids:
                agree_ids.append(agr.id)
                
            contract_cheque_obj = self.env['property.cont.payment'].search([('cont_id','in',cond_ids)])
            agree_cheque_obj = self.env['property.agree.payment'].search([('agree_id','in',agree_ids)])
                
            
        for line in contract_cheque_obj:
            name = line.name
            date = line.date
            cont_id = line.cont_id.id
            agree_id = False
            journal_id = line.journal_id.id
            amount = line.amount
            cust_bank_id = line.cust_bank_id.id
            ref = line.ref
            type = line.type
            property_id = line.property_id.id
            main_property_id = line.property_id.main_property_id.id
            partner_id = line.cont_id and line.cont_id.customer_id and line.cont_id.customer_id.id
            od_state = line.od_state
            transaction_type = 'receivable'
            if od_state not in ('cancel','replaced'):
                self.env['cashflow.analysis.master'].create({'name':name,'date':date,
            'cont_id':cont_id,'agree_id':agree_id,'journal_id':journal_id,
            'amount':amount,'cust_bank_id':cust_bank_id,'ref':ref,'type':type,'property_id':property_id,'main_property_id':main_property_id,'partner_id':partner_id,'od_state':od_state,'transaction_type':transaction_type})
        for a_line in agree_cheque_obj:
            name = a_line.name
            date = a_line.date
            cont_id = False
            agree_id = a_line.agree_id.id
            journal_id = a_line.journal_id.id
            partner_id = a_line.agree_id and a_line.agree_id.supplier_id and a_line.agree_id.supplier_id.id
            amount = a_line.amount
            cust_bank_id = a_line.cust_bank_id.id
            ref = a_line.ref
            type = a_line.type
            property_id = a_line.property_id.id
            main_property_id = a_line.property_id.main_property_id.id
            od_state = a_line.od_state
            transaction_type = 'payable'
            if od_state not in ('cancel','replaced'):
                self.env['cashflow.analysis.master'].create({'name':name,'date':date,
            'cont_id':cont_id,'agree_id':agree_id,'journal_id':journal_id,
            'amount':(-1 * amount),'cust_bank_id':cust_bank_id,'ref':ref,'type':type,'property_id':property_id,'main_property_id':main_property_id,'partner_id':partner_id,'od_state':od_state,'transaction_type':transaction_type})
        action = self.env.ref('ag_property_maintainence.action_od_cashflow_report')
        result = action.read()[0]
        return result  
            
            

            
    
    
    
    
    
    
  
