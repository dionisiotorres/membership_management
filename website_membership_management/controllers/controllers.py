from odoo import http
from odoo.http import request
import logging
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.portal.controllers.portal import CustomerPortal
import requests
_log=logging.getLogger(__name__)

class membership(WebsiteSale,CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super(membership, self)._prepare_portal_layout_values()
        return values
    
    @http.route()
    def pricelist_change(self, pl_id, **post):
        values=super(membership,self).pricelist_change(pl_id=pl_id, post=post)
        user = request.env.user
        if user.sudo().partner_id.active_membership:
            request.session['website_sale_current_pl'] = user.sudo().partner_id.active_membership.membership_plan_id.membership_pricelist.id
            request.website.sale_get_order(force_pricelist=user.sudo().partner_id.active_membership.membership_plan_id.membership_pricelist.id)
        return values

    @http.route('/my/membership/<model("membership.membership"):mydetails>/', website=True, auth='user',type='http')
    def membership_details(self,mydetails,**kw):
        values = self._prepare_portal_layout_values()
        reason=request.env['membership.reasons']
        values.update({
            'page_name': 'Memberships',
            'membership':mydetails,
            'membership_table':False,
            'reason':reason.search([])
            
        })
        return request.render('website_membership_management.membership_info',values) 

    @http.route(['/membership/cancel'],type='http', auth="user", methods=['POST'], website=True, csrf=False)
    def membership_cancel(self,**kw):
        
        
        reason=request.env['membership.reasons'].browse(int(kw['cancel_reason'])).name  
        reason=request.env['membership.reasons'].browse(int(kw['cancel_reason'])).name  
        user=request.env['membership.membership'].sudo().browse(int(kw['mem_mem_record']))
        if user.plan_state == 'in_progress':
            res=user.reset_to_close()
        else:
            res=user.get_cancel_mem()

        if res:
            user.reason=reason + " " + kw['comment_cancel'] 
            
        request.session['website_sale_current_pl'] = pricelist=request.env['product.pricelist'].search([('name','=','Public Pricelist')]).id
        order = request.website.sale_get_order()
        if order:
            order.sudo().unlink()
       
        
        return request.redirect('/my/memberships') 
 

    @http.route('/my/memberships', auth='user',website=True,type='http')
    def membership_table(self,sortby=None,page=1, **kw):

        values = self._prepare_portal_layout_values()

        
        searchbar_sortings = {
            'Newest': {'label': ('Latest'), 'order': 'name desc'},
            'name': {'label': ('Name'), 'order': 'name'},
        }
        if not sortby:
            sortby = 'Newest'
        sort_order = searchbar_sortings[sortby]['order']
        user_id = request.env['res.users'].sudo().browse(request._uid)
        memberships=request.env['membership.membership'].sudo().search([('customer_name','=',user_id.partner_id.id)],order=sort_order)
        values.update({
            'page_name': 'Memberships',
            'memberships':memberships,
            'membership_table':True,
            'searchbar_sortings':searchbar_sortings,
            'sortby':sortby
        })
        return request.render('website_membership_management.my_memberships',values)
    
    @http.route('/membership/',website=True,auth='user',type='http')
    def membership_products(self,**kw):
        product=request.env['product.template'].search([('is_a_membership','=',True)])
        return request.render('website_membership_management.membership_plan',{'mem_product':product})

    @http.route('/membership/update',method=['POST'],auth='user',website=True,csrf=False)
    def membership_data(self,**kw):
        user=request.env['website'].get_membership_count()
        if (kw['optradio']=='immediate'):
            vals=dict(
                immediate=True,
                after=False,
            )
        else:
            vals=dict(
                after=True,
                immediate=False,
            )
        user.sudo().write(vals)
        return request.redirect('/membership/')
    

    @http.route()
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        if request.env['product.product'].browse([int(product_id)]).is_a_membership:
            add_qty=0
            set_qty=1
        values=super(membership,self).cart_update(product_id, add_qty=add_qty, set_qty=set_qty, **kw)
        return values
    
    @http.route('/my/membership/buy',website=True,auth='user',type='http')
    def membership_buy(self,**kw):
        return request.render('website_membership_management.Membership|Buy',{})

    @http.route('/website/membership/renew',website=True,auth='user',type='json')
    def renew_membership(self,renew,**kw):
        if renew:
            done=request.env['membership.membership'].sudo().browse([int(renew)]).membership_renew()
            return True
        else:
            return False

    @http.route('/check/product_variant/membership',type='json',website=True,auth='public')
    def membership_check(self,product_id,**kw):
        if request.env['product.product'].sudo().browse([int(product_id)]).is_a_membership:
            return True
        else:
            return False

    