# Copyright 2019-2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from . import models
from . import wizard

from odoo import api, SUPERUSER_ID


def _post_init_hook(cr, registry):
    """Deactivate the server action 'Create Vendor Bills' once this app is installed"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    vendor_bill_server_action = env.ref("purchase.action_purchase_batch_bills")
    if vendor_bill_server_action:
        vendor_bill_server_action.write({"binding_model_id": ""})


def _uninstall_hook(cr, registry):
    """Activate the server action 'Create Vendor Bills' once this app is uninstalled"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    model = env["ir.model"].search([("model", "=", "purchase.order")])
    vendor_bill_server_action = env.ref("purchase.action_purchase_batch_bills")

    if vendor_bill_server_action:
        vendor_bill_server_action.write({"binding_model_id": model.id})
