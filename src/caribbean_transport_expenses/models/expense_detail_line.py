# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrExpenseDetailLine(models.Model):
    _name = "hr.expense.detail.line"
    _description = "Detalle de Gasto (Líneas)"
    _order = "id asc"

    # ==================================================
    # RELACIÓN CON GASTO PADRE
    # ==================================================

    expense_id = fields.Many2one(
        "hr.expense",
        string="Gasto",
        ondelete="cascade",
        required=True,
        index=True,
    )

    # ==================================================
    # CAMPOS PRINCIPALES DE LA LÍNEA
    # ==================================================

    supplier_id = fields.Many2one(
        "res.partner",
        string="Proveedor",
        domain="[('supplier_rank', '>', 0)]",
    )

    description = fields.Char(string="Descripción")

    quantity = fields.Float(string="Cantidad", default=1.0)

    unit_price = fields.Monetary(string="Precio Unitario")

    subtotal = fields.Monetary(
        string="Subtotal",
        compute="_compute_subtotal",
        store=True,
    )

    currency_id = fields.Many2one(
        related="expense_id.currency_id",
        store=True,
        readonly=True,
    )

    # ==================================================
    # CÁLCULO AUTOMÁTICO DEL SUBTOTAL
    # ==================================================

    @api.depends("quantity", "unit_price")
    def _compute_subtotal(self):
        """
        Calcula automáticamente:
        subtotal = cantidad * precio unitario
        """
        for rec in self:
            rec.subtotal = rec.quantity * rec.unit_price