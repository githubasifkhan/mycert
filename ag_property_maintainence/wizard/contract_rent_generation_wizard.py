from odoo import models, fields, api
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo import exceptions, _
from odoo.exceptions import Warning
import datetime as dt
from datetime import  timedelta, tzinfo, time, date, datetime
from dateutil.relativedelta import relativedelta 

class ContractrentGeneration(models.TransientModel):
	_name = 'contract.rent.generation.wiz'
	_description = 'ContractrentGeneration'

	#@api.one
	def no_of_years_intersect(self,ds,dt):
		from datetime import datetime
		d1 = datetime.strptime(str(ds), "%Y-%m-%d")
		d2 = datetime.strptime(str(dt), "%Y-%m-%d")
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
			
			
	#@api.one
	def recompute_no_of_years(self,ds,dt):
		from datetime import datetime
		d1 = datetime.strptime(str(ds), "%Y-%m-%d")
		d2 = datetime.strptime(str(dt), "%Y-%m-%d")
		days = abs((d2 - d1).days)+1
		if days <= 370:
			return 1
		elif days > 370 and days <=750:
			return 2
		elif days > 750 and days<=1100:
			return 3
		elif days > 1100 and days<=1465:
			return 4
		else:
			return 5
			
			
		
	#@api.one
	def get_add_year(self,ds,free):
		start_dt = datetime.strptime(str(ds), "%Y-%m-%d")
		free = free
		rent_dt = start_dt + relativedelta(years=free)
		new_date = rent_dt.strftime("%Y-%m-%d")
		return new_date


	#@api.one
	def get_min_condate(self,ds,free):
		start_dt = datetime.strptime(str(ds), "%Y-%m-%d")
		free = free
		rent_dt = False
		if free > 0:
			print 
			
			rent_dt = start_dt + timedelta(days=free)
		else:
			rent_dt = start_dt + timedelta(days=free-1)       		
		new_date = rent_dt.strftime("%Y-%m-%d")
		return new_date
		
	def days_between(self,d1, d2):
		from datetime import datetime
		d1 = datetime.strptime(str(d1), "%Y-%m-%d")
		d2 = datetime.strptime(str(d2), "%Y-%m-%d")
		val = abs((d2 - d1).days)+1
		if val==364 or val==366:
			return 365
			
		return val
		
	#@api.one
	def get_adjust_start_date(self,ds,con_start):
		con_start = datetime.strptime(con_start, '%Y-%m-%d').strftime('%d-%m-%Y')
		con_start_without_year = str(con_start)[:6]
		ds_year = ds[:4]
		new_date = con_start_without_year + ds_year
		new_date = datetime.strptime(new_date, '%d-%m-%Y').strftime('%Y-%m-%d')
		return str(new_date)
	#@api.one
	def get_end_date(self,d1):
		d1 = datetime.strptime(str(d1), '%Y-%m-%d')
		d1 = d1 + relativedelta(years=1)
		d1 = d1 + timedelta(days=-1)
		return str(d1)
		
	#@api.one
	def get_dummy_end_date(self,d1):
		d1 = datetime.strptime(str(d1)[:10], '%Y-%m-%d')
		d1 = d1 + timedelta(days=1)
		return str(d1)		
		
		
		
	#@api.one
	def get_month_end_date(self,d1):
		d1 = datetime.strptime(str(d1)[:10], '%Y-%m-%d')
		d1 = d1 + relativedelta(months=1)
		d1 = d1 + timedelta(days=-1)
		return str(d1)
		
	#@api.one
	def get_no_of_years(self,d1,d2):
		d1 = datetime.strptime(str(d1), '%Y-%m-%d')
		d2 = datetime.strptime(str(d2), '%Y-%m-%d')
		diffyears = d2.year - d1.year
		if diffyears == 0:
			diffyears = 1	
		return diffyears
	#@api.one
	def is_full_year(self,d1,d2):
	
		d1 = datetime.strptime(str(d1), '%Y-%m-%d')#.strftime('%d-%m-%Y')
		d2 = datetime.strptime(str(d2), '%Y-%m-%d')#.strftime('%d-%m-%Y')

		line1 = str(d1)[:5]
		line2 = str(d2)[:5]


		if line1 == '01-01' and line2 == '31-12':
			return True
		else:
			return False

	#@api.one
	def get_no_of_months(self,d1,d2):
		d1 = datetime.strptime(str(d1), '%Y-%m-%d')
		d2 = datetime.strptime(str(d2), '%Y-%m-%d')
		r = relativedelta.relativedelta(date2, date1)
		return r.months
		
	#@api.one
	def get_months_between_dates(self,d1,d2):
		from datetime import datetime
		d1 = datetime.strptime(str(d1), "%Y-%m-%d")
		d2 = datetime.strptime(str(d2), "%Y-%m-%d")
		val = float(abs((d2 - d1).days)+1) / float(30)
		val = int(round(val)) 
		return val   
		
	#@api.one
	def get_add_months(self,d1,var):
		d1 = datetime.strptime(str(d1), '%Y-%m-%d')
		d1 = d1 + relativedelta(months=var)
		return d1
	#@api.one
	def od_diff_month(self,d1, d2):
		from datetime import datetime
		d1 = datetime.strptime(str(d1)[:10], '%Y-%m-%d')
		d2 = datetime.strptime(str(d2)[:10], '%Y-%m-%d')
		return abs((d1.year - d2.year)*12 + d1.month - d2.month) 	
		
		
	#@api.one
	def get_adjust_end_date(self,ds,con_end,line_to_date):
		line_to_date = datetime.strptime(line_to_date, '%Y-%m-%d').strftime('%d-%m-%Y')
		line_to_date_without_year = str(line_to_date)[:6]
		ds_year = ds[:4]
		con_end = datetime.strptime(con_end, '%Y-%m-%d').strftime('%d-%m-%Y')
		con_end_without_year = str(con_end)[:6]
		new_date = line_to_date_without_year + ds_year
		new_date = datetime.strptime(new_date, '%d-%m-%Y').strftime('%Y-%m-%d')
		return str(new_date)
	def generate_contract_rent(self):
		contract_obj = self.env['property.contract']
		contract = self.contract_id
		start_date = contract.date_start
		con_end_date = contract.date_stop
	   # self.contract_id = contract and contract.id
		contract_total_val = contract.total_value
		unit_line = contract.unit_line
		total_value = 0
		if self.wiz_line:
			raise Warning("already generated") 
		for line in unit_line:
			min_dt = line.unit_from
			
			if line.free_unit_mth:
				min_dt = self.get_min_condate(line.unit_from,line.free_unit_mth)[0]
			od_s_date = min_dt
			line_end_date = line.unit_to
			no_of_months = [(self.od_diff_month(od_s_date,line_end_date) )][0] or 1
			if line.duration == 'yr':
				full_year = [self.is_full_year(od_s_date,line_end_date)][0]
				print ("ddddddddddddddddd",full_year)
				no_y = [self.get_no_of_years(od_s_date,line_end_date)][0]
				if full_year:
					print ("ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc")
					no_y = [self.recompute_no_of_years(od_s_date,line_end_date)][0]
					
				print ("ffffffffffffffffffffffffffffffno_y",no_y)
				
				for yr in range(0,no_y):
					start_date = [self.get_add_year(od_s_date,yr)][0]
					end_date = [self.get_end_date(start_date)][0]
					vals = {'wiz_id':self.id,
						'start_date':start_date,
						'end_date':end_date,
						'rent_amount':float(line.unit_rent)/float(no_y),
						'vat':float(line.vat)/float(no_y),
					}
					self.env['contract.rent.generation.wiz.line'].create(vals)
			else:
				no_y = self.no_of_years_intersect(od_s_date,line_end_date)[0]
				for yr in range(0,no_y):
					start_date = self.get_add_year(od_s_date,yr)[0]
					
					end_date = self.get_end_date(start_date)[0]

					if end_date > con_end_date:
						end_date = con_end_date
					dummy_end_date = self.get_dummy_end_date(end_date)[0]
					months_diff = float(self.od_diff_month(start_date,dummy_end_date)[0]) or 1
					amount = float(float(line.unit_rent) / float(no_of_months)) * months_diff
