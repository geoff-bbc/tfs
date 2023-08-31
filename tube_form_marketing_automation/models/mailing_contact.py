
from odoo import _,api, fields, models, tools, SUPERUSER_ID
from odoo.http import request
import datetime
from dateutil.relativedelta import relativedelta
import json




class Mailing(models.Model):
    _inherit = "mailing.contact"

    followup_2_notify_date = fields.Text(string="Follow Up 2 Notify Date")
    followup_3_notify_date = fields.Text(string="Follow Up 3 Notify Date")

    @api.model
    def create(self, vals_list):

        page_url = request.httprequest.form.get('Page_url')
        if page_url in ['roi-calculator','tube-end-forming-explained','specifying-tube-bender-tooling','tube-bender-buying-checklist','section-modulus-calculator']:
            follow_up_2_notify_date_set = datetime.date.today()
            res = super(Mailing, self).create(vals_list)
            vals_mailing_contact_create = {}
            if res.followup_2_notify_date:
                followup_2_notify_date_dict = eval(res.custom_data)
                followup_2_notify_date_dict[page_url] = str(follow_up_2_notify_date_set)
                vals_mailing_contact_create['followup_2_notify_date'] = json.dumps(followup_2_notify_date_dict)
            else:
                vals_mailing_contact_create['followup_2_notify_date'] = json.dumps({page_url: str(follow_up_2_notify_date_set)})

            res.sudo().write(vals_mailing_contact_create)

            if res :
                if res.is_blacklisted != True and page_url == 'tube-end-forming-explained':
                    followup_1_tef_explained = self.env.ref('tube_form_marketing_automation.followup_1_tef_explained_email_template')
                    followup_1_tef_explained.send_mail(res.id, force_send=True)

                elif res.is_blacklisted != True and page_url == 'specifying-tube-bender-tooling':
                    followup_1_tef_explained = self.env.ref('tube_form_marketing_automation.followup_1_specifying_tube_bender_email_template')
                    followup_1_tef_explained.send_mail(res.id, force_send=True)

                elif res.is_blacklisted != True and page_url == 'roi-calculator':
                    followup_1_tef_explained = self.env.ref('tube_form_marketing_automation.followup_1_roi_calculator_email_template')
                    followup_1_tef_explained.send_mail(res.id, force_send=True)

                elif res.is_blacklisted != True and page_url == 'section-modulus-calculator':
                    followup_1_tef_explained = self.env.ref('tube_form_marketing_automation.followup_1_section_modulus_calculator_email_template')
                    followup_1_tef_explained.send_mail(res.id, force_send=True)

                elif res.is_blacklisted != True and page_url == 'tube-bender-buying-checklist':
                    followup_1_tef_explained = self.env.ref('tube_form_marketing_automation.followup_1_tube_bender_buying_email_template')
                    followup_1_tef_explained.send_mail(res.id, force_send=True)

            return res
        else:
            return super(Mailing, self).create(vals_list)


    def completed_mailing_contact_form_cron(self):

        followup_notify_date_list = self.env["mailing.contact"].sudo().search_read([],['id','followup_2_notify_date','followup_3_notify_date','is_blacklisted'])
        follow_up_2_notify_day = self.env['ir.config_parameter'].sudo().get_param('follow_up_2_notify_day')
        follow_up_2_notify_date_set = datetime.date.today() + relativedelta(days=-int(follow_up_2_notify_day))
        follow_up_3_notify_day = self.env['ir.config_parameter'].sudo().get_param('follow_up_3_notify_day')
        follow_up_3_notify_date_set = datetime.date.today() + relativedelta(days=-int(follow_up_3_notify_day))

        for followup_notify_date_dict in followup_notify_date_list:

            if followup_notify_date_dict.get('followup_2_notify_date') :
                follow_up_2_notify_date_vals = eval(followup_notify_date_dict.get('followup_2_notify_date'))

                if 'tube-end-forming-explained' in follow_up_2_notify_date_vals :
                    if str(follow_up_2_notify_date_set) == follow_up_2_notify_date_vals.get('tube-end-forming-explained'):
                        mailing_contact_id = followup_notify_date_dict.get('id')
                        contacts = self.env["mailing.contact"].sudo().browse(mailing_contact_id)
                        vals_customer_write = {}
                        if contacts.followup_3_notify_date:
                            followup_3_notify_date_dict = eval(contacts.followup_3_notify_date)
                            followup_3_notify_date_dict['tube-end-forming-explained'] = str(follow_up_2_notify_date_set)
                            vals_customer_write['followup_3_notify_date'] = json.dumps(followup_3_notify_date_dict)
                        else:
                            vals_customer_write['followup_3_notify_date'] = json.dumps({'tube-end-forming-explained': str(follow_up_2_notify_date_set)})

                        write_mailing_contact = contacts.sudo().write(vals_customer_write)

                        if followup_notify_date_dict.get('is_blacklisted') != True:
                            contact_us_after_week_notify_email_template = self.env.ref('tube_form_marketing_automation.followup_2_tef_explained_email_template')
                            contact_us_after_week_notify_email_template.send_mail(mailing_contact_id,force_send=True)

                if 'specifying-tube-bender-tooling' in follow_up_2_notify_date_vals:
                    if str(follow_up_2_notify_date_set) == follow_up_2_notify_date_vals.get(
                            'specifying-tube-bender-tooling'):
                        mailing_contact_id = followup_notify_date_dict.get('id')
                        contacts = self.env["mailing.contact"].sudo().browse(mailing_contact_id)
                        vals_customer_write = {}
                        if contacts.followup_3_notify_date:
                            followup_3_notify_date_dict = eval(contacts.followup_3_notify_date)
                            followup_3_notify_date_dict['specifying-tube-bender-tooling'] = str(follow_up_2_notify_date_set)
                            vals_customer_write['followup_3_notify_date'] = json.dumps(followup_3_notify_date_dict)
                        else:
                            vals_customer_write['followup_3_notify_date'] = json.dumps(
                                {'specifying-tube-bender-tooling': str(follow_up_2_notify_date_set)})

                        write_mailing_contact = contacts.sudo().write(vals_customer_write)

                        if followup_notify_date_dict.get('is_blacklisted') != True:
                            contact_us_after_week_notify_email_template = self.env.ref('tube_form_marketing_automation.followup_2_specifying_tube_bender_email_template')
                            contact_us_after_week_notify_email_template.send_mail(mailing_contact_id, force_send=True)

                if 'tube-bender-buying-checklist' in follow_up_2_notify_date_vals:
                    if str(follow_up_2_notify_date_set) == follow_up_2_notify_date_vals.get('tube-bender-buying-checklist'):
                        mailing_contact_id = followup_notify_date_dict.get('id')
                        contacts = self.env["mailing.contact"].sudo().browse(mailing_contact_id)
                        vals_customer_write = {}
                        if contacts.followup_3_notify_date:
                            followup_3_notify_date_dict = eval(contacts.followup_3_notify_date)
                            followup_3_notify_date_dict['tube-bender-buying-checklist'] = str(follow_up_2_notify_date_set)
                            vals_customer_write['followup_3_notify_date'] = json.dumps(followup_3_notify_date_dict)
                        else:
                            vals_customer_write['followup_3_notify_date'] = json.dumps(
                                {'tube-bender-buying-checklist': str(follow_up_2_notify_date_set)})

                        write_mailing_contact = contacts.sudo().write(vals_customer_write)

                        if followup_notify_date_dict.get('is_blacklisted') != True:
                            contact_us_after_week_notify_email_template = self.env.ref('tube_form_marketing_automation.followup_2_tube_bender_buying_email_template')
                            contact_us_after_week_notify_email_template.send_mail(mailing_contact_id, force_send=True)

            if followup_notify_date_dict.get('followup_3_notify_date') :
                follow_up_3_notify_date_vals = eval(followup_notify_date_dict.get('followup_3_notify_date'))

                if 'tube-end-forming-explained' in follow_up_3_notify_date_vals :
                    if str(follow_up_3_notify_date_set) == follow_up_3_notify_date_vals.get('tube-end-forming-explained'):
                        mailing_contact_id = followup_notify_date_dict.get('id')

                        if followup_notify_date_dict.get('is_blacklisted') != True:
                            contact_us_after_week_notify_email_template = self.env.ref('tube_form_marketing_automation.followup_3_tef_explained_email_template')
                            contact_us_after_week_notify_email_template.send_mail(mailing_contact_id,force_send=True)
