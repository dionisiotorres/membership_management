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
from odoo.http import request
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

from odoo import api,fields,models
import logging

_log=logging.getLogger(__name__)


class MembershipProduct_Product(models.Model):
    _inherit = 'product.product'

    is_a_membership = fields.Boolean(string='Is a membership',default=False)
    membership_plan_id = fields.Many2one('membership.plan')

    @api.onchange('membership_plan_id')
    def on_change_membership_plan(self):
        override = self.env['res.config.settings'].sudo().get_values()['override_product_price']
        
        for current_rec in self:
            if current_rec.membership_plan_id:
                if override:
                    current_rec.lst_price = current_rec.membership_plan_id.price
                current_rec.type = 'service'
    
    @api.onchange('is_a_membership')
    def product_type(self):
        for current_rec in self:
            if current_rec.is_a_membership:
                current_rec.type = 'service'
            else:
                current_rec.type = 'consu'
    
    @api.multi
    def write(self,vals):
        if vals.get('is_a_membership'):
            vals['type']='service'
        res=super(MembershipProduct_Product,self).write(vals)

        return res

    @api.one
    @api.constrains('is_a_membership')
    def _check_description(self):
        price_list=list()
        product_variants = self.env['product.product'].search([('product_tmpl_id','=',self.product_tmpl_id.id)])
        override = self.env['res.config.settings'].sudo().get_values()['override_product_price']
        attribute_price = self.env['product.template.attribute.value']
        if override:
            for variant in product_variants:
                if variant.is_a_membership:
                    price_list.append(variant.membership_plan_id.price)
                    self.product_tmpl_id.list_price=min(price_list)
                    for price in attribute_price.sudo().search([('product_tmpl_id','=',variant.product_tmpl_id.id)]):
                        price.price_extra = 0.0


    @api.depends('list_price', 'price_extra')
    def _compute_product_lst_price(self):
        res = super(MembershipProduct_Product, self)._compute_product_lst_price()
        override = self.env['res.config.settings'].sudo().get_values()['override_product_price']
        if override:
            for product in self:
                if product.is_a_membership and product.membership_plan_id :
                    product.lst_price = product.membership_plan_id.price
        return res

