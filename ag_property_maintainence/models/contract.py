# -*- coding: utf-8 -*-
import re
import datetime as dt
from datetime import  timedelta, tzinfo, time, date, datetime
from dateutil.relativedelta import relativedelta 
#from monthdelta import monthdelta
import odoo
#from odoo.addons.base_geolocalize.models.res_partner import geo_find, geo_query_address
from odoo import SUPERUSER_ID
from odoo import models, fields, api,_
from odoo import exceptions, _
from odoo.exceptions import Warning
import pytz
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import  float_round,float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT as svrdt
from pprint import pprint
import math
import string
import ast


# Booking From
class PropertyBooking(models.Model):
	_name = 'property.booking'
	_description = "Property Booking"
	_inherit = ['mail.thread','portal.mixin']

	# 
	def unlink(self):
		state = self.state
		if state in ('done','cancel'):
			raise Warning("You can Delete in Draft State Only")
		return super(PropertyBooking,self).unlink()

	@api.model
	def create(self, vals):
		vals['name']  = self.env['ir.sequence'].next_by_code('property.booking') or 'New'
		return super(PropertyBooking,self).create(vals)

	name = fields.Char(string="Booking Ref.", copy=False , readonly=True, index=True, default='New')
	state = fields.Selection([('draft', 'Draft'),('done', 'Booked'),('cancel', 'Canceled'),], string='Status', readonly=True, copy=False, index=True, default='draft')
	date = fields.Date(string="Date", required=True, help="Booking Date")
	book_from  = fields.Date(string="Booking From",  help="From Date")
	book_to = fields.Date(string="Booking To", help="To Date")
	con_type = fields.Many2one('property.con.type',string="Type")
	customer_id = fields.Many2one('res.partner', string="Customer", required=True, help="Customer Name")
	amount = fields.Float(string="Amount", help="Booking Amount")
	move_id = fields.Many2one('account.move',string="Journal", track_visibility='onchange')
	user_id = fields.Many2one('res.users', string='Salesman', index=True, track_visibility='onchange', default=lambda self: self.env.user)
	build_id = fields.Many2one('property.master', required=True, string="Building")
	unit_ids = fields.Many2many('property.unit', 'rel_booking_unit','booking_id','unit_id',string="Units", required=True)
	generate_entries = fields.Boolean(string='Generate Entries')
	note = fields.Text('Terms and Conditions')
	currency_id = fields.Many2one('res.currency',string='Currency',default=lambda self: self.env.company.currency_id.id)

	@api.onchange('unit_ids')
	def get_amont(self):
		for rec in self:
			# if not rec.amount:
			amount = 0.0
			for line in rec.unit_ids:
				amount += line.annual_rent
			rec.amount = amount

	def action_booking_send(self):
		'''
		This function opens a window to compose an email
		'''
		self.ensure_one()
		ir_model_data = self.env['ir.model.data']
		try:
			
			template_id = ir_model_data.get_object_reference('ag_property_maintainence', 'email_template_edi_booking_done')[1]
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False
		ctx = dict(self.env.context or {})
		ctx.update({
		'default_model': 'property.booking',
		'active_model': 'property.booking',
		'active_id': self.ids[0],
		'default_res_id': self.ids[0],
		'default_use_template': bool(template_id),
		'default_template_id': template_id,
		'default_composition_mode': 'comment',
		'default_partner_ids': [(6,0,[self.customer_id.id])],
		'default_subject': "Contract Details",
		'custom_layout': "mail.mail_notification_paynow",
		'force_email': True,
		# 'mark_booking_as_sent': True,
		})

		# In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
		# object. Therefore, we pass the model description in the context, in the language in which
		# the template is rendered.
		lang = self.env.context.get('lang')
		if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
			template = self.env['mail.template'].browse(ctx['default_template_id'])
			if template and template.lang:
				lang = template._render_template(template.lang, ctx['default_model'], ctx['default_res_id'])

		self = self.with_context(lang=lang)
		# if self.state in ['draft', 'sent']:
		# 	ctx['model_description'] = _('Request for Quotation')
		# else:
		ctx['model_description'] = _('Lease Booking')

		return {
		'name': _('Compose Email'),
		'type': 'ir.actions.act_window',
		'view_mode': 'form',
		'res_model': 'mail.compose.message',
		'views': [(compose_form_id, 'form')],
		'view_id': compose_form_id,
		'target': 'new',
		'context': ctx,
		}


	# @api.returns('mail.message', lambda value: value.id)
	# def message_post(self, **kwargs):
	# 	if self.env.context.get('mark_booking_as_sent'):
	# 		self.filtered(lambda o: o.state == 'draft').write({'state': 'sent'})
	# 	return super(PropertyBooking, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

	#
	def done(self):
		self.ensure_one()
		get_param = self.env['ir.config_parameter'].sudo().get_param

		receipt_journal_id = get_param('ag_property_maintainence.receipt_journal_id') or False
		if not receipt_journal_id:
			raise Warning('Please Configure the Settings')
		receipt_journal_id = ast.literal_eval(receipt_journal_id)

		journal_id = receipt_journal_id
		partner_id = self.customer_id and self.customer_id.id or False
		journal_account_id = False
		if journal_id:
			journal = self.env['account.journal'].browse(journal_id)
			journal_account_id = journal.default_debit_account_id.id
		partner_account_id = False
		if partner_id:
			partner = self.env['res.partner'].browse(partner_id)
			partner_account_id = partner.property_account_receivable_id.id
		name = self.name
		amount = self.amount
		date = self.date
		move_vals = {'journal_id':journal_id,'date':date,'ref': name + _(' :: ') + str(self.customer_id.name)}
		move_line = []
		if journal_id and partner_account_id:
			bank_line_vals =  (0,0,{'account_id':journal_account_id,'partner_id':partner_id,'name':name,'credit':0.0,'debit':amount})
			customer_line_vals =  (0,0,{'account_id':partner_account_id,'partner_id':partner_id,'name':name,'credit':amount,'debit':0.0})
			move_line.append(bank_line_vals)
			move_line.append(customer_line_vals)
			move_vals['line_ids'] = move_line
			move_pool = self.env['account.move']
			move = move_pool.create(move_vals)
			move_id = move.id
			move.post()
			self.write({'move_id':move_id,'state': 'done'})
		else:
			raise Warning("Account/Jounral not set !!!!")   

	#
	def cancel(self):
		self.write({'state': 'cancel'})

# PropertyContract
class PropertyContract(models.Model):
	_name = 'property.contract'
	_description = "Property Contract"
	_inherit = ['mail.thread','portal.mixin', 'mail.activity.mixin']
	_order = "con_date desc"


	
	
	#
	def revert_process(self):
		date = self.date_stop
		account_line = self.account_line
		account_detail_line = self.account_detail_line
		for line in account_line:
			revenue = line.revenue
			
			line.deffered_revenue = revenue
	
		for a_line in account_detail_line:
			revenue = a_line.revenue
			
			a_line.deffered_revenue = revenue   
	
	#

	@api.model
	def create(self, vals):
		res = super(PropertyContract, self).create(vals)
		if res:
			res.is_contract = True
		return res

	def od_update_property_on_payment_lines(self):

		contract_ids = self.search([])
		for cont in contract_ids:
			for line in cont.payment_line:
				
				property_id = line.cont_id.build_id and line.cont_id.build_id.id
				line.property_id = property_id
						
	
	#
	def od_update_payment_status(self):
		contract_ids = self.search([])
		for cont in contract_ids:
			for line in cont.payment_line:
				if line.od_state == 'draft' and line.cont_id.state == 'cancel':
					line.od_state = 'cancel'
				if line.move_id:
					line.od_state = 'posted'
					
					
	#
	def od_update_revenue_status(self):
		contract_ids = self.search([])
		for cont in contract_ids:
			for line in cont.account_line:
				if line.od_state == 'draft' and line.cont_id.state == 'cancel':
					line.od_state = 'cancel'
				if line.move_id:
					line.od_state = 'posted'
					
	
	
	#
	def generate_revenue_only(self):
		contract_id = self.id
	
		wiz_obj = self.env['contract.revenue.calculation.wizard'].create({'contract_id':contract_id,'name':'wizard'})
		wiz_obj.generate_contract_revenue()
		self.rent_round_off()
	
	
	
	#
	def get_next_month_date(self,d1,start_count):
		d1 = datetime.strptime(str(d1)[:10], '%Y-%m-%d')
		d1 = d1 + relativedelta(months=start_count)
		return d1
	#
	def merge_samemonthline_revenue(self):
		contract = self
		revenue_lines = contract.account_line
		same_ids = []
		for line in revenue_lines:
			desc = line.desc
			unit_id = line.unit_id and line.unit_id.id
			cont_id = line.cont_id and line.cont_id.id
			same_ids = []
			same_month_lines = self.env['property.cont.account'].search([('unit_id', '=', unit_id),('cont_id','=',cont_id),('desc', '=', desc),('id', 'not in', same_ids)])

			tot_amount = 0

			new_date = False
			desc = ''
			if len(same_month_lines) >1:

				for s_line in same_month_lines:
					new_date = self.get_month_day_range(s_line.date)#[1]
					tot_amount = tot_amount + s_line.revenue
					same_ids.append(s_line)
					desc = ":"+s_line.date
				self.env['property.cont.account'].create({'revenue':tot_amount,'unit_id':unit_id,'cont_id':cont_id,'date':new_date,'desc':desc})
				for ids in same_ids:
					ids.unlink()
					ids.dummy()
				contract.dummy()
	
	
	def get_min_cond(self,date,free):
		start_dt = datetime.strptime(date, "%Y-%m-%d")
		new_date = start_dt + timedelta(days=free)
	 
		return new_date
	def dummy(self):
	 
		return True
	#
	@api.depends('unit_line')
	def _get_no_of_units(self):
		unit_ids = []
		
		if self.unit_line:
			for unit in self.unit_line:
				unit_ids.append(unit.id)	
			
		self.no_of_units = len(unit_ids)
		
	def get_add_month(self,date):
		start_dt = datetime.strptime(date, "%Y-%m-%d")
		start_dt = start_dt + relativedelta(months=+1)
	 
		return start_dt
		
		
	def get_month_day_range(self,date):
		date = datetime.strptime(str(date), "%Y-%m-%d")
		last_day = date + relativedelta(day=1, months=+1, days=-1)
		first_day = date + relativedelta(day=1)
		return str(last_day)[:10]#,str(last_day)[:10]
		
	def get_month_days(self,cal_month_s,cal_month_e):
		from datetime import datetime
		d1 = datetime.strptime(cal_month_s, "%Y-%m-%d")
		d2 = datetime.strptime(cal_month_e, "%Y-%m-%d")
		val = abs((d2 - d1).days)+1
		return val
			
		
		
	def get_no_of_months(self,date1,date2):
		no_of_months =0
		while (date1<date2):
			no_of_months = no_of_months + 1
			date1 = datetime.strptime(date1, "%Y-%m-%d") 
			date1 = str(date1 + relativedelta(months=+1))[:10]
		return no_of_months
			
	def get_con_start_date(self,date1):
		date1 = datetime.strptime(str(date1), "%Y-%m-%d")
		date1 = str(date1 + relativedelta(days=+1))[:10]
		return date1
	def get_con_end_date(self,date1):
		start_dt = datetime.strptime(str(date1), "%Y-%m-%d")
		rent_dt = start_dt + relativedelta(years=1)
		rent_dt = rent_dt + relativedelta(days=-1)
		new_date = rent_dt.strftime("%Y-%m-%d")
		return new_date
		
		

	
	
	#
	def generate_revenue_lines(self):
		total_value = self.total_value
		contract_start_date = self.date_start
		contract_date_stop = self.date_stop
		
		free_unit_mth = 0
		for unit_line in self.unit_line:
			free_unit_mth =  unit_line.free_unit_mth 
		new_start_date = self.get_min_cond(contract_start_date,free_unit_mth)
		
		
		next_date = str(new_start_date)[:10]
		no_of_months = self.get_no_of_months(next_date,contract_date_stop)
		if no_of_months <0:
			no_of_months = 1
		amt_ditributed = float(total_value) / float(no_of_months)

		while next_date < contract_date_stop:
			mo_start_date = self.get_month_day_range(next_date)#[0]
			mo_end_date = self.get_month_day_range(next_date)#[1]
			cal_month_s = mo_start_date
			cal_month_e = mo_end_date
			no_of_days = self.get_month_days(cal_month_s,cal_month_e)
			amt_ditributed = float(float(amt_ditributed) / float(no_of_days)) * float(no_of_days)
			if next_date > mo_start_date:
				cal_month_s = next_date
#            if next_date > cal_month_e:
#                cal_month_e = next_date
			diff_days = self.get_month_days(cal_month_s,cal_month_e)
			amt_ditributed = float(total_value) / float(no_of_months)
			amt_ditributed = float(float(amt_ditributed) / float(no_of_days)) * float(diff_days)
		   
#            if next_date > cal_month_e:
#                cal_month_e = next_date
			mo_start_date = self.get_month_day_range(next_date)#[0]
			mo_end_date = self.get_month_day_range(next_date)#[1]
			
			
			vals = {'revenue':amt_ditributed,
					'name': (datetime.strptime(next_date, "%Y-%m-%d")).strftime("%B"),
					'date':next_date,
					'cont_id':self.id
			}
			self.env['property.cont.account'].create(vals)
			next_date = str(self.get_add_month(next_date))[:10]
	  

	# 
	def unlink(self):
		state = self.state
		if state in ('progres','done','cancel'):
			raise Warning("You can Delete in Draft State Only")

		return super(PropertyContract,self).unlink()
	
		
	#
	def generate_rent_lines(self):
