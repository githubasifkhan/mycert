# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models

# UnitAnalysis
class cashflow_analysis_master(models.Model):
    _name = "cashflow.analysis.master"
    _description = "cashflow.analysis.master"
    name = fields.Char(string="Number", required=True)
    partner_id = fields.Many2one('res.partner',string="Partner")
    date = fields.Date(string="Date", required=True)
    cont_id = fields.Many2one('property.contract', ondelete='cascade', string="Contract")
    agree_id = fields.Many2one('property.agreement', ondelete='cascade', string="Agreement")
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    amount = fields.Float(string="Amount", required=True)
    cust_bank_id = fields.Many2one('property.bank', string="Issue Bank")
    ref = fields.Char(string="Reference")
    type = fields.Selection([
        ('deposit', 'Deposit'),
        ('payment', 'Payment'),
        ('commission_paid', 'Commission Paid'),
        ('commission_received', 'Commission Received'),
        ('settlement', 'Settlement'),
        ('vat', 'Vat'),('ejari', 'Ejari'),
        ], string='Payment Type',default='payment')
    property_id = fields.Many2one('property.master', string='Building')
    main_property_id = fields.Many2one('main.property', string='Property')
    od_state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancel'),
        ('posted', 'Posted'),
        ('replaced', 'Replaced'),
        ], string='Status',default='draft')
    transaction_type = fields.Selection([
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
        ], string='Type',default='receivable')
        
 
    

