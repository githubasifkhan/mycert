from odoo import models, fields, api
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo import exceptions, _
from odoo.exceptions import Warning

class UnitAvailabilityWizard(models.TransientModel):
	_name = 'unit.availability.wizard'
	_description = 'unit.availability.wizard'

	date = fields.Date(string="Date",default=fields.Datetime.now)

	state = fields.Selection([
		('occupied', 'Occupied Units'),
		('available', 'Available Units'),
		('draft_cancel', 'Draft/Cancel'),
		('not_used', 'Not Used'),
		], string='Status',default='available')
            
	def generate(self):
		date = self.date
		state = self.state
		return_unit_ids = []
		unit_objs = self.env['property.unit'].search([])
		all_units = []
		domain = []
		available_units = []
		not_used_anycontract = []
		for unit in unit_objs:
			all_units.append(unit.id)
		considering_unit =[]
	#        all_units = [664]

		for uni in all_units:
			contract_lines = self.env['property.cont.unit'].search([('unit_id', '=', uni)])
			if not contract_lines:
				not_used_anycontract.append(uni)
			considering_contact = []
			print ("mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm",contract_lines)
			for cont in contract_lines:
				print( "123456789",cont.cont_id.state)
				if cont.cont_id.state not in ('draft','cancel'):
					considering_unit.append(cont.unit_id.id)
					considering_contact.append(cont.cont_id and cont.cont_id.id)
			if considering_contact:
				latest_cont_id = max(line for line in considering_contact)
				print ("ggggggggggggggggggggg",latest_cont_id)
				latest_cont_obj = self.env['property.contract'].browse(latest_cont_id)
				print ("vvvvvvvvvvvvvvvvvv",latest_cont_obj)

				end_date = latest_cont_obj.date_stop
				print( "vvvvvvvvvvvvvvddddddddddddddvvvv",end_date)
				if not (end_date > date):
					available_units.append(uni)

		action = self.env.ref('ag_property_maintainence.property_unit_action')
		result = action.read()[0]
		if state == 'available':
			x = list(set(all_units) - set(considering_unit) - set(not_used_anycontract))
			return_unit_ids = list(set(list(available_units) + list(x) + list(not_used_anycontract)))
			domain.append(('id','in',return_unit_ids))


		elif state == 'draft_cancel':
			return_unit_ids = list(set(all_units) - set(considering_unit) - set(not_used_anycontract))
			domain.append(('id','in',return_unit_ids))

		elif state == 'not_used':
			return_unit_ids = list(set(not_used_anycontract))
			domain.append(('id','in',return_unit_ids))
		else:
			x = list(set(all_units) - set(considering_unit) - set(not_used_anycontract))
			available_units = list(set(list(available_units) + list(x)))
			return_unit_ids = list(set(considering_unit) - set(available_units))
			domain.append(('id','in',return_unit_ids))

		result['domain'] = domain
		return result


