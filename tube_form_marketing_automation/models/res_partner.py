
from odoo import api, fields, models, tools, SUPERUSER_ID
import datetime
from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = "res.partner"

    contact_us_email_notify_date = fields.Date(string="Contact Us Email Notify Date")
    is_blacklist = fields.Boolean(string="Email Blacklist")
    unsubscription_date = fields.Datetime(string="Unsubscription Date")

    def completed_contact_us_form_cron(self):
        contact_list = self.env["res.partner"].search([('contact_us_email_notify_date','=',[datetime.date.today()])])
        contact_us_after_week_notify_email_template = self.env.ref('tube_form_marketing_automation.completed_contact_us_form_after_week_template')

        for customer in contact_list:
            after_week_email_details = {
                'to_email_id': customer.email,
                'customer_name': customer.name
            }
            if customer.is_blacklist != True:
                contact_us_after_week_notify_email_template.with_context(**after_week_email_details).send_mail(customer.id,force_send=True)

    @api.onchange('is_blacklist')
    def _onchange_blacklist(self):
        if self.is_blacklist != True:
            self.unsubscription_date = False
        else:
            self.unsubscription_date = datetime.datetime.now()


