

from odoo import _,api, fields, models, tools, SUPERUSER_ID
from odoo.http import request
import datetime
from dateutil.relativedelta import relativedelta
import json
import logging

_logger = logging.getLogger(__name__)

class Lead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def create(self, vals_list):

        page_url = request.httprequest.form.get('Download')

        if page_url in ['Contact Us']:
            page_details = request.httprequest.form
            customer = self.env['res.partner'].sudo().search([('email', '=', vals_list['email_from'])], limit=1) or \
                       self.env['res.partner'].sudo().search([('phone', '=', vals_list['phone'])], limit=1)

            company_id = self.env['res.partner'].sudo().search([('name','=',vals_list['partner_name'])]).filtered(lambda r: r.company_type == 'company')
            user_id = self.env['res.users'].sudo().search(['&',('name', '=', 'Mike Thomas'),('email','=','mike.thomas@tfs-corp.com')])
            follow_up_2_notify_date_set = datetime.date.today()

            if not company_id:
                # create new company ----
                company_id = self.env['res.partner'].sudo().create({
                    'company_type': 'company',
                    'name': vals_list['partner_name'],
                    'x_studio_primary_business_relationship': 'Customer / Prospect'
                })

            if customer:
                vals_customer_write = {
                    'parent_id': company_id.id,
                    'user_id': user_id.id,
                    'name': vals_list['contact_name'],
                    'x_studio_primary_business_relationship': 'Customer / Prospect'
                }

                new_customer = self.env['res.partner'].browse(customer.id).sudo().write(vals_customer_write)

            else:
                vals_customer_create = {
                    'name': vals_list['contact_name'],
                    'phone': vals_list['phone'],
                    'email': vals_list['email_from'],
                    'parent_id': company_id.id,
                    'user_id': user_id.id,
                }

                #  create new customer ----
                customer = self.env['res.partner'].sudo().create(vals_customer_create)
            vals_list['partner_id'] = customer.id
            res = super(Lead, self).create(vals_list)

            customer.form_partner_list_ids.sudo().create({
                'followup_2_date': follow_up_2_notify_date_set,
                'form_name': page_url,
                'name' : vals_list['contact_name'],
                'email' : vals_list['email_from'],
                'form_partner_list_id' : customer.id,
                'crm_lead_id' : res.id
            })

            base_url = self.get_base_url()

            # send first email notification customer
            if customer.is_blacklist != True and page_url == 'Contact Us':
                first_contact_us_form_email_template = self.env.ref('tube_form_marketing_automation.completed_contact_us_form_template')
                first_contact_us_form_email_template.send_mail(customer.id, force_send=True)

            # send mike email notification to create a opportunity
            completed_contact_us_form_send_mike_email_template = self.env.ref('tube_form_marketing_automation.completed_contact_us_form_send_mike_email_template')
            completed_contact_us_form_send_mike_email_template.send_mail(res.id,force_send=True)

            return res

        else:
            return super(Lead, self).create(vals_list)

