# -*- coding: utf-8 -*-
import re
import datetime as dt
from datetime import  timedelta, tzinfo, time, date, datetime
from dateutil.relativedelta import relativedelta 
#from monthdelta import monthdelta
import odoo
#from odoo.addons.base_geolocalize.models.res_partner import geo_find, geo_query_address
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo import exceptions, _
from odoo.exceptions import Warning
import pytz
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT as svrdt
from pprint import pprint
import ast
	
class PropertyAgreement(models.Model):
	_name = 'property.agreement'
	_description = "Property Agreement"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = "con_date desc"
	
	
	
	#@api.one
	def closure(self):
		closure_lines = self.env['property.agree.closure'].search([('agree_id','=',self.id)])
		old_lines = self.env['property.agree.settle'].search([('agree_id','=',self.id)])
		
								
		for ol in old_lines:
			ol.unlink()
		
		
		

		
		if self.date_terminate:
			account_lines = self.env['property.agree.account'].search([('agree_id','=',self.id),('date','<=',self.date_terminate),('od_state','=','draft')])
			od_start_date = self.get_month_day_range(self.date_terminate)#[0]
			od_end_date = self.get_month_day_range(self.date_terminate)#[1]
			corresponding_account_lines = self.env['property.agree.account'].search([('cont_id','=',self.id),('date','>=',od_start_date),('od_state','=','draft'),('date','<=',od_end_date)])
			corresponding_account_lines_detail = self.env['property.agree.account.detail'].search([('agree_id','=',self.id),('date','>=',od_start_date),('date','<=',od_end_date)])
			not_considering_lines_detail = self.env['property.agree.account.detail'].search([('cont_id','=',self.id),('date','>',od_end_date)])
			not_considering_lines = self.env['property.agree.account'].search([('agree_id','=',self.id),('date','>',od_end_date),('od_state','=','draft')])
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
					
					
			final_account_lines = self.env['property.agree.account'].search([('agree_id','=',self.id)])
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
				self.env['property.agree.settle'].create({'name':'Security Deposit','amount':amount,'agree_id':self.id})
			bank_cash_type = self.env['account.account.type'].search([('name','=','Bank and Cash')])        
			bank_cash_accounts_obj = self.env['account.account'].search([('user_type_id','=',bank_cash_type[0].id)])
			bank_cash_accounts = []
			bank_cash_amount = 0
			for acc in bank_cash_accounts_obj:
				bank_cash_accounts.append(acc.id)
			entries_related_bankcash_obj = self.env['account.move.line'].search([('partner_id','=',self.supplier_id.id),('debit','>',0),('analytic_account_id','=',self.analytic_id and self.analytic_id.id),('account_id','in',bank_cash_accounts)])
			for entri in entries_related_bankcash_obj:
				bank_cash_amount = bank_cash_amount + entri.debit
			self.env['property.agree.settle'].create({'name':'Bank/Cash','amount':bank_cash_amount,'cont_id':self.id})
			self.env['property.agree.settle'].create({'name':'Revenue','amount':total_deffered,'cont_id':self.id})
			
			
					
						
		for closure_line in closure_lines:
			closure_line.unlink()
		analytic_id = self.analytic_id and self.analytic_id.id
		customer_id = self.supplier_id and self.supplier_id.id
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

			self.env['property.agree.closure'].create({'account_id':acc,'balance':balance,'name':'/','agree_id':cont_id,'generate_balance':generate_balance})
			
		self.closure_generated = True    
	
	
	#@api.multi
	def revert_process(self):
		date = self.date_stop
		account_line = self.account_line
		account_detail_line = self.account_detail_line
		for line in account_line:
			revenue = line.revenue
			line.write({'deferred_revenue':revenue})
	
		for a_line in account_detail_line:
			revenue = a_line.revenue
			a_line.write({'deferred_revenue':revenue})
	#@api.one
	def closure_confirm(self):
		closure_lines = self.env['property.agree.closure'].search([('agree_id','=',self.id)])
		get_param = self.env['ir.config_parameter'].sudo().get_param

		defualt_journal_id = get_param('ag_property_maintainence.settlement_journal_id') or False
		if not defualt_journal_id:
			raise Warning("settlement journal not defined")
		defualt_journal_id = ast.literal_eval(defualt_journal_id)


			
		cost_center = self.build_id and self.build_id.maintain_cc_id and self.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
			
		unit_line = self.unit_line
		for u_line in unit_line:
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
		#print('---cost center---',cost_center)
		lines = []
		debit = 0 
		credit = 0
		od_generate_balance = 0
		for closure_line in closure_lines:
			data = {}
			data['account_id'] = closure_line.account_id.id
			data['partner_id'] = self.supplier_id.id
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
			data['partner_id'] = self.supplier_id.id
			data['analytic_account_id'] = self.analytic_id.id
			data['name'] = self.analytic_id.name
			data['account_id'] = self.supplier_id.property_account_payable_id.id
			data['maintain_cc_id'] = cost_center
			data['unit_maintain_cc_id'] = [(6,0, unit_cost_center)]
			data['floor_maintain_cc_id'] = [(6,0, floor_cost_center)]
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
			payment_journal_id = get_param('ag_property_maintainence.payment_journal_id') or False
			payment_journal_id = ast.literal_eval(payment_journal_id)


			self.env['property.agree.payment'].create({'agree_id':self.id,'name':'00000','date':self.date_stop,'amount':od_generate_balance,'type':'settlement','journal_id':payment_journal_id,'cust_bank_id':False,'deposit':0})

	#@api.one
	def get_next_month_date(self,d1,start_count):
		d1 = datetime.strptime(str(d1)[:10], '%Y-%m-%d')
		d1 = d1 + relativedelta(months=start_count)
		return d1
		
		
		
	@api.onchange('build_id','date_start','date_stop')
	def build_id_onchange(self):
		build_id = self.build_id and self.build_id.id
		date_start = self.date_start
		date_stop = self.date_stop
		unit_line_ids = []
		self.unit_line = unit_line_ids
		if build_id:
			agreement_value = self.agreement_value

			unit_ids = self.env['property.unit'].search([('property_id', '=', build_id)])
			if unit_ids:
				for unit in unit_ids:
					net_area = unit.net_area
					if net_area == 0:
						net_area = 1
					vals = {'unit_id':unit.id,'net_area':net_area,'floor_id':unit.floor_id and unit.floor_id.id,'year_rent':float(agreement_value)/float(net_area),'duration':'yr','date_from':date_start,'date_to':date_stop,'unit_from':date_start,'unit_to':date_stop}
					unit_line_ids.append([vals])
				self.unit_line = unit_line_ids

			
		   
		   
	#@api.one
	def merge_samemonthline_revenue(self):
		contract = self
		revenue_lines = contract.account_line
		same_ids = []
		for line in revenue_lines:
			desc = line.desc
			unit_id = line.unit_id and line.unit_id.id
			agree_id = line.agree_id and line.agree_id.id
			same_ids = []
			same_month_lines = self.env['property.agree.account'].search([('unit_id', '=', unit_id),('agree_id','=',agree_id),('desc', '=', desc),('id', 'not in', same_ids)])

			tot_amount = 0

			new_date = False
			desc = ''
			if len(same_month_lines) >1:

				for s_line in same_month_lines:
					new_date = self.get_month_day_range(s_line.date)#[1]
					tot_amount = tot_amount + s_line.revenue
					same_ids.append(s_line)
					desc = ":"+s_line.date
				self.env['property.agree.account'].create({'revenue':tot_amount,'unit_id':unit_id,'agree_id':agree_id,'date':new_date,'desc':desc})
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
		
	def get_add_month(self,date):
		start_dt = datetime.strptime(date, "%Y-%m-%d")
		start_dt = start_dt + relativedelta(months=+1)
	 
		return start_dt
		
		
	def get_month_day_range(self,date):
		date = datetime.strptime(str(date), "%Y-%m-%d")
		last_day = date + relativedelta(day=1, months=+1, days=-1)
		first_day = date + relativedelta(day=1)
		return str(last_day)[:10] #str(first_day)[:10],
		
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
		date1 = datetime.strptime(date1, "%Y-%m-%d") 
		date1 = str(date1 + relativedelta(days=+1))[:10]
		return date1
	def get_con_end_date(self,date1):
		start_dt = datetime.strptime(str(date1), "%Y-%m-%d")
		rent_dt = start_dt + relativedelta(years=1)
		rent_dt = rent_dt + relativedelta(days=-1)
		new_date = rent_dt.strftime("%Y-%m-%d")
		return new_date
		
		

	
	
	#@api.one
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
					'agree_id':self.id
			}
			self.env['property.agree.account'].create(vals)
			next_date = str(self.get_add_month(next_date))[:10]
	  

	#@api.one
	def unlink(self):
		state = self.state
		if state in ('progres','done','cancel'):
			raise Warning("You can Delete in Draft State Only")
		return super(PropertyAgreement,self).unlink()
	#@api.one
	def generate_rent_lines(self):
		wiz_obj = self.env['agreement.rent.generation.wiz'].create({'contract_id':self.id,'name':'wizard'})
		wiz_obj.generate_contract_rent()
		self.write({'rent_done':1})
		return True

	#@api.one
	@api.depends('date_start','date_stop')
	def get_dates(self):
		for rec in self:
			if not rec.date_start:
				rec.date_start = datetime.today()
			if not rec.date_stop:
				rec.date_stop = datetime.today()
			if rec.date_start and rec.date_stop:
				d0 = datetime.today()
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
					if f_days and t_days >0:
						rec.progress = (float(f_days) / float(t_days))*100.0

	#@api.one

		
		
		


	#@api.one
	@api.depends('unit_line')
	def get_total_rent(self):
		val =0
		for line in self.unit_line:
			val += line.unit_rent
		self.con_value = val

	#@api.one
	@api.depends('unit_line','unit_line.year_rent')
	def _get_total(self):
		self.total_value = sum(line.year_rent for line in self.unit_line)
		self.agreement_value = sum(line.year_rent for line in self.unit_line)
	name = fields.Char(string="Contract Ref.", copy=False , readonly=True, index=True, default='Draft')
	state = fields.Selection([('draft', 'Waiting Approval'),('post','Approved'),('progres', 'In Progress'),('close','Closure'),('done', 'Completed'),('cancel', 'Terminated'),], string='Status', readonly=True, copy=False, index=True, default='draft')
	costing_method = fields.Selection([('net_area', 'Net Area'),('equal','Equal'),], string='Costing Method',default='net_area')
	renew_id = fields.Many2one('property.agreement', string="Renew")
	con_date = fields.Date(string="Date", required=True, help="Contract Date")
	date_start = fields.Date(string="Date Strat", required=True, help="From Date", track_visibility='onchange')
	date_stop = fields.Date(string="Date Stop", required=True, help="To Date", track_visibility='onchange')
	month_count = fields.Integer(string="Months", default=12)
	free_month = fields.Integer(string="Free Month", help="Free Period")
	con_type = fields.Many2one('property.con.type', required=True, string="Type")
	supplier_id = fields.Many2one('res.partner', string="LandLord", required=True, help="Customer Name")
	build_id = fields.Many2one('property.master', required=True, string="Building")
	main_property_id = fields.Many2one(related='build_id.main_property_id',store=True, string='Property')
	floor_id = fields.Many2one('property.floor', string="Floor")
	unit_avail = fields.Char(string="Available", compute="_get_property_state" ,default='')
	month_rent = fields.Float(string="Monthly Income",  help="Monthly Rental Income")
	con_value = fields.Float(string="Yearly Rent" , compute="get_total_rent")
	con_free_value = fields.Float(string="Cont Free Rent")
	total_value = fields.Float(string="Conract Value", help="Total Contract Value", compute="_get_total",store=True)
	pay_count = fields.Integer(string="Installments", help="Number of Payments")
	dep_value = fields.Float(string="Deposit", help="Deposit Amount")
	progress = fields.Integer(string="Progress", required=False, default=0, compute="get_dates")
	user_id = fields.Many2one('res.users', string='Salesman', index=True, track_visibility='onchange', default=lambda self: self.env.user)
	analytic_id =fields.Many2one('account.analytic.account', string="Analytic Account")
	move_id = fields.Many2one('account.move',string="Journal", track_visibility='onchange')
	is_terminate = fields.Boolean(string="Terminate")
	date_terminate = fields.Date(string="Termination Date", help="Date of Termination")
	booking_id = fields.Many2one('property.booking',string="Booking")
	booking_amt = fields.Float(string="Booking Amount")
	comm_perc = fields.Float(string="Commission %", help="Commission charged from Tenant",default=0)
	comm_rcvd = fields.Float(string="Commission", help="Commission charged from Tenant")
	agent_id = fields.Many2one('res.partner',string="Agent")
	agent_perc = fields.Float(string="Agent %", help="Agent Percentage",default=0)
	comm_paid =  fields.Float(string="Commission Paid", help="Commission Paid to Agent")
	company_id = fields.Many2one('res.company', 'Company',index=True, default=lambda self: self.env['res.company']._company_default_get('flight.network'))
	agreement_l = fields.Html(string="T&C", track_visibility='onchange')
	agreement_r = fields.Html(string="T&C", track_visibility='onchange')
	rent_line = fields.One2many('property.agree.rent','agree_id',string="Rent")
	unit_line = fields.One2many('property.agree.unit','agree_id',string="Units")
	payment_line = fields.One2many('property.agree.payment','agree_id',string="Payment")
	account_line = fields.One2many('property.agree.account','agree_id',string="Account")
	account_detail_line = fields.One2many('property.agree.account.detail','agree_id',string="Account Detail")
	closure_line  = fields.One2many('property.agree.closure','agree_id',string="Closure")
	settle_line  = fields.One2many('property.agree.settle','agree_id',string="Settle")
	agree_print = fields.Selection([('both','Both'),('left','Left'),('right','Right')],string="Print Format",default='both')
	attachment_line = fields.One2many('property.agree.attachment','agree_id',string="Attachments")
	parking_slot = fields.Char(string="Parking Slot")
	comm_rec_move_id = fields.Many2one('account.move',string="Comm Rec journal",)
	comm_paid_move_id = fields.Many2one('account.move',string="Comm Paid Journal",)
	agreement_value = fields.Float(string="Agreement Value",compute="_get_total",store=True)
	settlement_entry = fields.Many2one('account.move',string="Settlement Entry")  
	closure_generated = fields.Boolean(string="Closure Generated",default=False)  
	rent_done = fields.Integer('Rent Done',default=0,copy=False)
	payment_done = fields.Integer('Payment Done',default=0,copy=False)
	customer_id = fields.Many2one('res.partner', string="Customer", help="Customer Name")


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

	@api.depends('unit_line')
	def _get_property_state(self):
		res = ''
		if self.unit_line:
			for line in self.unit_line:

				if line.is_avail == 'occup':
					res = 'Unit Not Available'
		self.unit_avail = res
		   
		   
		   
	@api.onchange('renew_id')
	def renew_id_onchange(self):
		renewal_contract = self.renew_id
		if renewal_contract:
			supplier_id = renewal_contract.supplier_id and renewal_contract.supplier_id.id
			booking_id = renewal_contract.booking_id and renewal_contract.booking_id.id
			con_type = renewal_contract.con_type and renewal_contract.con_type.id
			build_id = renewal_contract.build_id and renewal_contract.build_id.id
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
			self.customer_id = supplier_id
			self.booking_id = booking_id
			self.con_type = con_type
			self.build_id = build_id
			self.parking_slot = parking_slot
			self.name = name
			self.dep_value = dep_value
			self.booking_amt = booking_amt
			self.user_id = user_id
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
				dict_vals = (0,0,{'unit_id':unit_id,'list_rent':0,'unit_rent':0,'unit_from':start_date,'unit_to':end_date,'floor_id':floor_id,'duration':duration,'is_avail':is_avail})
				print('---dict_vals---', dict_vals)

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

	@api.onchange('booking_id')
	def booking_onchange(self):
		self.customer_id = self.booking_id.customer_id.id
		self.booking_amt = self.booking_id.amount

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

	#@api.one
	def unit_lines(self):
		if len(self.unit_line) >0:
			self.unit_line.search([('auto_line','=',True)]).unlink()
		if len(self.payment_line) >0:
			self.payment_line.unlink()
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
		print('--unit line---',self.unit_line)

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

	#@api.one
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
			

	#@api.one
	def rent_round_off(self):
		total = sum(line.rent for line in self.rent_line)
		line_total = sum(round(line.revenue,2) for line in self.account_line)
		if total != line_total and self.account_line:
			max_id = max(line.id for line in self.account_line)
			line_pool = self.env['property.agree.account']
			line_obj = line_pool.browse(max_id)
			amount = total - line_total
			revenue = line_obj.revenue
			line_obj.write({'revenue':revenue + amount})
			
	#@api.one
	def get_min_date(self,ds,free):
		start_dt = datetime.strptime(ds, "%Y-%m-%d")
		free = free
		rent_dt = start_dt + timedelta(days=free)
		new_date = rent_dt.strftime("%Y-%m-%d")
		return new_date
			
			
	#@api.one
	def get_monthly_rent(self):
		total = self.total_value
	
		min_dt = self.date_start
		unit_line = self.unit_line
