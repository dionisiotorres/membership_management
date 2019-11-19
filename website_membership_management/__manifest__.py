# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
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
#################################################################################
{
  "name"                 :  "Website Membership Management",
  "summary"              :  "Odoo Website Membership Management allows you to manage various membership programs for your customers efficiently.",
  "category"             :  "Website",
  "version"              :  "1.2.2",
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/odoo-website-membership-management.html",
  "description"          :  """Odoo Website Membership Management
Membership Management in Odoo Website 
Odoo Membership Management
Membership-based services in Odoo
Manage recurring bills in Odoo
Membership Management Software in Odoo
Membership module for Odoo users
module for membership management in Odoo
recurring billing management in Odoo
Website Membership Module for Odoo
how to manage recurring services bills in Odoo
Membership Plans services
Membership
Odoo Membership
manage membership products in Odoo
Membership products
Odoo Subscription Management
Odoo Website Subscription management
Odoo booking & reservation management
Odoo appointment management
Odoo website appointment management""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=website_membership_management&custom_url=/membership/",
  "depends"              :  [
                             'website_sale',
                             'sale_management',
                            ],
  "data"                 :  [
                             'security/membership_security.xml',
                             'security/ir.model.access.csv',
                             'views/MembershipSequence.xml',
                             'data/email_successful.xml',
                             'data/email_reminder.xml',
                             'data/automatic_invoice.xml',
                             'wizard/MessageWizard.xml',
                             'wizard/cancel_reason_wizard.xml',
                             'views/MembershipPlan.xml',
                             'views/MembershipProduct.xml',
                             'views/Membership.xml',
                             'views/MembershipMainTemplate.xml',
                             'views/MembershipReason.xml',
                             'views/res_config_view.xml',
                             'views/MembershipCustomer.xml',
                             'views/MembershipMenu.xml',
                            ],
  "demo"                 :  [
                             'demo/membership_plan_demo.xml',
                             'demo/membership_product_demo.xml',
                             'demo/membership_demo.xml',
                             'demo/membership_reason_demo.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "price"                :  99,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}