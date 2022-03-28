# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import re
import datetime as dt
from datetime import  timedelta, tzinfo, time, date, datetime
from dateutil.relativedelta import relativedelta
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
import re
# Property
class PropertyOwnership(models.Model):
	_name = 'property.ownership'

	name = fields.Many2one('res.partner',string='Ownership',required=True)
	shared = fields.Float('Party %',required=True)
	remarks = fields.Text('Remarks')
	property_id = fields.Many2one('main.property',string='property')

	@api.onchange('shared')
	def onchangeshared(self):
		if not (self.shared >= 0 and self.shared <= 100):
			raise UserError('The shared party should be in the range 0 to 100')

	@api.model
	def create(self,vals):
		if 'shared' in vals and vals['shared']:
			if not (vals['shared'] > 0 and vals['shared'] <= 100):
				raise UserError('The shared party should be in the range 0 to 100')
		return super(PropertyOwnership,self).create(vals)

	def write(self,vals):
		if 'shared' in vals and vals['shared']:
			if not (vals['shared'] > 0 and vals['shared'] <= 100):
				raise UserError('The shared party should be in the range 0 to 100')
		return super(PropertyOwnership,self).write(vals)


class MainPropertyAttachment(models.Model):
	_name = 'main.property.attachment'
	_description = "Property Attachment"

	name = fields.Char(string="Name", required=True)
	attachment_type_id = fields.Many2one('property.attachment.type', string="Type", required=True)
	attachment = fields.Binary(string="Attachment")
	remarks = fields.Text(string="Remarks")
	property_id = fields.Many2one('main.property', ondelete='cascade', string="Property")
			


class PropertyMain(models.Model):
	_name = 'main.property'
	_description = "Property Main"
	_inherit = ['mail.thread']


	@api.model
	def create(self,vals):
		rec = super(PropertyMain,self).create(vals)
		# if 'ownership' in vals and vals['ownership']:
		if sum(self.env['property.ownership'].search([('property_id','=',rec.id)]).mapped('shared')) != 100 :
			raise UserError('The sum of all shared parties should be in 100 , please check!')
		return rec

	def write(self,vals):
		rec =	super(PropertyMain,self).write(vals)
		if sum(self.env['property.ownership'].search([('property_id','=',self.id)]).mapped('shared')) != 100 :
			raise UserError('The sum of all shared parties should be in 100 , please check!')
		return rec


	name = fields.Char('Property Name',required=True)
	ownership = fields.One2many('property.ownership','property_id',string='Ownership')
	country = fields.Many2one('res.country', string="Country",required=True)
	code = fields.Char('Property Code',size=5,copy=False)
	color = fields.Integer('Color Index', default=2)
	is_active = fields.Boolean('Active')
	zone = fields.Many2one("res.country.state", string="Zone",ondelete='restrict')
	attachment_line = fields.One2many('main.property.attachment','property_id',string="Attachments")
	portfolio = fields.Char('Portfolio')
	class_s = fields.Char('Class')
	condition = fields.Char('Condition')
	description = fields.Text('Description')
	buildings_count = fields.Integer(string="Number of Buildings",compute="_get_floor_unit_no")

	@api.depends('name')
	def _get_floor_unit_no(self):
		for rec in self:
			buildings_count = self.env['property.master'].search([('main_property_id','=',rec.id)])
			rec.buildings_count = len(buildings_count)

	def building_view(self):
		self.ensure_one()
		domain = [('main_property_id', '=', self.id)]
		context =  {'default_main_property_id': self.id}

		action = self.env.ref('ag_property_maintainence.property_master_action')
		result = action.read()[0]
		result['domain'] = domain
		result['context'] = context
		return result

	def copy(self, default=None):
		default = dict(default or {})
		default['code'] = "copy"
		default['name'] = "%s (copy)"%(self.name)
		return super(PropertyMain,self).copy(default)




	_sql_constraints = [
        ("code_uniq", "unique (code)", "The Property code must be unique!")
    	]