#        for line1 in unit_line:
#            min_dt = self.get_min_date(self.date_start,line1.free_unit_mth)[0]
		dt_start = datetime.strptime(str(min_dt), "%Y-%m-%d")
		dt_stop = datetime.strptime(str(self.date_stop), "%Y-%m-%d")
		val = relativedelta(dt_stop, dt_start)
		months = (12*(val.years) +(val.months+1))
			
			
		month_rent = float(total) / float(months)
		for line in self.rent_line:
			line.month_rent = month_rent


	#@api.one
	def acc_lines(self):
		total_value = self.total_value
		cost_center = self.build_id and self.build_id.maintain_cc_id and self.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
			
		unit_line = self.unit_line
		for u_line in unit_line:
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
		costing_method = self.costing_method
		
		array_units = []
		od_total_area = 0
		
		
		for od_li in self.unit_line:
			array_units.append(od_li.unit_id and od_li.unit_id.id)
			od_total_area = od_total_area + od_li.net_area
		no_of_units = len(list(set(array_units)))
		if no_of_units == 0:
			no_of_units = 1
		for od_line in self.unit_line:
			net_area = od_line.unit_id.net_area
#            if net_area == 0:
#            	net_area = 1
			if costing_method == 'net_area':
				x = float(float(total_value) / float(od_total_area)) * net_area
				od_line.year_rent = x
					   
			else:
				od_line.year_rent = float(total_value) / float(no_of_units)			

		
			
		if len(self.rent_line) == 0:
			raise Warning("No Rent Line Available")
		if len(self.unit_line) == 0:
			raise Warning("No Unit Line Available")
		if len(self.payment_line) >0:
			self.payment_line.unlink()
		if len(self.account_line) >0:
			self.account_line.unlink()
		loop = 0
		for rentline in self.rent_line:
			dt_from = datetime.strptime(str(rentline.date_from) ,"%Y-%m-%d")
			dt_to = datetime.strptime(str(rentline.date_to) ,"%Y-%m-%d")
			
			installment = rentline.instal or 1
			total = rentline.rent
			rent = rentline.month_rent
			free_month = 0
			deposit = 0
			if loop == 0:
				free_month = self.free_month
				deposit = self.dep_value
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
			get_param = self.env['ir.config_parameter'].sudo().get_param

			receipt_journal_id = get_param('ag_property_maintainence.receipt_journal_id') or False
			if not receipt_journal_id:
				raise UserError('Please Configure the Settings')
			receipt_journal_id = ast.literal_eval(receipt_journal_id)


			val = relativedelta(dt_to, dt_from)
			months = (12*(val.years) +(val.months+1))
			interval = months / installment
			mod_interval = divmod(months,installment)
			install_amt = total / installment
			
			res = []
			next_date = rent_start
			start = 1

				
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
				start += 1
			self.payment_line = res
		if deposit:
			vals = {
					'name': '00000',
					'date': next_date,
					'journal_id':receipt_journal_id,
					'amount':deposit,
					'deposit':0,
					'type':'deposit',
					'agree_id':self.id
				}
			self.env['property.agree.payment'].create(vals)
		if self.comm_paid:
			vals = {
					'name': '00000',
					'date': next_date,
					'journal_id':receipt_journal_id,
					'amount':self.comm_paid,
					'deposit':0,
					'type':'commission_paid',
					'agree_id':self.id
				}
			self.env['property.agree.payment'].create(vals)
				
		if self.comm_rcvd:
			vals = {
					'name': '00000',
					'date': next_date,
					'journal_id':receipt_journal_id,
					'amount':self.comm_rcvd,
					'deposit':0,
					'type':'commission_received',
					'agree_id':self.id
				}
			self.env['property.agree.payment'].create(vals)
				
		#Revenue lines Generation
		wiz_obj = self.env['agreement.revenue.calculation.wizard'].create({'contract_id':self.id,'name':'wizard'})
		wiz_obj.generate_agreement_revenue()
		self.rent_round_off()
		self.write({'payment_done':1})

		
	#@api.one
	def approve(self):
		if self.unit_avail: #Unit Not Available
			raise Warning("Unit(s) not Available")
		if self.date_start > self.date_stop:
			raise Warning("End Date should not be lesser than Start Date")
		name = self.env['ir.sequence'].next_by_code('property.agreement') or 'Draft'
		supplier_id = self.supplier_id and self.supplier_id.id or False
		analytic_pool = self.env['account.analytic.account']
		analytic_val = {'name':name,'partner_id':supplier_id,}#'use_tasks':True
		analytic = analytic_pool.create(analytic_val)
		self.write({'name':name, 'analytic_id':analytic.id,'state':'post'})
		self.unit_line.write({'date_from':self.date_start,'date_to':self.date_stop,'partner_id':supplier_id})

		self.ensure_one()
		get_param = self.env['ir.config_parameter'].sudo().get_param

		task_user_id = get_param('ag_property_maintainence.task_user_id') or False
		task_user_id = ast.literal_eval(task_user_id)
		

		project_id = self.env['project.project'].search([('analytic_account_id','=',analytic.id)],limit=1)
		task_pool = self.env['project.task']
		task_val = {'name':name + _(' - Contract Signing'),'project_id':project_id.id,'user_ids':[(6,0,[task_user_id])]}
		task = task_pool.create(task_val)

	#@api.one
	def post(self):
		self.ensure_one()
		get_param = self.env['ir.config_parameter'].sudo().get_param

		prepaid_rent_account = get_param('ag_property_maintainence.prepaid_account_id') or False
		prepaid_rent_account = ast.literal_eval(prepaid_rent_account)
		deposit_pay_account_id = get_param('ag_property_maintainence.deposit_pay_account_id') or False
		deposit_pay_account_id = ast.literal_eval(deposit_pay_account_id)
		cheque_account_id = get_param('ag_property_maintainence.payment_account_id') or False
		cheque_account_id = ast.literal_eval(cheque_account_id)
		agreement_journal_id = get_param('ag_property_maintainence.agreement_journal_id') or False
		agreement_journal_id = ast.literal_eval(agreement_journal_id)

		cost_center = self.build_id and self.build_id.maintain_cc_id and self.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
			
		unit_line = self.unit_line
		for u_line in unit_line:
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
		

		
		
		
#        defualt_journal_id = self.env['ir.values'].get_default('property.config.settings', 'defualt_journal_id') or 3
#        deffered_account_id = self.env['ir.values'].get_default('property.config.settings', 'deffered_account_id') or False
		deposit_account_id = get_param('ag_property_maintainence.deposit_account_id') or False
		deposit_account_id = ast.literal_eval(deposit_account_id)
