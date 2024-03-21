# -*- coding: utf-8 -*-
# from odoo import http


# class SalesOverride(http.Controller):
#     @http.route('/sales_override/sales_override', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sales_override/sales_override/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sales_override.listing', {
#             'root': '/sales_override/sales_override',
#             'objects': http.request.env['sales_override.sales_override'].search([]),
#         })

#     @http.route('/sales_override/sales_override/objects/<model("sales_override.sales_override"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sales_override.object', {
#             'object': obj
#         })
