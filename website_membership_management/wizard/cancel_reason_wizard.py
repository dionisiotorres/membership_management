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
import logging
_logger = logging.getLogger(__name__)


class CancelWizard(models.TransientModel):

    _name = "cancel.wizard"
    _description = "Wizard for getting Reason for cancel the membership."

    @api.model
    def is_cancel_module(self):
        return self._context.get('is_cancel',False)


    is_cancel = fields.Boolean(string="Cancel", default=is_cancel_module)
    reason_id = fields.Many2one('membership.reasons', string="Reason", required=True)
    comment = fields.Text(string="Comment")

    @api.multi
    def get_cancel_membership(self):
        membership_obj = self.env['membership.membership'].browse(self._context.get('active_ids', []))
        if membership_obj.get_cancel_mem():
            membership_obj.reason = self.reason_id.name + ": " + self.comment if self.comment else ""
        return True


    @api.multi
    def get_close_membership(self):
        membership_obj = self.env['membership.membership'].browse(self._context.get('active_ids', []))
        res = membership_obj.reset_to_close()
        if res:
            membership_obj.reason = self.reason_id.name +": "+ self.comment if self.comment else ""
        return res
