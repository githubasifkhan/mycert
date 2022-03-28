# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta , date
from odoo.tools.translate import _
from dateutil.relativedelta import relativedelta


class CreateBooking(models.TransientModel):
    _name = 'create.booking'


    def Generate_Booking(self):
        

        booking = self.env['property.booking']
        booking_sale = self.env['property.booking.sales']
        pur = self.env['property.unit'].browse(self.env.context.get('active_ids'))
        opp_type = ''
        building = []
        for rec in pur:
            if rec.property_id.id in building:
                continue
            else:
                ven = rec.property_id.id
                opp_type = rec.unit_type
                building.append(ven)
        data = []
        lead = 0
        for build in building:
            customer = 0
            lead = 0
            amount = 0
            # amount = 0
            units = []
            for rec in pur:
                if build == rec.property_id.id:
                    customer = rec.leads_id.partner_id.id
                    lead = rec.leads_id.id
                    opp_type = rec.unit_type
                    units.append(rec.id)
                    amount += rec.annual_rent

            
            vals = {
                'date':date.today(),
                'book_from':date.today(),
                'book_to':date.today() + relativedelta(days=+self.env.company.date_to_availability),
                'customer_id':customer,
                'lead_id':lead,
                'build_id':build,
                'amount':amount,
                'unit_ids':[(6, 0,units)],
            }
            data.append(vals) 
        domain = [
            ('lead_id', '=', lead)]
        if opp_type == 'Sales':
            booking_sale.create(data)
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
                'context': "{'default_lead_id': '%s'}" % lead
            }
        if opp_type == 'Lease': 
            booking.create(data)
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
                'context': "{'default_lead_id': '%s'}" % lead
            }
            
        
            

            