class PropertyMaster(models.Model):
	_name = 'property.master'
	_description = "Property Master"
	_inherit = ['mail.thread']
	
	
		
		
	#@api.multi
	def write(self, values):
		if values:
			if values.get('name'):
				new_name = values.get('name')
				if self.maintain_cc_id:
					self.maintain_cc_id.name = new_name
		if 'phone' in values and values['phone']:

			if re.match("^[0-9]*$", values['phone']) != None:
				pass
			else:
				raise UserError('Invalid Phone No ,Please enter a valid Phone Number') 
		if 'mobile' in values and values['mobile']:

			if re.match("^[0-9]*$", values['mobile']) != None:
				pass
			else:
				raise UserError('Invalid mobile No ,Please enter a valid Mobile Number') 
		if 'fax' in values and values['fax']:

			if re.match("^[0-9]*$", values['fax']) != None:
				pass
			else:
				raise UserError('Invalid Fax number , should add only numbers') 
		if 'pb_zip' in values and values['pb_zip']:

			if re.match("^[0-9]*$", values['pb_zip']) != None:
				pass
			else:
				raise UserError('Invalid Zip number , should add only numbers') 

		if 'email' in values and values['email']:

			if re.match("^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", values['email']) != None:
				pass
			else:
				raise UserError('Not a valid E-mail Format') 
					
				
			
		return super(PropertyMaster,self).write(values)
		
	
	@api.model
	def create(self,vals):
		property_name = vals.get('name')
		costcenter_pool = self.env['maintain.account.cost.center']
		costcenter_val = {'name':property_name,'code':vals.get('code')}
		costcenter = costcenter_pool.create(costcenter_val)
		vals['maintain_cc_id'] = costcenter.id
		if 'phone' in vals and vals['phone']:

			if re.match("^[0-9]*$", vals['phone']) != None:
				pass
			else:
				raise UserError('Invalid Phone No ,Please enter a valid Phone Number') 
		if 'mobile' in vals and vals['mobile']:

			if re.match("^[0-9]*$", vals['mobile']) != None:
				pass
			else:
				raise UserError('Invalid mobile No ,Please enter a valid Mobile Number') 
		if 'fax' in vals and vals['fax']:

			if re.match("^[0-9]*$", vals['fax']) != None:
				pass
			else:
				raise UserError('Invalid Fax number , should add only numbers') 
		if 'pb_zip' in vals and vals['pb_zip']:

			if re.match("^[0-9]*$", vals['pb_zip']) != None:
				pass
			else:
				raise UserError('Invalid Zip number , should add only numbers') 

		if 'email' in vals and vals['email']:

			if re.match("^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", vals['email']) != None:
				pass
			else:
				raise UserError('Not a valid E-mail Format') 
		return super(PropertyMaster,self).create(vals)

	@api.onchange('tot_sqft','com_area')
	@api.depends('tot_sqft','com_area')
	def _area_onchange(self):
		if self.tot_sqft >0 and self.com_area >0:
			self.net_area = self.tot_sqft - self.com_area
		else:
			self.net_area = self.tot_sqft

	@api.onchange('state_id')
	def _state_onchange(self):
		if self.state_id:
			self.country_id = self.state_id.country_id.id

	def copy(self, default=None):
		default = dict(default or {})
		default['code'] = "copy"
		default['name'] = "%s (copy)"%(self.name)
		return super(PropertyMaster,self).copy(default)

	name = fields.Char(string="Name", required=True, index=True)
	code = fields.Char(string="Code",size=5, required="1",copy=False)
	prop_type_id= fields.Many2one('property.type', string="Building Type")
	plot_no = fields.Char(string="Plot No.", required=True)
	street = fields.Char(string="Location", required=True)
	pb_zip = fields.Char(string="Zip",  change_default=True)
	city = fields.Char(string="City", required=True)
	state_id = fields.Many2one("res.country.state", string="State", required=True, ondelete='restrict')
	country_id = fields.Many2one('res.country', string="Country", ondelete='restrict')
	main_property_id = fields.Many2one('main.property', string="Property",required=True)
	email =fields.Char(string="Email")
	phone =fields.Char(string="Phone")
	fax =fields.Char(string="Fax")
	mobile = fields.Char(string="Mobile")
	geo_lat = fields.Char(string="Latitude", help="Geo Location Latitude")
	geo_lon = fields.Char(string="Longitude", help="Geo Location Longitude")
	tot_sqft = fields.Float(string="Total SQFT", required="1")
	com_area = fields.Float(string="Common Area", required="1")
	net_area = fields.Float(string="Net Area",compute="_area_onchange",store=True)
	plot =fields.Char(string="Plot") 
	community_id =fields.Many2one('property.community',string="Community") 
	floors_count = fields.Integer(string="Number of Floors",compute="_get_floor_unit_no")
	units_count = fields.Integer(string="Number of Units",compute="_get_floor_unit_no")
	owner_id = fields.Many2one('res.partner', string="Owner", required=True, help="Land Lord Name")
	unit_line = fields.One2many('property.unit','property_id','Units')
	facility_line = fields.One2many('property.facility.line','property_id','Facilities')
	attachment_line = fields.One2many('property.attachment','property_id',string="Attachments")
	#image = fields.Image("Image", max_width=128, max_height=128, readonly=True)

	image = fields.Binary("Photo", attachment=True,
		help="This field holds the image used as photo for the employee, limited to 1024x1024px.")
	image_map = fields.Binary("map image", attachment=True)
	image_1 = fields.Binary("Photo 1", attachment=True)
	image_2 = fields.Binary("Photo 2", attachment=True)
	image_3 = fields.Binary("Photo 3", attachment=True)
	image_4 = fields.Binary("Photo 4", attachment=True)
	color = fields.Integer('Color Index', default=1)
	multi_images = fields.One2many("property.multi.images", "property_template_id", "Multi Images")
	# image_medium = fields.Binary("Medium-sized photo", attachment=True,
	# 	help="Medium-sized photo of the employee. It is automatically "\
	# 		 "resized as a 128x128px image, with aspect ratio preserved. "\
	# 		 "Use this field in form views or some kanban views.")
	# image_small = fields.Binary("Small-sized photo", attachment=True,
	# 	help="Small-sized photo of the employee. It is automatically "\
	# 		 "resized as a 64x64px image, with aspect ratio preserved. "\
	# 		 "Use this field anywhere a small image is required.")
	maintain_cc_id = fields.Many2one('maintain.account.cost.center',string="Cost Center")
	contact_person = fields.Many2one('res.partner',string="Contact Person")

	_sql_constraints = [
        ("code_uniq", "unique (code)", "The Property code must be unique!")
    	]

	@api.depends('name')
	def _get_floor_unit_no(self):
		for rec in self:
			floors_count = self.env['property.floor'].search([('property_id','=',rec.id)])
			rec.floors_count = len(floors_count)
			units_count = self.env['property.unit'].search([('property_id','=',rec.id)])
			rec.units_count = len(units_count)

	def floor_view(self):
		self.ensure_one()
		domain = [('property_id', '=', self.id)]
		context =  {'default_property_id': self.id}

		action = self.env.ref('ag_property_maintainence.property_floor_action')
		result = action.read()[0]
		result['domain'] = domain
		result['context'] = context
		return result

	def unit_view(self):
		self.ensure_one()
		domain = [('property_id', '=', self.id)]
		context =  {'default_property_id': self.id}

		action = self.env.ref('ag_property_maintainence.property_unit_action')
		result = action.read()[0]
		result['domain'] = domain
		result['context'] = context
		return result

	
	#
	def _get_default_image(self):
		image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
		return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))

	defaults = {
		'active': 1,
		'image': _get_default_image,
		'color': 0,
	}
   
