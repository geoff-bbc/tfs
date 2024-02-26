import logging

_logger = logging.getLogger(__name__)

class TestModelWizard(models.TransientModel):
    _name =  ‘test.model.wizard’
    _description = ‘Test Model Wizard’
    test_field = fields.Char(string = ‘Test Field’)
    
    def action_done(self):
        records = self.env['test.model'].browse(self.env.context.get('active_ids'))
        for rec in records: 
            rec.write({'state' : ’done’})