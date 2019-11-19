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

from odoo import api, fields, models, _
from odoo.exceptions import Warning
import logging

_log=logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    journal_id = fields.Many2one('account.journal', string='Payment Method',
        domain=[('type', 'in', ('bank', 'cash'))],
        
        )
    override_product_price = fields.Boolean(string='Override Price',default=False,help="will set the price_extra field to 0 and forced the product to take price of plan")

   

    @api.multi
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        res.update({
            'journal_id':IrDefault.get('res.config.settings','journal_id'),
            'override_product_price':IrDefault.get('res.config.settings','override_product_price'),
            
        })
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('res.config.settings','journal_id', self.journal_id.id )
        IrDefault.set('res.config.settings','override_product_price', self.override_product_price )
        
        return True

    @api.model
    def enable_pricelists(self):
        
        enable_env = self.env['res.config.settings'].create({
                'sale_pricelist_setting'    :   'percentage',
                'multi_sales_price'         :   True,
                'journal_id'                :   self.env['account.journal'].search([('type','=','bank')]).id,
            })
        enable_env.execute()

    @api.onchange('override_product_price')
    def membership_price_manage(self):
        if self.override_product_price:
            membership_products = self.env['product.product'].sudo().search([('is_a_membership','=',True)])
            attribute_price = self.env['product.template.attribute.value']


            for product in membership_products:
                for price in attribute_price.sudo().search([('product_tmpl_id','=',product.product_tmpl_id.id)]):
                    price.price_extra = 0.0

        