# Geo Location Finder Start
# 	@api.one
# 	def geo_localize(self):
# 		street = self.name
# 		zip = self.street
# 		city = self.city
# 		state = self.state_id.name
# 		country = self.country_id.name
# 		addr = geo_query_address(street=street, zip=zip, city=city, state=state, country=country)
# 		result = geo_find(addr)
# 		if result:
# 			self.write({
# 						'geo_lat': result[0],
# 						'geo_lon': result[1]
# 						})
# 		return True

	# def geo_query_address(street=None, zip=None, city=None, state=None, country=None):
	# 	if country and ',' in country and (country.endswith(' of') or country.endswith(' of the')):
	# 		country = '{1} {0}'.format(*country.split(',', 1))
	# 	return tools.ustr(', '.join(filter(None, [street,
	# 											  ("%s %s" % (zip or '', city or '')).strip(),
	# 											  state,
	# 											  country])))
	#
	# def geo_find(addr):
	# 	url = 'https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address='
	# 	url += urllib.quote(addr.encode('utf8'))
	# 	try:
	# 		result = json.load(urllib.urlopen(url))
	# 	except UserError:
	# 		raise UserError(_('Cannot contact geolocation servers. Please make sure that your internet connection is up and running (%s).'))
	# 	if result['status'] != 'OK':
	# 		return None
	#
	# 	try:
	# 		geo = result['results'][0]['geometry']['location']
	# 		return float(geo['lat']), float(geo['lng'])
	# 	except (KeyError, ValueError):
	# 		return None
# Geo Location Finder End
	

	#@api.multi
	def _get_action(self, action_xmlid):
		# TDE TODO check to have one view + custo in methods
		action = self.env.ref(action_xmlid).read()[0]
		if self:
			action['display_name'] = self.display_name
		return action
		
	#@api.multi
	def get_property_master_action(self):
		return self._get_action('ag_property_maintainence.property_contract_action_property')



#Property Facility
class PropertyFacilityLine(models.Model):
	_name = 'property.facility.line'
	_description = "Property Facility Line"

	name = fields.Char(string="Name", required=True)
	# facility_id = fields.Many2one('product.product', string="Facility", required=True)
	remarks = fields.Text(string="Remarks")
	property_id = fields.Many2one('property.master', ondelete='cascade', string="Building")

# Property Attachment
class PropertyAttachment(models.Model):
	_name = 'property.attachment'
	_description = "Property Attachment"

	name = fields.Char(string="Name", required=True)
	attachment_type_id = fields.Many2one('property.attachment.type', string="Type", required=True)
	attachment = fields.Binary(string="Attachment")
	remarks = fields.Text(string="Remarks")
	property_id = fields.Many2one('property.master', ondelete='cascade', string="Building")