#        cheque_account_id = self.env['ir.values'].get_default('property.config.settings', 'cheque_account_id') or False
#        comm_recvd_id = self.env['ir.values'].get_default('property.config.settings', 'comm_recvd_id') or False
#        comm_paid_id = self.env['ir.values'].get_default('property.config.settings', 'comm_paid_id') or False
#        payment_line = self.payment_line
		analytic_id = self.analytic_id and self.analytic_id.id or False
#        journal_id = defualt_journal_id
		partner_id = self.supplier_id and self.supplier_id.id or False
#        agent_payable_acc_id = self.agent_id and self.agent_id.property_account_payable_id and self.agent_id.property_account_payable_id.id
#		
		name = self.name
#        date = self.con_date
		amount = self.agreement_value
		deposit = self.dep_value
#        total = amount
#        line_ids = []
#        recei_cust_acc_id = self.customer_id.property_account_receivable_id and self.customer_id.property_account_receivable_id.id
#        for line in payment_line:
# 			move_line = []
# 			move_line_paid = []
# 			if line.type == 'commission_received' and line.id not in line_ids:
# 				line_ids.append(line.id)     	
# 				journal_id = line.journal_id and line.journal_id.id			
# 				move_pool = self.env['account.move']    	
# 				move_vals = {'journal_id':journal_id,'date':date,'ref': name + _(' :: ') + str(self.customer_id.name)} 				
# 				line1 = (0,0,{'account_id':recei_cust_acc_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0.0,'debit':line.amount})  	
# 				line2 = (0,0,{'account_id':comm_recvd_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':line.amount,'debit':0})         		
# 				move_line.append(line1)         		
# 				move_line.append(line2)         		

