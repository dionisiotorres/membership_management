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

_log = logging.getLogger(__name__)


class Menu(models.Model):

    _inherit = "website.menu"

    is_protected = fields.Boolean(default=False, string='Is protected menu')

    @api.one
    def _compute_visible(self):
        res = super(Menu, self)._compute_visible()
        user_id = request.env['res.users'].sudo().browse(request._uid)
        
        if self.is_protected:
            self.is_visible = False

        if user_id.active_membership and user_id.active_membership.menu_ids:
            mem_menu_ids = user_id.active_membership.menu_ids.ids
            if self.id in mem_menu_ids:
                self.is_visible = True

        return res


class Page(models.Model):
    _inherit = 'website.page'


    @api.one
    def _compute_visible(self):
        res=super(Page,self)._compute_visible()
        user_id = request.env['res.users'].sudo().browse(request._uid)
        website_menu=self.env['website.menu'].sudo().search([('url','=',self.url),('website_id','=',self.website_id.id)])
        if website_menu:
            if website_menu.is_protected:
                self.is_visible=False
            if user_id.active_membership and user_id.active_membership.menu_ids:
                mem_menu_ids = user_id.active_membership.menu_ids.ids
                if website_menu.id in mem_menu_ids:
                    self.is_visible=True

        return res


