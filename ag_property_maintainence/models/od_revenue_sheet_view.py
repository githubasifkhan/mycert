# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models

# UnitAnalysis
class od_revenue_sheet_view(models.Model):
    _name = "od.revenue.sheet.view"
    _description = "Revenue Analysis"
    _auto = False
    _rec_name = 'name'
    name = fields.Char(string="Month")
    date = fields.Date(string="Date", required=True)
    property_id = fields.Many2one('property.master',string="Building")
    main_property_id = fields.Many2one('main.property',string="Property")
    cont_id = fields.Many2one('property.contract', ondelete='cascade', string="Contract")    
    partner_id = fields.Many2one('res.partner', string="Customer",)
    desc = fields.Char(string="Desc")
    revenue = fields.Float(string="Income",)
    unit_id = fields.Many2one('property.unit',string="Unit")
    move_id = fields.Many2one('account.move',string="Move")    
    
    @api.model
    def init(self):
        cr = self.env.cr
        tools.drop_view_if_exists(cr, 'od_revenue_sheet_view')
        cr.execute("""
            create or replace view od_revenue_sheet_view as (
                 SELECT min(acc.id) as id,
                    acc.name as name,
                    acc.date as date,
                    contract.build_id as property_id,
                    contract.main_property_id as main_property_id,
                    acc.cont_id as cont_id,
                    acc.partner_id as partner_id,
                    acc.desc as desc,
                    acc.revenue as revenue,
                    acc.move_id as move_id,
                    acc.unit_id as unit_id
                FROM property_cont_account_detail acc
                    LEFT JOIN property_contract contract ON contract.id = acc.cont_id
                GROUP BY
                    acc.name,
                    acc.date,
                    contract.main_property_id,
                    contract.build_id,
                    acc.cont_id,
                    acc.partner_id,
                    acc.desc,
                    acc.revenue,
                    acc.move_id,
                    acc.unit_id
            )
        """)