# Community
class PropertyCommunity(models.Model):
	_name = 'property.community'
	_description = "Property Community"

	name = fields.Char(string="Name",  required="1")
	code = fields.Char(string="Code",  required="1")

	_sql_constraints = [('code_uniq', 'unique(code)', 'Code must be unique...!'),]

# Property Type
class PropertyType(models.Model):
	_name = 'property.type'
	_description = "Property Type"

	name = fields.Char(string="Name",  required="1")
	# code = fields.Char(string="Code",  required="1")

	# _sql_constraints = [('code_uniq', 'unique(code)', 'Code must be unique...!'),]

# Floor Master
class propertyFloor(models.Model):
	_name = 'property.floor'
	_description = "Property Floor"
	_inherit = ['mail.thread']

	@api.onchange('gross_area','com_area')
	def _onchange_floor_area(self):
		self.net_area = self.gross_area - self.com_area
	
	def write(self,vals):
		if vals.get('property_id') and not vals.get('code'):
			vals['name'] = '%s/%s' %(self.env['property.master'].browse(vals.get('property_id')).code,self.code)
		elif not vals.get('property_id') and vals.get('code'):
			vals['name'] = '%s/%s' %(self.property_id.code,vals.get('code'))
		elif vals.get('property_id') and vals.get('code'):
			vals['name'] = '%s/%s' %(self.env['property.master'].browse(vals.get('property_id')).code,vals.get('code'))
		
		return super(propertyFloor,self).write(vals)

	@api.model
	def create(self,vals):
		# prop = vals.get('property_id')
		vals['name'] = '%s/%s' %(self.env['property.master'].browse(vals.get('property_id')).code,vals.get('code'))
		property_name = vals['name']
		costcenter_pool = self.env['floor.account.cost.center']
		costcenter_val = {'name':property_name,'code':vals.get('code')}
		costcenter = costcenter_pool.create(costcenter_val)
		costcenter.write({'code':costcenter.id})
		vals['floor_maintain_cc_id'] = costcenter.id
		return super(propertyFloor,self).create(vals)

	def copy(self, default=None):
		default = dict(default or {})
		default['code'] = "copy"
		default['floor_name'] = "%s (copy)"%(self.floor_name)
		return super(propertyFloor,self).copy(default)


	image = fields.Binary("Photo", attachment=True,
		help="This field holds the image used as photo for the employee, limited to 1024x1024px.")
	color = fields.Integer('Color Index', default=1)
	name = fields.Char(string="Sequence Name")
	code = fields.Char(string="Code",size=5, required="1",copy=False)
	floor_name = fields.Char(string="Name", required=True)
	level = fields.Char(string="Level", required=True)
	property_id = fields.Many2one('property.master', required=True, string="Building")
	gross_area = fields.Float(string="Total SQFT", required="1")
	com_area = fields.Float(string="Common Area", required="1")
	net_area = fields.Float(string="Net Area")
	unit_count = fields.Integer(string="No of Units",compute="_get_floor_unit_no")
	facility_line = fields.One2many('property.floor.facility.line','floor_id','Facilities')
	floor_maintain_cc_id = fields.Many2one('floor.account.cost.center', string='Floor Cost Center')

	_sql_constraints = [
        ("code_property_uniq", "unique (code, property_id)", "The Floor code must be unique for each property!")
    	]

	@api.depends('name')
	def _get_floor_unit_no(self):
		for rec in self:
			unit_count = self.env['property.unit'].search([('floor_id','=',rec.id)])
			rec.unit_count = len(unit_count)

	def unit_view(self):
		self.ensure_one()
		domain = [('floor_id', '=', self.id)]
		context =  {'default_floor_id': self.id}

		action = self.env.ref('ag_property_maintainence.property_unit_action')
		result = action.read()[0]
		result['domain'] = domain
		result['context'] = context
		return result

# # Floor Facility
class PropertyFloorFacilityLine(models.Model):
	_name = 'property.floor.facility.line'
	_description = "Floor Facility Line"

	name = fields.Char(string="Name", required=True)
	# facility_id = fields.Many2one('product.product', string="Facility", required=True)
	remarks = fields.Text(string="Remarks")
	floor_id = fields.Many2one('property.floor', ondelete='cascade', string="Floor")


