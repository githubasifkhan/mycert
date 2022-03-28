from odoo import models, fields, api
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo import exceptions, _
from odoo.exceptions import Warning
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo import exceptions, _
from odoo.exceptions import Warning
import datetime as dt
from datetime import  timedelta, tzinfo, time, date, datetime
from dateutil.relativedelta import relativedelta 

class UnitOccupiedWizard(models.TransientModel):
	_name = 'unit.occupied.wizard'
	_description = 'unit.occupied.wizard'    

	date = fields.Date(string="Date",default=fields.Datetime.now)
	state = fields.Selection([
		('occupied', 'Occupied Units'),
		('vaccant', 'Available Units'),
		], string='Status',default='occupied')
	status = fields.Selection([
		('occupied', 'Occupied Units'),
		('vaccant', 'Vaccant Units'),
		('overstay', 'Overstay Units'),
		], string='Status',default='occupied')


	#@api.one
	def get_occupied_units(self):
		date = self.date
		all_units = self.env['property.unit'].search([])
		unit_ids = []
		
		for unit in all_units:
			line_id = False
			line_ids = []
		
			property_cont_unit_objs = self.env['property.cont.unit'].search([('unit_to','>=',date),('unit_id','=',unit.id)])
			if property_cont_unit_objs:
				for line in property_cont_unit_objs:
					
					line_ids.append(line and line.id)
					
			if line_ids:
				line_id = max(line_ids)
				line_obj = self.env['property.cont.unit'].browse(line_id)
				contract = line_obj.cont_id
				contract_state = line_obj.cont_id and line_obj.cont_id.state
				if contract_state != 'cancel':
					unit_ids.append(line_obj.unit_id.id)
						
		return list(set(unit_ids))
		
	#@api.one
	def get_all_units(self,all_units):
		unit_ids = []
		for unit in all_units:
			unit_ids.append(unit.id)
		return list(set(unit_ids))
		
		
		
		
	#@api.one
	def get_vacant_days(self,ds,dt):
		from datetime import datetime
		d1 = datetime.strptime(str(ds), "%Y-%m-%d")
		d2 = datetime.strptime(str(dt), "%Y-%m-%d")
		days = abs((d1 - d2).days)+1
		return days
	def generate(self):
		date = self.date
		state = self.state
		status=self.status
		all_units = self.env['property.unit'].search([])
		existing_ids = self.env['od.unit.occupied.report'].search([])
		x_unit_ids = []
		existing_ids.unlink()
		existing_available_ids = self.env['od.unit.available.report'].search([])
		existing_available_ids.unlink()
		existing_vaccant_ids = self.env['od.unit.vaccant.report'].search([])
		existing_vaccant_ids.unlink()
		existing_overstay_ids = self.env['od.unit.overstay.report'].search([])
		existing_overstay_ids.unlink()

		if status == 'occupied':

			for unit in all_units:
				line_id = False
				line_ids = []
		
				property_cont_unit_objs = self.env['property.cont.unit'].search([('unit_to','>=',date),('unit_id','=',unit.id)])
				if property_cont_unit_objs:
					for line in property_cont_unit_objs:
					
						line_ids.append(line and line.id)
					
				if line_ids:                    
					
					line_id = max(line_ids)
					line_obj = self.env['property.cont.unit'].browse(line_id)

					contract = line_obj.cont_id
					contract_state = line_obj.cont_id and line_obj.cont_id.state
					if contract_state != 'cancel':
						last_year_rent = line_obj.unit_rent
						unit_id = line_obj.unit_id and line_obj.unit_id.id
						property_id = line_obj.cont_id and line_obj.cont_id.build_id and line_obj.cont_id.build_id.id
						partner_id = line_obj.cont_id and line_obj.cont_id.customer_id and line_obj.cont_id.customer_id.id
						annual_rent = line_obj.unit_id and line_obj.unit_id.annual_rent
						if line_obj.duration == 'mt':
							last_year_rent = line_obj.unit_rent * 12
						expiry_date = line_obj.unit_to
						x_unit_ids.append(unit_id)
						self.env['od.unit.occupied.report'].create({'partner_id':partner_id,'property_id':property_id,'unit_id':unit_id,'annual_rent':annual_rent,'expiry_date':expiry_date,'last_year_rent':last_year_rent})
					
			action = self.env.ref('ag_property_maintainence.od_unit_occupied_report_action').read()[0]
			return action
		else:

			dont_consider_units = self.get_occupied_units()[0]
			
			for unit in all_units:
				line_id = False
				line_ids = []
				
				property_cont_unit_objs = self.env['property.cont.unit'].search([('unit_id','=',unit.id)])
				if property_cont_unit_objs:
					for line in property_cont_unit_objs:
						if line.unit_to < date:
							line_ids.append(line and line.id)
						if (line.unit_to >= date) and (line.cont_id.state=='cancel'):
							line_ids.append(line and line.id)

				if line_ids:                    
					
					line_id = max(line_ids)
					line_obj = self.env['property.cont.unit'].browse(line_id)
					contract = line_obj.cont_id
					previous_rent = line_obj.unit_rent
					unit_id = line_obj.unit_id and line_obj.unit_id.id
					property_id = line_obj.cont_id and line_obj.cont_id.build_id and line_obj.cont_id.build_id.id
					unit_rent = line_obj.unit_id and line_obj.unit_id.annual_rent
					state = line_obj.cont_id and line_obj.cont_id.state
					customer_id=line_obj.cont_id and line_obj.cont_id.customer_id.id
					if line_obj.duration == 'mt':
						unit_rent = line_obj.list_rent * 12                        
					vacant_date = line_obj.unit_to
					vacant_days = self.get_vacant_days(date,vacant_date)#[0]
					x_unit_ids.append(unit_id)
					vacant_days_rent = (float(unit_rent) / float(365)) * vacant_days

					if unit_id not in [dont_consider_units]:
						self.env['od.unit.available.report'].create({'unit_id':unit_id,'unit_rent':unit_rent,'vacant_date':vacant_date,'previous_rent':previous_rent,
					'vacant_days':vacant_days,'vacant_days_rent':vacant_days_rent,'property_id':property_id,'status':state,'partner_id':customer_id})
				
				if (unit.expiry_remarks == 'Not Used In Contracts'):
					unit_id=unit.id
					previous_rent=0.00
					property_id=unit.property_id.id
					unit_rent=0.00
					vacant_date=False
					vacant_days=0.00
					vacant_days_rent=0.00
					state='not used'
					partner_id=" "
					self.env['od.unit.available.report'].create({'unit_id':unit_id,'unit_rent':unit_rent,'vacant_date':vacant_date,'previous_rent':previous_rent,
				'vacant_days':vacant_days,'vacant_days_rent':vacant_days_rent,'property_id':property_id,'status':state,'partner_id':customer_id})
			
			available_object=self.env['od.unit.available.report']
			if status=='vaccant':
				vaccant_data=available_object.search([])
				for vaccant in vaccant_data:
					if (vaccant.status=='cancel') or (vaccant.status=='done') or (vaccant.status=='not used'):
						unit_id=vaccant.unit_id.id
						previous_rent=vaccant.previous_rent
						property_id=vaccant.property_id.id
						unit_rent=vaccant.unit_rent
						vacant_date=vaccant.vacant_date
						vacant_days=vaccant.vacant_days
						vacant_days_rent=vaccant.vacant_days_rent
						state=vaccant.status
						partner_id=vaccant.partner_id.id
						self.env['od.unit.vaccant.report'].create({'unit_id':unit_id,'unit_rent':unit_rent,'vacant_date':vacant_date,'previous_rent':previous_rent,
				'vacant_days':vacant_days,'vacant_days_rent':vacant_days_rent,'property_id':property_id,'status':state,'partner_id':customer_id})
				action = self.env.ref('ag_property_maintainence.od_unit_vaccant_report_action').read()[0]
			
			if status=='overstay':
				overstay_data=available_object.search([])
				for overstay in overstay_data:
					if overstay.status=='progres':
						unit_id=overstay.unit_id.id
						previous_rent=overstay.previous_rent
						property_id=overstay.property_id.id
						unit_rent=overstay.unit_rent
						vacant_date=overstay.vacant_date
						vacant_days=overstay.vacant_days
						vacant_days_rent=overstay.vacant_days_rent
						state=overstay.status
						partner_id=overstay.partner_id.id
						self.env['od.unit.overstay.report'].create({'unit_id':unit_id,'unit_rent':unit_rent,'vacant_date':vacant_date,'previous_rent':previous_rent,
				'vacant_days':vacant_days,'vacant_days_rent':vacant_days_rent,'property_id':property_id,'status':state,'partner_id':customer_id})
				action = self.env.ref('ag_property_maintainence.od_unit_overstay_report_action').read()[0]
			return action	
				