class MembershipProduct(models.Model):
    _inherit='product.template'

    is_a_membership = fields.Boolean(string='Is a membership',default=False,related='product_variant_ids.is_a_membership',readonly=False)
    membership_plan_id = fields.Many2one('membership.plan',related='product_variant_ids.membership_plan_id',readonly=False)
    menu_ids = fields.Many2many('website.menu',string='membership menu')

    @api.onchange('membership_plan_id')
    def price_calc(self):
        override = self.env['res.config.settings'].sudo().get_values()['override_product_price']
        for current_rec in self:
            if current_rec.membership_plan_id:
                if override:
                    current_rec.list_price = current_rec.membership_plan_id.price
                current_rec.type = 'service'

    @api.onchange('is_a_membership')
    def product_type(self):
        for current_rec in self:
            if current_rec.is_a_membership:
                current_rec.type = 'service'
            else:
                current_rec.type = 'consu'
        
    @api.multi
    def write(self,vals):
        override = self.env['res.config.settings'].sudo().get_values()['override_product_price']
        if vals.get('membership_plan_id'):
            vals['type']='service'
            vals['is_a_membership']=True
            if override:
                vals['list_price']=self.membership_plan_id.price
        res=super(MembershipProduct,self).write(vals)
        return res

    @api.model
    def create(self,vals):
        override = self.env['res.config.settings'].sudo().get_values()['override_product_price']
        if vals.get('membership_plan_id'):
            vals['type']='service'
            if override:
                vals['list_price']=self.membership_plan_id.price
        res=super(MembershipProduct,self).create(vals)
        related_vals = {}
        if vals.get('is_a_membership'):
            related_vals['is_a_membership'] = vals['is_a_membership']
        if vals.get('membership_plan_id'):
            related_vals['membership_plan_id'] = vals['membership_plan_id']
            if override:
                related_vals['list_price'] = vals['list_price']
        if related_vals:
            res.write(related_vals)
        return res




    @api.multi
    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        res = super(MembershipProduct,self)._get_combination_info(combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist, parent_combination=parent_combination, only_template=only_template)
        override = self.env['res.config.settings'].sudo().get_values()['override_product_price']
        if product_id and override:
            product = self.env['product.product'].sudo().browse(int(res['product_id']))
            quantity = self.env.context.get('quantity', add_qty)
            context = dict(self.env.context, quantity=quantity, pricelist=pricelist.id if pricelist else False)
            if product.is_a_membership:
                product_template = self.with_context(context)
                list_price = product_template.currency_id._convert(
                    product.membership_plan_id.price, pricelist.currency_id, product_template._get_current_company(pricelist=pricelist),
                    fields.Date.today()
                    )
                price = list_price
                res.update({
                            'price': price,
                            'list_price': list_price,
                            })
        return res

    

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def get_membership_count(self):
        mem_obj = self.env['membership.membership']
        for current_record in self:
            current_record.membership_count = mem_obj.search_count([('so_origin', '=', current_record.id)])

    membership_count = fields.Integer(compute=get_membership_count, string="#Membership")
    membership_ids = fields.One2many("membership.membership", 'so_origin', string="Membership", readonly=True, copy=False)

    @api.multi
    def action_view_membership(self):
        membership_ids = self.env['membership.membership'].search([('so_origin', '=', self.id)])
        action = self.env.ref('website_membership_management.membership_action').read()[0]
       
        if len(membership_ids) > 1:
            action['domain'] = "[('id','in',%s)]" % membership_ids.ids
        elif len(membership_ids) == 1:
            action['views'] = [(self.env.ref('website_membership_management.membership_form').id, 'form')]
            action['res_id'] = membership_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    
    @api.multi
    def action_confirm(self):
        membership = self.env['membership.membership']
        for order in self:
            res = super(SaleOrder, order).action_confirm()
            if res:
                for line in order.order_line:
                    if line.product_id.is_a_membership:
                        vals = {
                                'customer_name': order.partner_id.id,
                                'tax_id': [(6, 0, line.tax_id.ids)], 
                                'membership_plan_id':line.product_id.membership_plan_id.id,
                                'price': line.price_unit, 
                                'trial_period': line.product_id.membership_plan_id.trial_period, 
                                'trial_plan_unit': line.product_id.membership_plan_id.trial_plan_unit, 
                                'trial_duration': line.product_id.membership_plan_id.trial_duration,
                                'auto_renewal':line.product_id.membership_plan_id.auto_renewal,
                                'product_id':line.product_id.id,
                                'create_uid': self._uid,
                                'source':'so',
                                'so_origin':order.id,
                                'menu_ids':[(6,0,line.product_id.menu_ids.ids)]
                                }
                        membership_id = membership.create(vals)
                        membership_id.confirm_membership()
            return res



    
    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        res  = super(SaleOrder,self)._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty,kwargs=kwargs)
        override = self.env['res.config.settings'].sudo().get_values()['override_product_price']
        if line_id is not False and override:
            order = self.sudo().browse(self.id)
            order_line = self._cart_find_product_line(product_id, line_id, **kwargs)[:1]
            product = request.env['product.product'].browse(int(product_id))
            if product.is_a_membership:
                
                values = {
                    'price_unit':  product.product_tmpl_id.currency_id._convert(
                product.membership_plan_id.price, order.pricelist_id.currency_id, product.product_tmpl_id._get_current_company(pricelist=order.pricelist_id),
                fields.Date.today()
                
            ),
                    
                }
                order_line.write(values)
                
        return res

    @api.onchange('order_line')
    def membership_product(self):
        override = self.env['res.config.settings'].sudo().get_values()['override_product_price']
        if override:
            count = 0
            for line in self.order_line:
                if line.product_id.is_a_membership:
                    count+=1
                    line.price_unit = line.product_id.membership_plan_id.price
                if count > 1:
                    raise UserError('cannot add more than one membership product')


            



class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    is_a_membership =  fields.Boolean(string="Is Membership",copy=False)

class ProductTemplateAttributeValue(models.Model):

    _inherit="product.template.attribute.value"


    @api.constrains('price_extra')
    def membership_price_manage(self):
        override = self.env['res.config.settings'].sudo().get_values()['override_product_price']
        if override and self.product_tmpl_id.is_a_membership and self.price_extra != 0:
            raise UserError('Unchecked the override price option in sales configuration setting under Membership to add the attribute price')
             

    
    