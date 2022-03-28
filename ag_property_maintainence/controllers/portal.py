# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class PortalContract(CustomerPortal):

    def _prepare_home_portal_values(self):
        values = super(PortalContract, self)._prepare_home_portal_values()
        contract_count = request.env['property.contract'].search_count([]) if request.env['property.contract'].check_access_rights('read', raise_exception=False) else 0
        values['contract_count'] = contract_count
        return values

    # ------------------------------------------------------------
    # My Invoices
    # ------------------------------------------------------------

    def _invoice_get_page_view_values(self, contract, access_token, **kwargs):
        values = {
            'page_name': 'contract',
            'contract': contract,
        }
        return self._get_page_view_values(contract, access_token, values, 'my_contracts_history', False, **kwargs)

    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_contracts(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        Contracts = request.env['property.contract']

        domain = []

        searchbar_sortings = {
            'date': {'label': _('Start Date'), 'order': 'date_start desc'},
            'duedate': {'label': _('End Date'), 'order': 'date_stop desc'},
            'name': {'label': _('Name'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('property.contract', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        contract_count = Contracts.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/contracts",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=contract_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        contract = Contracts.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_contracts_history'] = contract.ids[:100]

        values.update({
            'date': date_begin,
            'contract': contract,
            'page_name': 'contracts',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/contracts',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("ag_property_maintainence.portal_my_contracts", values)

    @http.route(['/my/contracts/<int:contract_id>'], type='http', auth="public", website=True)
    def portal_my_conract_detail(self, contract_id, access_token=None, report_type=None, download=False, **kw):
        try:
            contract_sudo = self._document_check_access('property.contract', contract_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=contract_sudo, report_type=report_type, report_ref='ag_property_maintainence.action_report_property_contract', download=download)

        values = self._invoice_get_page_view_values(contract_sudo, access_token, **kw)
        acquirers = values.get('acquirers')
        # if acquirers:
        #     country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
        #     values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(contract_sudo.amount_residual, contract_sudo.currency_id, country_id)

        return request.render("ag_property_maintainence.portal_contract_page", values)

    # ------------------------------------------------------------
    # My Home
    # ------------------------------------------------------------

    def details_form_validate(self, data):
        error, error_message = super(PortalContract, self).details_form_validate(data)
        # prevent VAT/name change if invoices exist
        partner = request.env['res.users'].browse(request.uid).partner_id
        if not partner.can_edit_vat():
            if 'vat' in data and (data['vat'] or False) != (partner.vat or False):
                error['vat'] = 'error'
                error_message.append(_('Changing VAT number is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'name' in data and (data['name'] or False) != (partner.name or False):
                error['name'] = 'error'
                error_message.append(_('Changing your name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'company_name' in data and (data['company_name'] or False) != (partner.company_name or False):
                error['company_name'] = 'error'
                error_message.append(_('Changing your company name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
        return error, error_message


class PortalSalesContract(CustomerPortal):
      
    def _prepare_home_portal_values(self):
        values = super(PortalSalesContract, self)._prepare_home_portal_values()
        contract_count = request.env['property.contract.sales'].search_count([]) if request.env['property.contract.sales'].check_access_rights('read', raise_exception=False) else 0
        values['salescontract_count'] = contract_count
        return values

    # ------------------------------------------------------------
    # My Invoices
    # ------------------------------------------------------------

    def _invoice_get_page_view_values(self, contract, access_token, **kwargs):
        values = {
            'page_name': 'sales contract',
            'contract': contract,
        }
        return self._get_page_view_values(contract, access_token, values, 'my_salescontracts_history', False, **kwargs)

    @http.route(['/my/salescontracts', '/my/salescontracts/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_salescontracts(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        Contracts = request.env['property.contract.sales']

        domain = []

        searchbar_sortings = {
            'date': {'label': _('Contract Date'), 'order': 'con_date desc'},
            'duedate': {'label': _('Contract Date'), 'order': 'con_date desc'},
            'name': {'label': _('Name'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('property.contract.sales', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        contract_count = Contracts.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/salescontracts",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=contract_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        contract = Contracts.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_salescontracts_history'] = contract.ids[:100]

        values.update({
            'date': date_begin,
            'contract': contract,
            'page_name': 'sales contracts',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/salescontracts',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("ag_property_maintainence.portal_my_salescontracts", values)

    @http.route(['/my/salescontracts/<int:contract_id>'], type='http', auth="public", website=True)
    def portal_my_salesconract_detail(self, contract_id, access_token=None, report_type=None, download=False, **kw):
        try:
            contract_sudo = self._document_check_access('property.contract.sales', contract_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=contract_sudo, report_type=report_type, report_ref='ag_property_maintainence.action_report_property_contract_sales', download=download)

        values = self._invoice_get_page_view_values(contract_sudo, access_token, **kw)
        acquirers = values.get('acquirers')
        # if acquirers:
        #     country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
        #     values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(contract_sudo.amount_residual, contract_sudo.currency_id, country_id)

        return request.render("ag_property_maintainence.portal_salescontract_page", values)

    # ------------------------------------------------------------
    # My Home
    # ------------------------------------------------------------

    def details_form_validate(self, data):
        error, error_message = super(PortalSalesContract, self).details_form_validate(data)
        # prevent VAT/name change if invoices exist
        partner = request.env['res.users'].browse(request.uid).partner_id
        if not partner.can_edit_vat():
            if 'vat' in data and (data['vat'] or False) != (partner.vat or False):
                error['vat'] = 'error'
                error_message.append(_('Changing VAT number is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'name' in data and (data['name'] or False) != (partner.name or False):
                error['name'] = 'error'
                error_message.append(_('Changing your name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'company_name' in data and (data['company_name'] or False) != (partner.company_name or False):
                error['company_name'] = 'error'
                error_message.append(_('Changing your company name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
        return error, error_message


class PortalBooking(CustomerPortal):
      
    def _prepare_home_portal_values(self):
        values = super(PortalBooking, self)._prepare_home_portal_values()
        booking_count = request.env['property.booking'].search_count([]) if request.env['property.booking'].check_access_rights('read', raise_exception=False) else 0
        values['booking_count'] = booking_count
        return values

    # ------------------------------------------------------------
    # My Invoices
    # ------------------------------------------------------------

    def _invoice_get_page_view_values(self, booking, access_token, **kwargs):
        values = {
            'page_name': 'booking',
            'booking': booking,
        }
        return self._get_page_view_values(booking, access_token, values, 'my_booking_history', False, **kwargs)

    @http.route(['/my/booking', '/my/booking/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_booking(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        bookings = request.env['property.booking']

        domain = []

        searchbar_sortings = {
            'date': {'label': _('Book From'), 'order': 'book_from desc'},
            'duedate': {'label': _('Book To'), 'order': 'book_to desc'},
            'name': {'label': _('Name'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('property.booking', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        booking_count = bookings.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/booking",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=booking_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        booking = bookings.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_booking_history'] = booking.ids[:100]

        values.update({
            'date': date_begin,
            'booking': booking,
            'page_name': 'booking',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/booking',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("ag_property_maintainence.portal_my_booking", values)

    @http.route(['/my/booking/<int:booking_id>'], type='http', auth="public", website=True)
    def portal_my_booking_detail(self, booking_id, access_token=None, report_type=None, download=False, **kw):
        try:
            booking_sudo = self._document_check_access('property.booking', booking_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=booking_sudo, report_type=report_type, report_ref='ag_property_maintainence.action_report_property_booking', download=download)

        values = self._invoice_get_page_view_values(booking_sudo, access_token, **kw)
        acquirers = values.get('acquirers')
        # if acquirers:
        #     country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
        #     values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(contract_sudo.amount_residual, contract_sudo.currency_id, country_id)

        return request.render("ag_property_maintainence.portal_booking_page", values)

    # ------------------------------------------------------------
    # My Home
    # ------------------------------------------------------------

    def details_form_validate(self, data):
        error, error_message = super(PortalBooking, self).details_form_validate(data)
        # prevent VAT/name change if invoices exist
        partner = request.env['res.users'].browse(request.uid).partner_id
        if not partner.can_edit_vat():
            if 'vat' in data and (data['vat'] or False) != (partner.vat or False):
                error['vat'] = 'error'
                error_message.append(_('Changing VAT number is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'name' in data and (data['name'] or False) != (partner.name or False):
                error['name'] = 'error'
                error_message.append(_('Changing your name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'company_name' in data and (data['company_name'] or False) != (partner.company_name or False):
                error['company_name'] = 'error'
                error_message.append(_('Changing your company name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
        return error, error_message

class PortalSalesBooking(CustomerPortal):
      
    def _prepare_home_portal_values(self):
        values = super(PortalSalesBooking, self)._prepare_home_portal_values()
        salesbooking_count = request.env['property.booking.sales'].search_count([]) if request.env['property.booking.sales'].check_access_rights('read', raise_exception=False) else 0
        values['salesbooking_count'] = salesbooking_count
        return values

    # ------------------------------------------------------------
    # My Invoices
    # ------------------------------------------------------------

    def _invoice_get_page_view_values(self, booking, access_token, **kwargs):
        values = {
            'page_name': 'sales booking',
            'booking': booking,
        }
        return self._get_page_view_values(booking, access_token, values, 'my_salesbooking_history', False, **kwargs)

    @http.route(['/my/salesbooking', '/my/salesbooking/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_salesbooking(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        bookings = request.env['property.booking.sales']

        domain = []

        searchbar_sortings = {
            'date': {'label': _('Book From'), 'order': 'book_from desc'},
            'duedate': {'label': _('Book To'), 'order': 'book_to desc'},
            'name': {'label': _('Name'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('property.booking.sales', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        salesbooking_count = bookings.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/salesbooking",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=salesbooking_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        booking = bookings.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_salesbooking_history'] = booking.ids[:100]

        values.update({
            'date': date_begin,
            'booking': booking,
            'page_name': 'sales booking',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/salesbooking',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("ag_property_maintainence.portal_my_salesbooking", values)

    @http.route(['/my/salesbooking/<int:salesbooking_id>'], type='http', auth="public", website=True)
    def portal_my_salesbooking_detail(self, salesbooking_id, access_token=None, report_type=None, download=False, **kw):
        try:
            booking_sudo = self._document_check_access('property.booking.sales', salesbooking_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=booking_sudo, report_type=report_type, report_ref='ag_property_maintainence.action_report_property_booking_sales', download=download)

        values = self._invoice_get_page_view_values(booking_sudo, access_token, **kw)
        acquirers = values.get('acquirers')
        # if acquirers:
        #     country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
        #     values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(contract_sudo.amount_residual, contract_sudo.currency_id, country_id)

        return request.render("ag_property_maintainence.portal_salesbooking_page", values)

    # ------------------------------------------------------------
    # My Home
    # ------------------------------------------------------------

    def details_form_validate(self, data):
        error, error_message = super(PortalSalesBooking, self).details_form_validate(data)
        # prevent VAT/name change if invoices exist
        partner = request.env['res.users'].browse(request.uid).partner_id
        if not partner.can_edit_vat():
            if 'vat' in data and (data['vat'] or False) != (partner.vat or False):
                error['vat'] = 'error'
                error_message.append(_('Changing VAT number is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'name' in data and (data['name'] or False) != (partner.name or False):
                error['name'] = 'error'
                error_message.append(_('Changing your name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'company_name' in data and (data['company_name'] or False) != (partner.company_name or False):
                error['company_name'] = 'error'
                error_message.append(_('Changing your company name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
        return error, error_message