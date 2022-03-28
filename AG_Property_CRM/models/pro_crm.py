
from odoo import api, fields, models, tools, _ , SUPERUSER_ID
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta,date
from odoo.exceptions import except_orm, ValidationError ,UserError
from dateutil.relativedelta import relativedelta
import math
from odoo.exceptions import Warning


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    property_requirments = fields.One2many('property.requirement','lead_id',string="Property Requirements")
    booking_count = fields.Integer(compute='_booking_count', string='# Bookings')
    contract_count = fields.Integer(compute='_booking_count', string='# Contracts')
    opp_type = fields.Selection([('Sales', 'Sales'),('Lease', 'Leasing'),], string='Type', index=True, required=True, default='Lease')

    def _booking_count(self):
        for rec in self:
            
            if self.opp_type == 'Sales':
                booking_sales_count = self.env['property.booking.sales'].sudo().search([('lead_id', '=', rec.id)])
                rec.booking_count = len(booking_sales_count)
            else:
                document_ids = self.env['property.booking'].sudo().search([('lead_id', '=', rec.id)])
                rec.booking_count = len(document_ids)
            contract_ids = self.env['property.contract'].sudo().search([('lead_id', '=', rec.id)])
            rec.contract_count = len(contract_ids)

    def booking_view(self):
        self.ensure_one()
        domain = [
            ('lead_id', '=', self.id)]
        if self.opp_type == 'Sales':
            return {
                'name': _('Property Booking '),
                'domain': domain,
                'res_model': 'property.booking.sales',
                'type': 'ir.actions.act_window',
                'view_id': False,
                'view_mode': 'tree,form',
                'view_type': 'form',
                'limit': 80,
                'create':False,
                'context': "{'default_lead_id': '%s'}" % self.id
            }
        else:
            return {
                'name': _('Property Booking '),
                'domain': domain,
                'res_model': 'property.booking',
                'type': 'ir.actions.act_window',
                'view_id': False,
                'view_mode': 'tree,form',
                'view_type': 'form',
                'limit': 80,
                'create':False,
                'context': "{'default_lead_id': '%s'}" % self.id
            }

    
    def contract_view(self):
        self.ensure_one()
        domain = [
            ('lead_id', '=', self.id)]
        context =  {'default_lead_id': self.id}

        action = self.env.ref('ag_property_maintainence.property_contract_action')
        result = action.read()[0]
        result['domain'] = domain
        result['context'] = context
        return result


    
            

