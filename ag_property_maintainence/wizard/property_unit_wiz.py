from odoo import models, fields, api
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo import exceptions, _
from odoo.exceptions import Warning

class PropertyUnitWiz(models.TransientModel):
    _name = 'property.unit.wiz'
    _description = 'Generate Units'    

    name = fields.Char(string="Name", required="1")
    property_id = fields.Many2one('property.master', string="Building", required="1") 
    floor_ids = fields.Many2many('property.floor',  string="Floor", required="1")
    unit_count = fields.Integer(string="Units Count", required="1")
    unit_cat_id = fields.Many2one('property.unit.category', string="Category", required="1") 
    gross_area = fields.Float(string="Total SQFT", required="1")
    common_area = fields.Float(string="Common Area", required="1")
    unit_type_id = fields.Many2one('property.unit.type', string="Unit Type", required="1") 
    unit_sub_type_id = fields.Many2one('property.unit.sub.type', string="Unit Sub Type", required="1") 
    unit_view_id = fields.Many2one('property.unit.view', string="Unit View", required="1") 
    unit_usage_id = fields.Many2one('property.unit.usage', string="Unit Usage", required="1") 
    start_date = fields.Date(string="Start Date", required="1") 
    
    def gen_unit(self):
        unit_obj = self.env['property.unit']
        floor_ids = self.floor_ids
        no_of_floors = len(floor_ids)
        if self.property_id and self.unit_count >0:
            count = 1
            line = self.unit_count
            for floor in floor_ids:
            	for x in range(0,line):
                	net_area = self.gross_area - self.common_area
                	unit_vals = {'name': self.name + ' -' + str(count),
                	            'unit_name': self.name + ' -' + str(count),
                            'unit_cat_id': self.unit_cat_id.id,
                            'property_id':self.property_id.id,
                            'floor_id': floor.id,
                            'code':count,
                            'gross_area':float(self.gross_area) / float(no_of_floors),
                            'common_area':float(self.common_area) / float(no_of_floors),
                            'net_area':float(net_area) / float(no_of_floors),
                            'unit_type_id':self.unit_type_id.id,
                            'unit_sub_type_id':self.unit_sub_type_id.id,
                            'unit_view_id':self.unit_view_id.id,
                            'unit_usage_id':self.unit_usage_id.id,
                            'start_date':self.start_date}
                	unit = unit_obj.create(unit_vals)
                	unit_id = unit.id
                	count += 1


