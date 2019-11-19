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
from odoo import api, fields, models, tools

from odoo.http import request
from odoo.addons.website.models import ir_http

import logging

_log=logging.getLogger(__name__)

class Website(models.Model):
    _inherit='website'
    
    def get_membership_count(self):
        if self._uid:
            user_id = self.env['res.users'].browse(self._uid)
            count=self.env['membership.membership'].search([('customer_name','=',user_id.partner_id.id)])
            return count
        return 0


    def get_current_pricelist(self):
    
        partner = self.env.user.partner_id
        if partner.active_membership:
            pl=partner.property_product_pricelist
        else:
            pl = super(Website,self).get_current_pricelist()

        return pl