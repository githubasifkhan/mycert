# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class PropertyConfiguration(models.TransientModel):
	_name = 'property.config.settings'
	_inherit = 'res.config.settings'

	defualt_journal_id = fields.Many2one('account.journal', string='Default Journal', required=True)
	payment_journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True)
	receipt_journal_id = fields.Many2one('account.journal', string='Receipt Journal', required=True)
	revenue_journal_id = fields.Many2one('account.journal', string='Revenue Journal', required=True)
	bounce_journal_id = fields.Many2one('account.journal', string='Bounce Journal', required=True)
	deffered_account_id = fields.Many2one('account.account', string='Deferred Account', required=True, domain=[('deprecated', '=', False)])
	revenue_account_id = fields.Many2one('account.account', string='Revenue Account', required=True, domain=[('deprecated', '=', False)])
	deposit_account_id = fields.Many2one('account.account', string='Deposit Recieved Account', required=True, domain=[('deprecated', '=', False)])
	deposit_pay_account_id = fields.Many2one('account.account', string='Deposit Paid Account', required=True, domain=[('deprecated', '=', False)])
	cheque_account_id= fields.Many2one('account.account', string='Inward Account', required=True, domain=[('deprecated', '=', False)])
	advance_account_id = fields.Many2one('account.account', string='Advance Account', required=True, domain=[('deprecated', '=', False)])
	bounce_account_id = fields.Many2one('account.account', string='Bank Charge A/c', required=True, domain=[('deprecated', '=', False)])
	cancel_account_id = fields.Many2one('account.account', string='Settlemtn Account', required=True, domain=[('deprecated', '=', False)])
	prepaid_account_id = fields.Many2one('account.account', string='Prepaid Rent A/c', required=True, domain=[('deprecated', '=', False)])
	payment_account_id = fields.Many2one('account.account', string='Outward Account', required=True, domain=[('deprecated', '=', False)])
	cost_account_id = fields.Many2one('account.account', string='Cost Account', required=True, domain=[('deprecated', '=', False)])
	comm_recvd_id = fields.Many2one('account.account', string='Comm Received', required=True, domain=[('deprecated', '=', False)])
	comm_paid_id = fields.Many2one('account.account', string='Comm Paid', required=True, domain=[('deprecated', '=', False)])
	payment_user_id = fields.Many2one('res.users', string='Payment Responsible', required=True)
	task_user_id = fields.Many2one('res.users', string='Admin Responsible', required=True)
	issue_user_id = fields.Many2one('res.users', string='Accounts Responsible', required=True)
	admincharges_product_id = fields.Many2one('product.product', string='Admin Charges', required=True)
	
	agreement_journal_id = fields.Many2one('account.journal', string='Agreement Journal', required=True)
	agreement_pay_journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True)
	agreement_receipt_journal_id = fields.Many2one('account.journal', string='Receipt Journal', required=True)
	agreement_costing_journal_id = fields.Many2one('account.journal', string='Costing Journal', required=True)
	settlement_journal_id = fields.Many2one('account.journal', string='Settlement Journal', required=True)
	lease_contract_pro = fields.Many2one('product.product', string='Lease Contract Product', required=True)
	agreement_advance_account_id = fields.Many2one('account.account', string='Advance Account', required=True)
	cheque_replacement = fields.Boolean(string='Cheque Replacement')
	day_wise_revenue = fields.Boolean(string='Day Wise Revenue',default=False)
	vat_journal_id = fields.Many2one('account.journal', string='Vat Journal',required=True)
	ejari_account_id = fields.Many2one('account.account', string='Ejari Account', required=True, domain=[('deprecated', '=', False)])




	@api.model
	def get_values(self):
		res = super(PropertyConfiguration, self).get_values()
		params = self.env['ir.config_parameter'].sudo()
		res.update(
			defualt_journal_id=int(params.get_param('ag_property_maintainence.defualt_journal_id')),

		)

		res.update(
			payment_journal_id=int(params.get_param('ag_property_maintainence.payment_journal_id')),

		)


		res.update(

			receipt_journal_id= int(params.get_param('ag_property_maintainence.receipt_journal_id')),

		)
		res.update(
			revenue_journal_id=int(params.get_param('ag_property_maintainence.revenue_journal_id')),

		)
		res.update(
			bounce_journal_id=int(params.get_param('ag_property_maintainence.bounce_journal_id')),

		)
		res.update(
			deffered_account_id=int(params.get_param('ag_property_maintainence.deffered_account_id')),

		)
		res.update(
			revenue_account_id=int(params.get_param('ag_property_maintainence.revenue_account_id')),

		)
		res.update(
			deposit_pay_account_id=int(params.get_param('ag_property_maintainence.deposit_pay_account_id')),

		)
		res.update(
			cheque_account_id=int(params.get_param('ag_property_maintainence.cheque_account_id')),

		)
		res.update(
			advance_account_id=int(params.get_param('ag_property_maintainence.advance_account_id')),

		)
		res.update(
			deposit_account_id=int(params.get_param('ag_property_maintainence.deposit_account_id')),

		)
		res.update(
			bounce_account_id=int(params.get_param('ag_property_maintainence.bounce_account_id')),

		)
		res.update(
			cancel_account_id=int(params.get_param('ag_property_maintainence.cancel_account_id')),

		)
		res.update(
			prepaid_account_id=int(params.get_param('ag_property_maintainence.prepaid_account_id')),

		)
		res.update(
			payment_account_id=int(params.get_param('ag_property_maintainence.payment_account_id')),

		)
		res.update(
			cost_account_id=int(params.get_param('ag_property_maintainence.cost_account_id')),

		)
		res.update(
			comm_recvd_id=int(params.get_param('ag_property_maintainence.comm_recvd_id')),

		)
		res.update(
			comm_paid_id=int(params.get_param('ag_property_maintainence.comm_paid_id')),

		)

		res.update(
			payment_user_id=int(params.get_param('ag_property_maintainence.payment_user_id')),

		)
		res.update(
			task_user_id=int(params.get_param('ag_property_maintainence.task_user_id')),

		)
		res.update(
			issue_user_id=int(params.get_param('ag_property_maintainence.issue_user_id')),

		)
		res.update(
			admincharges_product_id=int(params.get_param('ag_property_maintainence.admincharges_product_id')),

		)
		res.update(
			agreement_journal_id=int(params.get_param('ag_property_maintainence.agreement_journal_id')),

		)
		res.update(
			agreement_pay_journal_id=int(params.get_param('ag_property_maintainence.agreement_pay_journal_id')),

		)
		res.update(
			agreement_receipt_journal_id=int(params.get_param('ag_property_maintainence.agreement_receipt_journal_id')),

		)
		res.update(
			agreement_costing_journal_id=int(params.get_param('ag_property_maintainence.agreement_costing_journal_id')),

		)
		res.update(
			settlement_journal_id=int(params.get_param('ag_property_maintainence.settlement_journal_id')),

		)
		res.update(
			lease_contract_pro=int(params.get_param('ag_property_maintainence.lease_contract_pro')),

		)
		res.update(
			agreement_advance_account_id=int(params.get_param('ag_property_maintainence.agreement_advance_account_id')),

		)
		res.update(
			cheque_replacement=int(params.get_param('ag_property_maintainence.cheque_replacement')),

		)
		res.update(
			day_wise_revenue=params.get_param('ag_property_maintainence.day_wise_revenue'),

		)
		res.update(
			vat_journal_id=int(params.get_param('ag_property_maintainence.vat_journal_id')),

		)
		res.update(
			ejari_account_id=int(params.get_param('ag_property_maintainence.ejari_account_id')),

		)
		res.update(
			task_user_id=int(params.get_param('ag_property_maintainence.task_user_id')),

		)
		if not self.defualt_journal_id and self.receipt_journal_id:
			raise Warning("Please configure the Journals")

		return res
	#
	def set_values(self):

		super(PropertyConfiguration, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.defualt_journal_id",
														 self.defualt_journal_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.payment_journal_id",
														 self.payment_journal_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.receipt_journal_id",
														 self.receipt_journal_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.revenue_journal_id",
														 self.revenue_journal_id.id)


		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.bounce_journal_id",
														 self.bounce_journal_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.deffered_account_id",
														 self.deffered_account_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.revenue_account_id",
														 self.revenue_account_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.deposit_pay_account_id",
														 self.deposit_pay_account_id.id)

		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.cheque_account_id",
														 self.cheque_account_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.advance_account_id",
														 self.advance_account_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.deposit_account_id",
														 self.deposit_account_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.bounce_account_id",
														 self.bounce_account_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.cancel_account_id",
														 self.cancel_account_id.id)

		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.prepaid_account_id",
														 self.prepaid_account_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.payment_account_id",
														 self.payment_account_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.cost_account_id",
														 self.cost_account_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.comm_recvd_id",
														 self.comm_recvd_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.comm_paid_id",
														 self.comm_paid_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.payment_user_id",
														 self.payment_user_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.task_user_id",
														 self.task_user_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.issue_user_id",
														 self.issue_user_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.admincharges_product_id",
														 self.admincharges_product_id.id)

		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.agreement_journal_id",
														 self.agreement_journal_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.agreement_pay_journal_id",
														 self.agreement_pay_journal_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.agreement_receipt_journal_id",
														 self.agreement_receipt_journal_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.agreement_costing_journal_id",
														 self.agreement_costing_journal_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.settlement_journal_id",
														 self.settlement_journal_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.lease_contract_pro",
														 self.lease_contract_pro.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.agreement_advance_account_id",
														 self.agreement_advance_account_id.id)
		# self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.cheque_replacement",
		# 												 self.cheque_replacement.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.day_wise_revenue",
														 self.day_wise_revenue)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.vat_journal_id",
														 self.vat_journal_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.ejari_account_id",
														 self.ejari_account_id.id)
		self.env['ir.config_parameter'].sudo().set_param("ag_property_maintainence.task_user_id",
														 self.task_user_id.id)

	# 
	#
