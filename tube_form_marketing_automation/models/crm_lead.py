

from odoo import _,api, fields, models, tools, SUPERUSER_ID
from odoo.http import request
import datetime
from dateutil.relativedelta import relativedelta


class Lead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def create(self, vals_list):

        customer = self.env['res.partner'].sudo().search([('email', '=', vals_list['email_from'])], limit=1) or \
                   self.env['res.partner'].sudo().search([('phone', '=', vals_list['phone'])], limit=1)

        company_id = self.env['res.partner'].sudo().search([('name','=',vals_list['partner_name'])]).filtered(lambda r: r.company_type == 'company')
        user_id = self.env['res.users'].sudo().search(['&',('name', '=', 'Mike Thomas'),('email','=','mike.thomas@tfs-corp.com')])

        if not company_id:
            # create new company ----
            company_id = self.env['res.partner'].sudo().create({
                'company_type': 'company',
                'name': vals_list['partner_name'],
                'x_studio_primary_business_relationship': 'Customer / Prospect'
            })

        if customer:
            new_customer = self.env['res.partner'].browse(customer.id).sudo().write({
                'parent_id': company_id.id,
                'user_id': user_id.id,
                'contact_us_email_notify_date': datetime.date.today() + relativedelta(days=+7),
                'x_studio_primary_business_relationship': 'Customer / Prospect'
            })

        else:
            #  create new customer ----
            customer = self.env['res.partner'].sudo().create({
                'name': vals_list['contact_name'],
                'phone': vals_list['phone'],
                'email': vals_list['email_from'],
                'parent_id': company_id.id,
                'user_id': user_id.id,
                'contact_us_email_notify_date': datetime.date.today() + relativedelta(days=+7),
                'x_studio_primary_business_relationship': 'Customer / Prospect'
            })
        vals_list['partner_id'] = customer.id

        res = super(Lead, self).create(vals_list)
        base_url = self.get_base_url()

        # send first email notification customer
        first_email_details = {
            'to_email_id': customer.email,
            'customer_name': vals_list['contact_name']
        }
        if customer.is_blacklist != True:
            first_contact_us_form_email_template = self.env.ref('tube_form_marketing_automation.completed_contact_us_form_template')
            first_contact_us_form_email_template.with_context(**first_email_details).send_mail(customer.id, force_send=True)

        # send mike email notification to create a opportunity
        completed_contact_us_form_send_mike_email_template = self.env.ref('tube_form_marketing_automation.completed_contact_us_form_send_mike_email_template')
        completed_contact_us_form_send_mike_email_template.send_mail(res.id,force_send=True)

        return res