from odoo import models, fields, api
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo import exceptions, _
from odoo.exceptions import Warning
import datetime as dt
from datetime import  timedelta, tzinfo, time, date, datetime
from dateutil.relativedelta import relativedelta 

class AgreementRevenueGeneration(models.TransientModel):
	_name = 'agreement.revenue.calculation.wizard'
	_description = 'AgreementRevenuetGeneration'

	#
	def no_of_years_intersect(self,ds,dt):
		from datetime import datetime
		d1 = datetime.strptime(ds, "%Y-%m-%d")
		d2 = datetime.strptime(dt, "%Y-%m-%d")
		days = abs((d2 - d1).days)+1
		if days <= 366:
			return 1
		elif days > 366 and days <=730:
			return 2
		elif days > 730 and days<=1096:
			return 3
		elif days > 1096 and days<=1460:
			return 4
		else:
			return 5
    
	wiz_line = fields.One2many('agreement.revenue.calculation.wizard.line', 'wiz_id', string='Wiz Line',)
	contract_id = fields.Many2one('property.agreement','Agreement')
	name = fields.Char(string="Name",)

	
	def get_add_year(self,ds,free):
		start_dt = datetime.strptime(str(ds), "%Y-%m-%d")
		free = free
		rent_dt = start_dt + relativedelta(years=free)
		new_date = rent_dt.strftime("%Y-%m-%d")
		return new_date
	
	
	#
	def get_min_condate(self,ds,free):
		start_dt = datetime.strptime(ds, "%Y-%m-%d")
		free = free
		rent_dt = False
		if free > 0:
			print ('--true--')
			
			rent_dt = start_dt + timedelta(days=free)
		else:
			rent_dt = start_dt + timedelta(days=free-1)       		
		new_date = rent_dt.strftime("%Y-%m-%d")
		return new_date
        
	def days_between(self,d1, d2):
		from datetime import datetime
		d1 = datetime.strptime(d1, "%Y-%m-%d")
		d2 = datetime.strptime(d2, "%Y-%m-%d")
		val = abs((d2 - d1).days)+1
		if val==364 or val==366:
			return 365
			
		return val
        
	#
	def get_adjust_start_date(self,ds,con_start):
		con_start = datetime.strptime(con_start, '%Y-%m-%d').strftime('%d-%m-%Y')
		con_start_without_year = str(con_start)[:6]
		ds_year = ds[:4]
		new_date = con_start_without_year + ds_year
		new_date = datetime.strptime(new_date, '%d-%m-%Y').strftime('%Y-%m-%d')
		return str(new_date)
	#
	def get_end_date(self,d1):
		d1 = datetime.strptime(d1, '%Y-%m-%d')
		d1 = d1 + relativedelta(years=1)
		d1 = d1 + timedelta(days=-1)
		return str(d1)
	#
	def get_month_end_date(self,d1):
		d1 = datetime.strptime(str(d1)[:10], '%Y-%m-%d')
		d1 = d1 + relativedelta(months=1)
		d1 = d1 + timedelta(days=-1)
		return str(d1)
		
	#
	def get_no_of_years(self,d1,d2):
		d1 = datetime.strptime(str(d1), '%Y-%m-%d')
		d2 = datetime.strptime(str(d2), '%Y-%m-%d')
		diffyears = d2.year - d1.year
		if diffyears == 0:
			diffyears = 1	
		return diffyears 
	#
	def get_add_month(d1,var):
		d1 = datetime.strptime(d1, '%Y-%m-%d')
		d1 = d1 + relativedelta(months=var)
		return d1
	#
	def get_no_of_months(self,d1,d2):
		d1 = datetime.strptime(d1, '%Y-%m-%d')
		d2 = datetime.strptime(d2, '%Y-%m-%d')
		r = relativedelta.relativedelta(date2, date1)
		return r.months
		

	#
	def get_add_months(self,d1,var):
		d1 = datetime.strptime(str(d1), '%Y-%m-%d')
		d1 = d1 + relativedelta(months=var)
		return d1    	
		
	
		
		
	#
	def get_adjust_end_date(self,ds,con_end,line_to_date):
		line_to_date = datetime.strptime(line_to_date, '%Y-%m-%d').strftime('%d-%m-%Y')
		line_to_date_without_year = str(line_to_date)[:6]
		ds_year = ds[:4]
		con_end = datetime.strptime(con_end, '%Y-%m-%d').strftime('%d-%m-%Y')
		con_end_without_year = str(con_end)[:6]
		new_date = line_to_date_without_year + ds_year
		new_date = datetime.strptime(new_date, '%d-%m-%Y').strftime('%Y-%m-%d')
		return str(new_date)
	#   
	def get_month_day_range(self,date):
		date = datetime.strptime(str(date), '%Y-%m-%d')
		last_day = date + relativedelta(day=1, months=+1, days=-1)
		first_day = date + relativedelta(day=1)
		return first_day,last_day
		
	#   
	def get_months_between_dates(self,d1,d2):
		from datetime import datetime
		d1 = datetime.strptime(str(d1)[:10], "%Y-%m-%d")
		d2 = datetime.strptime(str(d2)[:10], "%Y-%m-%d")
		val = float(abs((d2 - d1).days)+1) / float(30)
		val = int(round(val)) 
		return val
		
	#   
	def get_no_of_days_currentmonth(self,d1,d2):
		from datetime import datetime
		# d1 = datetime.strptime(str(d1)[:10], "%Y-%m-%d")
		# d2 = datetime.strptime(str(d2)[:10], "%Y-%m-%d")
		d1 = datetime.date(d1)
		d2 = datetime.date(d2)
		val = abs((d2 - d1).days)+1 
		return val
	#   
	def is_first_dayof_month(self,d1):
		date = datetime.strptime(str(d1), '%Y-%m-%d')
		first_day = date + relativedelta(day=1)
		if str(first_day)[:10] == d1:
			return True
		else:
			return False
	def revenue_split_monthly(self): 
		revenue_lines = self.contract_id.account_line
		revenue_detail_lines = self.contract_id.account_detail_line
		cont_id = self.contract_id.id
		if revenue_lines:
			revenue_lines.unlink()
		used_ids = []
		for line in revenue_detail_lines:
			print ("YYYYYYYYYYYYYYYYYYYYYYYYY",line)
			if line not in used_ids:
				date = line.date
				m_start_date = str(self.get_month_day_range(date)[0])#[:10]#[0][0]
				m_end_date = str(self.get_month_day_range(date)[1])#[:10]#[0][1]
				same_month_revenue_ids = self.env['property.agree.account.detail'].search([('agree_id','=',cont_id),('date','>=',m_start_date),('date','<=',m_end_date)])
				name = self.get_month_day_range(date)[0]#[0][1]
				name = name.strftime("%B")
				amount = 0
		
				for rev_line in same_month_revenue_ids:
					if rev_line not in used_ids:
						used_ids.append(rev_line)
						amount = amount + round(rev_line.revenue,3)
				vals = {'agree_id':cont_id,'date':m_end_date,'revenue':round(amount,2),'name':name}
				print ("00000000000000000000000000000000000000000000t0--------------",vals)
				self.env['property.agree.account'].create(vals)
					
				
    	 	                   
	def revenue_split_monthly_unitwise(self):  	
		wiz_lines = self.wiz_line
		contract_obj = self.env['property.agreement']
		contract = self.contract_id.id
		revenue_detail_lines = self.contract_id.account_detail_line
		if revenue_detail_lines:
			revenue_detail_lines.unlink()
		for line in wiz_lines:
			no_of_months = self.get_months_between_dates(line.start_date,line.end_date)#[0]
			var = no_of_months
			is_first_dayof_month = self.is_first_dayof_month(line.start_date)#[0]
			if not is_first_dayof_month:
				var = var + 1
				
			for m in range(0,var):
				start_date = line.start_date
				start_date = str(self.get_add_months(start_date,m))[:10]#[0]
				end_date = line.end_date
				revenue = round(float(line.rent_amount)/float(no_of_months),2)
				s_month_start_date = self.get_month_day_range(start_date)[0]#[:10]#[0][0]
				s_month_end_date = self.get_month_day_range(start_date)[1]#[:10]#[0][1]
				e_month_start_date = self.get_month_day_range(end_date)[0]#[:10]#[0][0]
				e_month_end_date = self.get_month_day_range(end_date)[1]#[:10]#[0][1]
				desc = str(s_month_start_date) + "-" +str(s_month_end_date)
				if line.start_date and s_month_start_date and line.start_date > datetime.date(s_month_start_date):
					noofdays_currentmonth = 1
					noofdays_currentmonth = int(self.get_no_of_days_currentmonth(s_month_start_date, s_month_end_date))  # [0]
					new_val = float(revenue) / float(noofdays_currentmonth)

					considering_days = int(self.get_no_of_days_currentmonth(datetime.combine(line.start_date, datetime.min.time()),
														 s_month_end_date))  # [0]
					revenue = round(float(new_val) * considering_days, 2)



				if line.end_date and s_month_end_date and line.end_date < datetime.date(s_month_end_date):
					noofdays_currentmonth = 1
					noofdays_currentmonth = int(self.get_no_of_days_currentmonth(e_month_start_date,e_month_end_date))#[0]
					new_val = float(revenue) / float(noofdays_currentmonth)
					considering_days = int(self.get_no_of_days_currentmonth(e_month_start_date,datetime.combine(line.end_date,datetime.min.time())))  # [0]
					#[0]
					revenue = round(float(new_val) * considering_days,2)
					s_month_end_date = line.end_date


				unit_id = line.unit_id and line.unit_id.id
				vals = {'agree_id':contract,'unit_id':unit_id,'revenue':revenue,'date':s_month_end_date,'desc':desc
				}
				self.env['property.agree.account.detail'].create(vals)
		self.revenue_split_monthly()  			
			
    
    
	def generate_agreement_revenue(self):
		contract_obj = self.env['property.agreement']
		print ("11111111111111111111111111111111111111111111111111111111111000")
	  
		unit_line = self.contract_id.unit_line
		total_value = 0
		if self.wiz_line:
			raise Warning("already generated") 
		for line in unit_line:
			min_dt = line.unit_from
	#            if line.free_unit_mth:
	#            	min_dt = self.get_min_condate(line.unit_from,line.free_unit_mth)[0]
			od_s_date = min_dt
			line_end_date = line.unit_to
			if line.duration == 'yr' or line:
				print("11111111111111111111111111111111111111111111111",line)
				no_y = self.get_no_of_years(od_s_date,line_end_date)#[0]
				for yr in range(0,no_y):
					start_date = self.get_add_year(od_s_date,yr)#[0]
					end_date = self.get_end_date(start_date)#[0]
					vals = {'wiz_id':self.id,
						'unit_id':line.unit_id and line.unit_id.id,
						'start_date':start_date,
						'end_date':end_date,
						'rent_amount':float(line.year_rent)/float(no_y),
						'month_s_date':self.get_month_day_range(start_date)[0],#[0][0]
						'month_e_date':self.get_month_day_range(start_date)[1]#[0][1]
					}
					self.env['agreement.revenue.calculation.wizard.line'].create(vals)
	#            else: 
	#            	no_m = self.get_months_between_dates(od_s_date,line_end_date)[0]
	#            	for mn in range(0,no_m):
	#            		start_date = self.get_add_months(od_s_date,mn)[0]
	#            		end_date = self.get_month_end_date(start_date)[0]
	#            		vals = {'wiz_id':self.id,
	#                        'start_date':start_date,
	#            			'unit_id':line.unit_id and line.unit_id.id,
	#                        'end_date':end_date,
	#                        'rent_amount':float(line.unit_rent)/float(no_m),
	#            		}
	#            		self.env['agreement.revenue.calculation.wizard.line'].create(vals)          
	#        return {
	#            'name': _('Agreement Revenue'),
	#            'view_type': 'form',
	#            'view_mode': 'form',
	#            'res_model': 'agreement.revenue.calculation.wizard',
	#            'res_id': self.id,
	#            'target': 'new',
	#            'type': 'ir.actions.act_window',
	#        }            		
	
		self.revenue_split_monthly_unitwise()

	
class agreementrevenueGenerationline(models.TransientModel):
	_name = 'agreement.revenue.calculation.wizard.line'
	_description = 'agreement.revenue.calculation.wizard.line'
	_order = 'start_date asc'

	start_date = fields.Date('Start Date')
	month_s_date = fields.Date(string="Month Start Date")
	month_e_date = fields.Date(string="Month End Date")
	unit_id = fields.Many2one('property.unit',string="Unit")
	end_date = fields.Date('End Date')
	wiz_id = fields.Many2one('agreement.revenue.calculation.wizard',string='Wiz')
	type = fields.Char(string='Yearly Or Monthly')
	rent_amount = fields.Float('Amount')
	free_days = fields.Float('Free Days')


