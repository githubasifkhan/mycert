# -*- coding: utf-8 -*-
from odoo import models, fields, api,_


class WarningForContract(models.TransientModel):
	
	_name = "warning.wiz"

	contract=fields.Many2one('property.contract')
	def ok_button(self):
		print ('kkkkkkkkkk',self.contract)
		self.contract.payment_line.unlink()
