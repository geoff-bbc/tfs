
from odoo import _,api, fields, models, tools, SUPERUSER_ID
from odoo.http import request
import datetime
from dateutil.relativedelta import relativedelta
import json




class Mailing(models.Model):
    _inherit = "mailing.contact"

    followup_2_notify_date = fields.Text(string="Follow Up 2 Notify Date")
    followup_3_notify_date = fields.Text(string="Follow Up 3 Notify Date")
    mailing_contact_list_ids = fields.One2many('mailing.contact.list','mailing_contact_id',string="Mailing Contact List")

    @api.model
    def create(self, vals_list):

        page_url = request.httprequest.form.get('Download')
        if page_url in ['Tube End Forming Explained','Checklist for Tube Bender Tooling Specs','Tube Section Modulus Calculator and Tube Bending Formulas','ROI Calculator','Tube Bender Buying Checklist']:
            form_data = request.httprequest.form
            maling_contact = self.env['mailing.contact'].sudo().search([('email','=',vals_list['email'])],limit=1)
            if form_data.get('country_id'):
                country_id = self.env["res.country"].sudo().browse(int(form_data.get('country_id'))).name
            else:
                country_id = False
            form_details_dict = {
                'name': form_data.get('name'),
                'email': form_data.get('email'),
                'country': country_id,
                'Phone Number' :form_data.get('Phone Number'),
                'State / Province' : form_data.get('State / Province'),
                'Best Describes Me' : form_data.get('Best Describes Me'),
            }

            if maling_contact :
                maling_contact.mailing_contact_list_ids.sudo().create({
                    'creation_date' : datetime.datetime.now(),
                    'form_name' : form_data.get('Download') ,
                    'form_details' : json.dumps(form_details_dict),
                    'mailing_contact_id' : maling_contact.id
                })

                if page_url == 'Tube End Forming Explained':
                    followup_1_tef_explained = self.env.ref(
                        'tube_form_marketing_automation.followup_1_tef_explained_email_template')
                    followup_1_tef_explained.send_mail(maling_contact.id, force_send=True)

                elif page_url == 'Checklist for Tube Bender Tooling Specs':
                    followup_1_tef_explained = self.env.ref(
                        'tube_form_marketing_automation.followup_1_specifying_tube_bender_email_template')
                    followup_1_tef_explained.send_mail(maling_contact.id, force_send=True)

                elif page_url == 'ROI Calculator':
                    followup_1_tef_explained = self.env.ref(
                        'tube_form_marketing_automation.followup_1_roi_calculator_email_template')
                    followup_1_tef_explained.send_mail(maling_contact.id, force_send=True)

                elif page_url == 'Tube Section Modulus Calculator and Tube Bending Formulas':
                    followup_1_tef_explained = self.env.ref(
                        'tube_form_marketing_automation.followup_1_section_modulus_calculator_email_template')
                    followup_1_tef_explained.send_mail(maling_contact.id, force_send=True)

                elif page_url == 'Tube Bender Buying Checklist':
                    followup_1_tef_explained = self.env.ref(
                        'tube_form_marketing_automation.followup_1_tube_bender_buying_email_template')
                    followup_1_tef_explained.send_mail(maling_contact.id, force_send=True)

                return maling_contact

            else:
                res = super(Mailing, self).create(vals_list)

                res.mailing_contact_list_ids.sudo().create({
                    'creation_date' : datetime.datetime.now(),
                    'form_name' : form_data.get('Download') ,
                    'form_details' : json.dumps(form_details_dict),
                    'mailing_contact_id' : res.id
                })

                if page_url == 'Tube End Forming Explained':
                    followup_1_tef_explained = self.env.ref('tube_form_marketing_automation.followup_1_tef_explained_email_template')
                    followup_1_tef_explained.send_mail(res.id, force_send=True)

                elif page_url == 'Checklist for Tube Bender Tooling Specs':
                    followup_1_tef_explained = self.env.ref('tube_form_marketing_automation.followup_1_specifying_tube_bender_email_template')
                    followup_1_tef_explained.send_mail(res.id, force_send=True)

                elif page_url == 'ROI Calculator':
                    followup_1_tef_explained = self.env.ref('tube_form_marketing_automation.followup_1_roi_calculator_email_template')
                    followup_1_tef_explained.send_mail(res.id, force_send=True)

                elif page_url == 'Tube Section Modulus Calculator and Tube Bending Formulas':
                    followup_1_tef_explained = self.env.ref('tube_form_marketing_automation.followup_1_section_modulus_calculator_email_template')
                    followup_1_tef_explained.send_mail(res.id, force_send=True)

                elif page_url == 'Tube Bender Buying Checklist':
                    followup_1_tef_explained = self.env.ref('tube_form_marketing_automation.followup_1_tube_bender_buying_email_template')
                    followup_1_tef_explained.send_mail(res.id, force_send=True)

                return res
        else:
            return super(Mailing, self).create(vals_list)


    def completed_mailing_contact_form_cron(self):

        follow_up_2_notify_day = self.env['ir.config_parameter'].sudo().get_param('follow_up_2_notify_day')
        follow_up_2_notify_date_set = datetime.date.today() + relativedelta(days=-int(follow_up_2_notify_day))
        followup_2_notify_date_list = self.env["mailing.contact.list"].sudo().search([('creation_date','=',follow_up_2_notify_date_set)])
        today_date = datetime.datetime.today()
        for followup_2_notify_record in followup_2_notify_date_list:
            if 'Tube End Forming Explained' == followup_2_notify_record.form_name:

                write_mailing_contact = followup_2_notify_record.sudo().write({'followup_3_notify_date': today_date})

                followup_2_tef_explained_email_template = self.env.ref('tube_form_marketing_automation.followup_2_tef_explained_email_template')
                followup_2_tef_explained_email_template.send_mail(followup_2_notify_record.mailing_contact_id.id,force_send=True)


            if 'Checklist for Tube Bender Tooling Specs' == followup_2_notify_record.form_name:

                write_mailing_contact = followup_2_notify_record.sudo().write({'followup_3_notify_date': today_date})

                followup_2_specifying_tube_bender_email_template = self.env.ref('tube_form_marketing_automation.followup_2_specifying_tube_bender_email_template')
                followup_2_specifying_tube_bender_email_template.send_mail(followup_2_notify_record.mailing_contact_id.id, force_send=True)

            if 'Tube Bender Buying Checklist' == followup_2_notify_record.form_name:

                write_mailing_contact = followup_2_notify_record.sudo().write({'followup_3_notify_date': today_date})

                followup_2_tube_bender_buying_email_template = self.env.ref('tube_form_marketing_automation.followup_2_tube_bender_buying_email_template')
                followup_2_tube_bender_buying_email_template.send_mail(followup_2_notify_record.mailing_contact_id.id, force_send=True)



        # Followup 3 send mail notification

        follow_up_3_notify_day = self.env['ir.config_parameter'].sudo().get_param('follow_up_3_notify_day')
        follow_up_3_notify_date_set = datetime.date.today() + relativedelta(days=-(int(follow_up_3_notify_day)))
        followup_3_notify_date_list = self.env["mailing.contact.list"].sudo().search([('followup_3_notify_date', '=', follow_up_3_notify_date_set)])

        for followup_3_notify_record in followup_3_notify_date_list :
            if 'Tube End Forming Explained' == followup_3_notify_record.form_name:
                contact_us_after_week_notify_email_template = self.env.ref('tube_form_marketing_automation.followup_3_tef_explained_email_template')
                contact_us_after_week_notify_email_template.send_mail(followup_3_notify_record.mailing_contact_id.id,force_send=True)
