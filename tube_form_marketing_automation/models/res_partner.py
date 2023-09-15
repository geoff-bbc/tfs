
from odoo import api, fields, models, tools, SUPERUSER_ID
import datetime
import json
from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_blacklist = fields.Boolean(string="Email Blacklist")
    followup_2_notify_date = fields.Text(string="Follow Up 2 Notify Date")
    followup_3_notify_date = fields.Text(string="Follow Up 3 Notify Date")
    unsubscription_date = fields.Datetime(string="Unsubscription Date")
    contact_us_email_notify_date = fields.Date(string="Contact Us Email Notify Date")
    form_partner_list_ids = fields.One2many('form.partner.list','form_partner_list_id')

    def completed_contact_us_form_cron(self):
        # 1 week follow up mail send process
        follow_up_week_notify_date = datetime.date.today() + relativedelta(days=-7)
        followup_week_notify_date_list = self.env["form.partner.list"].sudo().search([('followup_2_date','=',follow_up_week_notify_date)])

        for followup_week_notify_record in followup_week_notify_date_list:

            if followup_week_notify_record.form_name == 'Contact Us':

                if followup_week_notify_record.form_partner_list_id.is_blacklist != True:
                    contact_us_after_week_notify_email_template = self.env.ref('tube_form_marketing_automation.completed_contact_us_form_after_week_template')
                    contact_us_after_week_notify_email_template.send_mail(followup_week_notify_record.id,force_send=True)


    @api.onchange('is_blacklist')
    def _onchange_blacklist(self):
        if self.is_blacklist != True:
            self.unsubscription_date = False
        else:
            self.unsubscription_date = datetime.datetime.now()


class FormPartnerList(models.Model):
    _name = "form.partner.list"

    form_partner_list_id = fields.Many2one('res.partner')
    form_name = fields.Char('Form Name')
    name = fields.Char('Name')
    email = fields.Char('Email')
    followup_2_date = fields.Date('Date')
    crm_lead_id = fields.Many2one('crm.lead',string = 'CRM Lead')

