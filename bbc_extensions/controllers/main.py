import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class TestModelWizard(models.TransientModel):
    _name =  'test.model.wizard'
    _description = 'Test Model Wizard'
    test_field = fields.Char(string = 'Test Field')
    
    def action_done(self):
        records = self.env['test.model'].browse(self.env.context.get('active_ids'))
        for rec in records: 
            rec.write({'state' : 'done'})
            
class NoQuotationSaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_quotation_send(self):
    self.ensure_one()

    if self.state != "sale":
    return False

    # Use this if you want to use the access token in your email-template:
    # self._portal_ensure_token()

    return super(NoQuotationSaleOrder, self).action_quotation_send()