# Unit Master
class PropertyUnit(models.Model):
	_name = 'property.unit'
	_description = "Property Unit"
	_inherit = ['mail.thread']

	#@api.multi
	def action_show_contract(self):
		action = self.env.ref('ag_property_maintainence.property_contract_action').read()[0]
		unit_id = self.id
		contract_ids = []
		unit_lines_in_contract = self.env['property.cont.unit'].search([('unit_id','=',unit_id)])
		for line in unit_lines_in_contract:
			contract_ids.append(line.cont_id and line.cont_id.id)

		domain = []


		if not contract_ids:
			raise Warning("no contract found")

		domain.append(('id','in',contract_ids))
		action['domain'] = domain
		return action

	@api.model
	def create(self,vals):
		vals['name'] = '%s/%s' %(self.env['property.floor'].browse(vals.get('floor_id')).name,vals.get('code'))
		unit_name = vals.get('name')
		product_pool = self.env['product.product']
		prod_val = {'name':unit_name,'type':'service'}
		product = product_pool.create(prod_val)
		vals['product_id'] = product.id
		property_name = vals.get('name')
		costcenter_pool = self.env['unit.account.cost.center']
		costcenter_val = {'name':property_name,'code':vals.get('code')}
		costcenter = costcenter_pool.create(costcenter_val)
		costcenter.write({'code':costcenter.id})
		vals['unit_maintain_cc_id'] = costcenter.id
		return super(PropertyUnit,self).create(vals)



	#@api.multi
	def write(self, values):
		if values:
			if values.get('name'):
				new_name = values.get('name')
				if self.product_id:
					self.product_id.name = new_name
		# if vals.get('property_id'):
		# 	prop = self.env['property.master'].browse(vals.get('property_id')).name
		# else:
		# 	prop = self.property_id.name
		if values.get('floor_id'):
			floor = self.env['property.floor'].browse(values.get('floor_id')).name
		else:
			floor = self.floor_id.name
		if values.get('code'):
			unit = values.get('code')
		else:
			unit = self.code
		values['name'] = '%s/%s' %(floor,unit)
		
		return super(PropertyUnit,self).write(values)

	def copy(self, default=None):
		default = dict(default or {})
		default['code'] = "copy"
		default['unit_name'] = "%s (copy)"%(self.unit_name)
		return super(PropertyUnit,self).copy(default)



	#@api.one
	@api.depends('rent_line')
	def _get_avail_date(self):
		for order in self:
			# unit_id = order.id
			# start_date = order.start_date
			# stop_date = order.stop_date
			# contract_line_obj = order.env['property.cont.unit']
			# contract_line = contract_line_obj.search([('unit_id', '=', unit_id)])
			# maxdate = False
			# for unit in contract_line:
			# 	date = unit.cont_id and unit.cont_id.date_stop
			# 	print('---date---',date)
			# 	if date and maxdate:
			# 		maxdate = max(date, maxdate)
			# 		print('---maxdate---',maxdate)
			# if stop_date:
			# 	order.available_date = False
			# if maxdate and start_date and maxdate > start_date and not stop_date:
			# 	order.available_date = maxdate
			# else:
			# 	order.available_date = start_date
			if order.rent_line:
				for unit in order.rent_line:
					if date.today() <= unit.date_to and date.today() >= unit.date_from:
						order.available_date = unit.date_to + relativedelta(days=+1)
						order.available_date_bool = True
					else:
						order.available_date = False
						order.available_date_bool = False
			else:
				order.available_date = False
				order.available_date_bool = False
			

	#@api.one
	@api.depends('unit_contract_line.name','unit_contract_line','name','unit_contract_line.cont_id.state')
	def _get_remarks(self):

		self.expiry_remarks = 'Not Used In Contracts'
		line = self.unit_contract_line
		if not line:
			self.expiry_remarks = 'Not Used In Contracts'
		dates = []
		for li in line:

			self.expiry_remarks = 'No Contract InProgress'

			if li.cont_id.state not in ('draft','post','cancel','done'):
				dates.append(li.cont_id.date_stop)
		if dates:
			self.expiry_remarks = 'Unit is not Available up to ' + str(max(dates))


	@api.onchange('floor_id')
	def _onchange_floor(self):
		if self.gross_area == 0 and self.floor_id.gross_area >0 and self.floor_id.unit_count >0:
			self.gross_area = self.floor_id.gross_area / self.floor_id.unit_count
		if self.common_area == 0 and self.floor_id.com_area >0 and self.floor_id.unit_count >0:
			self.common_area = self.floor_id.com_area / self.floor_id.unit_count

	@api.onchange('gross_area','common_area')
	def _onchange_unit_area(self):
		self.net_area = self.gross_area - self.common_area

	name = fields.Char(string="Sequence Name")
	unit_name = fields.Char(string="Name", required="1")
	code = fields.Char(string="Code",size=5, required="1",copy=False)
	color = fields.Integer('Color Index', default=1)
	expiry_remarks = fields.Char(string="Ex.Remarks",compute="_get_remarks")
	property_id = fields.Many2one('property.master',string="Building")
	main_property_id = fields.Many2one(related='property_id.main_property_id',store=True, string="Property")
	annual_rent = fields.Float(string="Annual Rent" )
	unit_cat_id = fields.Many2one('property.unit.category', string="Category")
	floor_id = fields.Many2one('property.floor', string="Floor")
	is_active = fields.Boolean(string="Active", default=True)
	unit_manager_id = fields.Many2one('res.users',string="Account Manager")
	product_id = fields.Many2one('product.product',string="CRM Product", readonly="1")
	municipality_num =fields.Char(string="Municipality")
	ew_contract_no = fields.Char(string="E & W Contract")
	gross_area = fields.Float(string="Gross Area" )
	common_area = fields.Float(string="Common Area")
	net_area = fields.Float(string="Net Area", required="1")
	unit_type_id = fields.Many2one('property.unit.type', string="Unit Type")
	unit_sub_type_id = fields.Many2one('property.unit.sub.type', string="Unit Sub Type")
	unit_view_id = fields.Many2one('property.unit.view', string="Unit View")
	unit_usage_id = fields.Many2one('property.unit.usage', string="Unit Usage")
	start_date = fields.Date(string="Start Date", help="Date - Unit First Available for Rent Out")
	stop_date = fields.Date(string="Stop Date", help="Date - Unit Discontnue from Renting Out")
	available_date = fields.Date(string="Available Date", compute="_get_avail_date",store=True)
	available_date_bool = fields.Boolean(string="Available Count", compute="_get_avail_date",store=True)
	rent_line = fields.One2many('unit.rent.line','unit_id', string="List Rent")
	facility_line = fields.One2many('unit.facility.line','unit_id', string="Facility")
	attachment_line = fields.One2many('property.unit.attachment','unit_id', string="Attachment")
	unit_contract_line = fields.One2many('property.cont.unit','unit_id', string="Contract Unit Line")
	unit_maintain_cc_id = fields.Many2one('unit.account.cost.center', string='Unit Cost Center')