#        self.env['property.agree.rent'].create({'date_from':self.date_start,'date_to':})
		# unit_obj = self.env['payment.cont.unit']
		# self.unit_line.compute_vat()
		
		
		wiz_obj = self.env['contract.rent.generation.wiz'].create({'contract_id':self.id,'name':'wizard'})
		wiz_obj.generate_contract_rent()
		self.write({'rent_done':1})
		return True

	#
	@api.depends('date_start', 'date_stop')
	def get_dates(self):
		for rec in self:
			if not rec.date_start:
				rec.date_start = datetime.today()
			if not rec.date_stop:
				rec.date_stop = datetime.today()
			if rec.date_start and rec.date_stop:
				d0 = datetime.today()
				d1 = 0
				d1 = datetime.strptime(str(rec.date_start), "%Y-%m-%d")
				d2 = datetime.strptime(str(rec.date_stop), "%Y-%m-%d")
				t_days = (d2 - d1).days

				if not rec.progress:
					rec.progress = 0
				if d0 < d1:
					rec.progress = 0
				if d0 > d2:
					rec.progress = 100
				if d0 > d1 and d0 < d2:
					f_days = (d0 - d1).days
					if f_days and t_days > 0:
						rec.progress = (float(f_days) / float(t_days)) * 100.0

	#
	@api.depends('unit_line')
	def _get_unit_state(self):
		res = ''
		if self.unit_line:
			for line in self.unit_line:
				if line.is_avail == 'occup':
					res = 'Unit Not Available'
		self.unit_avail = res

	#
	@api.depends('unit_line')
	def get_total_rent(self):
		val =0
		for line in self.unit_line:
			val += line.unit_rent
		self.con_value = val

	#
	@api.depends('unit_line.vat_amount_total','date_start','date_stop')
	def get_total_value(self):
		self.total_value = sum(line.vat_amount_total for line in self.unit_line)

	# #
	# @api.depends('rent_line.rent','date_start','date_stop')
	# def get_total(self):
	# 	self.total_value = sum(line.rent for line in self.rent_line)


	name = fields.Char(string="Contract Ref.", copy=False , readonly=True, index=True, default='Draft')
	state = fields.Selection([('draft', 'Waiting Approval'),('post','Approved'),('progres', 'In Progress'),('close','Closure'),('done', 'Completed'),('cancel', 'Terminated'),], string='Status', readonly=True, copy=False, index=True, default='draft')
	
	renew_id = fields.Many2one('property.contract', string="Renew")
	vat_value = fields.Float(string="Vat")
	ejari_value = fields.Float(string="Ejari")
	is_contract = fields.Boolean(string="Is a new contract?", default=False)
	contract_value = fields.Float(string="Contract Value")
	management_move_id = fields.Many2one('account.move',string="Management Journal", track_visibility='onchange')
	con_date = fields.Date(string="Date", required=True, help="Contract Date")
	date_start = fields.Date(string="Date Strat", required=True, help="From Date", track_visibility='onchange')
	date_stop = fields.Date(string="Date Stop", required=True, help="To Date", track_visibility='onchange')
	month_count = fields.Integer(string="Months", default=12)
	free_month = fields.Integer(string="Free Month", help="Free Period")
	con_type = fields.Many2one('property.con.type', required=True, string="Type")
	customer_id = fields.Many2one('res.partner', string="Customer", required=True, help="Customer Name")
	build_id = fields.Many2one('property.master', required=True, string="Building")
	main_property_id = fields.Many2one(related='build_id.main_property_id',store=True, string='Property')
	floor_id = fields.Many2one('property.floor', string="Floor")
	unit_avail = fields.Char(string="Available", compute="_get_unit_state" ,default='')
	month_rent = fields.Float(string="Monthly Income",  help="Monthly Rental Income")
	con_value = fields.Float(string="Yearly Rent" , compute="get_total_rent")
	con_free_value = fields.Float(string="Cont Free Rent")
	total_value = fields.Float(string="Contract Value", help="Total Contract Value", compute="get_total_value",store=True)
	pay_count = fields.Integer(string="Installments", help="Number of Payments")
	dep_value = fields.Float(string="Deposit", help="Deposit Amount")
	progress = fields.Integer(string="Progress", required=False, default=0, compute="get_dates")
	user_id = fields.Many2one('res.users', string='Salesman', index=True, track_visibility='onchange', default=lambda self: self.env.user)
	analytic_id =fields.Many2one('account.analytic.account', string="Analytic Account")
	move_id = fields.Many2one('account.move',string="Contract Journal", track_visibility='onchange')
	is_terminate = fields.Boolean(string="Terminate")
	date_terminate = fields.Date(string="Termination Date", help="Date of Termination")
	booking_id = fields.Many2one('property.booking',string="Booking")
	booking_amt = fields.Float(string="Booking Amount")
	comm_perc = fields.Float(string="Commission %", help="Commission charged from Tenant",default=0)
	comm_rcvd = fields.Float(string="Commission", help="Commission charged from Tenant")
	agent_id = fields.Many2one('res.partner',string="Agent")
	agent_perc = fields.Float(string="Agent Commission In %", help="Agent Percentage",default=0)
	comm_paid =  fields.Float(string="Commission Paid", help="Commission Paid to Agent")
	company_id = fields.Many2one('res.company', 'Company',index=True, default=lambda self: self.env['res.company']._company_default_get('flight.network'))
	agreement_l = fields.Html(string="T&C", track_visibility='onchange')
	agreement_r = fields.Html(string="T&C", track_visibility='onchange')
	rent_line = fields.One2many('property.cont.rent','cont_id',string="Rent")
	unit_line = fields.One2many('property.cont.unit','cont_id',string="Units")
	payment_line = fields.One2many('property.cont.payment','cont_id',string="Payment")
	invoices_line = fields.One2many('account.move','cont_id',string="Invoices")
	account_line = fields.One2many('property.cont.account','cont_id',string="Account")
	account_detail_line = fields.One2many('property.cont.account.detail','cont_id',string="Account Detail")
	closure_line  = fields.One2many('property.cont.closure','cont_id',string="Closure")
	settle_line  = fields.One2many('property.cont.settle','cont_id',string="Settle")
	settle_ter_line  = fields.One2many('property.settle','cont_id',string="Termination Settle")
	agree_print = fields.Selection([('both','Both'),('left','Left'),('right','Right')],string="Print Format",default='both')
	attachment_line = fields.One2many('property.cont.attachment','cont_id',string="Attachments")
	parking_slot = fields.Char(string="Parking Slot")
	comm_rec_move_id = fields.Many2one('account.move',string="Comm Rec journal",)
	comm_paid_move_id = fields.Many2one('account.move',string="Comm Paid Journal",)
	renewed = fields.Boolean('Renewed')
	no_of_units = fields.Integer(string="No.of Units", compute="_get_no_of_units")
	closure_generated = fields.Boolean(string="Closure Generated",default=False)
	settlement_entry = fields.Many2one('account.move',string="Settlement Entry")
	deposit_c_d = fields.Many2one('account.move',string="Deosit C/D")
	rent_done = fields.Integer('Rent Done',default=0,copy=False)
	payment_done = fields.Integer('Payment Done',default=0,copy=False)
	currency_id = fields.Many2one('res.currency',string='Currency',default=lambda self: self.env.company.currency_id.id)

	# contract_invoice_count = fields.Integer(string="Contract Invoice Count",compute="_get_contract_invoice_count")
	# contract_invoice_id=fields.Integer(string='Contract Invoice Id')

	_sql_constraints = [('name_uniq', 'unique(booking_id)', ' Contract Generated Against this booking'),]


	def action_contract_send(self):
		'''
		This function opens a window to compose an email
		'''
		self.ensure_one()
		ir_model_data = self.env['ir.model.data']
		try:
			template_id = ir_model_data.get_object_reference('ag_property_maintainence', 'email_template_edi_contract_done')[1]
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False
		ctx = dict(self.env.context or {})
		ctx.update({
		'default_model': 'property.contract',
		'active_model': 'property.contract',
		'active_id': self.ids[0],
		'default_res_id': self.ids[0],
		'default_use_template': bool(template_id),
		'default_template_id': template_id,
		'default_composition_mode': 'comment',
		'default_partner_ids': [(6,0,[self.customer_id.id])],
		'default_subject': "Contract Details",
		'custom_layout': "mail.mail_notification_paynow",
		'force_email': True,
		# 'mark_contract_as_sent': True,
		})

		# In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
		# object. Therefore, we pass the model description in the context, in the language in which
		# the template is rendered.
		lang = self.env.context.get('lang')
		if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
			template = self.env['mail.template'].browse(ctx['default_template_id'])
			if template and template.lang:
				lang = template._render_template(template.lang, ctx['default_model'], ctx['default_res_id'])

		self = self.with_context(lang=lang)
		# if self.state in ['draft', 'sent']:
		# 	ctx['model_description'] = _('Request for Quotation')
		# else:
		ctx['model_description'] = _('Lease Contract')

		return {
		'name': _('Compose Email'),
		'type': 'ir.actions.act_window',
		'view_mode': 'form',
		'res_model': 'mail.compose.message',
		'views': [(compose_form_id, 'form')],
		'view_id': compose_form_id,
		'target': 'new',
		'context': ctx,
		}


	# @api.returns('mail.message', lambda value: value.id)
	# def message_post(self, **kwargs):
	# 	if self.env.context.get('mark_contract_as_sent'):
	# 		self.filtered(lambda o: o.state == 'draft').write({'state': 'sent'})
	# 	return super(PropertyContract, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)


	
	@api.constrains('free_month','con_value','pay_count','dep_value','comm_perc','comm_rcvd','agent_perc','comm_paid')
	def check_negative(self):
		if self.free_month <0:
			raise Warning("Please Enter Value Greater Than Zero !")
		if self.con_value <0:
			raise Warning("Please Enter Value Greater Than Zero !")
		if self.pay_count <0:
			raise Warning("Please Enter Value Greater Than Zero !")
		if self.dep_value <0:
			raise Warning("Please Enter Value Greater Than Zero !")
		if self.comm_perc <0:
			raise Warning("Please Enter Value Greater Than Zero !")
		if self.comm_rcvd <0:
			raise Warning("Please Enter Value Greater Than Zero !")
		if self.agent_perc <0:
			raise Warning("Please Enter Value Greater Than Zero !")
		if self.comm_paid <0:
			raise Warning("Please Enter Value Greater Than Zero !")

	@api.onchange('con_date')
	def date_onchange(self):
		if not self.date_start:
		   self.date_start = self.con_date
		   
		   
		   
	@api.onchange('renew_id')
	def renew_id_onchange(self):
		renewal_contract = self.renew_id
		if renewal_contract:
			customer_id = renewal_contract.customer_id and renewal_contract.customer_id.id
			booking_id = renewal_contract.booking_id and renewal_contract.booking_id.id
			con_type = renewal_contract.con_type and renewal_contract.con_type.id
			build_id = renewal_contract.build_id and renewal_contract.build_id.id
#        	analytic_id = renewal_contract.analytic_id and renewal_contract.analytic_id.id
#            analytic_pool = self.env['account.analytic.account']
#            analytic_val = {'name':name,'partner_id':customer_id,'use_tasks':True,}
#            analytic = analytic_pool.create(analytic_val)
			parking_slot = renewal_contract.parking_slot 
			name = renewal_contract.name
			dep_value = renewal_contract.dep_value
			booking_amt = renewal_contract.booking_amt
			user_id = renewal_contract.user_id and renewal_contract.user_id.id
			progress = renewal_contract.progress
			date = str(datetime.now())[:10]
			start_date = self.get_con_start_date(renewal_contract.date_stop)
			end_date = self.get_con_end_date(start_date)
			self.con_date = date
			self.customer_id = customer_id
			self.booking_id = booking_id
			self.con_type = con_type
			self.build_id = build_id
			self.parking_slot = parking_slot
			self.name = name
			self.dep_value = dep_value
			self.booking_amt = booking_amt
			self.user_id = user_id
