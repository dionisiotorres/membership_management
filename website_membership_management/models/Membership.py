# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
import datetime
from odoo.tools import float_is_zero
from dateutil.relativedelta import relativedelta



_log=logging.getLogger(__name__)

class Membership(models.Model):
    _name='membership.membership'

   
    active = fields.Boolean(string="Active", default=True)
    name = fields.Char()
    customer_name = fields.Many2one('res.partner', string="Customer Name", required=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True),('is_a_membership','=',True)], required=True)
    tax_id = fields.Many2many('account.tax', string='Taxes')
    membership_plan_id = fields.Many2one('membership.plan',string='Membership Plan')
    trial_period = fields.Boolean(string='Trial period',default=False)
    trial_duration = fields.Integer(string="Trial Duration",required=True)
    trial_plan_unit = fields.Selection([('hour','Hour(s)'),('day','Day(s)'),('week','week(s)')],string='unit',required=True,default='hour')
    price = fields.Float(string="Price",  required=True)
    start_date = fields.Date(string="Start Date", readonly=True, track_visibility="onchange")
    end_date = fields.Date(compute='get_end_date', string="End Date", track_visibility='onchange',store=True)
    plan_state = fields.Selection([('draft','Draft'),('in_progress','In-progress'),('cancel','Cancelled'),('close','Cancelled'),('expired','Expired'),('renewed','Renewed'),('update','Updated'),('pending','Pending')], default='draft', string='State', track_visibility="always",copy=False)
    auto_renewal=fields.Boolean(string='Auto Renewal',default=False)
    so_origin = fields.Many2one('sale.order', string="Order Ref" )
    next_payment_date = fields.Datetime(string="Date of Next Payment",copy=False)
    invoice_ids = fields.Many2many("account.invoice", string='Invoices', readonly=True, copy=False)
    invoice_count =  fields.Integer(compute="get_invoiced_count", readonly=True, string='Invoices')
    membership_id = fields.Many2one('membership.membership', string="Membership Id", copy=False)
    source = fields.Selection([('so','Sale Order'),('manual','Manual')],'Related To', default="manual")
    so_origin = fields.Many2one('sale.order', string="Order Ref" )
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    immediate = fields.Boolean(default=True)
    after = fields.Boolean(default=False)
    reason = fields.Char(string="Reason", track_visibility="onchange")
    currency_id = fields.Many2one('res.currency', string='Currency',
                              default=lambda self: self.env['website'].get_current_website().get_current_pricelist().currency_id.id)
    last_renewal_date = fields.Date(string="Last renewal Date", readonly=True)

    menu_ids = fields.Many2many('website.menu',string='membership menu')

    @api.multi
    def unlink(self):
        for current_rec in self:
            if current_rec.plan_state not in ('draft', 'cancel'):
                raise UserError("You can't delete the record because its invoice is create. Try closing it instead")
            super(Membership, current_rec).unlink()
        return True


    @api.onchange('product_id')
    def plan_info(self):
        if self.product_id:
            self.membership_plan_id=self.product_id.membership_plan_id.id
            self.price=self.product_id.lst_price
            self.member_plan_id = self.product_id.membership_plan_id.id
            if self.product_id.membership_plan_id.trial_period:
                self.trial_period = self.product_id.membership_plan_id.trial_period
                self.trial_duration = self.product_id.membership_plan_id.trial_duration
                self.trial_plan_unit = self.product_id.membership_plan_id.trial_plan_unit
            else:
                self.trial_period = False
            if self.product_id.membership_plan_id.auto_renewal:
                self.auto_renewal = self.product_id.membership_plan_id.auto_renewal
            else:
                self.auto_renewal = False

        self.menu_ids=[(6,0,self.product_id.menu_ids.ids)]
            

    
    def confirm_membership(self):
        self.update_membership()
        if(self.plan_state=='draft'):
            if self.customer_name.all_membership:
                self.trial_period = False

            if self.trial_period:
                if self.trial_plan_unit=='hour':
                    add_trial = datetime.timedelta(hours=self.trial_duration)
                elif self.trial_plan_unit=='day':
                    add_trial = datetime.timedelta(days=self.trial_duration)
                elif self.trial_plan_unit=='week':
                    add_trial = datetime.timedelta(weeks=self.trial_duration)
            else:
                add_trial=datetime.timedelta(days=0)

            self.start_date = (datetime.datetime.today() + add_trial).date()
            self.next_payment_date=str(self.start_date)

            self.plan_state='in_progress' 
            self.mail_send()  
            self.action_invoice_create()
            self.assigningpricelist()
            
    @api.one
    @api.depends('start_date')
    def get_end_date(self):
        if self.start_date:
            add_duration = datetime.timedelta(days=1)
            if self.membership_plan_id.plan_unit=='day':
                add_duration = datetime.timedelta(days=self.membership_plan_id.duration)
            elif self.membership_plan_id.plan_unit=='month':
                add_duration = datetime.timedelta(days=(self.membership_plan_id.duration)*30)
            elif self.membership_plan_id.plan_unit=='year':  
                add_duration = datetime.timedelta(days=(self.membership_plan_id.duration)*365)                
    
            start_date=datetime.datetime.strptime(str(self.start_date),'%Y-%m-%d')

            self.end_date=(start_date + add_duration).date()

    @api.model
    def create(self, vals):
        vals['name'] =  self.env['ir.sequence'].next_by_code('membership.membership')
        res = super(Membership, self).create(vals)
        return res

    def mail_send(self):
        template_id=self.env.ref('website_membership_management.membership_confirm_email')
        template_id.send_mail(self.id,force_send=True)
    
    def reminder_mail_send(self):
        template_id=self.env.ref('website_membership_management.membership_reminder_email')
        template_id.send_mail(self.id,force_send=True)

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        company_id = self.env['account.invoice'].default_get(['company_id'])['company_id']
        name = fiscal_position_id = pos_id = False
        acc = self.customer_name.property_account_receivable_id.id
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        if self.source in ['api','manual']:
            fiscal_position_id = self.customer_name.property_account_position_id.id
        invoice_vals = {
            'name': self.so_origin.name or '' if self.source == 'so' else name,
            'origin': self.name,
            'type': 'out_invoice',
            'reference': self.membership_plan_id.name or self.name,
            'account_id':acc,
            'partner_id': self.customer_name.id,
            'journal_id': journal_id,
            'currency_id': self.so_origin.pricelist_id.currency_id.id or self.currency_id.id or self.env['website'].get_current_website().get_current_pricelist().currency_id.id,

            'payment_term_id': self.so_origin.payment_term_id.id or '',
            'fiscal_position_id': self.so_origin.fiscal_position_id.id or self.so_origin.partner_invoice_id.property_account_position_id.id if self.source == 'so' else fiscal_position_id,
            'company_id': self.so_origin.company_id.id if self.source == 'so' else company_id,
            'user_id': self.so_origin.user_id and self.so_origin.user_id.id if self.source == 'so' else self._uid,
            'date_invoice': str(self.next_payment_date or self.start_date),
            'is_a_membership' : True,
        }
        return invoice_vals
    
    @api.model
    def create_automatic_invoice(self):
        self.membership_state()
        memberships = self.search([('start_date','<=', fields.Datetime.now()),('plan_state','=','in_progress'),('auto_renewal','=',True),('next_payment_date','<=',fields.Datetime.now())])
        for membership in memberships:
            membership.action_invoice_create()
            membership.last_renewal_date = fields.Datetime.now()
        return True


    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        for membership in self:
            if not membership.active:
                raise UserError(_("You can't generate invoice of an Inactive Membership."))
            if membership.plan_state == 'draft':
                raise UserError("You can't generate invoice of a membership which is in draft state, please confirm it first.")
            
            group_key = membership.id if grouped else (membership.customer_name.id, membership.product_id.currency_id.id)
            
            if group_key not in invoices:
                inv_data = membership._prepare_invoice()
                invoice = inv_obj.create(inv_data)
                invoices[group_key] = invoice
            elif group_key in invoices and membership.name not in invoices[group_key].so_origin.split(', '):
                invoices[group_key].write({'origin': invoices[group_key].origin + ', ' + membership.name})
            if membership.quantity > 0:
                membership.invoice_line_create(invoices[group_key].id, membership.quantity)
        if invoices:
            message = 'Invoice Created'
            
            for inv in invoices.values():
                inv.compute_taxes()
                inv.action_invoice_open()
            self.invoice_ids =  [inv.id for inv in invoices.values()]
            
            if self.next_payment_date:
                next_payment_date = datetime.datetime.strptime(str(self.next_payment_date),'%Y-%m-%d %H:%M:%S') 
            else:
                start_date = str(self.start_date + " 00:00:00")
                next_payment_date = datetime.datetime.strptime(start_date,'%Y-%m-%d %H:%M:%S')
            if self.membership_plan_id.plan_unit == 'day':
                next_payment_date = next_payment_date  + relativedelta(days = self.membership_plan_id.duration)
            if self.membership_plan_id.plan_unit == 'month':
                next_payment_date = next_payment_date + relativedelta(months = self.membership_plan_id.duration)
            if self.membership_plan_id.plan_unit == 'year':
                next_payment_date = next_payment_date + relativedelta(years = self.membership_plan_id.duration)
            if self.membership_plan_id.plan_unit == 'hour':
                next_payment_date = next_payment_date + timedelta(hours = self.membership_plan_id.duration)
            self.next_payment_date = str(next_payment_date) or False
            wizard_id = self.env['membership.message.wizard'].create({'message':message})
        else:
            wizard_id = self.env['membership.message.wizard'].create({'message':'Membership Expired.'})
        return {
            'name': ("Message"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'membership.message.wizard',
                'res_id': wizard_id.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
        }

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        if self.auto_renewal:
            product = self.product_id.with_context(
                lang=self.customer_name.lang,
                partner=self.customer_name.id,
                quantity=self.quantity,
                date=self.start_date,
                pricelist=self.membership_plan_id.membership_pricelist.id,
                uom=self.product_id.uom_po_id.id or False
            )
        else:
            product = self.product_id.with_context(
                lang=self.customer_name.lang,
                partner=self.customer_name.id,
                quantity=self.quantity,
                date=self.start_date,
                pricelist=self.so_origin.pricelist_id.id,
                uom=self.product_id.uom_po_id.id or False
            )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % \
                            (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))
        fpos = self.customer_name.property_account_position_id
        if fpos:
            account = fpos.map_account(account)
        res = {
            'name': name,
            'origin': self.name,
            'account_id': account.id,
            'price_unit': self.price,
            'quantity': self.quantity,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'pricelist':self.so_origin.pricelist_id,

        }
        return res

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id})
                self.env['account.invoice.line'].create(vals)

    @api.multi
    def action_view_invoice(self):
        invoice_ids = self.mapped('invoice_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(invoice_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % invoice_ids.ids
        elif len(invoice_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.depends('invoice_ids')
    def get_invoiced_count(self):
        for rec in self: 
            rec.invoice_count = len(rec.invoice_ids)

    @api.model
    def membership_state(self):
        for cur_rec in self.search([]):
            if cur_rec.plan_state != 'draft' and cur_rec.end_date and not cur_rec.auto_renewal:
                if cur_rec.plan_state == 'in_progress' and str(datetime.datetime.now().date()) >= str(cur_rec.end_date) : 
                    cur_rec.plan_state='expired'
                    cur_rec.revokingpricelist()
                if not(self.env['membership.membership'].search([('customer_name.name','=',cur_rec.customer_name.name),('plan_state','=','in_progress')])):
                    pending_membership=self.env['membership.membership'].search([('customer_name.name','=',cur_rec.customer_name.name),('plan_state','=','pending')])
                    if pending_membership:
                        pending_membership.plan_state='draft'
                        pending_membership.confirm_membership()
        self.send_reminder_mail()
    
    @api.multi
    def membership_renew(self):
        for current_rec in self:
            if current_rec.plan_state in ['expired','close','cancel']:
                current_rec.create_membership()
                current_rec.plan_state='renewed'
                wizard_id = self.env['membership.message.wizard'].create({'message':'Membership Renewed.'})
                return {
                    'name':("Message"),
                    'view_mode': 'form',
                    'view_id': False,
                    'view_type': 'form',
                    'res_model': 'membership.message.wizard',
                    'res_id': wizard_id.id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                }
            return False

    @api.multi
    def create_membership(self):
        date = datetime.datetime.today()
        if self.trial_period:
            if self.trial_plan_unit == 'day':
                date = date + relativedelta(days=self.trial_duration)
            if self.trial_plan_unit == 'month':
                date = date + relativedelta(months=self.trial_duration)
            if self.trial_plan_unit == 'year':
                date = date + relativedelta(years=self.trial_duration)
            if self.trial_plan_unit == 'hour':
                date = date + relativedelta(hours=self.trial_duration)
        res = self.copy()
        res.start_date =str(date)
        res.membership_id = self.id
        self.state = "renewed"
        return res
        
    def assigningpricelist(self):
        self.customer_name.property_product_pricelist=self.membership_plan_id.membership_pricelist.id

    def revokingpricelist(self):
        pricelist=self.env['product.pricelist'].search([('name','=','Public Pricelist')])
        self.customer_name.property_product_pricelist=pricelist.id

    def update_membership(self):
        count=self.env['membership.membership'].search([('customer_name.name','=',self.customer_name.name),('plan_state','=','in_progress')])
        if count:
            if (count.immediate):
                count.reset_to_close()
                count.plan_state='update'
            elif count.after:
                self.plan_state='pending'
        else:
            return True

    def send_reminder_mail(self):
        for cur_rec in self.search([]):
            if cur_rec.plan_state != 'draft' and cur_rec.end_date: 
                advanced_date=(datetime.datetime.now() + datetime.timedelta(days=10)).date()
                if (advanced_date>=cur_rec.end_date and cur_rec.plan_state == 'in_progress'):
                    cur_rec.reminder_mail_send()
    
    @api.multi
    def get_cancel_mem(self):
        for current_rec in self:
            if current_rec.plan_state == 'draft':
                current_rec.plan_state = 'cancel'
            
        return True

    @api.multi
    def pay_cancel_invoice(self):
        for current_rec in self:
            for invoice_id in current_rec.invoice_ids:
                if invoice_id.state == 'draft':
                    res = invoice_id.action_cancel()
                elif invoice_id.state == 'open':
                    journal_id =  self.env["ir.default"].get('res.config.settings', 'journal_id')
                    if not journal_id:
                        raise UserError(_("Default Journal not found please the default journal in configuration under membership"))
                    journal = self.env['account.journal'].browse(journal_id)
                    res = invoice_id.pay_and_reconcile(pay_journal=journal)
        return True
    @api.multi
    def reset_to_close(self):
        for current_rec in self:
            if current_rec.plan_state not in ['close','cancel','renewed','update']:
                if current_rec.invoice_ids:
                    self.pay_cancel_invoice()
                    current_rec.revokingpricelist()
                current_rec.plan_state = 'close'
            if self._context.get('close_refund'):
                return current_rec.action_view_invoice()
        return True