#            	no_m = self.get_months_between_dates(od_s_date,line_end_date)[0]
#            	for mn in range(0,no_m):
#				start_date = self.get_add_months(str(od_s_date),mn)[0]
#            	end_date = self.get_month_end_date(start_date)[0]
					vals = {'wiz_id':self.id,
						'start_date':start_date,
						'end_date':end_date,
						'rent_amount':amount,
					}
					self.env['contract.rent.generation.wiz.line'].create(vals)
#        return {
#            'name': _('Rent'),
#            'view_type': 'form',
#            'view_mode': 'form',
#            'res_model': 'contract.rent.generation.wiz',
#            'res_id': self.id,
#            'target': 'new',
#            'type': 'ir.actions.act_window',
#        }
	  
					
		self.create_rent_line()
					
		
	def create_rent_line(self):
		wiz_line = self.wiz_line
		contact_id = self.contract_id and self.contract_id.id
		if self.contract_id.rent_line:
			self.contract_id.rent_line.unlink()
		contract_tot = 0
		contract_vat=0
		contract_obj = self.env['property.contract']
		contract = contract_obj.browse(contact_id)
		con_start_date = contract.date_start
		con_end_date = contract.date_stop
		contract_unit_line = contract.unit_line
		for uni_line in contract_unit_line:
			contract_tot = contract_tot + uni_line.unit_rent
			contract_vat=contract_vat+uni_line.vat
		
		
		dates = []
		rent_unit_ids = []
		for line in wiz_line:
			dates.append(line.start_date)
		dates = list(set(dates))
		for date in dates:
			amount = 0
			tax=0
			vals = {}
			line_ids = self.env['contract.rent.generation.wiz.line'].search([('wiz_id','=',self.id),('start_date','=',str(date))])
			date_end = False
			for w_line in line_ids:
				tax=tax+w_line.vat
				amount = amount + w_line.rent_amount
				date_end = w_line.end_date
			vals = {'date_from':date,
					'date_to':date_end,
					'rent':amount,
					'od_vat_rent':tax,
					'cont_id':contact_id}
			rent_line_id = self.env['property.cont.rent'].create(vals)
			rent_unit_ids.append(rent_line_id)
		tot_new = 0
		for new_line in rent_unit_ids:
			tot_new = tot_new + new_line.rent
		if self.contract_id.rent_line:
			max_id = max(line.id for line in self.contract_id.rent_line)
			line_obj = self.env['property.cont.rent'].browse(max_id)
			rent = line_obj.rent
			diff = contract_tot - tot_new
			line_obj.write({'rent':rent + diff})
			contract.get_monthly_rent()
	name = fields.Char(string="Name",)
	wiz_line = fields.One2many('contract.rent.generation.wiz.line', 'wiz_id', string='Wiz Line',)
	contract_id = fields.Many2one('property.contract','Contract')
class ContractrentGenerationline(models.TransientModel):
	_name = 'contract.rent.generation.wiz.line'
	_description = 'ContractrentGenerationline'
	_order = 'start_date asc'

	start_date = fields.Date('Start Date')
	unit_id = fields.Many2one('property.unit',string="Unit")
	end_date = fields.Date('End Date')
	wiz_id = fields.Many2one('contract.rent.generation.wiz',string='Wiz')
	type = fields.Char(string='Yearly Or Monthly')
	rent_amount = fields.Float('Amount')
	vat=fields.Float('Vat')
	org_start_date = fields.Date('Net Start Date')
	org_end_date = fields.Date('Net End Date')
	line_to_date = fields.Date('Line To Date')
	free_days = fields.Float('Free Days')
	
	
	
	