#	unit_contract_line = fields.One2many('property.cont.unit','unit_id', string="Contract Unit Line")
	image = fields.Binary("Photo", attachment=True,
		help="This field holds the image used as photo for the employee, limited to 1024x1024px.")
	image_1 = fields.Binary("Photo 1", attachment=True)
	image_2 = fields.Binary("Photo 2", attachment=True)
	image_3 = fields.Binary("Photo 3", attachment=True)
	image_4 = fields.Binary("Photo 4", attachment=True)
	image_5 = fields.Binary("Photo 5", attachment=True)
	image_6 = fields.Binary("Photo 6", attachment=True)
	image_7 = fields.Binary("Photo 7", attachment=True)
	image_8 = fields.Binary("Photo 8", attachment=True)
	image_9 = fields.Binary("Photo 9", attachment=True)
	image_10 = fields.Binary("Photo 10", attachment=True)
	multi_images = fields.One2many("property.multi.images", "unit_template_id", "Multi Images")
	unit_type = fields.Selection([('Sales', 'Saleable'),('Lease', 'Leasable'),], string='Leasable/Saleable', index=True, required=True, default='Lease')

	_sql_constraints = [
        ("code_floor_uniq", "unique (code, floor_id)", "The Unit code must be unique for each floor!")
    	]

	state = fields.Selection([
		('Available', 'Available'),
		('Lease Booked', 'Lease Booked'),
		('Leased', 'Leased'),
		('Sale Booked', 'Sale Booked'),
		('Sold', 'Sold'),], string='Status', readonly=True, copy=False, index=True, compute='_get_status')
	appear_status = fields.Selection([ ('Available', 'Available'),
		('Lease Booked', 'Lease Booked'),
		('Leased', 'Leased'),
		('Sale Booked', 'Sale Booked'),
		('Sold', 'Sold'),], string='Status', readonly=True, copy=False, index=True)

	end_date = fields.Date('End Date', compute='_get_status',readonly=True,store=True)


	@api.depends('name')
	def _get_status(self):
		for rec in self:
			if rec.unit_type == 'Sales':
				sales_contract = self.env['property.cont.unit.sales'].search([('unit_id','=',rec.id)])
				if sales_contract:
					rec.state = 'Sold'
					rec.appear_status = 'Sold'
					rec.end_date = False
				else:
					sales_booking = self.env['property.booking.sales'].search([('unit_ids','in',rec.id)])
					if sales_booking:
						for book in sales_booking:
							if date.today() >= book.book_from and date.today() <= book.book_to:
								rec.state = 'Sale Booked'
								rec.appear_status = 'Sale Booked'
								rec.end_date = book.book_to
							else:
								rec.state = 'Available'
								rec.appear_status = 'Available'
								rec.end_date = False
					else:
						rec.state = 'Available'
						rec.appear_status = 'Available'
						rec.end_date = False
			else:
				lease_contract = self.env['property.cont.unit'].search([('unit_id','=',rec.id)])
				if lease_contract:
					for cont in lease_contract:
						if date.today() >= cont.unit_from and date.today() <= cont.unit_to:
							rec.state = 'Leased'
							rec.appear_status = 'Leased'
							rec.end_date = cont.unit_to
						else:
							rec.state = 'Available'
							rec.appear_status = 'Available'
							rec.end_date = False
				else:
					lease_booking = self.env['property.booking'].search([('unit_ids','in',rec.id)])
					if lease_booking:
						for book in lease_booking:
							if date.today() >= book.book_from and date.today() <= book.book_to:
								rec.state = 'Lease Booked'
								rec.appear_status = 'Lease Booked'
								rec.end_date = book.book_to
							else:
								rec.state = 'Available'
								rec.appear_status = 'Available'
								rec.end_date = False
					else:
						rec.state = 'Available'
						rec.appear_status = 'Available'
						rec.end_date = False


	
		
		#related="product_id.image",
	# image_medium = fields.Binary("Medium-sized photo", attachment=True,
	# 	help="Medium-sized photo of the employee. It is automatically "\
	# 		 "resized as a 128x128px image, with aspect ratio preserved. "\
	# 		 "Use this field in form views or some kanban views.")
	# image_small = fields.Binary("Small-sized photo", attachment=True,
	# 	help="Small-sized photo of the employee. It is automatically "\
	# 		 "resized as a 64x64px image, with aspect ratio preserved. "\
	# 		 "Use this field anywhere a small image is required.")
	#
	def _get_default_image(self):
		image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
		return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))

	defaults = {
		'image': _get_default_image,
	}

	# _sql_constraints = [('code_uniq', 'unique(code)', 'Code must be unique...!'),]

