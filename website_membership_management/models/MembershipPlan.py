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
from odoo.exceptions import ValidationError
import logging

_log=logging.getLogger(__name__)



class MembershipPlan(models.Model):
    _name='membership.plan'
   

    name = fields.Char(string='Name',required=True)
    duration = fields.Integer(string='Duration',required=True)
    plan_unit = fields.Selection([('day','Days(s)'),('month','Month(s)'),('year','Year(s)')],string='Unit',required=True,default='day')
    price = fields.Float(string='Price',required=True)
    trial_period = fields.Boolean(string='Trial Period',default=False)
    trial_duration = fields.Integer(string="Trial Duration",required=True)
    trial_plan_unit = fields.Selection([('hour','Hour(s)'),('day','Day(s)'),('week','week(s)')],string='unit',required=True,default='hour')
    start = fields.Boolean(string='  Immediately', default=True)
    active = fields.Boolean(string='Active',default=True)
    auto_renewal = fields.Boolean(string='Auto Renewal',default=False)
    membership_id=fields.One2many('membership.membership', 'membership_plan_id', string="Memberships")
    total_membership = fields.Integer(string='#', compute="get_membership_count")
    membership_pricelist = fields.Many2one('product.pricelist',string='Pricelist')
    membership_description = fields.Text(string='Plan Description',required=True,translate=True)
    color = fields.Integer(string='Color Index')
    membership_product_ids = fields.One2many('product.product','membership_plan_id')
    currency_id = fields.Many2one('res.currency', string='Currency',
                              default=lambda self: self.env.user.company_id.currency_id)

    

    @api.multi
    def unlink(self):
        for current_rec in self:
            if current_rec.total_membership > 0:
                raise UserError("You can't delete the record because Memberships were create using this plan. Try deleting the memberships first.")
            for product in current_rec.membership_product_ids:
                product.is_a_membership = False
                product._check_description()
                product.unlink()
            super(MembershipPlan, current_rec).unlink()
        return True
    
    
    @api.one
    @api.constrains('duration','trial_duration','price')
    def duration_value_check(self):
        if self.duration < 1 or self.price < 1.00:
            raise ValidationError("Please enter a value greater than zero for the price or duration.")
        if self.trial_duration < 0 :
            raise ValidationError("Please Enter a positive value for Trial Duration")
            
    

    @api.multi
    def get_membership_count(self):
        for obj in self:
            obj.total_membership = len(obj.membership_id.ids)

    @api.onchange('trial_period')
    def onchange_trial_period(self):
        if self.trial_period:
            self.start = False

    @api.onchange('start')
    def onchange_start_immediately(self):
        if self.start:
            self.trial_period = False
            self.trial_duration = 0
           
    @api.multi
    def action_view_membership(self):
        membership_id = self.mapped('membership_id')
        _log.info('membership_id==================={}'.format(membership_id))
        action = self.env.ref('website_membership_management.membership_action').read()[0]
       
        if len(membership_id) > 1:
            action['domain'] = "[('id','in',%s)]" % membership_id.ids
        elif len(membership_id) == 1:
            action['views'] = [(self.env.ref('website_membership_management.membership_form').id, 'form')]
            action['res_id'] = membership_id.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

   