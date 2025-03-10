# Copyright 2019-2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details)

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.tools.safe_eval import safe_eval


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_downpayment = fields.Boolean(
        string="Is a down payment",
        help="Down payments are made when creating invoices from a purchase order."
        " They are not copied when duplicating a purchase order.",
    )

    def unlink(self):
        if self.filtered(
            lambda line: line.state in ("purchase", "done")
            and (line.invoice_lines or not line.is_downpayment)
        ):
            raise UserError(
                _(
                    """You can not remove an order line once the Purchase order is confirmed.\n
                    You should rather set the quantity to 0."""
                )
            )
        return super().unlink()

    @api.depends("product_qty", "price_unit", "taxes_id")
    def _compute_amount(self):
        res = super()._compute_amount()
        for line in self.filtered(lambda x: x.is_downpayment):
            line.update({"price_subtotal": 0.0})
        return res

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        if self._context.get("final_payment", False) and self.is_downpayment:
            if self.product_id.purchase_method == "purchase":
                qty = self.qty_invoiced
            else:
                qty = self.qty_received - self.qty_invoiced

            vals = {
                "name": "{}: {}".format(self.order_id.name, self.name),
                "currency_id": move and move.currency_id.id or self.currency_id.id,
                "purchase_line_id": self.id,
                "product_uom_id": self.product_uom.id,
                "product_id": self.product_id.id,
                "price_unit": self.price_unit,
                "quantity": qty,
                "analytic_distribution": self.analytic_distribution,
                "tax_ids": [(6, 0, self.taxes_id.ids)],
                "display_type": self.display_type or "product",
            }

            if move:
                vals.update({
                    "move_id": move.id,
                    "date_maturity": move.invoice_date_due,
                    "partner_id": move.partner_id.id,
                })

            return vals
        elif self.is_downpayment:
            if self.product_id.purchase_method == "purchase":
                qty = self.product_qty - self.qty_invoiced
            else:
                qty = self.qty_received - self.qty_invoiced

            vals = {
                "name": "{}: {}".format(self.order_id.name, self.name),
                "currency_id": move and move.currency_id.id or self.currency_id.id,
                "purchase_line_id": self.id,
                "product_uom_id": self.product_uom.id,
                "product_id": self.product_id.id,
                "price_unit": self.price_unit,
                "quantity": qty,
                "analytic_distribution": self.analytic_distribution,
                "tax_ids": [(6, 0, self.taxes_id.ids)],
                "display_type": self.display_type or "product",
            }
            if move:
                vals.update({
                    "move_id": move.id,
                    "date_maturity": move.invoice_date_due,
                    "partner_id": move.partner_id.id,
                })
            return vals
        else:
            return super()._prepare_account_move_line(move)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange("partner_id")
    def _set_partner_supplier_currency_id(self):
        self.currency_id = (
            self.partner_id.property_purchase_currency_id or self.partner_id.currency_id
        )

    def copy_data(self, default=None):
        if default is None:
            default = {}
        if "order_line" not in default:
            default["order_line"] = [
                (0, 0, line.copy_data()[0])
                for line in self.order_line.filtered(
                    lambda order_line: not order_line.is_downpayment
                )
            ]
        return super().copy_data(default)

    def action_view_invoice(self, invoices=False):
        res = super().action_view_invoice()
        res["context"] = dict(safe_eval(res.get("context")))
        invoices = self.mapped("invoice_ids")
        if self._context.get("purchase_bill", False):
            if "downpayment_line" in res["context"]:
                res["context"]["downpayment_line"] = True
            if len(invoices) > 1:
                action = self.env["ir.actions.act_window"]._for_xml_id(
                    "account.action_move_in_invoice_type"
                )
                action["domain"] = [("id", "in", invoices.ids)]
                return action
            elif len(invoices) == 1:
                res["views"] = [(self.env.ref("account.view_move_form").id, "form")]
                res["res_id"] = invoices.ids[0]
        elif self._context.get("final", False):
            if len(invoices) > 1:
                action = self.env["ir.actions.act_window"]._for_xml_id(
                    "account.action_move_in_invoice_type"
                )
                action["domain"] = [("id", "in", invoices.ids)]
                return action
            elif len(invoices) == 1:
                res["views"] = [(self.env.ref("account.view_move_form").id, "form")]
                res["res_id"] = invoices.ids[0]
            res["context"]["final_payment"] = True
        elif self._context.get("without_downpayment", False):
            if not invoices:
                raise UserError(
                    _(
                        """There is no invoiceable line.
                        If a product has a Received quantities control policy,
                        please make sure that a quantity has been received."""
                    )
                )
            res["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            res["res_id"] = invoices.ids[0]
        return res

    @api.depends("state", "order_line.qty_to_invoice")
    def _get_invoiced(self):
        """
        Sodexis override to skip the downpayment line
        in the vendor bill status calculation.
        """
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for order in self:
            if order.state not in ("purchase", "done"):
                order.invoice_status = "no"
                continue

            if any(
                not float_is_zero(line.qty_to_invoice, precision_digits=precision)
                for line in order.order_line.filtered(
                    lambda order_line: not order_line.display_type
                    and not order_line.is_downpayment
                )
                # Sodexis Override: added and not l.is_downpayment here
            ):
                order.invoice_status = "to invoice"
            elif (
                all(
                    float_is_zero(line.qty_to_invoice, precision_digits=precision)
                    for line in order.order_line.filtered(
                        lambda order_line: not order_line.display_type
                    )
                )
                and order.invoice_ids
            ):
                order.invoice_status = "invoiced"
            else:
                order.invoice_status = "no"
