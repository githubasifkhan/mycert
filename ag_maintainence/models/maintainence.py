
from odoo import api, fields, models, tools, _ , SUPERUSER_ID
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta,date
from odoo.exceptions import except_orm, ValidationError ,UserError
import math
import re
from odoo.exceptions import Warning

class TaskMaster(models.Model):
    _name = 'task.master'
    _description = 'Task Master'
    _rec_name = 'name'

    name = fields.Char(required=True,string='Task Name')
    active = fields.Boolean('Active', default=True, copy=False)

class MaintainenceType(models.Model):
    _name = "maintainence.type"

    name = fields.Char('Type Name')
    active = fields.Boolean('Active', default=True, copy=False)

class MaintenanceTag(models.Model):
      
    _name = "maintenance.tag"
    _description = "Maintenance Tags"

    name = fields.Char('Tag Name', required=True, translate=True)
    color = fields.Integer('Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

class AccountMove(models.Model):
    _inherit = "account.move"

    maintenance_id = fields.Many2one('maintainence.service',string="Maintenance Related")


class MaintainenceService(models.Model):
    _name = "maintainence.service"
    _inherit = 'mail.thread'
    _rec_name = 'sequence'
    _order = 'sequence desc'

    @api.model
    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('maintainence.service')
        if 'requestor_contact' in vals and vals['requestor_contact']:
      
            if re.match("^[0-9]*$", vals['requestor_contact']) != None:
                pass
            else:
                raise UserError('Invalid Phone No ,Please enter Numbers')
        if 'req_email' in vals and vals['req_email']:

            if re.match("^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", vals['req_email']) != None:
                pass
            else:
                raise UserError('Not a valid E-mail Format') 
        return super(MaintainenceService, self).create(vals)

    def write(self, vals):
        if 'requestor_contact' in vals and vals['requestor_contact']:
      
            if re.match("^[0-9]*$", vals['requestor_contact']) != None:
                pass
            else:
                raise UserError('Invalid Phone No ,Please enter Numbers')
        if 'req_email' in vals and vals['req_email']:

            if re.match("^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", vals['req_email']) != None:
                pass
            else:
                raise UserError('Not a valid E-mail Format') 
        return super(MaintainenceService, self).write(vals)


    sequence = fields.Char(string='Request No',  readonly=True,copy=False)
    requestor_name = fields.Char(string='Requestor Name',required=True)
    requested_date = fields.Datetime('Requested Date',default=datetime.today(),required=True)
    requestor_contact = fields.Char(string='Contact Number',help="Mobile Number of the contact",
                                      track_visibility='onchange', track_sequence=5, index=True,required=True)
    req_email = fields.Char(string='Email',help="Email of the contact",
                                      track_visibility='onchange', track_sequence=4, index=True)
    acc_bldng_id = fields.Many2one('property.master',string='Building',required=True)
    acc_floor_id = fields.Many2one('property.floor', string='Floor',required=True)
    acc_unit_id = fields.Many2one('property.unit', string='Unit',required=True)
    assigned_dept = fields.Many2one('task.master', string='Assigned Department')
    priority = fields.Selection([('0', 'Low'),('1', 'Low'), ('2', 'Medium'), ('3', 'High')], string='Priority',default='1')
    type = fields.Many2one('maintainence.type', string='Type',required=True,domain=[('active','=',True)])
    description = fields.Html(string='Complaint Description', copy=True,required=True)
    schedule_start_date = fields.Datetime(string='Schedule Start Date')
    schedule_end_date = fields.Datetime(string='Schedule End Date')
    shutdown_type = fields.Selection([('yes','Yes'),('no','No')],string="Shutdown Required",default='no')
    add_desc = fields.Html(string='Additional Description',copy=False)
    tot_cost = fields.Float(string='Actual Total Cost',required=True, compute='_amount_tot')
    estimate_tot_cost = fields.Float(string='Estimation Total Cost',required=True, compute='_amount_tot')
    work_order_line = fields.One2many('maintainence.service.line', 'operation_id', string='Details',copy=False, auto_join=True)
    analytic_count = fields.Integer('Analytic Count',compute="get_analytic_count")
    picking_count = fields.Integer('Analytic Count',compute="get_analytic_count")
    tag_ids = fields.Many2many('maintenance.tag', 'maintenance_service_tag_rel', 'main_id', 'tag_id', string='Tags', help="Classify and analyze your Maintenance categories like: Service ...etc")
    deadline_date = fields.Datetime(string='Deadline Date')
    state = fields.Selection([
        ('new', 'Draft'),
        ('confirm', 'Confirmed'),
        #('ir_approve', 'Waiting For Approval'),
        # ('approved','Approved'),
        ('wo_created', 'Open Work Order'),
        ('wo_closed', 'Closed Work Order'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled')], string='State', default="new")
    invoice_created = fields.Integer('Invocie Created',default=0)
    invoice_count = fields.Integer('Invocie Count',compute="get_analytic_count")

    def action_reject(self):
        self.write({'state':'reject'})

    def set_to_draft(self):
        self.write({'state':'new'})

    def action_cancel(self):
        self.write({'state':'cancel'})
    
    def action_close(self):
        self.write({'state':'wo_closed'})


    def create_invoice(self):
        for rec in self:
            invoice = self.env['account.move']
            customer = False
            if rec.acc_unit_id.rent_line:
                for rent in rec.acc_unit_id.rent_line:
                    if date.today() >= rent.date_from and date.today() < rent.date_to:
                        customer = rent.customer_id.id
                    else:
                        raise UserError('The contract of this unit %s is already over' %rec.acc_unit_id.name)
            else:
                raise UserError('This unit %s didnot have any contract related'%rec.acc_unit_id.name)
            data = []
            invoices = []
            # for unit in rec.unit_ids:
            if not self.env.company.maintainence_services_product:
                raise UserError('Please go to maintenance settings and add the product there')
            values = {
                'product_id':self.env.company.maintainence_services_product.id,
                'quantity':1,
                'price_unit':rec.tot_cost,
            }
            invoices.append((0,0,values))
            if not self.env.company.main_journal_id:
                raise UserError('Please go to maintenance settings and add the journal there')
            vals = {
                'invoice_date':date.today(),
                'type':'out_invoice',
                'ref':rec.sequence ,
                'partner_id':customer,
                'journal_id':self.env.company.main_journal_id.id,
                'maintenance_id':rec.id,
                'invoice_line_ids':invoices,
            }
            data.append(vals) 

            invoice.create(data) 
            rec.write({'invoice_created':1})


    def show_picking_lines(self):
        return {
			'name': 'Pickings',
			'type': 'ir.actions.act_window',
            'views': [(self.env.ref('stock.vpicktree').id,'tree'),(self.env.ref('stock.view_picking_form').id,'form')],
			'view_mode': 'tree,form',
			'view_type': 'form',
			'res_model': 'stock.picking',
			'domain': [('maintenance_id', '=', self.id)],
		}

    @api.depends('work_order_line')
    def _amount_tot(self):

        for record in self:
            cost = 0.0
            est_cost = 0.0
            for line in record.work_order_line:
                cost += line.total_cost
                est_cost += line.total_job_estimate


            record.tot_cost = cost
            record.estimate_tot_cost = est_cost

        return False

    def confirm_requisition(self):
        res = self.write({
            'state': 'confirm',
            #'confirmed_by_id': self.env.user.id,
           # 'confirmed_date': datetime.now()
        })
        return res

    def approve_requisition(self):
        res = self.write({
            'state': 'wo_created',
            #'confirmed_by_id': self.env.user.id,
           # 'confirmed_date': datetime.now()
        })
        return res

    def get_analytic_count(self):
        for rec in self:
            analytic = self.env['account.analytic.line'].search([('maintenance_id','=',rec.id)])
            rec.analytic_count = len(analytic)
            picking = self.env['stock.picking'].search([('maintenance_id','=',rec.id)])
            rec.picking_count = len(picking)
            invoice = self.env['account.move'].search([('maintenance_id','=',rec.id)])
            rec.invoice_count = len(invoice)

    def show_analytic_lines(self):
        return {
			'name': 'Analytic Accounts',
			'type': 'ir.actions.act_window',
            'views': [(self.env.ref('analytic.view_account_analytic_line_tree').id,'tree')],
			'view_mode': 'tree',
			'view_type': 'form',
			'res_model': 'account.analytic.line',
			'domain': [('maintenance_id', '=', self.id)],
		}

    def show_invoices(self):
              return {
			'name': 'Invoices',
			'type': 'ir.actions.act_window',
            # 'views': [(self.env.ref('analytic.view_account_analytic_line_tree').id,'tree')],
			'view_mode': 'tree,form',
			'view_type': 'form',
			'res_model': 'account.move',
			'domain': [('maintenance_id', '=', self.id)],
		}
        # return {
        #     'name': 'Analytic Accounts',
        #     'view_type': 'form',
        #     'view_mode': 'tree',
        #     'views': [(self.env.ref('view_analytic_account_tree_inherit').id,'tree')],
        #     'res_model': 'account.analytic.line',
        #     'domain': [('maintenance_id', '=', self.id)],
        #     'type': 'ir.actions.act_window',
        # }
        

    def close_requisition(self):
        for rec in self:
            analytic = self.env['account.analytic.line']
            data = []
            for line in rec.work_order_line:
                if line.stage_id.is_done == False:
                    raise UserError("Please check that all the job orders related to this requisition are completed")
                # if line.operation_type == 'emp':
                #     vals={
                #         'name':line.name,
                #         'amount':line.subtotal,
                #         'unit_amount':line.required_qty,
                #         'product_uom_id':line.uom_id.id,
                #         'employee_assigned':line.resource.id,
                #         'maintenance_id':rec.id,
                #         'account_id':line.account_id.id,
                #     }
                #     data.append(vals)
            picking = self.env['stock.picking'].search([('maintenance_id','=',rec.id),('state','not in',['done','cancel'])])
            for pick in picking:
                # raise UserError(pick.id)
                pick.move_ids_without_package.quantity_done = pick.move_ids_without_package.reserved_availability
                pick.button_validate()
            # raise UserError("jjjjjjj")
            # analytic.create(data)
            
        
        self.write({'state': 'wo_closed'})

    def cancel_requisition(self):
        res = self.write({
            'state': 'cancel',
            # 'confirmed_by_id': self.env.user.id,
            # 'confirmed_date': datetime.now()
        })
        return res

    @api.onchange('acc_bldng_id')
    def _onchange_get_floor_id(self):

        if self.acc_bldng_id:
            return{
                'domain':{'acc_floor_id':[('property_id','=',self.acc_bldng_id.id)]}
            }

        else:

            return {
                'domain':{'acc_floor_id':[]},
            }

    @api.onchange('acc_floor_id')
    def _onchange_get_unit_id(self):

        if self.acc_floor_id:
            return {
                'domain': {'acc_unit_id': [('floor_id', '=', self.acc_floor_id.id)]}
            }

        else:

            return {
                'domain': {'acc_unit_id': []},
            }

class MaintainenceServiceLine(models.Model):

    _name= 'maintainence.service.line'
    _description = 'Work Order Line'

    def _default(self):
        stage = self.env['job.order.stage'].search([('is_first','=',True)])
        if stage:
            for stages in stage:
                sid = stages.id
        else:
            raise UserError('You should assign one of the operation stage as first stage to came here as default')
        return sid


    sequence = fields.Integer(string='Sequence', default=1)
    sequence_ref = fields.Char(string='Operation No')
    operation_id = fields.Many2one('maintainence.service', string='Operation ID',  ondelete='cascade', index=True, copy=False)
    name = fields.Char(string='Operation Description',required=True)
    department = fields.Many2one('task.master', string='Assigned Department')
    # operation_type = fields.Selection([('equip','Equipment'),('emp','Employee')])
    # resource = fields.Many2one('hr.employee',string='Resource')
    # resource_cost = fields.Float(string='Cost')
    # required_qty = fields.Float(string='Required Quantity')
    # start_date = fields.Datetime(string='Start Date')
    # end_date = fields.Datetime(string='End Date')
    # deadline_date = fields.Datetime(string='Deadline Date')
    schedule_start_date = fields.Datetime(string='Schedule Start Date')
    schedule_end_date = fields.Datetime(string='Schedule End Date')
    # product_id = fields.Many2one('product.product', string="Item Type")
    # description = fields.Char(related='product_id.name',string="Item Description")
    # account_id = fields.Many2one('account.analytic.account',string="Analytic Account")
    # uom_id = fields.Many2one('uom.uom', string="UOM")
    # item_code = fields.Char(related='product_id.default_code',string='Item Code')
    # price_unit = fields.Float(string='Cost')
    # subtotal = fields.Float(string='Subtotal',compute="get_total_cost")
    stage_id = fields.Many2one('job.order.stage', string='Stage', ondelete='restrict',default=_default, tracking=True, index=True, copy=False,
                group_expand='_read_group_stage_ids')
    color = fields.Integer('Color Index', default=0)
    # estimated_start_date = fields.Datetime('Estimated Start date')
    # estimated_end_date = fields.Datetime('Estimated End date')
    failure_resolution = fields.Char(string='Failure Resolution')
    failure_cause = fields.Char(string='Failure Cause')
    failure_desc = fields.Html(string='Failure Description',copy=False)
    material_estimation_ids = fields.One2many('material.estimate','material_id','Material Estimation')
    labour_estimation_ids = fields.One2many('labour.estimate','labour_id','Labour Estimation')
    material_actual_line_ids = fields.One2many('materal.cost.line','material_job_cost_sheet_id','Material Job Cost Line')
    actual_timesheet_ids = fields.One2many('actual.labour.estimate', 'task_id', 'Timesheets')
    total_material_estimate = fields.Float(compute='_calculate_total',string='Total Material Estimate',default=0.0,readonly=True,store=True)
    total_labour_estimate = fields.Float(compute='_calculate_total',string='Total Labour Estimate',default=0.0,readonly=True,store=True)
    total_job_estimate = fields.Float(compute='_calculate_total',string='Total Job Estimate',default=0.0,readonly=True,store=True)
    total_material_cost = fields.Float(compute='_compute_total_material_cost',string="Total Material Cost",default=0.0)
    total_labour_cost = fields.Float(compute='_compute_total_material_cost',string="Total Labour Cost",default=0.0)
    total_cost = fields.Float(compute='_compute_total_cost',string='Total Cost',default=0.0)
    effective_hours = fields.Float(compute='_compute_total_hours',string='Total Hours',default=0.0)
    is_done = fields.Boolean('Is Done',default=False)
    probability = fields.Integer('Probability',default=0)
    material_diff = fields.Float('Material differance',compute="_calculate_diff")
    labour_diff = fields.Float('Labour differance',compute="_calculate_diff")
    total_diff = fields.Float('Total differance',compute="_calculate_diff")

    @api.depends('total_material_cost','total_material_estimate','total_labour_cost','total_labour_estimate','total_job_estimate','total_cost')
    def _calculate_diff(self):
        for rec in self:
            rec.material_diff = abs(rec.total_material_cost - rec.total_material_estimate)
            rec.labour_diff = abs(rec.total_labour_cost - rec.total_labour_estimate)
            rec.total_diff = abs(rec.total_cost - rec.total_job_estimate)


    def write(self,vals):
        # if vals.get('stage_id'):
        #     if vals.get('probability') == 100:
                # stage_id = self.env['crm.stage'].search([('is_done','=',True)])
                # for stage in stage_id:
                #     vals.update({'stage_id': stage.id})
                
        if 'stage_id' in vals:
            stage_id = self.env['job.order.stage'].browse(vals['stage_id'])
            if stage_id.is_done:
                vals.update({'probability': 100,'is_done':True})
            else:
                vals.update({'probability': 0,'is_done':False})

        return super(MaintainenceServiceLine,self).write(vals)



    def mark_as_done(self):
        for rec in self:
            if rec.operation_id:
                # main = self.env['maintainence.service']
                if rec.material_actual_line_ids:
                    picking = self.env['stock.picking']
                    data = []
                    for line in rec.operation_id.work_order_line:
                        if line.id == rec.id:
                            for actual in line.material_actual_line_ids:
                                vals={
                                    'product_id':actual.product_id,
                                    'name':line.name,
                                    'product_uom':actual.uom_id.id,
                                    'product_uom_qty':actual.quantity,
                                }
                                data.append((0,0,vals))

                    pick={
                        'origin':rec.operation_id.sequence,
                        'maintenance_id':rec.operation_id.id,
                        'scheduled_date':rec.operation_id.requested_date,
                        'picking_type_id':self.env.company.picking_type_id_property_main.id,
                        'location_id':self.env.company.location_id_property_main.id,
                        'location_dest_id':self.env.company.location_dest_id_property_main.id,
                        'move_ids_without_package':data,
                            }

                    pick_id = picking.create(pick)
                    pick_id.action_confirm()
                    pick_id.action_assign()
            stage_id = self.env['job.order.stage'].search([('is_done','=',True)])
            for stage in stage_id:
                # vals.update({'stage_id': stage.id})
                rec.write({
                    'stage_id': stage.id,
                })

    @api.depends('material_actual_line_ids.subtotal','actual_timesheet_ids.subtotal')
    def _compute_total_material_cost(self):
        total = 0.0
        labour_total = 0.0
        for line in self.material_actual_line_ids:
            total += line.subtotal
        for lines in self.actual_timesheet_ids:
            labour_total += (lines.unit_price * lines.hours) - (lines.unit_price * lines.hours) * (lines.discount or 0.0) / 100.0
        self.total_material_cost = total
        self.total_labour_cost = labour_total
    
    @api.depends('total_material_cost','total_labour_cost')
    def _compute_total_cost(self):
        total = 0.0
        for sheet in self:
            total = sheet.total_material_cost + sheet.total_labour_cost
            sheet.total_cost = total 

    @api.depends('actual_timesheet_ids.hours')
    def _compute_total_hours(self):
        for rec in self:
            total = 0.0
            for sheet in rec.actual_timesheet_ids : 
                total += sheet.hours
            rec.effective_hours = total 

    @api.depends('material_estimation_ids.subtotal','labour_estimation_ids.subtotal')
    def _calculate_total(self):
        total_job_cost = 0.0
        total_labour_cost = 0.0
        for order in self:
            material_price = 0.0
            for line in order.material_estimation_ids:
                material_price +=  (line.quantity * line.unit_price) - (line.quantity * line.unit_price) * (line.discount or 0.0) / 100.0
                
            order.total_material_estimate = material_price

                # total_job_cost += material_price
            labour_price = 0.0
            for line in order.labour_estimation_ids:
                labour_price +=  (line.unit_price * line.hours) - (line.unit_price * line.hours) * (line.discount or 0.0) / 100.0
            order.total_labour_estimate = labour_price

                # total_labour_cost += labour_price
			
            order.total_job_estimate = order.total_labour_estimate + order.total_material_estimate

    # def actual_material(self):
    #     if self.name:
    #         self.material_actual_line_ids.unlink()
    #         vals = {}
    #         loc = []
    #         location_obj = self.env['stock.location']
    #         task =self.id
    #         project = self.project_id.analytic_account_id.id
    #         sour_loc = location_obj.search([('usage','=','internal'),('barcode','=','WH-STOCK')])
    #         loc.append(sour_loc.id)
    #         dest_loc = location_obj.search([('usage','=','production')])
    #         loc.append(dest_loc.id)
    #         res = self.env['n2n.stock.move.analysis.view'].search([('analytic_id','=',project),('task_id','=',task),('source','in',loc),('destination','in',loc)])
    #         for i in res:
    #             self.env['materal.cost.line'].create({
    #                 'product_id': i.product_id.id, 
    #                 'quantity': i.qty, 
    #                 'uom_id': i.uom_id.id, 
	# 				'task_id':i.task_id.id,
	# 				'unit_price': i.price_unit,
	# 				'reference': i.picking_name,
	# 				'material_job_cost_sheet_id':self.id
    #                 })

    

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = [('active', '=', True)]
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
    # @api.onchange('resource')
    # def _onchange_resource(self):
    #     for line in self:
    #         cost = 0
    #         for l in line.operation_id.work_order_line:
    #             cost = l.resource.timesheet_cost
    #             l.resource_cost = cost
    # @api.depends('required_qty','required_qty','price_unit')
    # def get_total_cost(self):
    #     for rec in self:
    #         if rec.operation_type == 'emp':
    #             rec.subtotal = rec.required_qty * rec.resource_cost
    #         else:
    #             rec.subtotal = rec.required_qty * rec.price_unit


    # @api.onchange('resource')
    # def _onchnage_resource(self):
    #     self.resource_cost = self.resource.timesheet_cost



    #hide = fields.Boolean(string='Hide')# compute="_compute_hide")

    # @api.depends('operation_id.work_order_line')
    # def _sequence_ref(self):
    #     for line in self:
    #         if not line.sequence_ref:
    #             line.sequence_ref = 0

    #         no = 0
    #         for l in line.operation_id.work_order_line:
    #             no += 1
    #             l.sequence_ref = no

    # @api.depends('operation_type')
    # def _compute_hide(self):
    #     # simple logic, but you can do much more here
    #     if self.operation_type == 'emp':
    #         self.hide = True
    #     else:
    #         self.hide = False

class JobOrderStage(models.Model):
    _name = "job.order.stage"
    _description = "Job Order Stages"
    _rec_name = 'name'
    _order = "sequence, name, id"


    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    fold = fields.Boolean('Folded in Pipeline',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')
    active = fields.Boolean('Active',default=True)
    is_done = fields.Boolean('Is Done Stage ?',default=False)
    is_first = fields.Boolean('Is First Stage ?',default=False)
    requirements = fields.Text('Requirements', help="Enter here the internal requirements for this stage (ex: Offer sent to customer). It will appear as a tooltip over the stage's name.")
    

class AnalyticAccount(models.Model):
      
    _inherit = 'account.analytic.line'

    employee_assigned = fields.Many2one('hr.employee',string="Assigned Employee")
    maintenance_id = fields.Many2one('maintainence.service',string="Maintenance Request ID")

class StockPicking(models.Model):
      
    _inherit = 'stock.picking'

    maintenance_id = fields.Many2one('maintainence.service',string="Maintenance Request ID")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    picking_type_id_property_main = fields.Many2one('stock.picking.type',related="company_id.picking_type_id_property_main",string='Operation Type', readonly=False)
    location_id_property_main  = fields.Many2one('stock.location',related="company_id.location_id_property_main",string='Source Location', readonly=False)
    location_dest_id_property_main  = fields.Many2one('stock.location',related="company_id.location_dest_id_property_main",string='Destination Source Location', readonly=False)
    maintainence_services_product  = fields.Many2one('product.product',related="company_id.maintainence_services_product",string='Maintainence Services Product', readonly=False)
    main_journal_id  = fields.Many2one('account.journal',related="company_id.main_journal_id",string='Maintainence Journal', readonly=False)


class Company(models.Model):
    _inherit = "res.company"

    picking_type_id_property_main = fields.Many2one('stock.picking.type',string='Operation Type')
    location_id_property_main  = fields.Many2one('stock.location',string='Source Location')
    location_dest_id_property_main  = fields.Many2one('stock.location',string='Destination Source Location')
    maintainence_services_product  = fields.Many2one('product.product',string='Maintenance Services Product')
    main_journal_id  = fields.Many2one('account.journal',string='Maintenance_id Journal')



class MaterialEstimate(models.Model):
    _name = "material.estimate"

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        self.quantity = 1.0
        self.unit_price = self.product_id.standard_price
		
	
    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id
			
    @api.onchange('quantity', 'unit_price','discount')
    def onchange_quantity(self):
        price = 0.0
        for line in self:
            price =  (line.quantity * line.unit_price) - (line.quantity * line.unit_price) * (line.discount or 0.0) / 100.0
            line.subtotal = price
			
    material_id = fields.Many2one('maintainence.service.line','Operation Line' )
    type = fields.Selection([('equip','Equipment')],string='Type',default='equip',invisible=True, readonly=1)
    product_id = fields.Many2one('product.product','Product',required=True)
    description = fields.Text('Description')
    quantity = fields.Float('Quantity',default=0.0)
    uom_id = fields.Many2one('uom.uom','Unit Of Measure')
    unit_price = fields.Float('Unit Price',defaut=0.0)
    discount = fields.Float('Discount (%)',default=0.0)
    subtotal = fields.Float('Sub Total',defalut=0.0)
    currency_id = fields.Many2one('res.currency', compute='get_currency_id', string="Currency")


class ActualMaterialLine(models.Model):
    _name = "materal.cost.line"
	
    material_job_cost_sheet_id = fields.Many2one('maintainence.service.line','Operation Line')
    date = fields.Datetime('Date',invisible=True,default=datetime.now())
    # job_type_id = fields.Many2one('job.type',string='Job Type')
    product_id = fields.Many2one('product.product','Product',required=True)
    description = fields.Text('Description')
    reference = fields.Char('Reference')
    quantity = fields.Float('Quantity',default=1.0)
    uom_id = fields.Many2one('uom.uom','Unit Of Measure')
    unit_price = fields.Float('Cost/Unit Price',defaut=0.0)
    # actual_purchase_qty = fields.Float(compute='_compute_purchase_quantity',string='Actual Purchased Quantity',default=0.0)
    # actual_invoice_qty = fields.Float(compute='_compute_invoice_quantity',string='Actual Invoice Quantity',default=0.0)
    subtotal = fields.Float(compute='onchange_quantity',string='Sub Total',defalut=0.0)
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
    job_type = fields.Selection([('material','Material'),('labour','Labour'),('overhead','Overhead')],string="Job Cost Order Type")
    #Labour
    task_id = fields.Many2one('project.task', string="Task")
    hours = fields.Float('Hours',default=0.0)
    actual_timesheet_hours = fields.Float('Actual Timesheet Hours',default=0.0)
    #Overhead
    basis = fields.Char('Basis')


    @api.onchange('quantity', 'unit_price')
    def onchange_quantity(self):
        for line in self:
            price = line.quantity * line.unit_price
            if line.hours:
                price = line.hours * line.unit_price
            line.subtotal = price
			
	
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        self.description = self.product_id.name
		
	
    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id


class LabourEstimate(models.Model):
    _name = "labour.estimate"

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        # self.quantity = 1.0
        self.unit_price = self.product_id.standard_price
		

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id


    @api.onchange('hours','quantity', 'unit_price', 'discount')
    def onchange_quantity(self):
        price = 0.0
        for line in self:
            price = (line.unit_price * line.hours) - (line.unit_price * line.hours) * (line.discount or 0.0) / 100.0
            line.subtotal = price

    labour_id = fields.Many2one('maintainence.service.line','Operation Line')
    type = fields.Selection([('emp','Employee')],string='Type',  default='emp',invisible=True, readonly=1)
    product_id = fields.Many2one('product.product','Product',required=True)
    description = fields.Text('Description')
    quantity = fields.Float('Employees NO',default=0.0)
    uom_id = fields.Many2one('uom.uom','Unit Of Measure')
    unit_price = fields.Float('Unit Price',defaut=0.0)
    discount = fields.Float('Discount (%)',default=0.0)
    subtotal = fields.Float('Sub Total',defalut=0.0)
    currency_id = fields.Many2one('res.currency', compute='get_currency_id', string="Currency")
    hours = fields.Float('Hours', digits=(2,2))

	
    @api.constrains('hours')
    def _check_values(self):
        for rec in self:
            if rec.hours <= 0.0 :
                raise Warning(_('Working hours should not be zero or Negative.'))



class ActualLabourEstimate(models.Model):
    _name = "actual.labour.estimate"

	
    @api.onchange('employee_id')
    def onchange_product_id(self):
        res = {}
        if not self.employee_id:
            return res
        # self.quantity = 1.0
        self.unit_price = self.employee_id.timesheet_cost
		

    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id


    @api.onchange('hours','quantity', 'unit_price', 'discount')
    def onchange_quantity(self):
        price = 0.0
        for line in self:
            price = (line.unit_price * line.hours) - (line.unit_price * line.hours) * (line.discount or 0.0) / 100.0
            line.subtotal = price

    task_id = fields.Many2one('maintainence.service.line','Operation Line')
    type = fields.Selection([('emp','Employee')],string='Type',  default='emp',invisible=True, readonly=1)
    employee_id = fields.Many2one('hr.employee','Employee',required=True)
    description = fields.Text('Description')
    quantity = fields.Float('Employees NO',default=0.0)
    uom_id = fields.Many2one('uom.uom','Unit Of Measure')
    unit_price = fields.Float('Unit Price',defaut=0.0)
    discount = fields.Float('Discount (%)',default=0.0)
    subtotal = fields.Float('Sub Total',defalut=0.0)
    currency_id = fields.Many2one('res.currency', compute='get_currency_id', string="Currency")
    hours = fields.Float('Hours', digits=(2,2))

	
    @api.constrains('hours')
    def _check_values(self):
        for rec in self:
            if rec.hours <= 0.0 :
                raise Warning(_('Working hours should not be zero or Negative.'))