class PropertyRequirement(models.Model):
    _name = 'property.requirement'


    lead_id = fields.Many2one('crm.lead',string="Lead")
    opp_type = fields.Selection(related="lead_id.opp_type",store=True, string='Type')
    city = fields.Many2one('res.country.state',string="City")
    area = fields.Char(string="Area")
    category = fields.Many2one('property.unit.category',string="Category")
    net_area_from = fields.Float(string="Net Area From",default=0)
    net_area_to = fields.Float(string="Net Area To",default=99999)
    unit_type = fields.Many2one('property.unit.type',string="Unit Type")
    unit_subtype = fields.Many2one('property.unit.sub.type',string="Unit Subtype")
    unit_view = fields.Many2one('property.unit.view',string="Unit View")
    unit_usage = fields.Many2one('property.unit.usage',string="Unit Usage")
    annual_rent_from = fields.Float(string="Rent From",default=0)
    annual_rent_to = fields.Float(string="Rent To",default=99999)
    available_date = fields.Date(string="Availability Date",default=date.today())

    def search_units(self):
        for rec in self:
            domain = []
            if rec.opp_type:
                domain += [('unit_type','=',rec.opp_type)]
            if rec.available_date:
                if rec.available_date >= fields.Date.today():
                    domain += ['|',('end_date','<',rec.available_date),('appear_status','=','Available')]
                else:
                    raise UserError('The availability date should be as today or future dates only')
            else:
                domain += ['|',('available_date','<=',fields.Date.today()),('available_date','=',False)]
            if rec.annual_rent_from:
                domain += [('annual_rent','>=',rec.annual_rent_from)]
            if rec.annual_rent_to:
                domain += [('annual_rent','<=',rec.annual_rent_to)]
            if rec.category:
                domain += [('unit_cat_id','=',rec.category.id)]
            if rec.net_area_from:
                domain += [ ('net_area','>=',rec.net_area_from)]
            if rec.net_area_to:
                domain += [('net_area','<=',rec.net_area_to)]
            if rec.unit_type:
                domain += [('unit_type_id','=',rec.unit_type.id)]
            if rec.unit_subtype:
                domain += [('unit_sub_type_id','=',rec.unit_subtype.id)]
            if rec.unit_view:
                domain += [('unit_view_id','=',rec.unit_view.id)]
            if rec.unit_usage:
                domain += [('unit_usage_id','=',rec.unit_usage.id)]
            if rec.city:
                domain += [('property_id.state_id','=',rec.city.id)]
            if rec.area:
                domain += [('property_id.city','=',rec.area)]
            unit_objs = self.env['property.unit'].search(domain)
            unit_id = []
            for unit in unit_objs:
                # contract_lines = self.env['property.cont.unit'].search([('unit_id', '=', unit.id)])
                # if not contract_lines:
                unit.leads_id = rec.lead_id.id
                unit_id.append(unit.id)
            domains = [('id','in',unit_id)]
            action = self.env.ref('AG_Property_CRM.property_unit_action_search_reasults')
            result = action.read()[0]
            result['domain'] = domains
            # result['context'] = context
            return result

    
class PropertyUnit(models.Model):
    _inherit = 'property.unit'

    leads_id = fields.Many2one('crm.lead',string="Lead") 

    def booking_units(self):
        for rec in self:
            booking = self.env['property.booking']
            data = []
            vals = {
                'date':date.today(),
                'customer_id':rec.leads_id.partner_id.id,
                'lead_id':rec.leads_id.id,
                'build_id':rec.property_id.id,
                'unit_ids':[(6, 0,[rec.id])],
                'amount':rec.annual_rent,
            }
            data.append(vals) 

            booking.create(data)   

class PropertyBooking(models.Model):
    _name = 'property.booking.sales'
    _inherit = ['property.booking.sales','mail.thread']


    lead_id = fields.Many2one('crm.lead',string="Lead")  
    state = fields.Selection([('draft', 'Draft'),('submit', 'Submitted'),('approve', 'Approved'),('done', 'Booked'),('cancel', 'Canceled'),], string='Status', readonly=True, copy=False, index=True, default='draft')
    contract_count = fields.Integer(compute='_booking_count', string='# Contracts')

    def unlink(self):
        for rec in self:
            state = rec.state
            if state in ('done','approve'):
                raise UserError("You can Delete in Draft,submit and cancel States Only \n you can ask your manager to cancel it first")
            return super(PropertyBooking,rec).unlink()

    def action_submit(self):
        self.write({'state':'submit'})

    def action_approve(self):
        self.write({'state':'approve'})

    def create_contract(self):
        for rec in self:
            contract = self.env['property.contract.sales']
            data = []
            units = []
            for unit in rec.unit_ids:
                values = {
                    'unit_id':unit.id,
                    'list_rent':unit.annual_rent,
                    'unit_from':date.today(),
                    # 'unit_to':date.today() + relativedelta(years=+1,days=-1),
                    # 'unit_rent':unit.annual_rent,
                    'year_rent':unit.annual_rent,
                }
                units.append((0,0,values))
            vals = {
                'con_date':date.today(),
                # 'date_start':date.today(),
                # 'date_stop':date.today() + relativedelta(years=+1,days=-1) ,
                'booking_id':rec.id,
                'con_type':rec.con_type.id,
                'customer_id':rec.customer_id.id,
                'lead_id':rec.lead_id.id,
                'build_id':rec.build_id.id,
                'unit_line':units,
                # 'landlord':[6,0,[rec.landlord.ids]],
            }
            data.append(vals) 

            contract.create(data) 
            rec.write({'state':'done'})

    

    def _booking_count(self):
        for rec in self:
            contract_ids = self.env['property.contract.sales'].sudo().search([('booking_id', '=', rec.id)])
            rec.contract_count = len(contract_ids)
    
    def contract_view(self):
        self.ensure_one()
        domain = [
            ('booking_id', '=', self.id)]
        context =  {'default_booking_id': self.id}

        action = self.env.ref('ag_property_maintainence.property_contract_sales_action')
        result = action.read()[0]
        result['domain'] = domain
        result['context'] = context
        return result

