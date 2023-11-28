# Copyright 2023 Bluebird Cloud Consulting 
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json
from datetime import datetime

import requests
import logging

from odoo import fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom.line'

    def open_to_form_view(self):

        name = 'Component'
        res_model = 'mrp.bom.line' 
        view_name = 'mrp.bom.line.view.form'
        
        #document_id = self.browse(cr, uid, ids[0]).id

        #view = models.get_object_reference(cr, uid, name, view)
        #view_id = view and view[1] or False


        return {
            'name': (name),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': 732,
            'res_model': res_model, 
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': 25,
            'flags':{
                'mode':'edit'
                }
        }