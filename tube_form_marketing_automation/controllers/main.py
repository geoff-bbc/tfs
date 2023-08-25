import datetime

from odoo import http
from odoo.http import request

class propertModel(http.Controller):
    @http.route(['/unsubscribe-email'], auth='public',type='http', website=True)
    def unsubscribe_email_model(self, **post):

        user_email = post.get('email')
        customer = request.env['res.partner'].search([('email','=',user_email)],limit=1)
        base_url = customer.get_base_url()

        if customer.is_blacklist != True:
            customer.is_blacklist = True
            customer.unsubscription_date = datetime.datetime.now()
        else:
            customer.unsubscription_date = False

        return request.redirect(base_url)