# 				move_vals['line_ids'] = move_line         		
# 				move = move_pool.create(move_vals)         		
# 				self.comm_rec_move_id = move.id        		
# 			if line.type == 'commission_paid' and line.id not in line_ids:       		
# 				line_ids.append(line.id)  			
# 				journal_id = line.journal_id and line.journal_id.id 			
# 				if not agent_payable_acc_id:
# 					raise Warning("no agent defined or no account defined for agent")
# 				move_pool = self.env['account.move']  			
# 				move_vals_paid = {'journal_id':journal_id,'date':date,'ref': name + _(' :: ') + str(self.agent_id.name)}
# 				line_paid1 = (0,0,{'account_id':agent_payable_acc_id,'partner_id':self.agent_id and self.agent_id.id,'analytic_account_id':analytic_id,'name':name,'credit':line.amount,'debit':0})  			
# 				line_paid2 = (0,0,{'account_id':comm_paid_id,'partner_id':self.agent_id and self.agent_id.id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':line.amount})
# 				move_line_paid.append(line_paid1)
# 				move_line_paid.append(line_paid2)
# 				move_vals_paid['line_ids'] = move_line_paid
# 				move1 = move_pool.create(move_vals_paid)
# 				self.comm_paid_move_id = move1.id  
		renew_id = self.renew_id
		old_analytic_id = self.renew_id and self.renew_id.analytic_id and self.renew_id.analytic_id.id or False
		old_mov_lines = False

		if old_analytic_id:
			old_mov_lines = self.env['account.move.line'].search([('analytic_account_id', '=', old_analytic_id),('account_id', '=', deposit_account_id)])
		
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



		move_line = []
		move_vals = {}
		total = 0

		total = amount+deposit
		date = self.con_date
		move_vals = {'journal_id':agreement_journal_id,'date':date,'ref': name + _(' :: ') + str(self.supplier_id.name)}
		
