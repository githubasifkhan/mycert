from odoo import models, fields, api
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo import exceptions, _
from odoo.exceptions import Warning

class PropertyFloortWiz(models.TransientModel):
    _name = 'property.floor.wiz'
    _description = 'Generate Floor'    

    name = fields.Char(string="Name", required="1")
    property_id = fields.Many2one('property.master', string="Building", required="1") 
    floor_count =  fields.Integer(string="Floor Count", required="1") 
    gross_area = fields.Float(string="Total SQFT", required="1")
    com_area = fields.Float(string="Common Area", required="1")
    unit_count = fields.Integer(string="No of Units", required="1")
            
    @api.onchange('property_id')
    def property_id_onchange(self):
    	if self.property_id:
    		tot_sqft = self.property_id.tot_sqft
    		com_area = self.property_id.com_area
    		self.com_area = com_area
    		self.gross_area = tot_sqft	
    		self.floor_count = self.property_id.floors_count
    def gen_floor(self):
        floor_obj = self.env['property.floor']
        if self.property_id and self.floor_count >0:
            count = 1
            line = self.floor_count
            for x in range(0,line):
                net_area = self.gross_area - self.com_area
                floor_vals = {'name': self.name + ' -' + str(count),
                            'floor_name':self.name + ' -' + str(count),
                            'level': str(count),
                            'property_id':self.property_id.id,
                            'gross_area':self.gross_area,
                            'com_area':self.com_area,
                            'code': count,
                            'net_area':net_area,
                            'unit_count':self.unit_count}
                floor = floor_obj.create(floor_vals)
                flr_id = floor.id
                count += 1
