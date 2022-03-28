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


class od_unit_occupied_report(models.Model):
    _name = 'od.unit.occupied.report'
    partner_id = fields.Many2one('res.partner', 'Customer')    
    unit_id = fields.Many2one('property.unit', 'Unit')
    annual_rent = fields.Float(string='Annual Rent')
    expiry_date = fields.Date(string="Expiry Date")
    last_year_rent = fields.Float(string='Last Year Rent') 
    property_id = fields.Many2one('property.master', 'Building')
    expired_days = fields.Float(string='Expiry Days')
    expired_days_rent = fields.Float(string='Expiry Days Rent')


class od_unit_available_report(models.Model):
    _name = 'od.unit.available.report'
    unit_id = fields.Many2one('property.unit', 'Unit')
    unit_rent = fields.Float(string='Unit Rent')
    vacant_date = fields.Date(string="Expiry Date")
    previous_rent = fields.Float(string='Last Year Rent')
    vacant_days = fields.Float(string='Vacant Days')
    vacant_days_rent = fields.Float(string='Vacant Days Rent')
    property_id = fields.Many2one('property.master', 'Building')
    cont_id = fields.Many2one('property.contract',string='Contract') 
    status= fields.Selection([('draft', 'Waiting Approval'),('post','Approved'),('progres', 'In Progress'),('close','Closure'),('done', 'Completed'),('cancel', 'Terminated'),], string='Status',)#fields.Char(string='State')
    partner_id = fields.Many2one('res.partner', 'Customer') 


class od_unit_vaccant_report(models.Model):
    _name = 'od.unit.vaccant.report'
    unit_id = fields.Many2one('property.unit', 'Unit')
    unit_rent = fields.Float(string='Unit Rent')
    vacant_date = fields.Date(string="Expiry Date")
    previous_rent = fields.Float(string='Last Year Rent')
    vacant_days = fields.Float(string='Vacant Days')
    vacant_days_rent = fields.Float(string='Vacant Days Rent')
    property_id = fields.Many2one('property.master', 'Building')
    cont_id = fields.Many2one('property.contract',string='Contract') 
    status=fields.Char(string='State')
    partner_id = fields.Many2one('res.partner', 'Customer') 


class od_unit_overstay_report(models.Model):
    _name = 'od.unit.overstay.report'
    unit_id = fields.Many2one('property.unit', 'Unit')
    unit_rent = fields.Float(string='Unit Rent')
    vacant_date = fields.Date(string="Expiry Date")
    previous_rent = fields.Float(string='Last Year Rent')
    vacant_days = fields.Float(string='Vacant Days')
    vacant_days_rent = fields.Float(string='Vacant Days Rent')
    property_id = fields.Many2one('property.master', 'Building')
    cont_id = fields.Many2one('property.contract',string='Contract') 
    status=fields.Char(string='State')
    partner_id = fields.Many2one('res.partner', 'Customer') 