#        	self.analytic_id = analytic_id
			self.progress = progress
			self.date_start = start_date
			self.date_stop = end_date
			unit_line = renewal_contract.unit_line
			line_vals = []
			for line in unit_line:

				unit_id = line.unit_id and line.unit_id.id
				agree_id = self.id
				list_rent = line.list_rent
				floor_id = line.floor_id and line.floor_id.id
				duration = line.duration
				is_avail = line.is_avail
				net_area = line.net_area
				unit_sqft = line.unit_sqft
				percent = line.percent
				free_unit_mth = line.free_unit_mth
				year_rent = line.year_rent
				line_disc = line.line_disc
				unit_rent = line.unit_rent
				build_id = self.build_id.id
				dict_vals = (0,0,{'unit_id':unit_id,'list_rent':0,'unit_rent':0,'unit_from':start_date,'unit_to':end_date,
				'floor_id':floor_id,'duration':duration,'is_avail':is_avail,'build_id':build_id,
				'percent':percent,'unit_sqft':unit_sqft,'net_area':net_area,'line_disc':line_disc,
				'year_rent':year_rent,'free_unit_mth':free_unit_mth,'unit_rent':unit_rent})
				line_vals.append(dict_vals)
			self.unit_line = line_vals        		



	@api.onchange('date_start','month_count')
	def date_start_onchange(self):
		if self.date_start and self.month_count >0:
			m_count = self.month_count 
			date_from = datetime.strptime(str(self.date_start), "%Y-%m-%d")
			month_end = date_from + relativedelta(months=m_count)
			rent_end = month_end - relativedelta(days=1)
			self.date_stop = rent_end

	@api.onchange('comm_perc','con_value','agent_perc')
	def comm_agent_onchange(self):
		if self.comm_perc >0 and self.con_value >0:
			self.comm_rcvd = self.con_value * (self.comm_perc/100)
		if self.agent_perc >0 and self.con_value >0:
			self.comm_paid = self.con_value * (self.agent_perc/100)

	# #
	@api.onchange('booking_id')
	def booking_onchange(self):
		self.customer_id = self.booking_id.customer_id.id
		self.booking_amt = self.booking_id.amount
		self.build_id=self.booking_id.build_id
		self.date_start=self.booking_id.book_from
		self.date_stop=self.booking_id.book_to
		self.con_date=self.booking_id.date
		ls=[]
		for line in self.booking_id.unit_ids:
			line_vals = {}
			unit_id =line and line.id
			floor_id =  line.floor_id and line.floor_id.id
			net_area =line.net_area
			avail='avail'
			duration='yr'
			vat_value=self.con_type.vat_id.amount
			dict_vals = (0,0,{'unit_id':unit_id,'unit_rent':0,'unit_from':self.date_start,'unit_to':self.date_stop,
			'floor_id':floor_id,'net_area':net_area,'is_avail':avail,'duration':duration})
			ls.append(dict_vals)
			# line_vals['unit_line']=ls
			self.unit_line=ls
				
		

	# @api.onchange('build_id','floor_id','date_start','date_stop')
	# def cont_unit_onchange(self):
	#     self.unit_line.unlink()

	@api.onchange('con_type')
	def temlate_onchange(self):
		template_l = self.con_type.template_l
		template_r = self.con_type.template_r
		self.agreement_l = template_l
		self.agreement_r = template_r
	
	@api.onchange('comm_perc','agent_perc')
	def commission_onchange(self):
		if self.comm_perc >0 and self.con_value >0:
			self.ccomm_rcvd = self.con_value * (self.comm_perc/100)
		if self.agent_perc >0 and self.con_value >0:
			self.comm_paid = self.con_value * (self.agent_perc/100)

	def py_up_round(self,x):
		y = int(x)
		if x>y:
			y+=1
			return y
		else:return y

	#
	def unit_lines(self):
		if len(self.unit_line) >0:
			self.unit_line.search([('auto_line','=',True)]).unlink()
		if len(self.payment_line) >0:
			self.payment_line.unlink()
		if len(self.invoices_line) >0:
			self.invoices_line.unlink()
		if len(self.account_line) >0:
			self.account_line.unlink()
		date = self.date_start
		con_year_rent = self.con_value
		res = []
		for rntline in self.rent_line:
			if rntline.date_from > date:
				rent = rntline.rent
				for lines in self.unit_line:
					if not lines.auto_line:
						amount = 0
						if rent >0 and con_year_rent >0: 
							amount = (rent / con_year_rent) * lines.year_rent
						res.append((0,0,{
								'unit_id': lines.unit_id,
								'build_id': lines.build_id,
								'floor_id': lines.floor_id,
								'net_area': lines.net_area,
								'unit_sqft': lines.unit_sqft,
								'gross_area': lines.gross_area,
								'unit_from': rntline.date_from,
								'unit_to': rntline.date_to,
								'date_from': lines.date_from,
								'date_to': lines.date_to,
								'is_avail': lines.is_avail,
								'year_rent':amount,
								'unit_rent':amount,
								'auto_line':True,
								}))
		self.unit_line = res

	def get_min_condate(self):
		i =[]
		for line in self.unit_line:
			start_dt = datetime.strptime(line.unit_from, "%Y-%m-%d")
			free = line.free_unit_mth
			rent_dt = start_dt + timedelta(days=free)
			new_date = rent_dt.strftime("%Y-%m-%d")
			i.append(new_date)
		mindate = min(i)
		return mindate

	#
	def year_rent_round_off(self):
		total = self.con_value
		line_total = sum(line.rent for line in self.rent_line)
		if total != line_total:
			max_id = max(line.id for line in self.rent_line)
			line_pool = self.env['property.cont.rent']
			line_obj = line_pool.browse(max_id)
			amount = total - line_total
			rent = line_obj.rent
			line_obj.write({'rent':rent + amount})
		revenue_total = sum(line.revenue for line in self.account_line)
		deffered_revenue_total = sum(line.deffered_revenue for line in self.account_line)
		if total != revenue_total or total != deffered_revenue_total:
			max_id = max(line.id for line in self.account_line)
			line_pool = self.env['property.cont.account']
			line_obj = line_pool.browse(max_id)
			r_amount = total - revenue_total
			dr_amount = total - deffered_revenue_total
			revenue = line_obj.revenue
			deffered_revenue = line_obj.deffered_revenue
			line_obj.write({'revenue':revenue + r_amount,'deffered_revenue':deffered_revenue + dr_amount})
			

	#
	def rent_round_off(self):
		total = sum(line.rent for line in self.rent_line)
		line_total = sum(round(line.revenue,2) for line in self.account_line)
		line_unit_wise_totamt = sum(round(line.revenue,2) for line in self.account_detail_line)
		if total != line_total and self.account_line:
			max_id = max(line.id for line in self.account_line)
			line_pool = self.env['property.cont.account']
			line_obj = line_pool.browse(max_id)
			amount = total - line_total
			revenue = line_obj.revenue
			deffered_revenue = line_obj.deffered_revenue
			line_obj.write({'revenue':revenue + amount,'deffered_revenue':deffered_revenue + amount})
			
			
		if total != line_unit_wise_totamt and self.account_detail_line:
			max_id = max(line.id for line in self.account_detail_line)
			line_pool = self.env['property.cont.account.detail']
			line_obj = line_pool.browse(max_id)
			amount = total - line_unit_wise_totamt
			revenue = line_obj.revenue
			deffered_revenue = line_obj.deffered_revenue
			line_obj.write({'revenue':revenue + amount,'deffered_revenue':deffered_revenue + amount})
			
	#
	def get_min_date(self,ds,free):
		start_dt = datetime.strptime(str(ds), "%Y-%m-%d")
		free = free
		rent_dt = start_dt + timedelta(days=free)
		new_date = rent_dt.strftime("%Y-%m-%d")
		return new_date
			
			
	#
	def get_monthly_rent(self):
		total = self.total_value
	
		min_dt = self.date_start
		unit_line = self.unit_line
		for line1 in unit_line:
			min_dt = self.get_min_date(self.date_start,line1.free_unit_mth)#[0]
		dt_start = datetime.strptime(min_dt, "%Y-%m-%d")
		dt_stop = datetime.strptime(str(self.date_stop), "%Y-%m-%d")
		val = relativedelta(dt_stop, dt_start)
		months = (12*(val.years) +(val.months+1))
			
			
		month_rent = float(total) / float(months)
		for line in self.rent_line:
			line.month_rent = month_rent
			
			
			
			


	# #
	def acc_lines(self):
		get_param = self.env['ir.config_parameter'].sudo().get_param
		if not get_param('ag_property_maintainence.settlement_journal_id'):
			raise UserError(_('Please make sure that you set the lease contract product in the Property Setting Page'))
		if len(self.rent_line) == 0:
			raise Warning("No Rent Line Available")
		if len(self.unit_line) == 0:
			raise Warning("No Unit Line Available")
		if len(self.payment_line) >0:
			wiz = self.env['warning.wiz'].create({'contract': self.id})
			return {

					'name': 'Warning',
					'type': 'ir.actions.act_window',
					'res_model': 'warning.wiz',
					'view_mode': 'form',
					'view_type': 'form',
					'res_id': wiz.id,
					'context':self.id,
					'target': 'new'
				}
		cont_start_date = self.date_start
		if len(self.account_line) >0:
			self.account_line.unlink()
		if len(self.invoices_line) >0:
			self.invoices_line.unlink()
		loop = 0
		for rentline in self.rent_line:
			dt_from = datetime.strptime(str(rentline.date_from) ,"%Y-%m-%d")
			dt_to = datetime.strptime(str(rentline.date_to) ,"%Y-%m-%d")
			
			installment = rentline.instal or 1
			total = rentline.rent
			rent = rentline.month_rent
			vat=rentline.od_vat_rent
			free_month = 0
			deposit = 0
			vat = 0
			ejari = 0
			if loop == 0:
				free_month = self.free_month
				deposit = self.dep_value
				vat = self.vat_value
				ejari = self.ejari_value
			# Rent Start and End Check with Free Period
			rent_start = dt_from
			if free_month >0:
				free_from = rent_start
				rent_start = rent_start + relativedelta(months=free_month)
				free_to = rent_start - relativedelta(days=1)
			rent_stop = dt_to
		 
			#Start date analysis
			first_m_fday = dt_from.replace(day=1)
			first_m_end = dt_from + relativedelta(day=31)
			fm_diff = 0
			if first_m_fday != dt_from:
				fm_diff = ((first_m_end - dt_from).days)+1

			#End date analysis
			last_m_fday = dt_to.replace(day=1)
			last_m_end = dt_to + relativedelta(day=31)
			lm_diff =0
			if last_m_end != dt_to:
				lm_diff = ((dt_to - last_m_fday).days)+1

			# Receipt Line Generation


			self.ensure_one()
			

			receipt_journal_id = get_param('ag_property_maintainence.receipt_journal_id') or False
			if not receipt_journal_id:
				raise Warning('Please Configure the Settings')
			receipt_journal_id = ast.literal_eval(receipt_journal_id)


			val = relativedelta(dt_to, dt_from)
			months = (12*(val.years) +(val.months+1))
			interval = months / installment
			mod_interval = divmod(months,installment)
			install_amt = total / installment
			
			res = []
			invoice = self.env['account.move']
			next_date = rent_start
			start = 1

			# if vat>0:
			# 	vat_journal_id = self.env['ir.values'].get_default('property.config.settings', 'vat_journal_id') or False
			#
			# 	res.append((0,0,{
			# 						'name': '00000',
			# 						'date': next_date,
			# 						'journal_id':receipt_journal_id,
			# 						'deposit':0,
			# 						'amount':vat,
			# 						'type':'vat'
			# 						}))

			
				
			for x in range(0,installment):
				if start == 1 and deposit >0:
					booking = self.booking_amt
					if deposit > booking:
						deposit = deposit - booking
						inst_amt = install_amt
					else:
						deposit = 0
						inst_amt = install_amt - (booking - deposit)
					res.append((0,0,{
								'name': '00000',
								'date': next_date,
								'journal_id':receipt_journal_id,
								'deposit':0,
								'amount':inst_amt,
								'type':'payment'
								}))
					# raise UserError(get_param('ag_property_maintainence.lease_contract_pro'))
					inv = []
					# inv.append()
					vals = {
						'cont_id':self.id,
						'invoice_date':next_date,
						'type':'out_invoice',
						'ref':self.name,
						'partner_id':self.customer_id.id,
						'invoice_line_ids':[(0,0,{
							'product_id':int(get_param('ag_property_maintainence.lease_contract_pro')),
							'quantity':1,
							# 'account_id':get_param('ag_property_maintainence.payment_account_id'),
							'tax_ids':False,
							'price_unit':inst_amt})]}
					inv.append(vals)
					invoice.create(inv)
				else:
					if start > 1:
						next_date = next_date + relativedelta(months=interval)
					res.append((0,0,{
								'name': '00000',
								'date': next_date,
								'journal_id':receipt_journal_id,
								'deposit':0,
								'amount':install_amt,
								'type':'payment',
								}))
					# raise UserError(get_param('ag_property_maintainence.lease_contract_pro'))
					# inv = []
					# inv.append((0,0,{
					# 		'product_id':self.env['product.product'].browse(get_param('ag_property_maintainence.lease_contract_pro')),
					# 		'quantity':1,
					# 		# 'account_id':1,
					# 		'tax_ids':False,
					# 		'price_unit':install_amt}))
					inv = []
					# inv.append()
					# raise UserError(get_param('ag_property_maintainence.lease_contract_pro'))
					vals = {
						'cont_id':self.id,
						'invoice_date':next_date,
						'type':'out_invoice',
						'ref':self.name,
						'partner_id':self.customer_id.id,
						'invoice_line_ids':[(0,0,{
							'product_id':int(get_param('ag_property_maintainence.lease_contract_pro')),
							'quantity':1,
							# 'account_id':get_param('ag_property_maintainence.payment_account_id'),
							'tax_ids':False,
							'price_unit':install_amt})]}
					inv.append(vals)
					invoice.create(inv)
				start += 1
			self.payment_line = res
			
		if deposit:
			vals = {
					'name': '00000',
					'date': cont_start_date,
					'journal_id':receipt_journal_id,
					'amount':deposit,
					'deposit':0,
					'type':'deposit',
					'cont_id':self.id
				}
			self.env['property.cont.payment'].create(vals)

		if vat:
			vals = {
					'name': '00000',
					'date': cont_start_date,
					'journal_id':receipt_journal_id,
					'amount':vat,
					'deposit':0,
					'type':'vat',
					'cont_id':self.id
				}
			self.env['property.cont.payment'].create(vals)

		if ejari:
			vals = {
					'name': '00000',
					'date': cont_start_date,
					'journal_id':receipt_journal_id,
					'amount':ejari,
					'deposit':0,
					'type':'ejari',
					'cont_id':self.id
				}
			self.env['property.cont.payment'].create(vals)


		if self.comm_paid:
			vals = {
					'name': '00000',
					'date': next_date,
					'journal_id':receipt_journal_id,
					'amount':self.comm_paid,
					'deposit':0,
					'type':'commission_paid',
					'cont_id':self.id
				}
			self.env['property.cont.payment'].create(vals)
				
		if self.comm_rcvd:
			vals = {
					'name': '00000',
					'date': next_date,
					'journal_id':receipt_journal_id,
					'amount':self.comm_rcvd,
					'deposit':0,
					'type':'commission_received',
					'cont_id':self.id
				}
			self.env['property.cont.payment'].create(vals)
				
		#Revenue lines Generation
		wiz_obj = self.env['contract.revenue.calculation.wizard'].create({'contract_id':self.id,'name':'wizard'})
		wiz_obj.generate_contract_revenue()
		self.rent_round_off()
		self.write({'payment_done':1})

		
	#
	def approve(self):

		approve_ls=[]
		attachment_ls=[]
		type_obj=self.env['property.attachment.type'].search([('od_approve','=',True)])
		
		if type_obj:
			# for line in type_obj:
			# 	approve_ls.append(line.name)
			# for att in self.attachment_line:
			# 	attachment_ls.append(att.attachment_type_id.name)
			# if set(approve_ls)!=set(attachment_ls):
			if not self.attachment_line:
				raise Warning("Add documents(Attachments)")

		
		if self.unit_avail: #Unit Not Available
			raise Warning("Unit(s) not Available")
		if self.date_start > self.date_stop:
			raise Warning("End Date should not be lesser than Start Date")
		if not self.account_line:#No Revenue Lines
			raise Warning("No Revenue Lines")
		name = self.name
		if self.name == 'Draft':
			name = self.env['ir.sequence'].next_by_code('property.contract') or 'Draft'
			self.name = name
		customer_id = self.customer_id and self.customer_id.id or False
		analytic_pool = self.env['account.analytic.account']
		analytic_val = {'name':name,'partner_id':customer_id,}#'use_tasks':True,
		analytic = analytic_pool.create(analytic_val)
		if self.renew_id:
			self.write({'state':'post','analytic_id':analytic.id})
		else:
			
			self.write({'analytic_id':analytic.id,'state':'post'})
		self.unit_line.write({'date_from':self.date_start,'date_to':self.date_stop,'partner_id':self.customer_id.id})

		self.ensure_one()
		get_param = self.env['ir.config_parameter'].sudo().get_param

		task_user_id = get_param('ag_property_maintainence.task_user_id') or False
		task_user_id = ast.literal_eval(task_user_id)
		print('--task user id--',task_user_id)
		project_id = self.env['project.project'].search([('analytic_account_id','=',analytic.id)],limit=1)
		task_pool = self.env['project.task']
		task_val = {'name':name + _(' - Contract Signing'),'project_id':project_id.id,'user_id':task_user_id,}
		task = task_pool.create(task_val)

	#
	def post(self):
		confirm_ls=[]
		attachment_ls=[]
		type_obj=self.env['property.attachment.type'].search([('od_confirm','=',True)])
		
		if type_obj:
			# for line in type_obj:
			# 	confirm_ls.append(line.name)
			# for att in self.attachment_line:
			# 	attachment_ls.append(att.attachment_type_id.name)
			# if set(confirm_ls)!=set(attachment_ls):
				# raise Warning("Add required documents")
			if not self.attachment_line:
				raise Warning("Add documents(Attachments)")


		cost_center = self.build_id and self.build_id.maintain_cc_id and self.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
		if not cost_center:
			raise Warning("Define costcenter in property")
			
		unit_line = self.unit_line
		for u_line in unit_line:
			unit_id = u_line.unit_id and u_line.unit_id.id
			cont_id = u_line.cont_id and u_line.cont_id.id
			customer_id = u_line.cont_id.customer_id and u_line.cont_id.customer_id.id
			unit_rent = u_line.unit_rent
			date_start = u_line.cont_id.date_start 
			date_stop = u_line.cont_id.date_stop
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
			self.env['unit.rent.line'].create({'unit_id':unit_id,'cont_id':cont_id,'customer_id':customer_id,'date_from':date_start,'date_to':date_stop,'total_amount':unit_rent})
			
		renew_id = self.renew_id
		old_analytic_id = self.renew_id and self.renew_id.analytic_id and self.renew_id.analytic_id.id or False
		old_mov_lines = False
		self.ensure_one()
		get_param = self.env['ir.config_parameter'].sudo().get_param

		defualt_journal_id = get_param('ag_property_maintainence.defualt_journal_id') or 3
		defualt_journal_id = ast.literal_eval(defualt_journal_id)
		print('--default journal---',defualt_journal_id)
		deffered_account_id = get_param('ag_property_maintainence.deffered_account_id') or False
		deffered_account_id = ast.literal_eval(deffered_account_id)
		deposit_account_id = get_param('ag_property_maintainence.deposit_account_id') or False
		deposit_account_id = ast.literal_eval(deposit_account_id)
		#deffered_account_new_id = get_param('ag_property_maintainence.deffered_account_new_id') or False
		#deffered_account_new_id = ast.literal_eval(deffered_account_new_id)
		#deposit_account_new_id = get_param('ag_property_maintainence.deposit_account_new_id') or False
		#deposit_account_new_id = ast.literal_eval(deposit_account_new_id)
		# pdc_account_new_id = get_param('ag_property_maintainence.pdc_account_new_id') or False
		# pdc_account_new_id = ast.literal_eval(pdc_account_new_id)
		vat_account_new = self.con_type.account_id.id

		#ejari_account_new_id = get_param('ag_property_maintainence.ejari_account_new_id') or False
		#ejari_account_new_id = ast.literal_eval(ejari_account_new_id)
		
		if old_analytic_id:
			old_mov_lines = self.env['account.move.line'].search([('analytic_account_id', '=', old_analytic_id),('account_id', '=', deposit_account_id)])
		
		cheque_account_id = get_param('ag_property_maintainence.cheque_account_id') or False
		cheque_account_id = ast.literal_eval(cheque_account_id)
		comm_recvd_id = get_param('ag_property_maintainence.comm_recvd_id') or False
		comm_recvd_id = ast.literal_eval(comm_recvd_id)
		comm_paid_id = get_param('ag_property_maintainence.comm_paid_id') or False
		comm_paid_id = ast.literal_eval(comm_paid_id)
		payment_line = self.payment_line
		analytic_id = self.analytic_id and self.analytic_id.id or False
		journal_id = defualt_journal_id
		partner_id = self.customer_id and self.customer_id.id or False
		agent_payable_acc_id = self.agent_id and self.agent_id.property_account_payable_id and self.agent_id.property_account_payable_id.id
		
		name = self.name
		date = self.con_date
		amount = self.total_value
		deposit = self.dep_value
		total = amount
		vat_value = self.vat_value
		ejari_value = self.ejari_value
		total_new = total + vat_value + ejari_value + deposit
		line_ids = []
		recei_cust_acc_id = self.customer_id.property_account_receivable_id and self.customer_id.property_account_receivable_id.id
		for line in payment_line:
			move_line = []
			move_line_paid = []
			move_line_vat=[]
			if line.type == 'commission_received' and line.id not in line_ids:
				line_ids.append(line.id)     	
				journal_id = line.journal_id and line.journal_id.id			
				move_pool = self.env['account.move']    	
				move_vals = {'journal_id':journal_id,'date':date,'ref': name + _(' :: ') + str(self.customer_id.name)} 				
				if self.is_contract:
					line1 = (0,0,{'account_id':recei_cust_acc_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':line.amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					line2 = (0,0,{'account_id':comm_recvd_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':line.amount,'debit':0.0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})         		
					move_line.append(line1)  
					move_line.append(line2)  
				else:
					line1 = (0,0,{'account_id':recei_cust_acc_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':line.amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})  	
					line2 = (0,0,{'account_id':comm_recvd_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':line.amount,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})         		
					move_line.append(line1)         		
					move_line.append(line2)         		

				move_vals['line_ids'] = move_line         		
				move = move_pool.create(move_vals) 
				move.post()        		
				self.comm_rec_move_id = move.id        		
			if line.type == 'commission_paid' and line.id not in line_ids:
				line_ids.append(line.id)  			
				journal_id = line.journal_id and line.journal_id.id 			
				if not agent_payable_acc_id:
					raise Warning("no agent defined or no account defined for agent")
				move_pool = self.env['account.move']  			
				move_vals_paid = {'journal_id':journal_id,'date':date,'ref': name + _(' :: ') + str(self.agent_id.name)}
				line_paid1 = (0,0,{'account_id':agent_payable_acc_id,'partner_id':self.agent_id and self.agent_id.id,'analytic_account_id':analytic_id,'name':name,'credit':line.amount,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})  			
				line_paid2 = (0,0,{'account_id':comm_paid_id,'partner_id':self.agent_id and self.agent_id.id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':line.amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				move_line_paid.append(line_paid1)
				move_line_paid.append(line_paid2)
				move_vals_paid['line_ids'] = move_line_paid
				move1 = move_pool.create(move_vals_paid)
				move1.post()
				self.comm_paid_move_id = move1.id

		move_line = []
		move_vals = {}
		if deposit >0:
			total = amount+deposit
		date = self.con_date
		move_vals = {'journal_id':journal_id,'date':date,'ref': name + _(' :: ') + str(self.customer_id.name)}
		
		old_lines = []
		if old_mov_lines:
			o_amt = 0
			for l in old_mov_lines:
				o_amt = o_amt + l.credit
			od_debit =  (0,0,{'account_id':deposit_account_id,'partner_id':partner_id,'analytic_account_id':old_analytic_id,'name':name,'credit':0.0,'debit':o_amt,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			od_credit =  (0,0,{'account_id':deposit_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':o_amt,'debit':0.0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})

			old_lines.append(od_credit)
			old_lines.append(od_debit)
			if renew_id:
				j = self.env['account.move'].create({'partner_id':partner_id,'journal_id':journal_id,'date':date,'line_ids':old_lines,'ref':renew_id.analytic_id.name})
				j.post()
				self.deposit_c_d = j.id    	    
		
		if journal_id: #and cheque_account_id and deffered_account_id and deposit_account_id and deffered_account_new_id and deposit_account_new_id and pdc_account_new_id:
			# if self.is_contract:
			# 	#cheque_line_vals = (0,0,{'account_id':pdc_account_new_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':total_new,'maintain_cc_id':cost_center})
			# 	#defferd_line_vals =  (0,0,{'account_id':deffered_account_new_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0.0,'maintain_cc_id':cost_center})
			# 	#deposit_line_vals =  (0,0,{'account_id':deposit_account_new_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':deposit,'debit':0.0,'maintain_cc_id':cost_center})
			# 	vat_line_vals = (0,0,{'account_id':vat_account_new,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':vat_value,'debit':0.0,'maintain_cc_id':cost_center})
			# 	#ejari_line_vals =  (0,0,{'account_id':ejari_account_new_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':ejari_value,'debit':0.0,'maintain_cc_id':cost_center})
			# else:
			cheque_line_vals = (0,0,{'account_id':cheque_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':total,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			defferd_line_vals =  (0,0,{'account_id':deffered_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0.0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			deposit_line_vals =  (0,0,{'account_id':deposit_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':deposit,'debit':0.0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			move_line.append(cheque_line_vals)
			move_line.append(defferd_line_vals)
			# if vat_line_vals:
			# 	move_line.append(vat_line_vals)
			# if ejari_line_vals:
			# 	move_line.append(ejari_line_vals)
			if deposit >0:
				move_line.append(deposit_line_vals)
			move_vals['line_ids'] = move_line
			move_pool = self.env['account.move']
			move = move_pool.create(move_vals)
			move_id = move.id
			
			move.post()
			self.write({'move_id':move_id,'state': 'progres'})
			if renew_id:
				renew_id.renewed = True
				renew_id.state = 'done'
#                self.analytic_id = renew_id.analytic_id.id
			
		else:
			print('---this is approved--one--s')
			raise Warning("Account/Jounral not set !!!!")    

		
	#
	def reset(self):
		self.rent_line.unlink()
		self.payment_line.unlink()
		self.account_line.unlink()
		self.invoices_line.unlink()
		self.write({'state': 'draft','rent_done':0,'payment_done':0})
		
		
		
	def get_month_day_range(self,date):
		date = datetime.strptime(str(date), "%Y-%m-%d")
		last_day = date + relativedelta(day=1, months=+1, days=-1)
		first_day = date + relativedelta(day=1)
		return str(last_day)[:10]#,str(last_day)[:10]

	#
	def closure(self):
		closure_lines = self.env['property.cont.closure'].search([('cont_id','=',self.id)])
		old_lines = self.env['property.settle'].search([('cont_id','=',self.id)])
		
								
		for ol in old_lines:
			ol.unlink()
		
		
		

		
		if self.date_terminate:
			account_lines = self.env['property.cont.account'].search([('cont_id','=',self.id),('date','<=',self.date_terminate),('od_state','=','draft')])
			od_start_date = self.get_month_day_range(self.date_terminate)#[0]
			od_end_date = self.get_month_day_range(self.date_terminate)#[1]
			corresponding_account_lines = self.env['property.cont.account'].search([('cont_id','=',self.id),('date','>=',od_start_date),('od_state','=','draft'),('date','<=',od_end_date)])
			corresponding_account_lines_detail = self.env['property.cont.account.detail'].search([('cont_id','=',self.id),('date','>=',od_start_date),('date','<=',od_end_date)])
			not_considering_lines_detail = self.env['property.cont.account.detail'].search([('cont_id','=',self.id),('date','>',od_end_date)])
			not_considering_lines = self.env['property.cont.account'].search([('cont_id','=',self.id),('date','>',od_end_date),('od_state','=','draft')])
			if not_considering_lines:
				for ncl in not_considering_lines:
				   
					ncl.write({'deffered_revenue':0})
			
			
			if not_considering_lines_detail:
				for ncld in not_considering_lines_detail:
				   
					ncld.write({'deffered_revenue':0})
			
			if corresponding_account_lines_detail:
				for cald in corresponding_account_lines_detail:
					line_date = cald.date
					if self.date_terminate < line_date:
						x_days = self.get_month_days(od_start_date,self.date_terminate)
						x_amt = float(float(cald.revenue) / float(30)) * x_days
						cald.write({'deffered_revenue':x_amt})
					
			for li in account_lines:
				revenue = li.revenue
				li.write({'deffered_revenue':revenue})
			if corresponding_account_lines:
				line_date = corresponding_account_lines.date
				if self.date_terminate < line_date:
					x_days = self.get_month_days(od_start_date,self.date_terminate)
					x_amt = float(float(corresponding_account_lines.revenue) / float(30)) * x_days
					corresponding_account_lines.write({'deffered_revenue':x_amt})
					
					
			final_account_lines = self.env['property.cont.account'].search([('cont_id','=',self.id)])
			total_deffered = 0
			if final_account_lines:
				for fal in final_account_lines:
					total_deffered = total_deffered + fal.deffered_revenue
					
					
			
			if self.dep_value or self.deposit_c_d:
				amount = self.dep_value
				if not amount:
					move_line = self.env['account.move.line'].search([('move_id','=',self.deposit_c_d.id),('debit','>',0)])
					if move_line:
						move_line = move_line[0]
					amount = move_line.debit
				self.env['property.settle'].create({'name':'Security Deposit','amount':amount,'cont_id':self.id})
			bank_cash_type = self.env['account.account.type'].search([('name','=','Bank and Cash')])        
			bank_cash_accounts_obj = self.env['account.account'].search([('user_type_id','=',bank_cash_type[0].id)])
			bank_cash_accounts = []
			bank_cash_amount = 0
			for acc in bank_cash_accounts_obj:
				bank_cash_accounts.append(acc.id)
			entries_related_bankcash_obj = self.env['account.move.line'].search([('partner_id','=',self.customer_id.id),('debit','>',0),('analytic_account_id','=',self.analytic_id and self.analytic_id.id),('account_id','in',bank_cash_accounts)])
			for entri in entries_related_bankcash_obj:
				bank_cash_amount = bank_cash_amount + entri.debit
			self.env['property.settle'].create({'name':'Bank/Cash','amount':bank_cash_amount,'cont_id':self.id})
			self.env['property.settle'].create({'name':'Revenue','amount':total_deffered,'cont_id':self.id})
			
			
					
						
		for closure_line in closure_lines:
			closure_line.unlink()
		analytic_id = self.analytic_id and self.analytic_id.id
		customer_id = self.customer_id and self.customer_id.id
		acc_ids = []
		cont_id = self.id
		move_line_obj = self.env['account.move.line'].search([('partner_id', '=', customer_id)])
		for line in move_line_obj:
			acc_ids.append(line.account_id and line.account_id.id)
		acc_ids = list(set(acc_ids))
		for acc in acc_ids:
			debit = 0
			credit = 0
			move_line = self.env['account.move.line'].search([('partner_id', '=', customer_id),('account_id', '=', acc),('analytic_account_id','=',analytic_id)])
			for moveli in move_line:
				debit = debit + moveli.debit
				credit = credit + moveli.credit
			acc_obj = self.env['account.account'].browse(acc)
			balance = debit - credit
			if acc_obj.user_type_id.id == 3 or acc_obj.user_type_id.id == 14:
				generate_balance = 0
			else:
				generate_balance = balance

			self.env['property.cont.closure'].create({'account_id':acc,'balance':balance,'name':'/','cont_id':cont_id,'generate_balance':generate_balance})
			
		self.closure_generated = True
#        self.write({'state': 'close'})

 


	#
	def closure_confirm(self):
		closure_lines = self.env['property.cont.closure'].search([('cont_id','=',self.id)])
		self.ensure_one()
		get_param = self.env['ir.config_parameter'].sudo().get_param

		defualt_journal_id = get_param('ag_property_maintainence.settlement_journal_id') or False
		defualt_journal_id = ast.literal_eval(defualt_journal_id)
		#defualt_journal_id = self.env['ir.default'].get('property.config.settings', 'settlement_journal_id') or False
		if not defualt_journal_id:
			raise Warning("settlement journal not defined") 
			
		cost_center = self.build_id and self.build_id.maintain_cc_id and self.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
			
		unit_line = self.unit_line
		for u_line in unit_line:
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
		lines = []
		debit = 0 
		credit = 0
		od_generate_balance = 0
		for closure_line in closure_lines:
			data = {}
			data['account_id'] = closure_line.account_id.id
			data['partner_id'] = self.customer_id.id
			data['analytic_account_id'] = self.analytic_id.id
			data['name'] = self.analytic_id.name
			od_generate_balance = od_generate_balance + closure_line.generate_balance
			if closure_line.generate_balance < 0:
				data['debit'] = abs(closure_line.generate_balance)
				debit = debit + closure_line.generate_balance
			else:
				data['credit'] = closure_line.generate_balance
				credit = credit + closure_line.generate_balance
				
			if data.get('debit') or data.get('credit') > 0:
				lines.append((0,0,data))

		unbalanced_amount = credit+debit
		if (unbalanced_amount) != 0:
			data = {}
			data['partner_id'] = self.customer_id.id
			data['analytic_account_id'] = self.analytic_id.id
			data['name'] = self.analytic_id.name
			data['account_id'] = self.customer_id.property_account_receivable_id.id
			data['maintain_cc_id'] = cost_center
			data['unit_maintain_cc_id'] = unit_cost_center
			data['floor_maintain_cc_id'] = floor_cost_center
			if (unbalanced_amount) < 0:
				data['credit'] = abs(unbalanced_amount)
			else:
				data['debit'] = unbalanced_amount
			if data.get('debit') or data.get('credit') > 0:
				lines.append((0,0,data))

		result = self.env['account.move'].create({'journal_id':defualt_journal_id,'ref':self.analytic_id.name,'line_ids':lines})
		result.post()
		self.settlement_entry = result and result.id or None
		if self.is_terminate:
			for line in self.payment_line:
				if not line.move_id:
					line.od_state = 'cancel'
				
				
			for aline in self.account_line:
				if not aline.move_id:
					aline.od_state = 'cancel'
			self.write({'state': 'cancel'})
		else:
			self.write({'state': 'done'})
		if abs(od_generate_balance) >0:
			self.ensure_one()
			get_param = self.env['ir.config_parameter'].sudo().get_param

			payment_journal_id = get_param('ag_property_maintainence.payment_journal_id') or False
			payment_journal_id = ast.literal_eval(payment_journal_id)

			self.env['property.cont.payment'].create({'cont_id':self.id,'name':'00000','date':self.date_stop,'amount':od_generate_balance,'type':'settlement','journal_id':payment_journal_id,'cust_bank_id':False,'deposit':0})

	#
	def set_to_draft(self):
		if self.settlement_entry:
			self.settlement_entry.unlink()
		self.state = 'progres'

	#
	def action_show_cheque(self):
		action = self.env.ref('property_management.property_cheque_action').read()[0]
		domain = []
		domain.append(('cont_id','=',self.id))
		action['domain'] = domain
		return action

			
			
	# 
	# 
	@api.constrains('unit_line') 
	def _check_constriant(self): 
		unit_lines = self.unit_line 
		periodical = []

		for line in unit_lines:
			periodical.append(line.duration)
		periodical = list(set(periodical))
		if len(periodical) >1:
			raise Warning(_("Invalid action, for one contract you can only choose either monthly or yearly wise"))
	
	# Contract invoice View,Creation,Getting Values

	# #
	# def action_contract_view_invoice(self):
	# 	invoice_id=self.contract_invoice_id
	# 	domain = [('type','=','out_invoice'),('id','=',invoice_id)]
	# 	model_data = self.env['ir.model.data']
	# 	# Select the view
	# 	tree_view = model_data.get_object_reference('account', 'invoice_tree')
	# 	form_view = model_data.get_object_reference('account', 'invoice_form')
	# 	return {
	# 			'name':('Invoices'),
	# 			'view_type': 'form',
	# 			'view_mode': 'tree,form',
	# 			'res_model': 'account.invoice',
	# 			'domain':domain,
	# 			'views': [(tree_view and tree_view[1] or False, 'tree'),(form_view and form_view[1] or False, 'form')],
	# 			'type': 'ir.actions.act_window',
	# 		}
	# # 
	# def _get_contract_invoice_count(self):
	# 	account = self.env['account.invoice']
	# 	invoice_id=self.contract_invoice_id
	# 	print 'contract_invoice_count',invoice_id
	# 	self.contract_invoice_count =len(account.search([('type','=','out_invoice'),('id','=',invoice_id)]))
	# 	print 'Invoice value.....',self.contract_invoice_count
	# 	return self.contract_invoice_count
	# def create_customer_invoice(self):
	# 	datas=[]
	# 	datas = self.get_vat_line()
	# 	invoice_pool = self.env['account.invoice']
	# 	# journal_id = self._get_sale_journal()
	# 	for line in self.payment_line:
	# 		if line.type=='vat':
	# 			invoice_date = line.date
	# 	partner = self.customer_id
	# 	values = {
	# 					# 'name':inv_name or '',
	# 					# 'number':inv_name or '',
	# 					'date_invoice':invoice_date,
	# 					'partner_id':partner.id,
	# 					'account_id':partner.property_account_receivable_id and partner.property_account_receivable_id.id or False,
	# 					'type':'out_invoice',
	# 					'id':self.id,
		
						
	# 					}
	# 	invoice_line_val  = [(0,0,res) for res in datas]
	# 	values['invoice_line_ids'] = invoice_line_val
	# 	invoice = invoice_pool.create(values)

	# 	self.contract_invoice_id=invoice

	# 	print 'heloooo',self.contract_invoice_id
	# 	# if invoice:
	# 	# 	invoice.action_invoice_open()
	# 	# self.add_invoice_to_service(invoice)
	# def get_vat_line(self):
	# 	datas = []
	# 	val={}
	# 	contract_date=self.date_start+"-"+self.date_stop
	# 	total_rent=0
	# 	for line in self.rent_line:
	# 		print 'totalllllllllll'
	# 		total_rent=total_rent+line.rent
	# 	account_id=self.con_type.vat_account.id
	# 	analytic_id=analytic_id = self.analytic_id and self.analytic_id.id or " "
	# 	# print 'total rent',total_rent
	# 	vals = {
	# 		'quantity':1,
	# 		'name':contract_date,
	# 		'price_unit':total_rent,
	# 		'account_id':account_id,
	# 		'account_analytic_id':analytic_id
	# 		}
	# 	datas.append(vals)
	# 	return datas


		



class PropertyContRent(models.Model):
	_name = 'property.cont.rent'
	_description = "Contract Rent"
	_order = "date_from asc"

	date_from = fields.Date(string="Date From", track_visibility='onchange' , required=True)
	date_to = fields.Date(string="Date To", track_visibility='onchange' , required=True)
	month_count = fields.Integer(string="Days")
	percent = fields.Float(string="Percent")
	con_value = fields.Float(string="Yearly Rent")
	rent = fields.Float(string="Rent", track_visibility='onchange')
	month_rent = fields.Float(string="Monthly Rent",  help="Monthly Rental Income")
	instal = fields.Integer(string="Installments",default=1, help="Number of Payments" )
	cont_id = fields.Many2one('property.contract', ondelete='cascade', string="Contract")
	od_vat_rent=fields.Float(string="Vat")

	_sql_constraints = [('date_from', 'date_to', 'Date From-To must be unique per Contract...!'),]

	# @api.onchange('con_value','percent')
	# def onchange_con_value(self):
	#     conval = (self.con_value / 12) * self.month_count
	#     if conval >0 and self.percent >0 and self.month_count>0:
	#         rent = conval + ((conval * self.percent) / 100)
	#         self.rent = rent
	#         self.month_rent = rent / self.month_count
	#     else:
	#         if conval >0 and self.month_count >0:
	#             rent = conval
	#             self.rent = rent
	#             self.month_rent = rent / self.month_count

# Contract Units

##############################################################################################################
class PropertyContUnit(models.Model):
	_name = 'property.cont.unit'
	_description = "Contract Unit"
	
	
	
	def get_month_days(self,cal_month_s,cal_month_e):
		from datetime import datetime
		d1 = datetime.strptime(cal_month_s, "%Y-%m-%d")
		d2 = datetime.strptime(cal_month_e, "%Y-%m-%d")
		val = abs((d2 - d1).days)+1
		return val
	def leapyr(self,ds,de):
		year_ds = int(ds[:4])
		year_de = int(de[:4])
		no_of_years = (year_de - year_ds) + 1
		leap_years = []
		for year in range(0,no_of_years):
			n = year+int(ds[:4])
			if n%4==0 and n%100!=0:
				leap_years.append(n)
			elif n%400==0:
				leap_years.append(n)
		
		return len(list((tuple(leap_years))))
	@api.model
	def create(self, vals):
		vals['name']  = self.env['ir.sequence'].next_by_code('property.cont.unit') or 'New'
		return super(PropertyContUnit,self).create(vals)
	#   
	def get_months_between_dates(self,d1,d2):
		from datetime import datetime
		d1 = datetime.strptime(str(d1)[:10], "%Y-%m-%d")
		d2 = datetime.strptime(str(d2)[:10], "%Y-%m-%d")
		val = float(abs((d2 - d1).days)+1) / float(30)
		val = int(round(val)) 
		return val
		
	#   
	def od_get_no_of_years(self,ds,dt):
		from datetime import datetime
		d1 = datetime.strptime(str(ds)[:10], "%Y-%m-%d")
		d2 = datetime.strptime(str(dt)[:10], "%Y-%m-%d")
		days = abs((d2 - d1).days)+1
		if days <= 366:
			return 1
		elif days > 366 and days <=740:
			return 2
		elif days > 740 and days<=1100:
			return 3
		elif days > 1100 and days<=1480:
			return 4
		else:
			return 5       	
		
	#   
	def od_diff_month(self,d1, d2):
		from datetime import datetime
		return (d1.year - d2.year)*12 + d1.month - d2.month
		
	#   
	def get_months_between_dates(self,d1,d2):
		from datetime import datetime
		d1 = datetime.strptime(str(d1)[:10], "%Y-%m-%d")
		d2 = datetime.strptime(str(d2)[:10], "%Y-%m-%d")
		val = float(abs((d2 - d1).days)+1) / float(30)
		val = int(round(val)) 
		return val
		
	#   
	def get_months_between_dates_noround(self,d1,d2):
		from datetime import datetime
		d1 = datetime.strptime(str(d1)[:10], "%Y-%m-%d")
		d2 = datetime.strptime(str(d2)[:10], "%Y-%m-%d")
		val = float(abs((d2 - d1).days)+1) / float(30)
 
		return val 

	@api.onchange('unit_id')
	def onchange_unit(self):
		if self.unit_id.floor_id:
			self.floor_id = self.unit_id.floor_id
		if self.unit_id.net_area:
			self.net_area = self.unit_id.net_area
		if self.unit_id.gross_area:
			self.gross_area = self.unit_id.gross_area

		unit_id = self.unit_id
		date_start = self.cont_id.date_start
		date_stop = self.cont_id.date_stop
		cont_id = self.cont_id.id
		contract_line_obj = self.env['property.cont.unit']
		contract_line = contract_line_obj.search([('unit_id', '=', unit_id.id),('cont_id','!=',cont_id)])
		if len(contract_line) >0:
			for unit in contract_line:
				start_dt = unit.cont_id and unit.cont_id.date_stop
				end_dt = unit.cont_id and unit.cont_id.date_stop
				if start_dt <= date_start and end_dt >= date_stop:
					self.is_avail = 'occup'
				elif start_dt >= date_start and start_dt <= date_stop:
					self.is_avail = 'occup'
				elif end_dt >= date_start and end_dt <= date_stop:
					self.is_avail = 'occup'
				else:
					self.is_avail = 'avail'
		else:
			self.is_avail = 'avail'
	name = fields.Char(string="Name")
	unit_id = fields.Many2one('property.unit', string="Unit", required=True)
	net_area = fields.Float(string="Net Area", track_visibility='onchange')
	gross_area = fields.Float(string="Gross Area", track_visibility='onchange')
	unit_sqft = fields.Float(string="Rent/SQFT", track_visibility='onchange')
	list_rent = fields.Float(string="Unit Rent", track_visibility='onchange')
	duration = fields.Selection([('mt', 'Monthly'),('yr', 'Yearly'),], string='Period', index=True, required=True, default='yr')
	year_rent = fields.Float(string="Total Rent", track_visibility='onchange')
	unit_rent = fields.Float(string="Rent Due", required=True, track_visibility='onchange')
	free_unit_mth = fields.Integer(string="Free Days", help="Free Period")
	line_disc = fields.Float(string="Disc", track_visibility='onchange')
	mth_count = fields.Integer(string="Days", help="Rental Period")
	auto_line = fields.Boolean(string="Base Rent")
	is_avail = fields.Selection([('avail','Available'),('occup','Occupied')],string="Available")
	percent = fields.Float(string="Percent")
	unit_from = fields.Date(string="Date From", required=True, track_visibility='onchange')
	unit_to = fields.Date(string="Date To", required=True, track_visibility='onchange')
	date_from = fields.Date(string="Contract Date From", track_visibility='onchange')
	date_to = fields.Date(string="Contract Date To", track_visibility='onchange')
	partner_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange')
	cont_id = fields.Many2one('property.contract', ondelete='cascade', string="Contract")
	unit_manager_id = fields.Many2one(related="cont_id.user_id")
	build_id = fields.Many2one('property.master',string="Building")
	main_property_id = fields.Many2one(related='build_id.main_property_id',store=True, string='Property')
	floor_id = fields.Many2one('property.floor', string="Floor")

	vat=fields.Float(string="Vat")
	vat_amount_total=fields.Float(string="Total",compute="compute_vat",store=True)
	


	#
	@api.depends('list_rent','unit_rent','year_rent','unit_from','unit_to')
	@api.onchange('list_rent','unit_rent','year_rent','unit_from','unit_to')
	def compute_vat(self):
		for rec in self:
			tax_amt = rec.cont_id.con_type.vat_id.amount
			rec.vat = tax_amt/100*rec.unit_rent
			rec.vat_amount_total=rec.unit_rent+rec.vat


	_sql_constraints = [('unit_id', 'cont_id', 'Unit must be unique per Contract...!'),]


	@api.onchange('unit_id')
	def unit_onchange(self):
		dt_from = self.cont_id.date_start
		dt_to = self.cont_id.date_stop
		self.list_rent = self.unit_id.annual_rent
		if self.unit_id and not self.unit_from:
			self.unit_from = dt_from
			self.unit_to = dt_to
		rent_lines  = self.unit_id.rent_line
		if len(rent_lines) >0 and self.unit_id:
			line_ids = rent_lines.search([('date_from','<=',dt_from),('date_to','>=',dt_from),('unit_id','=',self.unit_id.id)])
			for line in line_ids:
				self.unit_sqft = line.sqft 
				# self.list_rent = line.rent
				list_rent = line.rent 
				sqft_rent = line.sqft 
				duration = line.duration

	@api.onchange('unit_from','unit_to')
	def unit_start_onchange(self):
		if self.unit_from and self.unit_to:
			dt_from = datetime.strptime(str(self.unit_from), "%Y-%m-%d")
			dt_to = datetime.strptime(str(self.unit_to), "%Y-%m-%d")
			mth_count = (dt_to - dt_from).days
			self.mth_count = mth_count + 1          

	@api.onchange('unit_id','unit_rent','unit_from','unit_to','year_rent','percent','mth_count','free_unit_mth','unit_sqft','net_area','list_rent','line_disc','duration')
	def onchange_unit_values(self):

		

		if self.unit_from and self.unit_to:
			d1 = datetime.strptime(str(self.unit_from), "%Y-%m-%d")
			d2 = datetime.strptime(str(self.unit_to), "%Y-%m-%d")
			free = self.free_unit_mth
			d3 = d1 + timedelta(days=free)
			no_of_leapyear = self.leapyr(str(d1),str(d2))
			tdays = (d2 - d1).days
			tdays = tdays + 1
			rdays = (d2 - d1).days
			no_of_months = self.get_months_between_dates(d2,d1)#[0]
			no_of_years = self.od_get_no_of_years(str(d2),str(d1))#[0]
			rdays = ((rdays + 1) - no_of_leapyear)
			if rdays==364 :
				rdays=rdays+1
			
			yr_rent =0
			if self.unit_sqft >0:
				if self.duration =='yr':
# 					yr_rent = self.unit_sqft * self.net_area * no_of_years

# 					if no_of_years == 1:
# 					# if free and not d3 :

# 						no_of_days_betw = 30
# 						actual_days = 12
# 						var = float(float(yr_rent) / float(actual_days))
# 						one_day_rent =  float(var) / float(30)   
# 						free_days_rent = one_day_rent *  free
# 						yr_rent = yr_rent - free_days_rent
										   
# #                    self.year_rent = yr_rent
# #                    self.unit_rent = yr_rent - self.line_disc
					yr_rent = self.unit_sqft * self.net_area
					one_day_rent =  float(yr_rent) / float(365)   
					yr_rent =one_day_rent * rdays
					free_days_rent = one_day_rent *  free
					yr_rent = yr_rent - free_days_rent
				else:
#                    yr_rent = (((self.unit_sqft * self.net_area) *12) / 365) * tdays
					yr_rent = (self.unit_sqft * self.net_area) * no_of_months
#                    self.year_rent = yr_rent
#                    self.unit_rent = yr_rent - self.line_disc
			if self.list_rent >0:
				
				if self.duration =='yr':
# 					yr_rent = self.list_rent * no_of_years
					
# 					if no_of_years == 1:
# 					# if free and  not d3 :
# 						no_of_days_betw = 30
# 						actual_days = 12

# 						var = float(float(yr_rent) / float(actual_days))
# 						one_day_rent =  float(var) / float(30)   
# 						free_days_rent = one_day_rent *  free
# 						yr_rent = yr_rent - free_days_rent

# #                    self.year_rent = yr_rent
# #                    self.unit_rent = yr_rent - self.line_disc
					
					yr_rent=self.list_rent
					one_day_rent =  float(yr_rent) / float(365)   
					yr_rent =one_day_rent * rdays
					free_days_rent = one_day_rent *  free
					yr_rent = yr_rent - free_days_rent

				else:
					
#                   yr_rent = ((self.list_rent * 12 ) / 365) * tdays
					yr_rent = self.list_rent * no_of_months
#                    self.year_rent = yr_rent
#                    self.unit_rent = yr_rent - self.line_disc
					

			conval = yr_rent
			if self.percent >0:
				yr_rent = yr_rent + ((yr_rent * self.percent) / 100)
			self.year_rent = yr_rent
			self.unit_rent = yr_rent - self.line_disc	
#                conval = yr_rent + ((yr_rent * self.percent) / 100)
#            if conval and tdays and self.duration =='yr':
#                self.year_rent = ((conval/tdays) * rdays) 
#                self.unit_rent = ((conval/tdays) * rdays) - self.line_disc
		self.compute_vat()

# Contract Payments
class PropertyContPayment(models.Model):
	_name = 'property.cont.payment'
	_description = "Contract Payment"
	_order = "type asc,date"
	
	##################################################################
	@api.model
	def create(self,vals):
		cont_id = vals.get('cont_id')
		cont_obj = self.env['property.contract'].browse(cont_id)
		build_id = cont_obj.build_id and cont_obj.build_id.id
		vals['property_id'] = build_id
		return super(PropertyContPayment,self).create(vals)

	
	#
	def replace_cheque_entry(self):
		active_ids = self._context.get('active_id')
		cheque_obj = self
		if cheque_obj.replaced_move_id:
			raise Warning("entry already generated") 
			
		journal_id = cheque_obj.journal_id and cheque_obj.journal_id.id
		old_name = cheque_obj.name + '(replaced)'
#        cheque_replacement = self.env['ir.values'].get_default('property.config.settings', 'cheque_replacement') or False
#        if not cheque_replacement:
#            raise Warning(_("Cheque replacement not enabled in settings"))
					
		new_name = cheque_obj.name
		date = cheque_obj.date
		deposit = cheque_obj.deposit
		amount = cheque_obj.amount
		cont_id = cheque_obj.cont_id and cheque_obj.cont_id.id
		submit = cheque_obj.submit
		analytic_id = cheque_obj.cont_id.analytic_id and cheque_obj.cont_id.analytic_id.id
		cost_center = cheque_obj.cont_id.build_id and cheque_obj.cont_id.build_id.maintain_cc_id and cheque_obj.cont_id.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
		unit_line = cheque_obj.cont_id.unit_line
		for u_line in unit_line:
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
		old_lines = []
		partner_id = cheque_obj.partner_id and cheque_obj.partner_id.id
		cheque_obj.name = old_name
		recivable_acc_id = cheque_obj.partner_id.property_account_receivable_id.id
#    	self.env['property.cont.payment'].create({'journal_id':journal_id,'name':'0000','date':date,'deposit':deposit,'amount':amount,'cont_id':cont_id,'submit':submit,'partner_id':partner_id})
		od_debit =  (0,0,{'account_id':recivable_acc_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':old_name,'credit':0.0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
		od_credit =  (0,0,{'account_id':recivable_acc_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':old_name,'credit':amount,'debit':0.0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})

		old_lines.append(od_credit)
		old_lines.append(od_debit)
		analytic_obj = cheque_obj.agree_id.analytic_id

		result = self.env['account.move'].create({'journal_id':journal_id,'ref':cheque_obj.cont_id.name,'line_ids':old_lines})
		cheque_obj.replaced_move_id = result.id
		result.post()
#    	return True
		




	#
	def od_replace_cheque(self):
		if len(self._context.get('active_ids', [])) > 1:
			raise Warning("you cannot select two record at a time") 
		domain = []
		action = self.env.ref('property_management.action_replace_check_wiz')
		result = action.read()[0]
		ctx = dict()
		value = self.env['property.cont.payment'].browse(self._context.get('active_ids', [])[0]).amount
		if self.env['property.cont.payment'].browse(self._context.get('active_ids', [])[0]).od_state == 'replaced':
			raise Warning("already replaced")
			
		
		ctx.update({
			'default_payment_id': self._context.get('active_ids', [])[0],
			'default_cheque_value':value
		})        
		 
		result['context'] = ctx       
		return result
	#
	@api.depends('cont_id')
	def _get_state(self):
		state = self.cont_id.state
		self.state = state	

	#
	@api.depends('cont_id','name')
	def _get_partner(self):
		cont_id = self.cont_id
		if cont_id:
			self.partner_id = self.cont_id.customer_id.id or False

	name = fields.Char(string="Number", required=True)
	replaced_move_id = fields.Many2one('account.move', string='Replaced Entry')
	date = fields.Date(string="Date", required=True)
	journal_id = fields.Many2one('account.journal', string='Journal', required=True)
	deposit = fields.Float(string="Deposit", required=True)
	amount = fields.Float(string="Amount", required=True)
	cust_bank_id = fields.Many2one('property.bank', string="Issue Bank")
	ref = fields.Char(string="Reference")
	submit = fields.Selection([('hand','In Hand'),('bank','Deposited')], string="Submit",default='hand')
	move_id = fields.Many2one('account.move',string="Contract Journal", track_visibility='onchange')
	ret_date = fields.Date(string="Ret. Date")
	ret_charge = fields.Float(string="Charge")
	rev_move_id = fields.Many2one('account.move',string="Retn. JV", track_visibility='onchange')
	sub_date = fields.Date(string="Sub.Date")
	type = fields.Selection([
		('deposit', 'Deposit'),
		('payment', 'Payment'),
		('commission_paid', 'Commission Paid'),
		('commission_received', 'Commission Received'),
		('settlement', 'Settlement'),
		('vat', 'Vat'),
		('ejari', 'Ejari'),
		], string='Type',default='payment')
	sub_move_id = fields.Many2one('account.move',string="ReSub. JV", track_visibility='onchange')
	partner_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange', store=True, compute="_get_partner")
	cont_id = fields.Many2one('property.contract', ondelete='cascade', string="Contract")
	state = fields.Char(string='State',store=True, compute="_get_state")
	cont_state = fields.Selection([('draft', 'Waiting Approval'),('post','Approved'),('progres', 'In Progress'),('close','Closure'),('done', 'Completed'),('cancel', 'Terminated'),],string='Contract State',readonly=True,store=True,default='draft',related='cont_id.state')
	property_id = fields.Many2one('property.master', string='Building')
	
	
	
	od_state = fields.Selection([
		('draft', 'Draft'),
		('cancel', 'Cancel'),
		('posted', 'Posted'),
		('replaced', 'Replaced'),
		], string='Status',default='draft')
	od_vat_invoice_no=fields.Char(string='Inv No',default='/')
	clearing_date=fields.Date(string='Clearing Date')
	# journal_ob=fields.Many2one('property.config.settings',string='Contract Config')
	
	# vat=fields.Float(string="Vat",compute="compute_vat")
	# vat_amount_total=fields.Float(string="Total",compute="compute_vat" )
	


	# #
	# @api.depends('amount')
	# def compute_vat(self):
	# 	self.vat = self.cont_id.con_type.vat_percentage/100*self.amount
	# 	self.vat_amount_total=self.amount+self.vat
	
	# Bank Deposit Flag

	def bank_deposit(self):
		self.write({'submit':'bank'})
	#
	def payment_account_move(self):

		
		cost_center = self.cont_id and self.cont_id.build_id and self.cont_id.build_id.maintain_cc_id and self.cont_id.build_id.maintain_cc_id.id     
		unit_cost_center = []
		floor_cost_center = []
		unit_line = self.cont_id.unit_line
		for u_line in unit_line:
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
	
	
		if self.type != 'settlement':
			if self.cont_id.state == 'cancel':
				raise Warning("Contract terminated already")
					
		   
	
#		if self.cont_id.state == 'cancel':
#		    raise Warning("Contract terminated already")		        
		if self.type == 'commission_paid':
			if self.move_id and self.move_id.id:
				raise Warning("already posted")	

			line_vals = []
			agent_payable_acc_id = self.cont_id.agent_id and self.cont_id.agent_id.property_account_payable_id and self.cont_id.agent_id.property_account_payable_id.id
			cust_bank_id = self.journal_id and self.journal_id.default_debit_account_id.id
			part_id = self.cont_id.agent_id and self.cont_id.agent_id.id
			analytic_id = self.cont_id.analytic_id and self.cont_id.analytic_id.id or False
			name = self.name
			if not cust_bank_id:
				raise Warning("no account defined inside the journal")
			if not agent_payable_acc_id:
				raise Warning("agent or agent payable account not defined")
			amount = self.amount
			date = self.clearing_date
			move_vals = {'journal_id':self.journal_id and self.journal_id.id,'date':date,'ref': str(self.cont_id.name) +"\t"+  name}
 
			
			line1 = (0,0,{'account_id':agent_payable_acc_id,'partner_id':part_id,'name':name,'credit':0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			line2 = (0,0,{'account_id':cust_bank_id,'partner_id':part_id,'name':name,'credit':amount,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})				
			line_vals.append(line1)
			line_vals.append(line2)
			move_vals['line_ids'] = line_vals
			move_pool = self.env['account.move']
			move = move_pool.create(move_vals)
			move.post()
			self.move_id = move.id
		elif self.type == 'commission_received':
			if self.move_id and self.move_id.id:
				raise Warning("already posted")	
			line_vals = []
			cust_rec_acc_id = self.cont_id.customer_id and self.cont_id.customer_id.property_account_receivable_id and self.cont_id.customer_id.property_account_receivable_id.id
			cust_bank_id = self.journal_id and self.journal_id.default_debit_account_id.id
			part_id = self.cont_id.customer_id and self.cont_id.customer_id.id
			analytic_id = self.cont_id.analytic_id and self.cont_id.analytic_id.id or False
			#pdc_account_new_id = self.env['ir.default'].get('property.config.settings', 'pdc_new_id') or False

			name = self.name 
			if not cust_bank_id:
				raise Warning("no account defined inside the journal")
			if not cust_rec_acc_id:
				raise Warning("customer or customer receivable account not defined")
			amount = self.amount
			date = self.clearing_date#self.date
			move_vals = {'journal_id':self.journal_id and self.journal_id.id,'date':date,'ref': str(self.cont_id.name) +"\t"+  name}

			if self.cont_id.is_contract:
				#line1 = (0,0,{'account_id':pdc_account_new_id,'partner_id':part_id,'name':name,'credit':amount,'debit':0,'maintain_cc_id':cost_center})
				line2 = (0,0,{'account_id':cust_bank_id,'partner_id':part_id,'name':name,'credit':0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			else:
				line1 = (0,0,{'account_id':cust_rec_acc_id,'partner_id':part_id,'name':name,'credit':amount,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				line2 = (0,0,{'account_id':cust_bank_id,'partner_id':part_id,'name':name,'credit':0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})				
			line_vals.append(line1)
			line_vals.append(line2)
			move_vals['line_ids'] = line_vals
			move_pool = self.env['account.move']
			move = move_pool.create(move_vals)
			move.post()
			self.move_id = move.id
		
			
		elif self.type == 'settlement':
			if self.move_id and self.move_id.id:
				raise Warning("already posted")
			debit_acc_id = False
			credit_acc_id = False
			line_vals = []

			cust_rec_acc_id = self.cont_id.customer_id and self.cont_id.customer_id.property_account_receivable_id and self.cont_id.customer_id.property_account_receivable_id.id
			cust_bank_id = self.journal_id and self.journal_id.default_debit_account_id.id
			part_id = self.cont_id.customer_id and self.cont_id.customer_id.id
			analytic_id = self.cont_id.analytic_id and self.cont_id.analytic_id.id or False
			name = self.name
	 
			if not cust_bank_id:
				raise Warning("no account defined inside the journal")
			if not cust_rec_acc_id:
				raise Warning("customer or customer receivable account not defined")
			if self.amount <0:
				credit_acc_id = cust_bank_id
				debit_acc_id = cust_rec_acc_id
			else:
				credit_acc_id = cust_rec_acc_id
				debit_acc_id = cust_bank_id	    
				 
				
			amount = self.amount
			date = self.clearing_date
			move_vals = {'journal_id':self.journal_id and self.journal_id.id,'date':date,'ref': str(self.cont_id.name) +"\t"+  name}
			line1 = ()
			line2 = ()

			if amount > 0:
				line1 = (0,0,{'account_id':credit_acc_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				line2 = (0,0,{'account_id':debit_acc_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			else:
				line1 = (0,0,{'account_id':credit_acc_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':abs(amount),'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				line2 = (0,0,{'account_id':debit_acc_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':abs(amount),'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})			
			line_vals.append(line1)
			line_vals.append(line2)
			move_vals['line_ids'] = line_vals
			move_pool = self.env['account.move']
			move = move_pool.create(move_vals)
			move.post()
			self.move_id = move.id


		elif self.type == 'vat':

			if self.move_id and self.move_id.id:
				raise Warning("already posted")

			if self.od_vat_invoice_no == '/':
				self.ensure_one()
				get_param = self.env['ir.config_parameter'].sudo().get_param
				journal_id = get_param('ag_property_maintainence.vat_journal_id') or False
				journal_id = ast.literal_eval(journal_id)
				#journal_id=self.env['ir.default'].get('property.config.settings', 'vat_journal_id') or False
				journal_ob=self.env['account.journal'].browse(journal_id)
				inv_seq =journal_ob.sequence_id

				if not inv_seq:
					raise UserError(_('Journal Entry Sequence not set'))

				name = inv_seq.with_context(ir_sequence_date=self.date).next_by_id()
				self.od_vat_invoice_no = name

			line_vals=[]
			cust_rec_acc_id=self.cont_id.con_type.vat_id and self.cont_id.con_type.vat_id.account_id and self.cont_id.con_type.vat_id.account_id.id or " "
			cust_bank_id = self.journal_id and self.journal_id.default_debit_account_id.id
			part_id = self.cont_id.customer_id and self.cont_id.customer_id.id
			analytic_id = self.cont_id.analytic_id and self.cont_id.analytic_id.id or " "
			#pdc_account_new_id = self.env['ir.default'].get('property.config.settings', 'pdc_new_id') or False
			name = self.name

			if not cust_bank_id:
				raise Warning("no account defined inside the journal")
			if not cust_rec_acc_id:
				raise Warning("customer or customer receivable account not defined")
			if self.amount <0:
				credit_acc_id = cust_bank_id
				debit_acc_id = cust_rec_acc_id
			else:
				credit_acc_id = cust_rec_acc_id
				debit_acc_id = cust_bank_id

			amount = self.amount
			date = self.clearing_date
			move_vals = {'journal_id':self.journal_id and self.journal_id.id or " ",'date':date,'ref': str(self.cont_id.name) +"\t"+  name}
			line1 = ()
			line2 = ()

			if amount > 0:
				if self.cont_id.is_contract:
					#line1 = (0,0,{'account_id':pdc_account_new_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0,'maintain_cc_id':cost_center})
					line2 = (0,0,{'account_id':cust_bank_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				else:
					line1 = (0,0,{'account_id':cust_rec_acc_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					line2 = (0,0,{'account_id':cust_bank_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			else:
				if self.cont_id.is_contract:
					#line1 = (0,0,{'account_id':pdc_account_new_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':abs(amount),'debit':0,'maintain_cc_id':cost_center})
					line2 = (0,0,{'account_id':cust_bank_id,'partner_id':part_id,'analytic_account_id':debit_analytic_id,'name':name,'credit':0,'debit':abs(amount),'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				else:
					line1 = (0,0,{'account_id':cust_rec_acc_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':abs(amount),'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					line2 = (0,0,{'account_id':cust_bank_id,'partner_id':part_id,'analytic_account_id':debit_analytic_id,'name':name,'credit':0,'debit':abs(amount),'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			line_vals.append(line1)
			line_vals.append(line2)
			move_vals['line_ids'] = line_vals
			move_pool = self.env['account.move']
			move = move_pool.create(move_vals)
			move.post()
			self.move_id = move.id

		elif self.type == 'ejari':

			if self.move_id and self.move_id.id:
				raise Warning("already posted")

			line_vals=[]
			self.ensure_one()
			get_param = self.env['ir.config_parameter'].sudo().get_param
			cust_rec_acc_id= get_param('ag_property_maintainence.cust_rec_acc_id') or False
			cust_rec_acc_id = ast.literal_eval(cust_rec_acc_id)
			cust_bank_id = self.journal_id and self.journal_id.default_debit_account_id.id
			part_id = self.cont_id.customer_id and self.cont_id.customer_id.id
			analytic_id = self.cont_id.analytic_id and self.cont_id.analytic_id.id or " "
			#pdc_account_new_id = self.env['ir.default'].get('property.config.settings', 'pdc_new_id') or False
			name = self.name
	 
			if not cust_bank_id:
				raise Warning("no account defined inside the journal")
			if not cust_rec_acc_id:
				raise Warning("customer or customer receivable account not defined")
			if self.amount <0:
				credit_acc_id = cust_bank_id
				debit_acc_id = cust_rec_acc_id
			else:
				credit_acc_id = cust_rec_acc_id
				debit_acc_id = cust_bank_id	    
		
			amount = self.amount
			date = self.clearing_date
			move_vals = {'journal_id':self.journal_id and self.journal_id.id or " ",'date':date,'ref': str(self.cont_id.name) +"\t"+  name}
			line1 = ()
			line2 = ()

			if amount > 0:
				if self.cont_id.is_contract:
					#line1 = (0,0,{'account_id':pdc_account_new_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0,'maintain_cc_id':cost_center})
					line2 = (0,0,{'account_id':cust_bank_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				else:
					line1 = (0,0,{'account_id':cust_rec_acc_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					line2 = (0,0,{'account_id':cust_bank_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			else:
				if self.cont_id.is_contract:
					#line1 = (0,0,{'account_id':pdc_account_new_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':abs(amount),'debit':0,'maintain_cc_id':cost_center})
					line2 = (0,0,{'account_id':cust_bank_id,'partner_id':part_id,'analytic_account_id':debit_analytic_id,'name':name,'credit':0,'debit':abs(amount),'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				else:
					line1 = (0,0,{'account_id':cust_rec_acc_id,'partner_id':part_id,'analytic_account_id':analytic_id,'name':name,'credit':abs(amount),'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					line2 = (0,0,{'account_id':cust_bank_id,'partner_id':part_id,'analytic_account_id':debit_analytic_id,'name':name,'credit':0,'debit':abs(amount),'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})			
			line_vals.append(line1)
			line_vals.append(line2)
			move_vals['line_ids'] = line_vals
			move_pool = self.env['account.move']
			move = move_pool.create(move_vals)
			move.post()
			self.move_id = move.id



		elif self.type == 'payment' :

			self.ensure_one()
			get_param = self.env['ir.config_parameter'].sudo().get_param
			deposit_account_id = get_param('ag_property_maintainence.deposit_account_id') or False
			deposit_account_id = ast.literal_eval(deposit_account_id)
			advance_account_id = get_param('ag_property_maintainence.advance_account_id') or False
			advance_account_id = ast.literal_eval(advance_account_id)
			cheque_account_id = get_param('ag_property_maintainence.cheque_account_id') or False
			cheque_account_id = ast.literal_eval(cheque_account_id)
			# deffered_account_new_id = get_param('ag_property_maintainence.deffered_account_new_id') or False
			# deffered_account_new_id = ast.literal_eval(deffered_account_new_id)
			# advance_account_new_id = self.env['ir.default'].get('property.config.settings', 'advance_new_id') or False
			# pdc_account_new_id = self.env['ir.default'].get('property.config.settings', 'pdc_new_id') or False
			journal_id = self.journal_id.id	       	
			partner_id = self.cont_id.customer_id and self.cont_id.customer_id.id or False
			analytic_id = self.cont_id.analytic_id and self.cont_id.analytic_id.id or False			       	
			journal_account_id = False
			if journal_id:
				journal = self.env['account.journal'].browse(journal_id)
				journal_account_id = journal.default_debit_account_id.id             	
						
			partner_account_id = False 
			if partner_id:
				partner = self.env['res.partner'].browse(partner_id)
				partner_account_id = partner.property_account_receivable_id.id
											
							
			name = self.name                  
			amount = self.amount                              	
			
			deposit = self.deposit                  
			total = amount 				        		
						
			if deposit >0:
				total = amount+deposit			        		
			
			
			date = self.clearing_date      	
			move_vals = {'journal_id':journal_id,'date':date,'ref': str(self.cont_id.name) +"\t"+  name}          	
			move_line = []        	
				
			if amount > 0 or deposit > 0:
				if journal_account_id or cheque_account_id or advance_account_id or partner_account_id :#and pdc_account_new_id and deffered_account_new_id and advance_account_new_id:
					# if self.cont_id.is_contract:
					# 	#cheque_account_id = (0,0,{'account_id':pdc_account_new_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':total,'debit':0.0,'maintain_cc_id':cost_center})
					# 	bank_line_vals =  (0,0,{'account_id':journal_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':total,'maintain_cc_id':cost_center})
					# 	#advance_line_vals =  (0,0,{'account_id':deffered_account_new_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':total,'maintain_cc_id':cost_center})
					# 	#customer_line_vals =  (0,0,{'account_id':advance_account_new_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':total,'debit':0.0,'maintain_cc_id':cost_center})
					# else:
					cheque_account_id = (0,0,{'account_id':cheque_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':total,'debit':0.0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					bank_line_vals =  (0,0,{'account_id':journal_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':total,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					advance_line_vals =  (0,0,{'account_id':advance_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':total,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					customer_line_vals =  (0,0,{'account_id':partner_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':total,'debit':0.0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					move_line.append(cheque_account_id)
					move_line.append(bank_line_vals)
					move_line.append(advance_line_vals)
					move_line.append(customer_line_vals)
					move_vals['line_ids'] = move_line
					move_pool = self.env['account.move']
					move = move_pool.create(move_vals)
					move.post()
					if self.move_id:
						self.write({'sub_move_id':move.id,'rev_move_id':False,'ret_date':False,'submit':'bank'})
					else:
						self.write({'move_id':move.id,'submit':'bank'})
				else:
					print('---check the warning--')
					raise Warning("Account/Jounral not set !!!!")
		else:
			self.ensure_one()
			get_param = self.env['ir.config_parameter'].sudo().get_param
			deposit_account_id = get_param('ag_property_maintainence.deposit_account_id') or False
			deposit_account_id = ast.literal_eval(deposit_account_id)
			advance_account_id = get_param('ag_property_maintainence.advance_account_id') or False
			advance_account_id = ast.literal_eval(advance_account_id)
			cheque_account_id = get_param('ag_property_maintainence.cheque_account_id') or False
			cheque_account_id = ast.literal_eval(cheque_account_id)
			#pdc_account_new_id = self.env['ir.default'].get('property.config.settings', 'pdc_new_id') or False
			journal_id = self.journal_id.id	       	
			partner_id = self.cont_id.customer_id and self.cont_id.customer_id.id or False
			analytic_id = self.cont_id.analytic_id and self.cont_id.analytic_id.id or False			       	
			journal_account_id = False		     
			if journal_id:
				journal = self.env['account.journal'].browse(journal_id)
				journal_account_id = journal.default_debit_account_id.id             	
						
			partner_account_id = False 
			if partner_id:
				partner = self.env['res.partner'].browse(partner_id)
				partner_account_id = partner.property_account_receivable_id.id
											
							
			name = self.name                  
			amount = self.amount                              	
			
			deposit = self.deposit                  
			total = amount 				        		
						
			if deposit >0:
				total = amount+deposit			        		
			
			
			date = self.clearing_date       	
			move_vals = {'journal_id':journal_id,'date':date,'ref': str(self.cont_id.name) +"\t"+  name}          	
			move_line = []        	
				
			if amount > 0 or deposit > 0:
				if journal_account_id or cheque_account_id or advance_account_id or partner_account_id :#and pdc_account_new_id:
					if self.cont_id.is_contract:
						#cheque_account_id = (0,0,{'account_id':pdc_account_new_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':total,'debit':0.0,'maintain_cc_id':cost_center})
						bank_line_vals =  (0,0,{'account_id':journal_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':total,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					else:
						cheque_account_id = (0,0,{'account_id':cheque_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':total,'debit':0.0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
						bank_line_vals =  (0,0,{'account_id':journal_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':total,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					# advance_line_vals =  (0,0,{'account_id':advance_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':amount,'maintain_cc_id':cost_center})
					# customer_line_vals =  (0,0,{'account_id':partner_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0.0,'maintain_cc_id':cost_center})
					move_line.append(cheque_account_id)
					move_line.append(bank_line_vals)
					# move_line.append(advance_line_vals)
					# move_line.append(customer_line_vals)
					move_vals['line_ids'] = move_line
					move_pool = self.env['account.move']
					move = move_pool.create(move_vals)
					move.post()
					if self.move_id:
						self.write({'sub_move_id':move.id,'rev_move_id':False,'ret_date':False,'submit':'bank'})
					else:
						self.write({'move_id':move.id,'submit':'bank'})
				else:
					print('---this first one--')
					raise Warning("Account/Jounral not set !!!!")
		
		self.od_state = 'posted'
	
	# 
	def payment_move(self):
		if self.cont_id.state in ('draft','post','renew'):
			raise Warning("Contract not Confirmed !!!!") 
		elif self.move_id:
			raise Warning("Posted Journal Exist !!!!")
		else:
			if not self.clearing_date:
				self.clearing_date=date.today()
			self.payment_account_move()

	
	#
	def submit_payment_move(self):
		if not self.sub_date:
			raise Warning("Re Submit Date not set !!!!")
		elif self.sub_move_id:
			raise Warning("Reversal Journal Exist !!!!")
		elif not self.rev_move_id:
			raise Warning("Return Journal Doesn't Exist !!!!")
		elif self.sub_date < self.date:
			raise Warning("Re Submit Date should be Greater than Post Date")
		elif self.ret_date and self.sub_date < self.ret_date:
			raise Warning("Resubmit Date should be Greater than Return Date")
		else: 
			self.payment_account_move()

	#
	def reverse_payment_move(self):
		cost_center = self.cont_id and self.cont_id.build_id and self.cont_id.build_id.maintain_cc_id and self.cont_id.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
		unit_line = self.cont_id.unit_line
		for u_line in unit_line:
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
		if not self.ret_date:
			raise Warning("Return Date not set")
		elif self.rev_move_id:
			raise Warning("Reversal Journal Exist")
		elif not self.move_id:
			raise Warning("Posted Journal Doesn't Exit")
		elif self.ret_date < self.date:
			raise Warning("Return Date should be Greater than Post Date")
		elif self.sub_date and self.ret_date < self.sub_date:
			raise Warning("Return Date should be Greater than Resubmit Date")
		else:
			if self.sub_move_id:
				ac_move_id = self.sub_move_id
			else:
				ac_move_id = self.move_id
			date = self.ret_date or fields.Date.today()
			self.ensure_one()
			get_param = self.env['ir.config_parameter'].sudo().get_param

			bounce_journal_id = get_param('ag_property_maintainence.bounce_journal_id') or False
			bounce_journal_id = ast.literal_eval(bounce_journal_id)
			journal_id = bounce_journal_id or ac_move_id.journal_id.id,
			bounce_account_id = get_param('ag_property_maintainence.bounce_account_id') or False
			bounce_account_id = ast.literal_eval(bounce_account_id)

			partner_id = self.cont_id.customer_id and self.cont_id.customer_id.id or False
			analytic_id = self.cont_id.analytic_id and self.cont_id.analytic_id.id or False
			partner_account_id = False
			if partner_id:
					partner = self.env['res.partner'].browse(partner_id)
					partner_account_id = partner.property_account_receivable_id.id
			acmove_line = self.env['account.move.line']
			line_ids = acmove_line.search([('move_id','=',ac_move_id.id)])
			move_vals = {'journal_id':journal_id,'date':date,'ref':_('reversal of: ') +ac_move_id.name}
			ret_charge = self.ret_charge
			move_line = []
			if journal_id and bounce_account_id:
				for acm_line in line_ids:
					line_vals = (0,0,{'account_id':acm_line.account_id.id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':_('reversal of: ') + acm_line.name,'credit':acm_line.debit,'debit':acm_line.credit,'amount_currency': -acm_line.amount_currency,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					move_line.append(line_vals)
				if ret_charge >0:
					charge_line_vals = (0,0,{'account_id':bounce_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':_('return charges of: ') + acm_line.name,'credit':ret_charge,'debit':0.0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					tenant_line_vals = (0,0,{'account_id':partner_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':_('return charges of: ') + acm_line.name,'credit':0.0,'debit':ret_charge,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					move_line.append(charge_line_vals)
					move_line.append(tenant_line_vals)
				move_vals['line_ids'] = move_line
				move_pool = self.env['account.move']
				move = move_pool.create(move_vals)
				move.post()
				self.write({'rev_move_id':move.id,'sub_move_id':False,'sub_date':False})

				payment_user_id = get_param('ag_property_maintainence.task_user_id') or False
				payment_user_id = ast.literal_eval(payment_user_id)

				analytic_id = self.cont_id.analytic_id and self.cont_id.analytic_id.id or False
				project_id = self.env['project.project'].search([('analytic_account_id','=',analytic_id)],limit=1)
				task_pool = self.env['project.task']
				task_val = {'name':self.cont_id.name + _(' - Cheque Return'),'project_id':project_id.id,'user_id':payment_user_id,}
				task = task_pool.create(task_val)

			else:
				print('--this second one--')
				raise Warning("Account/Jounral not set !!!!")

	def vat_print_invoice(self):
		datas = {
			'ids': [self.id],
			'model': 'property.cont.payment',
			'form': self.read(self)
		}
		return {
			'type': 'ir.actions.report.xml',
			'report_name': 'report.property_payment_vat_print',
			'report_type': 'qweb',
			'datas': datas,
			'res_model': 'property.cont.payment',
			'src_model': 'property.cont.payment',
		}

	#
	# def amount_to_text(self,amount):
	#
	# 	check_amount_in_words = amount_to_text_en.amount_to_text(math.floor(amount), lang='en', currency='')
	# 	check_amount_in_words = check_amount_in_words.replace(' and Zero Cent', '') # Ugh
	# 	decimals = amount % 1
	# 	if decimals >= 10**-2:
	# 		check_amount_in_words += _(' and %s/100') % str(int(round(float_round(decimals*100, precision_rounding=1))))
	# 	od_check_amount_in_words= check_amount_in_words.replace(',','')
	# 	od_check_amount_in_words=od_check_amount_in_words.encode('ascii','ignore')
	#
	# 	return od_check_amount_in_words

	def get_unit_no(self):
		unit_ls=[]
		for line in self.cont_id.unit_line:
			unit_id=line.unit_id.name.encode('ascii','ignore')
			unit_ls.append(unit_id)
		
		unit_ls=list(set(unit_ls))
		unit_ls=','.join(unit_ls)
		return unit_ls

	def get_floor_no(self):

		floor_ls=[]
		for line in self.cont_id.unit_line:
			floor_id=line.floor_id.name.encode('ascii','ignore')
			floor_id=string.capwords(floor_id)
			floor_ls.append(floor_id)
		
		floor_ls=list(set(floor_ls))
		floor_ls=','.join(floor_ls)
		return floor_ls

		
# Contract Account

class PropertyContAccountdetail(models.Model):
	_name = 'property.cont.account.detail'
	_description = "Contract Account Detail"
	_order = "unit_id,date asc"
	def dummy(self):
		return True
	#
	@api.depends('cont_id','name')
	def _get_partner(self):
		cont_id = self.cont_id
		if cont_id:
			self.partner_id = self.cont_id.customer_id.id or False
	name = fields.Char(string="Month")
	date = fields.Date(string="Date", required=True)
	unit_id = fields.Many2one('property.unit',string="Unit")
	revenue = fields.Float(string="Income", required=True)
	deffered_revenue = fields.Float(string="De.Income")
		
	move_id = fields.Many2one('account.move',string="Journal", track_visibility='onchange')
	partner_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange', store=True, compute="_get_partner")
	cont_id = fields.Many2one('property.contract', ondelete='cascade', string="Contract")
	desc = fields.Char(string="Desc")
	
class PropertyContAccount(models.Model):
	_name = 'property.cont.account'
	_description = "Contract Account"
	_order = "date asc"
	def dummy(self):
	 
		return True

	#
	@api.depends('cont_id','name')
	def _get_partner(self):
		cont_id = self.cont_id
		if cont_id:
			self.partner_id = self.cont_id.customer_id.id or False

	name = fields.Char(string="Month")
	date = fields.Date(string="Date", required=True)
	revenue = fields.Float(string="Income", required=True)
	deffered_revenue = fields.Float(string="De.Income")
	move_id = fields.Many2one('account.move',string="Journal", track_visibility='onchange')
	partner_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange', store=True, compute="_get_partner")
	cont_id = fields.Many2one('property.contract', ondelete='cascade', string="Contract")
	desc = fields.Char(string="Desc")
	od_state = fields.Selection([
		('draft', 'Draft'),
		('cancel', 'Cancel'),
		('posted', 'Posted'),
		], string='Status',default='draft')
	#   
	def get_month_day_range(self,date):
		date = datetime.strptime(str(date), '%Y-%m-%d')
		last_day = date + relativedelta(day=1, months=+1, days=-1)
		first_day = date + relativedelta(day=1)
		return str(last_day)#, last_day


	# 
	def revenue_move(self):
		
		cost_center = self.cont_id and self.cont_id.build_id and self.cont_id.build_id.maintain_cc_id and self.cont_id.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
		unit_line = self.cont_id.unit_line
		for u_line in unit_line:
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
		if not self.deffered_revenue:
			raise Warning("You cannot Post it")
	
		if self.cont_id.state == 'cancel':
			raise Warning("Contract already terminated !!!!")
	
		if self.cont_id.state in ('draft','post','renew'):
			raise Warning("Contract not Confirmed !!!!") 
		elif self.move_id:
			raise Warning("Journal Entry Exist !!!!")
		else:

			self.ensure_one()
			get_param = self.env['ir.config_parameter'].sudo().get_param

			revenue_journal_id = get_param('ag_property_maintainence.revenue_journal_id') or False
			revenue_journal_id = ast.literal_eval(revenue_journal_id)
			deffered_account_id = get_param('ag_property_maintainence.deffered_account_id') or False
			deffered_account_id = ast.literal_eval(deffered_account_id)
			revenue_account_id = get_param('ag_property_maintainence.revenue_account_id') or self.cont_id and self.cont_id.con_type and self.cont_id.con_type.account_id and self.cont_id.con_type.account_id.id or  False
			revenue_account_id = ast.literal_eval(revenue_account_id)
			advance_account_id = get_param('ag_property_maintainence.advance_account_id') or False
			advance_account_id = ast.literal_eval(advance_account_id)
			#deffered_account_new_id = self.env['ir.default'].get('property.config.settings', 'deffered_new_id') or False
			#rent_account_new_id = self.env['ir.default'].get('property.config.settings', 'rent_account_id') or False
			#advnc_account_new_id = self.env['ir.default'].get('property.config.settings', 'advance_new_id') or False
			
			journal_id = revenue_journal_id
			partner_id = self.cont_id.customer_id.id or False

			analytic_id = self.cont_id.analytic_id and self.cont_id.analytic_id.id or False
			partner_account_id = False
			if partner_id:

					partner = self.env['res.partner'].browse(partner_id)
					partner_account_id = partner.property_account_receivable_id.id

			name = self.name
			amount = self.revenue
			date = self.date
			move_vals = {'journal_id':journal_id,'date':date,'ref':self.cont_id.name}
			move_line = []
			if revenue_journal_id and deffered_account_id and revenue_account_id and advance_account_id:
				#revenue_line_vals = (0,0,{'account_id':revenue_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0.0})

				
				#move_line.append(revenue_line_vals)
			   # move_line.append(deffered_line_vals)
			   # move_line.append(advance_line_vals)
				#move_line.append(customer_line_vals)
				m_start_date = str(self.get_month_day_range(date))[:10]#[0][0]
				m_end_date = str(self.get_month_day_range(date))[:10]#[0][1]
				details_line_ids = self.env['property.cont.account.detail'].search([('cont_id','=',self.cont_id.id),('date','>=',m_start_date),('date','<=',m_end_date)])
				tot_revenue = 0
				for d_line in details_line_ids:
					product_id = d_line.unit_id and d_line.unit_id.product_id and d_line.unit_id.product_id.id or False
					# if self.cont_id.is_contract:
					# 	revenue_line_vals = (0,0,{'account_id':rent_account_new_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':round(d_line.deffered_revenue,2),'debit':0.0,'product_id':product_id,'maintain_cc_id':cost_center})
					# else:
					revenue_line_vals = (0,0,{'account_id':revenue_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':round(d_line.deffered_revenue,2),'debit':0.0,'product_id':product_id,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					move_line.append(revenue_line_vals)
					tot_revenue = tot_revenue + round(d_line.deffered_revenue,2)
				# if self.cont_id.is_contract:
				# 	customer_line_vals =  (0,0,{'account_id':advnc_account_new_id,'partner_id':partner_id,'analytic_account_id':analytic_id,
				# 	'name':name,'credit':0.0,'debit':tot_revenue,'maintain_cc_id':cost_center})
				# else:
				customer_line_vals =  (0,0,{'account_id':partner_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,
				'name':name,'credit':0.0,'debit':tot_revenue,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				deffered_line_vals =  (0,0,{'account_id':deffered_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,
				'name':name,'credit':0.0,'debit':tot_revenue,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				advance_line_vals =  (0,0,{'account_id':advance_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,
				'name':name,'credit':tot_revenue,'debit':0.0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				move_line.append(deffered_line_vals)
				move_line.append(advance_line_vals)
				move_line.append(customer_line_vals)
				move_vals['line_ids'] = move_line
				move_pool = self.env['account.move']
				move = move_pool.create(move_vals)
				move_id = move.id
				move.post()
				self.write({'move_id':move_id})
			else:
				print('---this thid one--')
				raise Warning("Account/Jounral not set  !!!!")
		self.od_state = 'posted'

# Contract Attachment
class PropertyContAttachment(models.Model):
	_name = 'property.cont.attachment'
	_description = "Contract Attachment"

	name = fields.Char(string="Name", required=True)
	attachment_type_id = fields.Many2one('property.attachment.type', string="Type", required=True)
	attachment = fields.Binary(string="Attachment",required=True)
	remarks = fields.Text(string="Remarks")
	cont_id = fields.Many2one('property.contract', ondelete='cascade', string="Contract")

# Contract Closure
class PropertyContClosure(models.Model):
	_name = 'property.cont.closure'
	_description = "Contract Closure"

	name = fields.Char(string="Head", required=True)
	account_id = fields.Many2one('account.account', string='Account', required=True)
	balance = fields.Float(string="Balance",)
	cont_id = fields.Many2one('property.contract', ondelete='cascade', string="Contract")
	generate_entries = fields.Boolean('Generate Entries')
	generate_balance = fields.Float('Generate Entries')

# Contract Settle
class PropertyContSettle(models.Model):
	_name = 'property.cont.settle'
	_description = "Contract Settle"

	name = fields.Char(string="Reason", required=True)
	account_id = fields.Many2one('account.account', string='Account', required=True)
	amount = fields.Float(string="Amount",)
	cont_id = fields.Many2one('property.contract', ondelete='cascade', string="Contract")
	
	
class PropertySettle(models.Model):
	_name = 'property.settle'
	_description = "Contract Settlement"

	name = fields.Char(string="Name")
	amount = fields.Float(string="Amount",)
	cont_id = fields.Many2one('property.contract', ondelete='cascade', string="Contract")    

# Property Contract Type
class PropertyConType(models.Model):
	_name = 'property.con.type'
	_description = "Contract Type"
   
	name = fields.Char(string="Name",  required="1")
	template_l = fields.Html(string="Left Template")
	template_r = fields.Html(string="Right Template")
	account_id = fields.Many2one("account.account",'Account')
	agree_print = fields.Selection([('both','Both'),('left','Left'),('right','Right')],string="Print Format",default='both')

	vat_id = fields.Many2one('account.tax',string="Vat")
	# vat_account=fields.Many2one("account.account",string="Vat Account")
	_sql_constraints = [('name_uniq', 'unique(name)', 'Name must be unique...!'),]

class AccountMove(models.Model):
	_inherit = 'account.move'

	cont_id = fields.Many2one('property.contract',string="Contract")

class AccountMoveLine(models.Model):

	_inherit = 'account.move.line'

	maintain_cc_id = fields.Many2one('maintain.account.cost.center', string='Cost Center')
	floor_maintain_cc_id = fields.Many2many('floor.account.cost.center', string='Floor Cost Center')
	unit_maintain_cc_id = fields.Many2many('unit.account.cost.center', string='Unit Cost Center')

	# @api.onchange('account_id')
	# def move_line_account_change(self):

	# 	if self.journal_id and self.journal_id.maintain_cc_id:
	# 		self.maintain_cc_id = self.journal_id.maintain_cc_id.id

	
	

	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
 
		