class PropertyBooking(models.Model):
    _name = 'property.booking'
    _inherit = ['property.booking','mail.thread']


    lead_id = fields.Many2one('crm.lead',string="Lead")  
    state = fields.Selection([('draft', 'Draft'),('submit', 'Submitted'),('approve', 'Approved'),('done', 'Booked'),('cancel', 'Canceled'),], string='Status', readonly=True, copy=False, index=True, default='draft')
    contract_count = fields.Integer(compute='_booking_count', string='# Contracts')

    def unlink(self):
        for rec in self:
            state = rec.state
            if state in ('done','approve'):
                raise UserError("You can Delete in Draft,submit and cancel States Only \n you can ask your manager to cancel it first")
            return super(PropertyBooking,rec).unlink()

    def action_submit(self):
        self.write({'state':'submit'})

    def action_approve(self):
        self.write({'state':'approve'})

    def create_contract(self):
        for rec in self:
            contract = self.env['property.contract']
            data = []
            units = []
            for unit in rec.unit_ids:
                values = {
                    'unit_id':unit.id,
                    'list_rent':unit.annual_rent,
                    'unit_from':date.today(),
                    'unit_to':date.today() + relativedelta(years=+1,days=-1),
                    'unit_rent':unit.annual_rent,
                    'year_rent':unit.annual_rent,
                }
                units.append((0,0,values))
            vals = {
                'con_date':date.today(),
                'date_start':date.today(),
                'date_stop':date.today() + relativedelta(years=+1,days=-1) ,
                'booking_id':rec.id,
                'con_type':rec.con_type.id,
                'customer_id':rec.customer_id.id,
                'lead_id':rec.lead_id.id,
                'build_id':rec.build_id.id,
                'unit_line':units,
            }
            data.append(vals) 

            contract.create(data) 
            rec.write({'state':'done'})

    

    def _booking_count(self):
        for rec in self:
            contract_ids = self.env['property.contract'].sudo().search([('booking_id', '=', rec.id)])
            rec.contract_count = len(contract_ids)
    
    def contract_view(self):
        self.ensure_one()
        domain = [
            ('booking_id', '=', self.id)]
        context =  {'default_booking_id': self.id}

        action = self.env.ref('ag_property_maintainence.property_contract_action')
        result = action.read()[0]
        result['domain'] = domain
        result['context'] = context
        return result

class PropertyContractUnit(models.Model):
    _inherit = 'property.cont.unit'

    unit_rent = fields.Float(string="Rent Due", required=False, track_visibility='onchange')

class PropertyContract(models.Model):
    _inherit = 'property.contract'  


    lead_id = fields.Many2one('crm.lead',string="Lead")     

class PropertyContractSales(models.Model):
    _inherit = 'property.contract.sales'  


    lead_id = fields.Many2one('crm.lead',string="Lead")            
        

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    date_to_availability = fields.Integer(related="company_id.date_to_availability",string='Number of Booking date allowed', readonly=False)

class Company(models.Model):
    _inherit = "res.company"

    date_to_availability = fields.Integer(string='Number of Booking date allowed')
           