# Unit List Rent
class UnitRentLine(models.Model):
	_name = 'unit.rent.line'
	_description = "Unit Rent Line"

	name = fields.Char(string="Remarks")
	duration = fields.Selection([('mt', 'Monthly'),('yr', 'Yearly'),], string='Period', index=True, required=True, default='yr')

	rent = fields.Float(string=" Rent")
	sqft = fields.Float(string="SQFT Rent")
	total_amount = fields.Float(string="Total Amt")
	unit_id = fields.Many2one('property.unit', ondelete='cascade', string="Unit")
	customer_id = fields.Many2one('res.partner',string="Customer")
	cont_id = fields.Many2one('property.contract',string="Contract")
	date_from = fields.Date(string="Date From", track_visibility='onchange' , required=True)
	date_to = fields.Date(string="Date To", track_visibility='onchange' , required=True)



	@api.onchange('rent','sqft')
	def onchange_rent(self):
		if self.rent >0 and self.sqft >0 :
			raise Warning("Monthly Rent OR SQFT Rent can't set Together!!!!")


# Unit Facility
class UnitFacilityLine(models.Model):
	_name = 'unit.facility.line'
	_description = "Unit Facility Line"

	name = fields.Char(string="Name", required=True)
	# facility_id = fields.Many2one('product.product', string="Facility", required=True)
	remarks = fields.Text(string="Remarks")
	unit_id = fields.Many2one('property.unit', ondelete='cascade', string="Unit")

# Unit Attachment
class PropertyUnitAttachment(models.Model):
	_name = 'property.unit.attachment'
	_description = "Property Unit Attachment"

	name = fields.Char(string="Name", required=True)
	attachment_type_id = fields.Many2one('property.attachment.type', string="Type", required=True)
	attachment = fields.Binary(string="Attachment")
	remarks = fields.Text(string="Remarks")
	unit_id = fields.Many2one('property.unit', ondelete='cascade', string="Unit")

# Unit Type
class UnitCategory(models.Model):
	_name = 'property.unit.category'
	_description = "Unit Category"

	name = fields.Char(string="Name",  required="1")
	code = fields.Char(string="Code",  required="1")
#    is_cost = fields.Boolean(string="Cost Booking")
#    is_revenue = fields.Boolean(string="Revenue Booking")

	_sql_constraints = [('code_uniq', 'unique(code)', 'Code must be unique...!'),]

# Unit Type
class UnitType(models.Model):
	_name = 'property.unit.type'
	_description = "Unit Type"

	name = fields.Char(string="Name",  required="1")
	# code = fields.Char(string="Code",  required="1")

	# _sql_constraints = [('code_uniq', 'unique(code)', 'Code must be unique...!'),]

# Unit SUb Type
class UnitSubType(models.Model):
	_name = 'property.unit.sub.type'
	_description = "Unit Sub Type"

	name = fields.Char(string="Name",  required="1")
	# code = fields.Char(string="Code",  required="1")
	is_cost = fields.Boolean(string="Cost Booking")
	is_revenue = fields.Boolean(string="Revenue Booking")

	# _sql_constraints = [('code_uniq', 'unique(code)', 'Code must be unique...!'),]

