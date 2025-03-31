import datetime

from odoo import http
from odoo.http import request

class propertModel(http.Controller):
    @http.route(['/unsubscribe-email'], auth='public', type='http', website=True)
    def unsubscribe_email_model(self, **post):
        user_email = post.get('email')
        customer = request.env['res.partner'].search([('email', '=', user_email)],limit=1)
        base_url = customer.get_base_url()
        if customer:
            if customer.is_blacklist != True:
                customer.sudo().write({'is_blacklist': True,
                                       'unsubscription_date': datetime.datetime.now()})
        request.env.cr.commit()
        return request.redirect(base_url)

    @http.route(['/unsubscribe-emailing-list'], auth='public', type='http', website=True)
    def unsubscribe_email_model(self, **post):
        user_email = post.get('email')
        mailing_blacklisted_email = request.env['mail.blacklist'].search([('email','=', user_email)],limit=1)
        base_url = mailing_blacklisted_email.get_base_url()

        if not mailing_blacklisted_email:
            request.env['mail.blacklist'].sudo()._add(user_email)

        request.env.cr.commit()
        return request.redirect(base_url)
