from odoo import fields, models

class ResConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    follow_up_2_notify_day = fields.Integer(string='2nd Followup Delay (In Days)',config_parameter = "follow_up_2_notify_day")
    follow_up_3_notify_day = fields.Integer(string='3rd Followup Delay (In Days)',config_parameter = "follow_up_3_notify_day")