# Unit View
class UnitView(models.Model):
	_name = 'property.unit.view'
	_description = "Unit View"

	name = fields.Char(string="Name",  required="1")
	# code = fields.Char(string="Code",  required="1")

	# _sql_constraints = [('code_uniq', 'unique(code)', 'Code must be unique...!'),]

# Unit Category
class UnitUsage(models.Model):
	_name = 'property.unit.usage'
	_description = "Unit Usage"

	name = fields.Char(string="Name",  required="1")
	# code = fields.Char(string="Code",  required="1")

	# _sql_constraints = [('code_uniq', 'unique(code)', 'Code must be unique...!'),]








# Property Attachment Type
class AttachmentType(models.Model):
	_name = 'property.attachment.type'
	_description = "Attachment Type"

	name = fields.Char(string="Name",  required="1")
	# code = fields.Char(string="Code",  required="1")
	od_confirm=fields.Boolean(string='Confirm')
	od_approve=fields.Boolean(string='Approve')
	_sql_constraints = [('code_uniq', 'unique(code)', 'Code must be unique...!'),]
#
# 	# @api.multi
# 	# def set_approve_defaults(self):
# 	# 	return self.env['ir.values'].sudo().set_default(
# 	# 		'property.attachment.type', 'approve', self.approve)
# Tenant Bank
class PropertyBank(models.Model):
	_name = 'property.bank'
	_description = "Property Bank"

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		recs = self.browse()
		if name:
			recs = self.search((args + ['|', ('name', 'ilike', name), ('code', 'ilike', name)]),
							   limit=limit)
		if not recs:
			recs = self.search([('name', operator, name)] + args, limit=limit)
		return recs.name_get()

	name = fields.Char(string="Bank",  required="1")
	code = fields.Char(string="Code",  required="1")


# class MaintainAccountDivision(models.Model):
#     _name = 'maintain.account.division'
#     _description = "Account Division"
#
#     code = fields.Char(string='Code',required=True)
#     name = fields.Char(string='Name',required=True)

# class MaintainAccountBranch(models.Model):
#     _name = 'maintain.account.branch'
#     _description = "Account Brahck"
#
#     code = fields.Char(string='Code',required=True)
#     name = fields.Char(string='Name',required=True)

class MaintainAccountCostCenter(models.Model):
    _name = 'maintain.account.cost.center'
    _description = "Account Cost Center"

    code = fields.Char(string='Code',required=True)
    seq = fields.Integer(string="Sequence")
    name = fields.Char(string='Name',required=True)
    #branch_id = fields.Many2one('maintain.account.branch',string='Branch')
   # div_id = fields.Many2one('maintain.account.division',string='Division')
    #div_mgr_id = fields.Many2one('res.users',string="Division Manager")
    target= fields.Float(string="Sales Target",help="This is for Day Report...Not for Incentive")

class FloorAccountCostCenter(models.Model):
    _name = 'floor.account.cost.center'
    _description = "Account Cost Center"

    code = fields.Char(string='Code',required=True)
    seq = fields.Integer(string="Sequence")
    name = fields.Char(string='Name',required=True)
    #branch_id = fields.Many2one('maintain.account.branch',string='Branch')
   # div_id = fields.Many2one('maintain.account.division',string='Division')
    #div_mgr_id = fields.Many2one('res.users',string="Division Manager")
    target= fields.Float(string="Sales Target",help="This is for Day Report...Not for Incentive")

class UnitAccountCostCenter(models.Model):
    _name = 'unit.account.cost.center'
    _description = "Account Cost Center"

    code = fields.Char(string='Code',required=True)
    seq = fields.Integer(string="Sequence")
    name = fields.Char(string='Name',required=True)
    #branch_id = fields.Many2one('maintain.account.branch',string='Branch')
   # div_id = fields.Many2one('maintain.account.division',string='Division')
    #div_mgr_id = fields.Many2one('res.users',string="Division Manager")
    target= fields.Float(string="Sales Target",help="This is for Day Report...Not for Incentive")


class PropertyMultiImages(models.Model):
	_name = "property.multi.images"

	image = fields.Binary("Images")
	description = fields.Char("Description")
	title = fields.Char("title")
	property_template_id = fields.Many2one("property.master", "Building")
	unit_template_id = fields.Many2one("property.unit", "Unit")

# class UnitMultiImages(models.Model):
# 	_name = "unit.multi.images"

# 	image = fields.Binary("Images")
# 	description = fields.Char("Description")
# 	title = fields.Char("title")
# 	unit_template_id = fields.Many2one("property.unit", "Unit")

