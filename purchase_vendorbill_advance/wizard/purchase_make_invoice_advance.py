# Copyright 2019-2023 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseAdvancePaymentInv(models.TransientModel):
    _name = "purchase.advance.payment.inv"
    _description = "Purchase Advance Payment"

    @api.model
    def _count(self):
        return len(self._context.get("active_ids", []))

    @api.model
    def _default_product_id(self):
        product_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("purchase.default_deposit_product_id")
        )
        return self.env["product.product"].browse(int(product_id))

    @api.model
    def _get_advance_payment_method(self):
        if self._count() == 1:
            purchase_obj = self.env["purchase.order"]
            order = purchase_obj.browse(self._context.get("active_ids"))[0]
            if (
                order.order_line.filtered(lambda dp: dp.is_downpayment)
                and order.invoice_ids.filtered(
                    lambda invoice: invoice.state != "cancel"
                )
                or order.order_line.filtered(
                    lambda order_line: order_line.qty_to_invoice < 0
                )
            ):
                if order.invoice_status == "no":
                    return "percentage"
                return "all"
            elif order.invoice_status in ("invoiced", "no"):
                return "percentage"
            else:
                return "delivered"
        return "all"

    advance_payment_method = fields.Selection(
        [
            ("delivered", "Billable lines"),
            ("all", "Billable lines (deduct down payments)"),
            ("percentage", "Down payment (percentage)"),
            ("fixed", "Down payment (fixed amount)"),
        ],
        string="What do you want to bill?",
        default=_get_advance_payment_method,
    )
    amount = fields.Float(
        "Down Payment Amount",
        digits="Account",
        help="The amount to be invoiced in advance, taxes excluded.",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Down Payment Product",
        domain=[("type", "=", "service")],
        default=_default_product_id,
    )
    count = fields.Integer(default=_count, string="Order Count")

    def _get_advance_details(self, order):
        context = {"lang": order.partner_id.lang}
        if self.advance_payment_method == "percentage":
            if all(self.product_id.taxes_id.mapped("price_include")):
                amount = order.amount_total * self.amount / 100
            else:
                amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount)
        else:
            amount = self.amount
            name = _("Down Payment")
        del context

        return amount, name

    def _prepare_invoice(self, order, po_line, amount, name, account_id, tax_ids):
        vals = {
            "partner_id": order.partner_id.id,
            "currency_id": order.partner_id.property_purchase_currency_id.id
            or order.partner_id.currency_id.id,
            "move_type": "in_invoice",
            "invoice_origin": order.name,
            "ref": False,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": name,
                        "account_id": account_id,
                        "price_unit": amount,
                        "quantity": 1.0,
                        "product_uom_id": self.product_id.uom_id.id,
                        "product_id": self.product_id.id,
                        "purchase_line_id": po_line.id,
                        "tax_ids": [(6, 0, tax_ids)],
                        "analytic_distribution": po_line.analytic_distribution,
                    },
                )
            ],
            "fiscal_position_id": order.fiscal_position_id.id
            or order.partner_id.property_account_position_id.id,
            "purchase_id": order.id,
            "prepayment_bill": True,
        }
        return vals

    def _create_invoice(self, order, po_line, amount):
        inv_obj = self.env["account.move"]
        ir_property_obj = self.env["ir.property"]

        account_id = False
        if self.product_id.id:
            account_id = order.fiscal_position_id.map_account(
                self.product_id.property_account_expense_id
                or self.product_id.categ_id.property_account_expense_categ_id
            ).id
        if not account_id:
            inc_acc = ir_property_obj._get(
                "property_account_expense_categ_id", "product.category"
            )
            account_id = (
                order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
            )
        if not account_id:
            raise UserError(
                _(
                    """There is no Expense account defined for this product: "%s".
                    You may have to install a chart of account from Accounting app,
                    settings menu."""
                )
                % (self.product_id.name,)
            )

        if self.amount <= 0.00:
            raise UserError(_("The value of the down payment amount must be positive."))
        amount, name = self._get_advance_details(order)
        taxes = self.product_id.supplier_taxes_id.filtered(
            lambda r: not order.company_id or r.company_id == order.company_id
        )
        if order.fiscal_position_id and taxes:
            tax_ids = order.fiscal_position_id.map_tax(taxes).ids
        else:
            tax_ids = taxes.ids
        invoice = inv_obj.create(
            self._prepare_invoice(order, po_line, amount, name, account_id, tax_ids)
        )
        invoice.message_post_with_view(
            "mail.message_origin_link",
            values={"self": invoice, "origin": order},
            subtype_id=self.env.ref("mail.mt_note").id,
        )

        return invoice

    def create_vendor_bills(self):
        purchase_orders = self.env["purchase.order"].browse(
            self._context.get("active_ids", [])
        )
        company_id = purchase_orders.mapped("company_id")
        if company_id:
            self = self.with_company(company_id).with_context(
                default_company_id=company_id.id
            )
        if self.advance_payment_method == "delivered":
            self.check_invoice_status(purchase_orders)
            journal_id = (
                self.env["account.journal"]
                .with_context(without_downpayment=True)
                .search(
                    [("type", "in", ["purchase"]), ("company_id", "=", company_id.id)],
                    limit=1,
                )
            )
            inv = (
                self.env["account.move"]
                .with_context(without_downpayment=True)
                .create({"move_type": "in_invoice", "journal_id": journal_id.id})
            )
            # base invoice creation includes invoice line vals
            # base add context skip_invoice_sync = True
            # during invoice creation to avoid recursion in line_ids calculation
            # here we create invoice and lines seperately
            # after invoice creation we need to disable the skip_invoice_sync
            inv = inv.with_context(skip_invoice_sync=False)
            inv.update({"purchase_id": purchase_orders.id})
            inv._onchange_purchase_auto_complete()
            inv.update({"currency_id": purchase_orders.currency_id.id})
            if all(
                line.purchase_line_id.is_downpayment for line in inv.invoice_line_ids
            ):
                for line in inv.invoice_line_ids:
                    line.quantity = 1
                inv.move_type = "in_refund"
        elif self.advance_payment_method == "all":
            if not any(line.is_downpayment for line in purchase_orders.order_line):
                self.check_invoice_status(purchase_orders)
            journal_id = (
                self.env["account.journal"]
                .with_context(final=True, final_payment=True)
                .search(
                    [("type", "in", ["purchase"]), ("company_id", "=", company_id.id)],
                    limit=1,
                )
            )
            inv = (
                self.env["account.move"]
                .with_context(final=True, final_payment=True)
                .create({"move_type": "in_invoice", "journal_id": journal_id.id})
            )
            # base invoice creation includes invoice line vals
            # base add context skip_invoice_sync = True
            # during invoice creation to avoid recursion in line_ids calculation
            # here we create invoice and lines seperately
            # after invoice creation we need to disable the skip_invoice_sync
            inv = inv.with_context(skip_invoice_sync=False)
            inv.update({"purchase_id": purchase_orders.id})
            inv._onchange_purchase_auto_complete()
            inv.update({"currency_id": purchase_orders.currency_id.id})
            if all(
                line.purchase_line_id.is_downpayment for line in inv.invoice_line_ids
            ):
                for line in inv.invoice_line_ids:
                    line.quantity = 1
                inv.move_type = "in_refund"
        else:
            purchase_line_obj = self.env["purchase.order.line"]
            for order in purchase_orders:
                # Create down payment section if necessary
                if not any(
                    line.display_type and line.is_downpayment
                    for line in order.order_line
                ):
                    self.env["purchase.order.line"].create(
                        self._prepare_down_payment_section_values(order)
                    )
                amount, name = self._get_advance_details(order)
                if self.product_id.purchase_method != "purchase":
                    raise UserError(
                        _(
                            """The down payment product should have a control policy set to
                            "Ordered quantities". Please update your down payment product."""
                        )
                    )
                if self.product_id.type != "service":
                    raise UserError(
                        _(
                            """The down payment product should be of type 'Service'.
                            Please use another product or update this product."""
                        )
                    )
                taxes = self.product_id.supplier_taxes_id.filtered(
                    lambda r: not order.company_id or r.company_id == order.company_id
                )
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                else:
                    tax_ids = taxes.ids
                analytic_distributions = order.order_line.filtered(
                    lambda order_line: not order_line.display_type
                    and order_line.analytic_distribution
                ).mapped("analytic_distribution")
                order_max_sequence = max(order.mapped("order_line.sequence"))
                po_line = purchase_line_obj.create(
                    {
                        "name": _("Advance: %s") % (time.strftime("%m %Y"),),
                        "price_unit": amount,
                        "product_qty": 0.0,
                        "order_id": order.id,
                        "product_uom": self.product_id.uom_id.id,
                        "product_id": self.product_id.id,
                        "analytic_distribution": {
                            k: v for d in analytic_distributions for k, v in d.items()
                        }
                        if analytic_distributions
                        else False,
                        "taxes_id": [(6, 0, tax_ids)],
                        "is_downpayment": True,
                        "date_planned": order.date_order,
                        "sequence": order_max_sequence + 1,
                    }
                )
                self._create_invoice(order, po_line, amount)
        purchase_orders = purchase_orders.with_context(purchase_bill=True)
        if self._context.get("create_bill", False):
            return purchase_orders.action_view_invoice()
        return {"type": "ir.actions.act_window_close"}

    def check_invoice_status(self, purchase_order):
        if purchase_order and purchase_order.invoice_status in ["invoiced", "no"]:
            raise UserError(_("There is nothing to invoice."))

    def _prepare_down_payment_section_values(self, order):
        context = {"lang": order.partner_id.lang}

        po_values = {
            "name": _("Down Payments"),
            "product_uom_qty": 0.0,
            "product_qty": 0.0,
            "order_id": order.id,
            "display_type": "line_section",
            "is_downpayment": True,
            "sequence": order.order_line and order.order_line[-1].sequence + 1 or 10,
        }

        del context
        return po_values
