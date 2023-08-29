
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

            return res
        else:
            return super(Mailing, self).create(vals_list)



