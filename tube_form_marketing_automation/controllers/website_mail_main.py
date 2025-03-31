# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http
from odoo.http import request
from odoo.addons.website_mail.controllers.main import WebsiteMail

import logging
_logger = logging.getLogger(__name__)

class WebsiteMail(WebsiteMail):

    @http.route(['/website_mail/follow'], type='json', auth="public", website=True)
    def website_message_subscribe(self, id=0, object=None, message_is_follower="on", email=False, **post):
        # TDE FIXME: check this method with new followers
        res_id = int(id)
        is_follower = message_is_follower == 'on'
        record = request.env[object].browse(res_id).exists()
        if not record:
            return False

        record.check_access_rights('read')
        record.check_access_rule('read')

        # search partner_id
        if request.env.user != request.website.user_id:
            partner_ids = request.env.user.partner_id.ids
        else:
            # mail_thread method
            partner_ids = [p.id for p in request.env['mail.thread'].sudo()._mail_find_partner_from_emails([email], records=record.sudo()) if p]
            if not partner_ids or not partner_ids[0]:
                name = email.split('@')[0]
                partner_ids = request.env['res.partner'].sudo().create({'name': name, 'email': email}).ids
        
        # add or remove follower
        if is_follower:
            record.sudo().message_unsubscribe(partner_ids)
            return False
        else:
            # add partner to session
            request.session['partner_id'] = partner_ids[0]
            record.sudo().message_subscribe(partner_ids)

            # Send mail workflow3 while clicking on follow button from blog or blog post
            if partner_ids:
                self.send_email_marketing_automation(partner_ids)
            return True
        

    def send_email_marketing_automation(self, partner_ids):
        # Send mail workflow3 while clicking on follow button from blog or blog post
        for rec in partner_ids:
            try:
                template = request.env.ref('tube_form_marketing_automation.workflow_3_subscribe_email_template')
                template.sudo().send_mail(rec, force_send=True)
            except Exception as e:
                _logger.error(f"Error on sending mail while blog or blog post subscribe: {e}")
        return True