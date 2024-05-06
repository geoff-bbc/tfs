# Copyright 2019-2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details)

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    prepayment_bill = fields.Boolean(
        help="This Flag is set to True while creating a Down Payment on a Purchase Order.",
    )

    @api.model
    def _prepare_down_payment_section_line(self, **optional_values):
        """
        Prepare the dict of values to create a new down payment section
        for a sales order line.

        :param optional_values: any parameter that should be added to
        the returned down payment section
        """
        context = {"lang": self.partner_id.lang}
        down_payments_section_line = {
            "display_type": "line_section",
            "name": _("Prepayments"),
            "product_id": False,
            "product_uom_id": False,
            "quantity": 0,
            "discount": 0,
            "price_unit": 0,
            "account_id": False,
        }
        del context
        if optional_values:
            down_payments_section_line.update(optional_values)
        return down_payments_section_line

    @api.onchange("purchase_vendor_bill_id", "purchase_id")
    def _onchange_purchase_auto_complete(self):  # noqa
        if not self.purchase_id and not self.purchase_vendor_bill_id:
            return
        company_id = self.purchase_id.company_id.id
        if self._context.get("final", False):
            if self.purchase_vendor_bill_id.vendor_bill_id:
                self.invoice_vendor_bill_id = (
                    self.purchase_vendor_bill_id.vendor_bill_id
                )
                self._onchange_invoice_vendor_bill()
            elif self.purchase_vendor_bill_id.purchase_order_id:
                self.purchase_id = self.purchase_vendor_bill_id.purchase_order_id

            if not self.purchase_id:
                return

            # Copy partner.
            self.partner_id = self.purchase_id.partner_id
            self.fiscal_position_id = self.purchase_id.fiscal_position_id
            self.invoice_payment_term_id = self.purchase_id.payment_term_id
            self.currency_id = self.purchase_id.currency_id

            new_lines = self.env["account.move.line"]
            precision = self.env["decimal.precision"].precision_get(
                "Product Unit of Measure"
            )

            down_payment_section_added = False
            initial_sequence = 10

            for line in self.purchase_id.order_line.sorted(
                lambda order_line: order_line.is_downpayment
            ) - self.invoice_line_ids.mapped("purchase_line_id"):
                if not down_payment_section_added and line.is_downpayment:
                    downpayment_section_line_data = (
                        self._prepare_down_payment_section_line()
                    )
                    downpayment_section_line_data["sequence"] = initial_sequence + 1
                    downpayment_line = new_lines.new(downpayment_section_line_data)
                    new_lines += downpayment_line
                    down_payment_section_added = True
                if not float_is_zero(
                    line.qty_to_invoice, precision_digits=precision
                ) or (line.is_downpayment and line.qty_invoiced == 1):
                    data = line._prepare_account_move_line(self)
                    data.update(
                        {
                            "move_id": self.id,
                            "currency_id": self.currency_id.id,  # Mandatory field
                        }
                    )

                    if "sequence" in data:
                        initial_sequence = data["sequence"]
                    else:
                        data["sequence"] = initial_sequence + 1

                    new_line = new_lines.new(data)
                    new_lines += new_line
            # Compute invoice_origin.
            origins = set(new_lines.mapped("purchase_line_id.order_id.name"))
            self.invoice_origin = ",".join(list(origins))
            if any(line.purchase_line_id.is_downpayment for line in new_lines):
                downpayment_amount = 0.0
                other_line_amount = 0.0
                for line in new_lines:
                    unit_price = line.price_unit
                    if line.purchase_line_id.is_downpayment:
                        downpayment_amount += line.price_subtotal
                        if self._context.get("use_old_method_for_old_rec"):
                            line.quantity = -1
                        else:
                            line.quantity = line.purchase_line_id.qty_to_invoice
                    else:
                        other_line_amount += line.price_total
                    # To avoid recomputation of price_unit due to quantity update
                    # from an oca module "account_invoice_pricelist"
                    # Updated price_unit for the new move_lines created through Prepayments (unit_price = line.price_unit)
                    line.price_unit = unit_price
                if downpayment_amount > other_line_amount:
                    for line in new_lines:
                        unit_price = line.price_unit
                        if line.purchase_line_id.is_downpayment:
                            if self._context.get("use_old_method_for_old_rec"):
                                line.quantity = 1
                            else:
                                line.quantity = -1 * line.purchase_line_id.qty_to_invoice
                        else:
                            line.update({"quantity": -(line.quantity)})
                        # To avoid recomputation of price_unit due to quantity update
                        # from an oca module "account_invoice_pricelist"
                        # Updated price_unit for the new move_lines created through Prepayments (unit_price = line.price_unit)
                        line.price_unit = unit_price
                    self.env.context = dict(self.env.context)
                    self.env.context.update({"is_refund": True})
                    self.move_type = "in_refund"
            self.invoice_line_ids += new_lines
            self.filtered(
                lambda m: m.currency_id.round(m.amount_total) < 0
                and m.move_type != "in_refund"
            ).action_switch_invoice_into_refund_credit_note()
            # Compute ref.
            refs = set(self.line_ids.mapped("purchase_line_id.order_id.partner_ref"))
            refs = [ref for ref in refs if ref]
            self.ref = ",".join(refs)
            # Compute payment_reference. invoice_payment_ref
            if len(refs) == 1:
                self.payment_reference = refs[0]
            return {}
        elif self._context.get("without_downpayment", False):
            if self.purchase_vendor_bill_id.vendor_bill_id:
                self.invoice_vendor_bill_id = (
                    self.purchase_vendor_bill_id.vendor_bill_id
                )
                self._onchange_invoice_vendor_bill()
            elif self.purchase_vendor_bill_id.purchase_order_id:
                self.purchase_id = self.purchase_vendor_bill_id.purchase_order_id

            if not self.purchase_id:
                return

            # Copy partner.
            self.partner_id = self.purchase_id.partner_id
            self.fiscal_position_id = self.purchase_id.fiscal_position_id
            self.invoice_payment_term_id = self.purchase_id.payment_term_id
            self.currency_id = self.purchase_id.currency_id

            new_lines = self.env["account.move.line"]
            precision = self.env["decimal.precision"].precision_get(
                "Product Unit of Measure"
            )
            for (
                line
            ) in self.purchase_id.order_line - self.purchase_id.order_line.filtered(
                lambda x: x.is_downpayment
            ):
                if not float_is_zero(
                    line.qty_to_invoice, precision_digits=precision
                ) or (line.is_downpayment and line.qty_invoiced == 1):
                    data = line._prepare_account_move_line(self)
                    new_line = new_lines.new(data)
                    new_lines += new_line
            origins = set(new_lines.mapped("purchase_line_id.order_id.name"))
            self.invoice_origin = ",".join(list(origins))
            self.invoice_line_ids += new_lines
            self.filtered(
                lambda m: m.currency_id.round(m.amount_total) < 0
            ).action_switch_invoice_into_refund_credit_note()
            # Compute ref.
            refs = set(self.line_ids.mapped("purchase_line_id.order_id.partner_ref"))
            refs = [ref for ref in refs if ref]
            self.ref = ",".join(refs)
            # Compute payment_reference.
            if len(refs) == 1:
                self.payment_reference = refs[0]
            return {}
        else:
            rec = super()._onchange_purchase_auto_complete()
            if not self.journal_id:
                self.update(
                    {
                        "journal_id": self.env["account.journal"].search(
                            [
                                ("type", "in", ["purchase"]),
                                ("company_id", "=", company_id),
                            ],
                            limit=1,
                        )
                    }
                )
            if not self.invoice_origin:
                self.invoice_origin = self.purchase_id.name
            return rec

    def unlink(self):
        downpayment_lines = self.mapped("invoice_line_ids.purchase_line_id").filtered(
            lambda line: line.is_downpayment
        )
        res = super().unlink()
        if downpayment_lines:
            downpayment_lines.unlink()
        return res

    def action_post(self):
        # inherit of the function from account.move to validate a new tax and
        # the priceunit of a downpayment
        res = super().action_post()
        down_payment_lines = self.line_ids.filtered(
            lambda move_line: move_line.purchase_line_id.is_downpayment
        )
        for line in down_payment_lines:
            try:
                line.purchase_line_id.taxes_id = line.tax_ids
                line.purchase_line_id.price_unit = line.price_unit
            except UserError:
                # a UserError here means the PO was locked, which prevents
                #  changing the taxes
                # just ignore the error - this is a nice to have feature and
                #  should not be blocking
                _logger.info("usr-err PO was locked just ignore the error")
        return res
