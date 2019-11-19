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

class membershipcustomer(models.Model):
    _inherit='res.partner'

    active_membership = fields.Many2one('membership.membership',string='Active Membership',compute='get_active_membership')
    all_membership = fields.One2many('membership.membership',inverse_name='customer_name')

    @api.one
    @api.depends('all_membership')
    def get_active_membership(self):
        for membership in self.all_membership:
            if membership.plan_state == 'in_progress':
                self.active_membership=membership.id
                break
        else:
            self.active_membership=None

