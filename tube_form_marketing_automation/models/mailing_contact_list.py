
from odoo import _,api, fields, models, tools, SUPERUSER_ID
from odoo.http import request
import datetime
from dateutil.relativedelta import relativedelta
import json




class Mailing(models.Model):
    _name = "mailing.contact.list"
    _description = 'Mailing Contact List'

    creation_date = fields.Date(string='Date')
    followup_3_notify_date = fields.Date(string='Followup 3 Notification Date')
    form_name = fields.Char(string='Form Name')
    form_details = fields.Text(string='Form Details')
    followup_boolean = fields.Boolean(string='2nd Followup Check')
    email = fields.Char(string="Email")
    mailing_contact_id = fields.Many2one('mailing.contact',string="Mailing Contact")
