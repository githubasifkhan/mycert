# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models

# UnitAnalysis
class UnitAnalysis(models.Model):
    _name = "property.unit.analysis"
    _description = "Unit Analysis"
    _auto = False
    _order = "unit_id ASC"
    
    property_id = fields.Many2one('property.master',string="Building")
    renew_id = fields.Many2one('property.contract',string="Renewed Contract")
    contract_id = fields.Many2one('property.contract', string="Contract")
    floor_id = fields.Many2one('property.floor', string="Floor")
    unit_id = fields.Many2one('property.unit', string="unit")
    state = fields.Selection([('draft', 'Waiting Approval'),('post','Approved'),('progres', 'In Progress'),('close','Closure'),('done', 'Completed'),('cancel', 'Terminated'),], string='Status')
    c_end_date = fields.Date(string="C.Expire Date")
    unit_manager_id = fields.Many2one('res.users',string="Account Manager")
    product_id = fields.Many2one('product.product',string="CRM Product")
    municipality_num =fields.Char(string="Municipality")
    ew_contract_no = fields.Char(string="E & W Contract")
    net_area = fields.Float(string="Net Area")
    common_area = fields.Float(string="Common Area")
    gross_area = fields.Float(string="Gross Area" )
    unit_type_id = fields.Many2one('property.unit.type', string="Unit Type")
    unit_sub_type_id = fields.Many2one('property.unit.sub.type', string="Unit Sub Type")
    unit_view_id = fields.Many2one('property.unit.view', string="Unit View")
    unit_usage_id = fields.Many2one('property.unit.usage', string="Unit Usage")
    partner_id = fields.Many2one('res.partner', string="Partner")
    total_value = fields.Float(string="C.value")
	
    @api.model
    def init(self):
        cr = self.env.cr
        tools.drop_view_if_exists(cr, 'property_unit_analysis')
        cr.execute("""
            create or replace view property_unit_analysis as (
                 SELECT
                    pcu.id as id,
                    pcu.unit_id AS unit_id,
                    pcu.cont_id as contract_id,
                    pcu.build_id as property_id,
                    
                    pcu.floor_id as floor_id,
                    contract.date_stop as c_end_date,
                    contract.state as state,
                    pc.unit_manager_id as unit_manager_id,
                    pc.product_id as product_id,
                    pc.municipality_num as municipality_num,
                    pc.ew_contract_no as ew_contract_no,
                    pc.net_area as net_area,
                    pc.common_area as common_area,
                    pc.gross_area as gross_area,
                    pc.unit_type_id as unit_type_id,
                    pc.unit_sub_type_id as unit_sub_type_id,
                    pc.unit_view_id as unit_view_id,
                    pc.unit_usage_id as unit_usage_id,
                    contract.customer_id as partner_id,
                    contract.total_value as total_value,
                    contract.renew_id as renew_id
                    
                    
                    
                    
                    
                FROM property_cont_unit pcu
                    left join property_unit pc on(pc.id = pcu.unit_id)
                    LEFT JOIN property_contract contract ON(contract.id = pcu.cont_id)
            
            
        
            )
        """)
# UnitReport
class UnitReport(models.Model):
    _name = "property.unit.report"
    _description = "Unit Report"
    _auto = False
    _rec_name = 'name'
    _order = "id ASC"
    
    name = fields.Char(string="Name")
    property_id = fields.Many2one('property.master',string="Building")
    main_property_id = fields.Many2one('main.property',string="Property")
    unit_cat_id = fields.Many2one('property.unit.category', string="Category")
    floor_id = fields.Many2one('property.floor', string="Floor")
    is_active = fields.Boolean(string="Active")
    unit_manager_id = fields.Many2one('res.users',string="Account Manager")
    product_id = fields.Many2one('product.product',string="CRM Product")
    municipality_num =fields.Char(string="Municipality")
    ew_contract_no = fields.Char(string="E & W Contract")
    net_area = fields.Float(string="Net Area")
    common_area = fields.Float(string="Common Area")
    gross_area = fields.Float(string="Gross Area" )
    unit_type_id = fields.Many2one('property.unit.type', string="Unit Type")
    unit_sub_type_id = fields.Many2one('property.unit.sub.type', string="Unit Sub Type")
    unit_view_id = fields.Many2one('property.unit.view', string="Unit View")
    unit_usage_id = fields.Many2one('property.unit.usage', string="Unit Usage")
    start_date = fields.Date(string="Start Date")
    stop_date = fields.Date(string="Stop Date")
    status = fields.Char(string="Status")
    available_date = fields.Date(string="Available Date")
    tdays = fields.Integer(string="Total")
    rdays = fields.Integer(string="Rented")
    idays = fields.Integer(string="Idle")
    rent = fields.Float(string="Rent")
	
    @api.model
    def init(self):
        cr = self.env.cr
        tools.drop_view_if_exists(cr, 'property_unit_report')
        cr.execute("""
            create or replace view property_unit_report as (
                 SELECT
                    unit.id,
                    unit.name,
                    unit.property_id,
                    unit.main_property_id,
                    unit.unit_cat_id,
                    unit.floor_id,
                    unit.is_active,
                    unit.unit_manager_id,
                    unit.product_id,
                    unit.municipality_num,
                    unit.ew_contract_no,
                    unit.net_area,
                    unit.common_area,
                    unit.gross_area,
                    unit.unit_type_id,
                    unit.unit_sub_type_id,
                    unit.unit_view_id,
                    unit.unit_usage_id,
                    unit.start_date,
                    unit.stop_date,	
                    CASE 
                        WHEN MAX(cont.date_to) > current_date
                            THEN  'Occupied'
                        WHEN unit.stop_date IS NOT NULL
                            THEN  'Discontinued'
                        WHEN unit.is_active IS FALSE
                            THEN  'Not Available'
                        ELSE 'Available'
                    END AS status,
                    CASE 
                        WHEN MAX(cont.date_to) IS NOT NULL AND unit.is_active IS TRUE
                            THEN  MAX(cont.date_to) + 1
                        WHEN unit.is_active IS FALSE
                            THEN NULL
                        ELSE unit.start_date
                    END AS available_date,
                    CASE 
                        WHEN unit.stop_date IS NOT NULL
                            THEN unit.stop_date - unit.start_date
                        ELSE (current_date - unit.start_date) + 1
                    END AS tdays,
                    CASE 
                        WHEN cont.date_from IS NOT NULL
                        THEN ((current_date - cont.date_from) + 1) 
                        ELSE 0
                    END as rdays,
                    ((CASE 
                        WHEN unit.stop_date IS NOT NULL
                            THEN unit.stop_date - unit.start_date 
                        ELSE (current_date - unit.start_date) + 1
                    END) - 
                    (CASE 
                        WHEN cont.date_from IS NOT NULL
                        THEN ((current_date - cont.date_from) + 1) 
                        ELSE 0
                    END) ) AS idays,
                    SUM(cont.unit_rent) AS rent
                     
                FROM
                    property_unit unit
                    LEFT JOIN property_cont_unit cont ON unit.id = cont.unit_id
                GROUP BY
                    unit.id,
                    unit.name,
                    unit.property_id,
                    unit.main_property_id,
                    unit.unit_cat_id,
                    unit.floor_id,
                    unit.is_active,
                    unit.unit_manager_id,
                    unit.product_id,
                    unit.municipality_num,
                    unit.ew_contract_no,
                    unit.net_area,
                    unit.common_area,
                    unit.gross_area,
                    unit.unit_type_id,
                    unit.unit_sub_type_id,
                    unit.unit_view_id,
                    unit.unit_usage_id,
                    unit.start_date,
                    unit.stop_date,
                    cont.unit_rent,
                    cont.date_from,	
                    cont.date_to
            )
        """)






# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models

# UnitAnalysis
class ExpiryAnalysis(models.Model):
    _name = "property.expiry.analysis"
    _description = "Expiry Analysis"
    _auto = False
    _order = "unit_id ASC"
    
    property_id = fields.Many2one('property.master',string="Building")
    main_property_id = fields.Many2one('main.property',string="Property")
    renew_id = fields.Many2one('property.contract',string="Renewed Contract")
    contract_id = fields.Many2one('property.contract', string="Contract")
    floor_id = fields.Many2one('property.floor', string="Floor")
    unit_id = fields.Many2one('property.unit', string="unit")
    state = fields.Selection([('draft', 'Waiting Approval'),('post','Approved'),('progres', 'In Progress'),('close','Closure'),('done', 'Completed'),('cancel', 'Terminated'),], string='Status')
    c_end_date = fields.Date(string="C.Expire Date")
    unit_manager_id = fields.Many2one('res.users',string="Account Manager")
    product_id = fields.Many2one('product.product',string="CRM Product")
    municipality_num =fields.Char(string="Municipality")
    ew_contract_no = fields.Char(string="E & W Contract")
    net_area = fields.Float(string="Net Area")
    common_area = fields.Float(string="Common Area")
    gross_area = fields.Float(string="Gross Area" )
    unit_type_id = fields.Many2one('property.unit.type', string="Unit Type")
    unit_sub_type_id = fields.Many2one('property.unit.sub.type', string="Unit Sub Type")
    unit_view_id = fields.Many2one('property.unit.view', string="Unit View")
    unit_usage_id = fields.Many2one('property.unit.usage', string="Unit Usage")
    partner_id = fields.Many2one('res.partner', string="Partner")
    total_value = fields.Float(string="C.value")
	
    @api.model
    def init(self):
        cr = self.env.cr
        tools.drop_view_if_exists(cr, 'property_expiry_analysis')
        cr.execute("""
            create or replace view property_expiry_analysis as (
                 SELECT
                    pcu.id as id,
                    pcu.unit_id AS unit_id,
                    pcu.cont_id as contract_id,
                    pcu.build_id as property_id,
                    pcu.main_property_id as main_property_id,
                    
                    pcu.floor_id as floor_id,
                    contract.date_stop as c_end_date,
                    contract.state as state,
                    pc.unit_manager_id as unit_manager_id,
                    pc.product_id as product_id,
                    pc.municipality_num as municipality_num,
                    pc.ew_contract_no as ew_contract_no,
                    pc.net_area as net_area,
                    pc.common_area as common_area,
                    pc.gross_area as gross_area,
                    pc.unit_type_id as unit_type_id,
                    pc.unit_sub_type_id as unit_sub_type_id,
                    pc.unit_view_id as unit_view_id,
                    pc.unit_usage_id as unit_usage_id,
                    contract.customer_id as partner_id,
                    contract.total_value as total_value,
                    contract.renew_id as renew_id
                    
                    
                    
                    
                    
                FROM property_cont_unit pcu
                    left join property_unit pc on(pc.id = pcu.unit_id)
                    LEFT JOIN property_contract contract ON(contract.id = pcu.cont_id)
            
                WHERE contract.state != 'draft'
    
            )
        """)
