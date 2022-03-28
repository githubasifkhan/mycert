from odoo import models, fields, api
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from odoo import models, fields, api
from odoo import exceptions, _
from odoo.exceptions import Warning
import datetime as dt
from datetime import  timedelta, tzinfo, time, date, datetime
from dateutil.relativedelta import relativedelta
import ast

class ContractRevenueGeneration(models.TransientModel):
    _name = 'contract.revenue.calculation.wizard'
    _description = 'ContractRevenuetGeneration'

    #
    def no_of_years_intersect(self,ds,dt):
        from datetime import datetime
        d1 = datetime.strptime(ds, "%Y-%m-%d")
        d2 = datetime.strptime(dt, "%Y-%m-%d")
        days = abs((d2 - d1).days)+1
        if days <= 366:
            return 1
        elif days > 366 and days <=730:
            return 2
        elif days > 730 and days<=1096:
            return 3
        elif days > 1096 and days<=1460:
            return 4
        else:
            return 5
    
    wiz_line = fields.One2many('contract.revenue.calculation.wizard.line', 'wiz_id', string='Wiz Line',)
    contract_id = fields.Many2one('property.contract','Contract')
    name = fields.Char(string="Name",)
        
    #
    def get_add_year(self,ds,free):
        start_dt = datetime.strptime(str(ds), "%Y-%m-%d")
        free = free
        rent_dt = start_dt + relativedelta(years=free)
        new_date = rent_dt.strftime("%Y-%m-%d")
        return new_date


    #
    def get_min_condate(self,ds,free):
        start_dt = datetime.strptime(ds, "%Y-%m-%d")
        free = free
        rent_dt = False
        if free > 0:
            
            
            rent_dt = start_dt + timedelta(days=free)
        else:
            rent_dt = start_dt + timedelta(days=free-1)             
        new_date = rent_dt.strftime("%Y-%m-%d")
        return new_date
        
    def days_between(self,d1, d2):
        from datetime import datetime
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        val = abs((d2 - d1).days)+1
        if val==364 or val==366:
            return 365
            
        return val
        
    #
    def get_adjust_start_date(self,ds,con_start):
        con_start = datetime.strptime(con_start, '%Y-%m-%d').strftime('%d-%m-%Y')
        con_start_without_year = str(con_start)[:6]
        ds_year = ds[:4]
        new_date = con_start_without_year + ds_year
        new_date = datetime.strptime(new_date, '%d-%m-%Y').strftime('%Y-%m-%d')
        return str(new_date)
    #
    def get_end_date(self,d1):
       # d1 = datetime.combine(d1,datetime.min.time())
        d1 = datetime.strptime(str(d1), '%Y-%m-%d')
        d1 = d1 + relativedelta(years=1)
        d1 = d1 + timedelta(days=-1)
        new_date = d1
        return new_date




    #
    def get_month_end_date(self,d1):
        d1 = datetime.strptime(str(d1)[:10], '%Y-%m-%d')
        d1 = d1 + relativedelta(months=1)
        d1 = d1 + timedelta(days=-1)
        return str(d1)
        
    #
    def get_no_of_years(self,d1,d2):
        print('---enteered yr function---')
        d1 = datetime.strptime(str(d1), '%Y-%m-%d')
        d2 = datetime.strptime(str(d2), '%Y-%m-%d')
        days = abs((d2 - d1).days)+1
        print('--days---',days)
        diffyears = d2.year - d1.year
        print('--diffyears---', diffyears)
        if diffyears == 1 and days >720:
            diffyears = 2
        
        if diffyears == 0:
            diffyears = 1   
        return diffyears 
    #
    def get_add_month(d1,var):
        d1 = datetime.strptime(d1, '%Y-%m-%d')
        d1 = d1 + relativedelta(months=var)
        return d1
    #
    def get_no_of_months(self,d1,d2):
        d1 = datetime.strptime(d1, '%Y-%m-%d')
        d2 = datetime.strptime(d2, '%Y-%m-%d')
        r = relativedelta.relativedelta(d2, d1)
        return r.months
        

    #
    def get_add_months(self,d1,var):
        d1 = datetime.strptime(str(d1), '%Y-%m-%d')
        d1 = d1 + relativedelta(months=var)
        return d1       
        
    
        
        
    #
    def get_adjust_end_date(self,ds,con_end,line_to_date):
        line_to_date = datetime.strptime(line_to_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        line_to_date_without_year = str(line_to_date)[:6]
        ds_year = ds[:4]
        con_end = datetime.strptime(con_end, '%Y-%m-%d').strftime('%d-%m-%Y')
        con_end_without_year = str(con_end)[:6]
        new_date = line_to_date_without_year + ds_year
        new_date = datetime.strptime(new_date, '%d-%m-%Y').strftime('%Y-%m-%d')
        return str(new_date)
    #   
    def get_month_day_range(self,date):

        #date = datetime.combine(date, datetime.min.time())
        date = datetime.strptime(str(date), '%Y-%m-%d')
        last_day = date + relativedelta(day=1, months=+1, days=-1)

        print('---last_day--',last_day)
        first_day = date + relativedelta(day=1)
        print('---first_day--', first_day)
        return  first_day, last_day
    #   
    def get_nxt_month_day_range(self,date):
        date = datetime.strptime(str(date), '%Y-%m-%d')
        first_day = date + relativedelta(day=1,months=+1)
        return first_day
        
    #   
    def get_months_between_dates(self,d1,d2):
        print('---enter month function---')
        from datetime import datetime
        d1 = datetime.strptime(str(d1)[:10], "%Y-%m-%d")
        d2 = datetime.strptime(str(d2)[:10], "%Y-%m-%d")
        val = float(abs((d2 - d1).days)+1) / float(30)
        print('---before val---',val)
        val = int(round(val))
        print('---after val--',val)
        return val
        
    #   
    def get_no_of_days_currentmonth(self,d1,d2):
        from datetime import datetime
        # d1 = datetime.strptime(str(d1)[:10], "%Y-%m-%d")
        # d1 = datetime.strptime(d1, "%Y-%m-%d %H.%M")
        # d1 = datetime.strftime(d1,"%Y-%m-%d")
        print("---------d1-----",d1)
        print("---------d2-----",d2)

        # d1 = datetime.strptime(str(d1), '%Y-%m-%d')
        d1 = datetime.date(d1)
        d2 = datetime.date(d2)
        print("---------d1-----", d1)
        print("---------d2-----", d2)
        # d2 = datetime.strptime(str(d2)[:10], "%Y-%m-%d")
        # d2 = datetime.strptime(d2, "%Y-%m-%d %H.%M")
        # d2 = datetime.strftime(d2,"%Y-%m-%d")
        # d2 = datetime.strptime(str(d2), '%Y-%m-%d')
        val = abs((d2 - d1).days)+1 
        return val

    #   
    def is_first_dayof_month(self,d1):
        date = datetime.strptime(str(d1), '%Y-%m-%d')
        first_day = date + relativedelta(day=1)
        if str(first_day)[:10] == d1:
            return True
        else:
            return False
    def revenue_split_monthly(self): 
        revenue_lines = self.contract_id.account_line
        #cost_lines = self.contract_id.account_new_line
        revenue_detail_lines = self.contract_id.account_detail_line
        #cost_detail_lines = self.contract_id.account_new_detail_line
        cont_id = self.contract_id.id
    
        if revenue_lines:
            revenue_lines.unlink()
        # if cost_lines:
        #     cost_lines.unlink()
        used_ids = []
        for line in revenue_detail_lines:
            if line not in used_ids:
                date = line.date
                m_start_date = str(self.get_month_day_range(date)[0])#[:10]#[0][0]
                m_end_date = str(self.get_month_day_range(date)[1])#[:10]#[0][1]
                same_month_revenue_ids = self.env['property.cont.account.detail'].search([('cont_id','=',cont_id),('date','>=',m_start_date),('date','<=',m_end_date)])
                name = self.get_month_day_range(date)[0]#[1]

                name = name.strftime("%B")#strftime
                amount = 0
        
                for rev_line in same_month_revenue_ids:
                    if rev_line not in used_ids:
                
                        used_ids.append(rev_line)
                        amount = round(rev_line.revenue,3)

                
                vals = {'cont_id':cont_id,'date':m_end_date,'deffered_revenue':round(amount,2),'revenue':round(amount,2),'name':name}
                self.env['property.cont.account'].create(vals)
        # for line in cost_detail_lines:
        #     if line not in used_ids:
        #         date = line.date
        #         m_start_date = str(self.get_month_day_range(date)[0][0])[:10]
        #         m_end_date = str(self.get_month_day_range(date)[0][1])[:10]
        #         same_month_revenue_ids = self.env['property.cont.new.account.detail'].search([('cont_id','=',cont_id),('date','>=',m_start_date),('date','<=',m_end_date)])
        #         name = self.get_month_day_range(date)[0][1]
        #         name = name.strftime("%B")
        #         amount = 0
        #
        #         for rev_line1 in same_month_revenue_ids:
        #             if rev_line1 not in used_ids:
        #
        #                 used_ids.append(rev_line1)
        #                 amount = amount + round(rev_line1.revenue_new,3)
        #
        #
        #         vals = {'cont_id':cont_id,'date':m_end_date,'revenue_new':round(amount,2),'deffered_revenue_new':round(amount,2),'name':name}
        #         self.env['property.cont.new.account'].create(vals)



    def revenue_split_monthly_unitwise(self):   
        wiz_lines = self.wiz_line
        contract_obj = self.env['property.contract']
        contract = self.contract_id.id
        contract_end_date_nxt_month = str(self.get_nxt_month_day_range(self.contract_id.date_stop))[:10]     #[0]
        revenue_detail_lines = self.contract_id.account_detail_line
        #cost_detail_lines = self.contract_id.account_new_detail_line
        contract_value = self.contract_id.contract_value
        if revenue_detail_lines:
            revenue_detail_lines.unlink()
        # if cost_detail_lines:
        #     cost_detail_lines.unlink()
        for line in wiz_lines:
#           x_end_date = line.end_date
#           if x_end_date >= contract_end_date:
#               x_end_date = contract_end_date
                
            no_of_months = self.get_months_between_dates(line.start_date,line.end_date)#[0]
            var = no_of_months
            is_first_dayof_month = self.is_first_dayof_month(line.start_date)#[0]
            if not is_first_dayof_month:
                var = var + 1
#           if x_end_date > contract_end_date:
#               var = var - 1
                            
                
            for m in range(0,var):
                start_date = line.start_date
                start_date = str(self.get_add_months(start_date,m))[:10]#[0]
                end_date = line.end_date
                revenue = round(float(line.rent_amount)/float(no_of_months),2)
                cntvalue = round(float(line.rent_amount_new) / float(no_of_months),2)
                print("revenue", line.rent_amount)
                s_month_start_date = self.get_month_day_range(start_date)[0]#[:10]#[0][0]
                s_month_end_date = self.get_month_day_range(start_date)[1]#[:10]#[0][1]
                e_month_start_date = self.get_month_day_range(end_date)[0]#[:10]#[0][0]
                e_month_end_date = self.get_month_day_range(end_date)[1]#[:10]#[0][1]
                desc = str(s_month_start_date) + "-" + str(s_month_end_date)
                print('----startmothss---', datetime.date(s_month_start_date))
                print('----startmothss---', line.start_date)
                print('----endmothss---', datetime.date(s_month_end_date))
                print('----endmothss---', line.end_date)
                if line.start_date and s_month_start_date and line.start_date > datetime.date(s_month_start_date):
                    noofdays_currentmonth = 1
                    print('----startmothss---',s_month_start_date)
                    print('----endmothss---', s_month_end_date)
                    noofdays_currentmonth = int(self.get_no_of_days_currentmonth(s_month_start_date,s_month_end_date))#[0]
                    new_val = float(revenue) / float(noofdays_currentmonth)
                    cnt_val = float(cntvalue) / float(noofdays_currentmonth)
                    considering_days = int(self.get_no_of_days_currentmonth(datetime.combine(line.start_date, datetime.min.time()),s_month_end_date))#[0]
                    revenue = round(float(new_val) * considering_days,2)
                    cntvalue = round(float(cnt_val) * considering_days,2)

                if line.end_date and s_month_end_date and line.end_date < datetime.date(s_month_end_date):
                    noofdays_currentmonth = 1
                    print('----sendmothss---', datetime.date(s_month_end_date))
                    print('----stenartmothss---', line.end_date)
                    noofdays_currentmonth = int(self.get_no_of_days_currentmonth(e_month_start_date,e_month_end_date))#[0]
                    new_val = float(revenue) / float(noofdays_currentmonth)
                    cnt_val = float(cntvalue) / float(noofdays_currentmonth)
                    considering_days = int(self.get_no_of_days_currentmonth(e_month_start_date,datetime.combine(line.end_date, datetime.min.time())))#[0]
                    revenue = round(float(new_val) * considering_days,2)
                    cntvalue = round(float(cnt_val) * considering_days,2)
                    s_month_end_date = line.end_date
                unit_id = line.unit_id and line.unit_id.id
                vals = {'cont_id':contract,'unit_id':unit_id,'revenue':revenue,'deffered_revenue':revenue,'date':s_month_end_date,'desc':desc
                }
                # vals1 = {'cont_id':contract,'unit_id':unit_id,'revenue_new':cntvalue,'deffered_revenue_new':cntvalue,'date':s_month_end_date,'desc':desc
                # }
                if contract_end_date_nxt_month and s_month_end_date and contract_end_date_nxt_month > str(s_month_end_date):
                    self.env['property.cont.account.detail'].create(vals)
                    #self.env['property.cont.new.account.detail'].create(vals1)
        self.revenue_split_monthly()            
            



    def day_wise_revenue_calculation(self):  
        wiz_lines = self.wiz_line
        contract_obj = self.env['property.contract']
        contract = self.contract_id.id
        contract_end_date_nxt_month = str(self.get_nxt_month_day_range(self.contract_id.date_stop))[:10]  #[0]
        revenue_detail_lines = self.contract_id.account_detail_line
        #cost_detail_lines = self.contract_id.account_new_detail_line
        contract_value = self.contract_id.contract_value
        if revenue_detail_lines:
            revenue_detail_lines.unlink()
        # if cost_detail_lines:
        #     cost_detail_lines.unlink()
        for line in wiz_lines:
#           x_end_date = line.end_date
#           if x_end_date >= contract_end_date:
#               x_end_date = contract_end_date
                
            no_of_months = self.get_months_between_dates(line.start_date,line.end_date)#[0]
            var = no_of_months
            is_first_dayof_month = self.is_first_dayof_month(line.start_date)#[0]
            if not is_first_dayof_month:
                var = var + 1

#           if x_end_date > contract_end_date:
#               var = var - 1
                            
                
            for m in range(0,var):
                start_date = line.start_date

                start_date = str(self.get_add_months(start_date,m))[:10]#[0]
                end_date = line.end_date
                s_month_start_date = self.get_month_day_range(start_date)[0]#[:10]#[0][0]
                s_month_end_date = self.get_month_day_range(start_date)[1]#[:10]#[0][1]
                e_month_start_date = self.get_month_day_range(end_date)[0]#[:10]#[0][0]
                e_month_end_date = self.get_month_day_range(end_date)[1]#[:10]#[0][1]
                desc = str(s_month_start_date) + "-" +str(s_month_end_date)
                noofdays_currentmonth = int(self.get_no_of_days_currentmonth(s_month_start_date,s_month_end_date))#[0]
                print('---noofdays_currmont---',noofdays_currentmonth)
                revenue=round(float(line.rent_amount)* noofdays_currentmonth,2)
                print('---revenue---',revenue)
                cntvalue=round(float(line.rent_amount_new)* noofdays_currentmonth,2)
                print('---cntvalue---',cntvalue)
                if line.start_date and s_month_start_date and line.start_date > datetime.date(s_month_start_date):
                    noofdays_currentmonth = 1
                    noofdays_currentmonth = int(self.get_no_of_days_currentmonth(s_month_start_date,s_month_end_date))#[0]
                    considering_days = int(self.get_no_of_days_currentmonth(datetime.combine(line.start_date, datetime.min.time()),s_month_end_date))#[0]
                    revenue = round(float(line.rent_amount) * considering_days,2)
                    cntvalue = round(float(line.rent_amount_new) * considering_days,2)
                if line.end_date and s_month_end_date and line.end_date < datetime.date(s_month_end_date):
                    noofdays_currentmonth = 1
                    noofdays_currentmonth = int(self.get_no_of_days_currentmonth(e_month_start_date,e_month_end_date))#[0]
                    considering_days = int(self.get_no_of_days_currentmonth(e_month_start_date,datetime.combine(line.end_date, datetime.min.time())))#[0]
                    revenue = round(float(line.rent_amount) * considering_days,2)
                    cntvalue = round(float(line.rent_amount_new) * considering_days,2)
                    s_month_end_date = line.end_date
                unit_id = line.unit_id and line.unit_id.id
                vals = {'cont_id':contract,'unit_id':unit_id,'revenue':revenue,'deffered_revenue':revenue,'date':s_month_end_date,'desc':desc
                }
                vals1 = {'cont_id':contract,'unit_id':unit_id,'revenue_new':cntvalue,'deffered_revenue_new':cntvalue,'date':s_month_end_date,'desc':desc
                }
                if contract_end_date_nxt_month and s_month_end_date and contract_end_date_nxt_month > str(s_month_end_date):
                    self.env['property.cont.account.detail'].create(vals)
                    #self.env['property.cont.new.account.detail'].create(vals1)
        self.revenue_split_monthly()            
            
    
    
    def generate_contract_revenue(self):

        contract_obj = self.env['property.contract']
      
        unit_line = self.contract_id.unit_line
        length = len(unit_line)
        total_value = 0
        self.ensure_one()
        get_param = self.env['ir.config_parameter'].sudo().get_param

        day_wise_revenue = get_param('ag_property_maintainence.day_wise_revenue',default=False) or False
        day_wise = False
        if day_wise_revenue:
            day_wise = ast.literal_eval(day_wise_revenue)
        dd = day_wise
        # if not day_wise_revenue:
        #     raise Warning("Please configure the Journals")
        # day_wise_revenue = ast.literal_eval(day_wise_revenue)
        # print('--day wise---',day_wise_revenue)
        #


        if self.wiz_line:
            raise Warning("already generated") 
        for line in unit_line:
            min_dt = line.unit_from
            if line.free_unit_mth:
                min_dt = self.get_min_condate(line.unit_from,line.free_unit_mth)#[0]
            od_s_date = min_dt
            line_end_date = line.unit_to



            if line.duration == 'yr':
                no_y = self.get_no_of_years(od_s_date,line_end_date)#[0]
                print('===no of y===',no_y)
                no_days=0
                for yr in range(0,no_y):
                    start_date = self.get_add_year(od_s_date,yr)#[0]
                    print('--startdate--',start_date)
                    new_date = datetime.strptime(start_date, '%Y-%m-%d')
                    print('--newdate--', new_date)
                    #st_date = datetime.date(new_date)
                   # print('---ststtdate--',st_date)
                    end_date = self.get_end_date(start_date)#[0]
                   # ed_date = datetime.date(end_date)
                    print('---enddate--', type(end_date))
                    rent_amount=float(line.unit_rent)/float(no_y)
                    print('---rent_amount--', rent_amount)
                    rent_amount_new = float(self.contract_id.contract_value)/float(no_y)
                    print('---rent_amount_new--', rent_amount_new)
                    if dd:
                        no_days=no_days + int(self.get_no_of_days_currentmonth(new_date,datetime.combine(end_date, datetime.min.time())))

                        #int(self.get_no_of_days_currentmonth(datetime.combine(start_date, datetime.min.time()),datetime.combine(end_date, datetime.min.time())))#[0]
                        rent_amount= float(line.unit_rent)/float(no_days)
                        rent_amount_new = float(self.contract_id.contract_value)/float(no_days)
                    print('---rent_amount_new1--', self.get_month_day_range(start_date)[0])
                    print('---rent_amount_new--', self.get_month_day_range(start_date)[1])
                    vals = {'wiz_id':self.id,
                        'unit_id':line.unit_id and line.unit_id.id,
                        'start_date':start_date,
                        'end_date':end_date,
                        'rent_amount':rent_amount,
                        'rent_amount_new':rent_amount_new/length,
                        'month_s_date':self.get_month_day_range(start_date)[0],
                        'month_e_date':self.get_month_day_range(start_date)[1]
                    }
                    self.env['contract.revenue.calculation.wizard.line'].create(vals)
            else: 
                no_m = self.get_months_between_dates(od_s_date,line_end_date)#[0]
                
                no_days=0
                for mn in range(0,no_m):
                    start_date = self.get_add_months(od_s_date,mn)#[0]
                    end_date = self.get_month_end_date(start_date)#[0]
                    rent_amount=float(line.unit_rent)/float(no_m)
                    rent_amount_new = float(self.contract_id.contract_value)/float(no_m)
                    if dd:
                        no_days=no_days + int(self.get_no_of_days_currentmonth(start_date,end_date))#[0])
                        rent_amount= float(line.unit_rent)/float(no_days)
                        rent_amount_new = float(self.contract_id.contract_value)/float(no_days)
                    vals = {'wiz_id':self.id,
                        'start_date':start_date,
                        'unit_id':line.unit_id and line.unit_id.id,
                        'end_date':end_date,
                        'rent_amount':rent_amount,
                        'rent_amount_new':rent_amount_new/length,
                    }
                    self.env['contract.revenue.calculation.wizard.line'].create(vals)          
        if dd:
            self.day_wise_revenue_calculation()
        else:
            self.revenue_split_monthly_unitwise()



    
class ContractrevenueGenerationline(models.TransientModel):
    _name = 'contract.revenue.calculation.wizard.line'
    _description = 'contract.revenue.calculation.wizard.line'
    _order = 'start_date asc'

    start_date = fields.Date('Start Date')
    month_s_date = fields.Date(string="Month Start Date")
    month_e_date = fields.Date(string="Month End Date")
    unit_id = fields.Many2one('property.unit',string="Unit")
    end_date = fields.Date('End Date')
    wiz_id = fields.Many2one('contract.revenue.calculation.wizard',string='Wiz')
    type = fields.Char(string='Yearly Or Monthly')
    rent_amount = fields.Float('Amount')
    rent_amount_new = fields.Float('Cost Amount')
    free_days = fields.Float('Free Days')



