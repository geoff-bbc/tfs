
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


    def completed_contact_us_form_cron(self):

        followup_2_notify_date_list = self.env["res.partner"].sudo().search_read([],['id','followup_2_notify_date','is_blacklist'])
        follow_up_2_notify_day = self.env['ir.config_parameter'].sudo().get_param('follow_up_2_notify_day')
        follow_up_3_notify_date_set = datetime.date.today() + relativedelta(days=-int(follow_up_2_notify_day))

        for followup_2_notify_date_dict in followup_2_notify_date_list:

            if followup_2_notify_date_dict.get('followup_2_notify_date') :
                follow_up_2_notify_date_vals = eval(followup_2_notify_date_dict.get('followup_2_notify_date'))

                if 'contact-us' in follow_up_2_notify_date_vals :
                    if str(follow_up_3_notify_date_set) == follow_up_2_notify_date_vals.get('contact-us'):
                        contact_id = followup_2_notify_date_dict.get('id')
                        contacts = self.env["res.partner"].sudo().browse(contact_id)
                        vals_customer_write = {}
                        if contacts.followup_3_notify_date:
                            followup_3_notify_date_dict = eval(contacts.followup_3_notify_date)
                            followup_3_notify_date_dict['contact-us'] = str(follow_up_3_notify_date_set)
                            vals_customer_write['followup_3_notify_date'] = json.dumps(followup_3_notify_date_dict)
                        else:
                            vals_customer_write['followup_3_notify_date'] = json.dumps({'contact-us': str(follow_up_3_notify_date_set)})

                        new_customer = contacts.sudo().write(vals_customer_write)

                        if followup_2_notify_date_dict.get('is_blacklist') != True:
                            contact_us_after_week_notify_email_template = self.env.ref('tube_form_marketing_automation.completed_contact_us_form_after_week_template')
                            contact_us_after_week_notify_email_template.send_mail(contact_id,force_send=True)

                if 'tube-end-forming-explained' in follow_up_2_notify_date_vals :
                    if str(follow_up_3_notify_date_set) == follow_up_2_notify_date_vals.get('tube-end-forming-explained'):
                        contact_id = followup_2_notify_date_dict.get('id')
                        contacts = self.env["res.partner"].sudo().browse(contact_id)
                        vals_customer_write = {}
                        if contacts.followup_3_notify_date:
                            followup_3_notify_date_dict = eval(contacts.followup_3_notify_date)
                            followup_3_notify_date_dict['contact-us'] = str(follow_up_3_notify_date_set)
                            vals_customer_write['followup_3_notify_date'] = json.dumps(followup_3_notify_date_dict)

                        else:
                            vals_customer_write['followup_3_notify_date'] = json.dumps(
                                {'contact-us': str(follow_up_3_notify_date_set)})

                        new_customer = contacts.sudo().write(vals_customer_write)

                        if followup_2_notify_date_dict.get('is_blacklist') != True:
                            contact_us_after_week_notify_email_template = self.env.ref('tube_form_marketing_automation.followup_2_tef_explained_email_template')
                            contact_us_after_week_notify_email_template.send_mail(contact_id,force_send=True)

    @api.onchange('is_blacklist')
    def _onchange_blacklist(self):
        if self.is_blacklist != True:
            self.unsubscription_date = False
        else:
            self.unsubscription_date = datetime.datetime.now()