#        
		if agreement_journal_id and prepaid_rent_account and deposit_pay_account_id and cheque_account_id:
			cheque_line_vals = (0,0,{'account_id':cheque_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':total,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			defferd_line_vals =  (0,0,{'account_id':prepaid_rent_account,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			deposit_line_vals =  (0,0,{'account_id':deposit_pay_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':deposit,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
			move_line.append(cheque_line_vals)
			move_line.append(defferd_line_vals)
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
		else:
			raise Warning("Account/Jounral not set !!!!")    

	#@api.one
	def reset(self):
		self.write({'state': 'draft','rent_done':0,'payment_done':0})

	#@api.one
	def closure(self):
		self.write({'state': 'close'})

	#@api.one
	def validate(self):
		if self.is_terminate:
			if date_terminate:
				self.write({'state': 'cancel'})
			else:
				raise Warning("Termination Date not set !!!")
		else:
			self.write({'state': 'done'})

# Contract Rent
class PropertyAgreeRent(models.Model):
	_name = 'property.agree.rent'
	_description = "Agreement Rent"
	_order = "date_from asc"

	date_from = fields.Date(string="Date From", track_visibility='onchange' , required=True)
	date_to = fields.Date(string="Date To", track_visibility='onchange' , required=True)
	month_count = fields.Integer(string="Days")
	percent = fields.Float(string="Percent")
	con_value = fields.Float(string="Yearly Rent")
	rent = fields.Float(string="Rent", track_visibility='onchange')
	month_rent = fields.Float(string="Monthly Rent",  help="Monthly Rental Income")
	instal = fields.Integer(string="Installments",default=1, help="Number of Payments" )
	agree_id = fields.Many2one('property.agreement', ondelete='cascade', string="Contract")

	_sql_constraints = [('date_from', 'date_to', 'Date From-To must be unique per Agreement...!'),]

	@api.onchange('con_value','percent')
	def onchange_con_value(self):
		conval = (self.con_value / 12) * self.month_count
		if conval >0 and self.percent >0 and self.month_count>0:
			rent = conval + ((conval * self.percent) / 100)
			self.rent = rent
			self.month_rent = rent / self.month_count
		else:
			if conval >0 and self.month_count >0:
				rent = conval
				self.rent = rent
				self.month_rent = rent / self.month_count

# Contract Units
class PropertyAgreeUnit(models.Model):
	_name = 'property.agree.unit'
	_description = "Agreement Unit"
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
	#@api.one
	def get_months_between_dates(self,d1,d2):
		from datetime import datetime
		d1 = datetime.strptime(str(d1)[:10], "%Y-%m-%d")
		d2 = datetime.strptime(str(d2)[:10], "%Y-%m-%d")
		val = float(abs((d2 - d1).days)+1) / float(30)
		val = int(round(val)) 
		return val
	#@api.one
	def od_diff_month(self,d1, d2):
		from datetime import datetime
		return (d1.year - d2.year)*12 + d1.month - d2.month
		
	

	@api.onchange('unit_id')
	def onchange_unit(self):
		if self.unit_id.floor_id:
			self.floor_id = self.unit_id.floor_id
		if self.unit_id.net_area:
			self.net_area = self.unit_id.net_area
		if self.unit_id.gross_area:
			self.gross_area = self.unit_id.gross_area

		unit_id = self.unit_id
		date_start = self.agree_id.date_start
		date_stop = self.agree_id.date_stop
		agree_id = self.agree_id.id
		contract_line_obj = self.env['property.agree.unit']
		contract_line = contract_line_obj.search([('unit_id', '=', unit_id.id),('agree_id','!=',agree_id)])
		if len(contract_line) >0:
			for unit in contract_line:
				start_dt = unit.agree_id and unit.agree_id.date_stop
				end_dt = unit.agree_id and unit.agree_id.date_stop
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

	unit_id = fields.Many2one('property.unit', string="Unit", required=True, domain=[('stop_date', '=', False),('is_active', '=', True)])
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
#    percent = fields.Float(string="Percent")
	unit_from = fields.Date(string="Date From", required=True, track_visibility='onchange')
	unit_to = fields.Date(string="Date To", required=True, track_visibility='onchange')
	date_from = fields.Date(string="Contract Date From", track_visibility='onchange')
	date_to = fields.Date(string="Contract Date To", track_visibility='onchange')
	partner_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange')
	agree_id = fields.Many2one('property.agreement', ondelete='cascade', string="Contract")
	build_id = fields.Many2one('property.master',string="Building")
	floor_id = fields.Many2one('property.floor', string="Floor")

	_sql_constraints = [('unit_id', 'agree_id', 'Unit must be unique per Agreement...!'),]

	@api.onchange('unit_id')
	def unit_onchange(self):
		dt_from = self.agree_id.date_start
		dt_to = self.agree_id.date_stop
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
#    @api.one
#    def od_get_no_of_years(self,ds,dt):
#        from datetime import datetime
#        d1 = datetime.strptime(str(ds), "%Y-%m-%d")
#        d2 = datetime.strptime(str(dt, "%Y-%m-%d")
#        days = abs((d2 - d1).days)+1
#        if days <= 366:
#            return 1
#        elif days > 366 and days <=730:
#            return 2
#        elif days > 730 and days<=1096:
#            return 3
#        elif days > 1096 and days<=1460:
#            return 4
#        else:
#            return 5         

	@api.onchange('unit_id','unit_from','unit_to','year_rent','duration')
	def onchange_unit_values(self):
		if self.unit_from and self.unit_to:
			d1 = datetime.strptime(str(self.unit_from), "%Y-%m-%d")
			d2 = datetime.strptime(str(self.unit_to), "%Y-%m-%d")
			free = self.free_unit_mth
			d3 = d1 + timedelta(days=free)
			no_of_leapyear = self.leapyr(str(d1),str(d2))
			tdays = (d2 - d1).days
			tdays = tdays + 1
			rdays = (d2 - d3).days
			no_of_months = self.od_diff_month(d2,d3)
		#            no_of_years = self.od_get_no_of_years(d2,d3)[0]
			rdays = ((rdays + 1) - no_of_leapyear)
			yr_rent =0
			if self.unit_sqft >0:
				if self.duration =='yr':
					yr_rent = ((self.unit_sqft * self.net_area) / 365) * tdays
				else:
	#                    yr_rent = (((self.unit_sqft * self.net_area) *12) / 365) * tdays
					yr_rent = (self.unit_sqft * self.net_area) * no_of_months
					self.year_rent = yr_rent
					self.unit_rent = yr_rent - self.line_disc
			if self.list_rent >0:
				if self.duration =='yr':
					yr_rent = (self.list_rent / 365) * tdays
				else:
			#                    yr_rent = ((self.list_rent * 12 ) / 365) * tdays
					yr_rent = self.list_rent * no_of_months
					self.year_rent = yr_rent
					self.unit_rent = yr_rent - self.line_disc
			conval = yr_rent
			# if self.percent >0 and conval >0:
			# 	conval = yr_rent + ((yr_rent * self.percent) / 100)
			if conval and tdays and self.duration =='yr':
				self.year_rent = ((conval/tdays) * rdays) 
				self.unit_rent = ((conval/tdays) * rdays) - self.line_disc

# Contract Payments
class PropertyAgreePayment(models.Model):
	_name = 'property.agree.payment'
	_description = "Agreement Payment"
	
	
	
	#@api.multi
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
		cont_id = cheque_obj.agree_id and cheque_obj.agree_id.id
		submit = cheque_obj.submit
		analytic_id = cheque_obj.agree_id.analytic_id and cheque_obj.agree_id.analytic_id.id
		cost_center = cheque_obj.agree_id.build_id and cheque_obj.agree_id.build_id.maintain_cc_id and cheque_obj.agree_id.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
			
		unit_line = cheque_obj.agree_id.unit_line
		for u_line in unit_line:
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
		old_lines = []
		partner_id = cheque_obj.partner_id and cheque_obj.partner_id.id
		cheque_obj.name = old_name
		recivable_acc_id = cheque_obj.partner_id.property_account_payable_id.id
#    	self.env['property.cont.payment'].create({'journal_id':journal_id,'name':'0000','date':date,'deposit':deposit,'amount':amount,'cont_id':cont_id,'submit':submit,'partner_id':partner_id})
		od_debit =  (0,0,{'account_id':recivable_acc_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':old_name,'credit':0.0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
		od_credit =  (0,0,{'account_id':recivable_acc_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':old_name,'credit':amount,'debit':0.0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})

		old_lines.append(od_credit)
		old_lines.append(od_debit)
		analytic_obj = cheque_obj.agree_id.analytic_id

		result = self.env['account.move'].create({'journal_id':journal_id,'ref':cheque_obj.agree_id.name,'line_ids':old_lines})
		cheque_obj.replaced_move_id = result.id
		result.post()    
	
	
  
	
	
	
	

	#@api.one
	@api.depends('agree_id','name')
	def _get_partner(self):
		agree_id = self.agree_id
		if agree_id:
			self.partner_id = self.agree_id.supplier_id.id or False
			
	#@api.multi
	def od_agree_replace_cheque(self):
		if len(self._context.get('active_ids', [])) > 1:
			raise Warning("you cannot select two record at a time") 
		domain = []
		action = self.env.ref('property_management.action_replace_check_wiz_agreement')
		result = action.read()[0]
		ctx = dict()
		value = self.env['property.agree.payment'].browse(self._context.get('active_ids', [])[0]).amount
		if self.env['property.agree.payment'].browse(self._context.get('active_ids', [])[0]).od_state == 'replaced':
			raise Warning("already replaced")
			
		ctx.update({
			'default_payment_id': self._context.get('active_ids', [])[0],
			'default_cheque_value':value
		})
		 
		result['context'] = ctx       
		return result
			
			
			
	@api.model
	def create(self,vals):
		cont_id = vals.get('agree_id')
		cont_obj = self.env['property.agreement'].browse(cont_id)
		build_id = cont_obj.build_id and cont_obj.build_id.id
		vals['property_id'] = build_id
		return super(PropertyAgreePayment,self).create(vals)                
			

	name = fields.Char(string="Number", required=True)
	date = fields.Date(string="Date", required=True)
	journal_id = fields.Many2one('account.journal', string='Journal', required=True)
	deposit = fields.Float(string="Deposit", required=True)
	amount = fields.Float(string="Amount", required=True)
	cust_bank_id = fields.Many2one('property.bank', string="Issue Bank")
	ref = fields.Char(string="Reference")
	submit = fields.Selection([('hand','In Hand'),('bank','Deposited')], string="Submit",default='hand')
	move_id = fields.Many2one('account.move',string="Journal", track_visibility='onchange')
	ret_date = fields.Date(string="Ret. Date")
	ret_charge = fields.Float(string="Charge")
	rev_move_id = fields.Many2one('account.move',string="Retn. JV", track_visibility='onchange')
	sub_date = fields.Date(string="Sub.Date")
	type = fields.Selection([
		('deposit', 'Deposit'),
		('payment', 'Payment'),
		('commission_paid', 'Commission Paid'),
		('commission_received', 'Commission Received'),
		], string='Status',default='payment')
	sub_move_id = fields.Many2one('account.move',string="ReSub. JV", track_visibility='onchange')
	partner_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange', store=True, compute="_get_partner")
	agree_id = fields.Many2one('property.agreement', ondelete='cascade', string="Contract")
	property_id = fields.Many2one('property.master', ondelete='cascade', string="Building")
	replaced_move_id = fields.Many2one('account.move', string='Replaced Entry')
	od_state = fields.Selection([
		('draft', 'Draft'),
		('cancel', 'Cancel'),
		('posted', 'Posted'),
		('replaced', 'Replaced'),
		], string='Status',default='draft')
	
	# Bank Deposit Flag

	def bank_deposit(self):
		self.write({'submit':'bank'})
	#@api.multi
	def payment_account_move(self):
		payable_acc_id = self.partner_id and self.partner_id.property_account_payable_id and self.partner_id.property_account_payable_id.id
		self.ensure_one()
		get_param = self.env['ir.config_parameter'].sudo().get_param

		cost_account_id = get_param('ag_property_maintainence.agreement_advance_account_id') or False
		cost_account_id = ast.literal_eval(cost_account_id)
		cheque_account_id = get_param('ag_property_maintainence.payment_account_id') or False
		cheque_account_id = ast.literal_eval(cheque_account_id)

		bank_acc_id = self.journal_id and self.journal_id.default_debit_account_id.id
		date = self.date
		partner_id = self.agree_id.supplier_id and self.agree_id.supplier_id.id
		move_vals = {'journal_id':self.journal_id and self.journal_id.id,'date':date,'ref': str(self.agree_id.name)}
		analytic_id = self.agree_id.analytic_id and self.agree_id.analytic_id.id or False
		cost_center = self.agree_id.build_id and self.agree_id.build_id.maintain_cc_id and self.agree_id.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
			
		unit_line = self.agree_id.unit_line
		for u_line in unit_line:
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
		name = self.name
		amount = self.amount
		line_vals = []
		line1 = (0,0,{'account_id':payable_acc_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
		line2 = (0,0,{'account_id':cost_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
		line3 = (0,0,{'account_id':cheque_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':amount,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
		line4 = (0,0,{'account_id':bank_acc_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
		line_vals.append(line1)
		line_vals.append(line2)
		line_vals.append(line3)
		line_vals.append(line4)
		move_vals['line_ids'] = line_vals
		move_pool = self.env['account.move']
		move = move_pool.create(move_vals)
		move.post()
		self.move_id = move.id	
		self.od_state = 'posted'	
#		

	
	#@api.multi
	def payment_move(self):
		if self.agree_id.state in ('draft','post','renew'):
			raise Warning("Contract not Confirmed !!!!") 
		elif self.move_id:
			raise Warning("Posted Journal Exist !!!!")
		else:
			self.payment_account_move()
	
	#@api.multi
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

	#@api.multi
	def reverse_payment_move(self):
		cost_center = self.agree_id.build_id and self.agree_id.build_id.maintain_cc_id and self.agree_id.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
			
		unit_line = self.agree_id.unit_line
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

			partner_id = self.agree_id.customer_id and self.agree_id.customer_id.id or False
			analytic_id = self.agree_id.analytic_id and self.agree_id.analytic_id.id or False
			partner_account_id = False
			if partner_id:
					partner = self.env['res.partner'].browse(partner_id)
					partner_account_id = partner.property_account_receivable_id.id
			acmove_line = self.env['account.move.line']
			line_ids = acmove_line.search([('move_id','=',ac_move_id.id)])
			move_vals = {'journal_id':journal_id,'date':date,'ref':_('reversal of: ') + ac_move_id.name}
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


				analytic_id = self.agree_id.analytic_id and self.agree_id.analytic_id.id or False
				project_id = self.env['project.project'].search([('analytic_account_id','=',analytic_id)],limit=1)
				task_pool = self.env['project.task']
				task_val = {'name':self.agree_id.name + _(' - Cheque Return'),'project_id':project_id.id,'user_ids':[(6,0,[payment_user_id])]}
				task = task_pool.create(task_val)

			else:
				raise Warning("Account/Jounral not set !!!!")
		
# Contract Account

class PropertyAgreeAccountdetail(models.Model):
	_name = 'property.agree.account.detail'
	_description = "Agreement Account Detail"
	_order = "unit_id,date asc"
	def dummy(self):
		return True
	#@api.one
	@api.depends('agree_id','name')
	def _get_partner(self):
		agree_id = self.agree_id
		if agree_id:
			self.partner_id = self.agree_id.supplier_id.id or False
	name = fields.Char(string="Month")
	date = fields.Date(string="Date", required=True)
	unit_id = fields.Many2one('property.unit',string="Unit")
	revenue = fields.Float(string="Income", required=True)
	move_id = fields.Many2one('account.move',string="Journal", track_visibility='onchange')
	partner_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange', store=True, compute="_get_partner")
	agree_id = fields.Many2one('property.agreement', ondelete='cascade', string="Contract")
	desc = fields.Char(string="Desc")
	
class PropertyAgreeAccount(models.Model):
	_name = 'property.agree.account'
	_description = "Agreement Account"
	_order = "date asc"
	def dummy(self):
	 
		return True

	#@api.one
	@api.depends('agree_id','name')
	def _get_partner(self):
		agree_id = self.agree_id
		if agree_id:
			self.partner_id = self.agree_id.supplier_id.id or False

	name = fields.Char(string="Month")
	date = fields.Date(string="Date", required=True)
	revenue = fields.Float(string="Income", required=True)
	move_id = fields.Many2one('account.move',string="Journal", track_visibility='onchange')
	partner_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange', store=True, compute="_get_partner")
	agree_id = fields.Many2one('property.agreement', ondelete='cascade', string="Contract")
	desc = fields.Char(string="Desc")
	
	od_state = fields.Selection([
		('draft', 'Draft'),
		('cancel', 'Cancel'),
		('posted', 'Posted'),
		], string='Status',default='draft')
	#@api.one
	def get_month_day_range(self,date):
		date = datetime.strptime(str(date), '%Y-%m-%d')
		last_day = date + relativedelta(day=1, months=+1, days=-1)
		first_day = date + relativedelta(day=1)
		return  str(last_day)    #first_day,


	#@api.multi
	def revenue_move(self):
		cost_center = self.agree_id.build_id and self.agree_id.build_id.maintain_cc_id and self.agree_id.build_id.maintain_cc_id.id
		unit_cost_center = []
		floor_cost_center = []
			
		unit_line = self.agree_id.unit_line
		for u_line in unit_line:
			unit_cost_center.append(u_line.unit_id.unit_maintain_cc_id.id)
			floor_cost_center.append(u_line.unit_id.floor_id.floor_maintain_cc_id.id)
		if self.agree_id.state in ('draft','post','renew'):
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
			revenue_account_id = get_param('ag_property_maintainence.revenue_account_id') or False
			revenue_account_id = ast.literal_eval(revenue_account_id)
			advance_account_id = get_param('ag_property_maintainence.advance_account_id') or False
			advance_account_id = ast.literal_eval(advance_account_id)
			cost_account_id = get_param('ag_property_maintainence.cost_account_id') or False
			cost_account_id = ast.literal_eval(cost_account_id)
			prepaid_account_id = get_param('ag_property_maintainence.prepaid_account_id') or False
			prepaid_account_id = ast.literal_eval(prepaid_account_id)
			agreement_advance_account_id = get_param('ag_property_maintainence.agreement_advance_account_id') or False
			agreement_advance_account_id = ast.literal_eval(agreement_advance_account_id)
			agreement_costing_journal_id = get_param('ag_property_maintainence.agreement_costing_journal_id') or False
			agreement_costing_journal_id = ast.literal_eval(agreement_costing_journal_id)


			journal_id = revenue_journal_id
			partner_id = self.agree_id.supplier_id and self.agree_id.supplier_id.id or False
			analytic_id = self.agree_id.analytic_id and self.agree_id.analytic_id.id or False
			partner_account_id = False
			if partner_id:
					partner = self.env['res.partner'].browse(partner_id)
					partner_account_id = partner.property_account_payable_id.id
			name = self.name
			amount = self.revenue
			date = self.date
			move_vals = {'journal_id':agreement_costing_journal_id,'date':date}
			move_line = []
			if cost_account_id and prepaid_account_id and agreement_advance_account_id and agreement_costing_journal_id:
				#revenue_line_vals = (0,0,{'account_id':revenue_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':amount,'debit':0.0})

				
				#move_line.append(revenue_line_vals)
			   # move_line.append(deffered_line_vals)
			   # move_line.append(advance_line_vals)
				#move_line.append(customer_line_vals)
				m_start_date = str(self.get_month_day_range(date))[:10]#[0][0]
				m_end_date = str(self.get_month_day_range(date))[:10]#[0][1]
				details_line_ids = self.env['property.agree.account.detail'].search([('agree_id','=',self.agree_id.id),('date','>=',m_start_date),('date','<=',m_end_date)])
				tot_revenue = 0
				for d_line in details_line_ids:
					product_id = d_line.unit_id and d_line.unit_id.product_id and d_line.unit_id.product_id.id or False
					revenue_line_vals = (0,0,{'account_id':cost_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':round(d_line.revenue,2),'product_id':product_id,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
					move_line.append(revenue_line_vals)
					tot_revenue = tot_revenue + round(d_line.revenue,2)
				customer_line_vals =  (0,0,{'account_id':partner_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':tot_revenue,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				deffered_line_vals =  (0,0,{'account_id':prepaid_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':tot_revenue,'debit':0,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				advance_line_vals =  (0,0,{'account_id':agreement_advance_account_id,'partner_id':partner_id,'analytic_account_id':analytic_id,'name':name,'credit':0,'debit':tot_revenue,'maintain_cc_id':cost_center,'unit_maintain_cc_id':[(6,0, unit_cost_center)],'floor_maintain_cc_id':[(6,0, floor_cost_center)]})
				move_line.append(deffered_line_vals)
				move_line.append(advance_line_vals)
				move_line.append(customer_line_vals)           
				move_vals['line_ids'] = move_line
				move_pool = self.env['account.move']
				move = move_pool.create(move_vals)
				move_id = move.id
				move.post()
				self.od_state = 'posted'
				self.write({'move_id':move_id})
			else:
				raise Warning("Account/Jounral not set  !!!!")

# Contract Attachment
class PropertyAgreeAttachment(models.Model):
	_name = 'property.agree.attachment'
	_description = "Agreement Attachment"

	name = fields.Char(string="Name", required=True)
	attachment_type_id = fields.Many2one('property.attachment.type', string="Type", required=True)
	attachment = fields.Binary(string="Attachment")
	remarks = fields.Text(string="Remarks")
	agree_id = fields.Many2one('property.agreement', ondelete='cascade', string="Contract")

# Contract Closure
class PropertyAgreeClosure(models.Model):
	_name = 'property.agree.closure'
	_description = "Agreement Closure"


	agree_id = fields.Many2one('property.agreement', ondelete='cascade', string="Contract")
	
	
	
	name = fields.Char(string="Head", required=True)
	account_id = fields.Many2one('account.account', string='Account', required=True)
	balance = fields.Float(string="Balance",)
	generate_entries = fields.Boolean('Generate Entries')
	generate_balance = fields.Float('Generate Entries')

# Contract Settle
class PropertyAgreeSettle(models.Model):
	_name = 'property.agree.settle'
	_description = "agreement Settle"
#    _order = "date asc"

	name = fields.Char(string="Reason", required=True)
	account_id = fields.Many2one('account.account', string='Account', required=True)
	amount = fields.Float(string="Amount", required=True)
	agree_id = fields.Many2one('property.agreement', ondelete='cascade', string="Contract")
	

class PropertyUtilityType(models.Model):
	_name = 'property.utility.type'
	_description = "Utility Type"
	name = fields.Char(string='Name')    
	account_id = fields.Many2one('account.account', string='Account')
	journal_id = fields.Many2one('account.journal', string='Journal')
	product_id = fields.Many2one('product.product', string='Product')
	trhr = fields.Float(string="TRHR")
	vat_id = fields.Many2one('account.tax', string='Vat')


   
class PropertyUtilityLine(models.Model):
	_name = 'property.utility.line'
	_description = "Utility Lines"
	_order = "id desc"


	
	
		   
	@api.model
	def create(self,vals):
		name = self.env['ir.sequence'].next_by_code('property.utility.line')
		vals['name'] = name
		
		return super(PropertyUtilityLine,self).create(vals)    
	#@api.one
	@api.depends('qty','unit_price','admin_charge')
	def _get_total(self):
		qty = self.qty
		# self.total = float(qty * self.unit_price) + self.admin_charge

		self.total = float(qty * self.type_id.trhr * self.unit_price) + self.admin_charge
			
	
	@api.onchange('previous_read','present_read')
	def present_read_onchange(self):
		if self.previous_read or self.present_read:
			self.qty = self.present_read - self.previous_read
	
	type_id = fields.Many2one('property.utility.type', string='Type')
	from_date = fields.Date(string='From Date')
	to_date = fields.Date(string='To Date')
	product_id = fields.Many2one('product.product', string='Product')
	name = fields.Char('Name',default="/")

	previous_read = fields.Float(string="Previous Read")
	present_read = fields.Float(string="Present Read")
	qty = fields.Float(string="Consumption")
	unit_price = fields.Float(string="Unit Price")
	# TRHR = fields.Float(string="TRHR")
	admin_charge = fields.Float(string="Admin.C")
	remarks = fields.Char(string="Remarks")
	state = fields.Selection([('draft', 'Draft'),('post','Post')], string='Status',default='draft')
	total = fields.Float(string="Total", store=True, compute="_get_total")


	
