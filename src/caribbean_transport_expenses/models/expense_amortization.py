# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class HrExpenseAmortizationLine(models.Model):
    _name = "hr.expense.amortization.line"
    _description = "Línea de amortización de préstamo"
    _order = "installment_number asc"

    _sql_constraints = [
        (
            'unique_installment_per_expense',
            'unique(expense_id, installment_number)',
            'No puede existir más de una cuota con el mismo número para este préstamo.'
        )
    ]

    expense_id = fields.Many2one(
        "hr.expense",
        string="Gasto",
        ondelete="cascade",
        required=True,
        index=True,
    )

    installment_number = fields.Integer(string="Cuota")
    date = fields.Date(string="Fecha", index=True)

    capital_amount = fields.Monetary(string="Capital")
    interest_amount = fields.Monetary(string="Interés")
    total_amount = fields.Monetary(string="Total cuota")
    remaining_balance = fields.Monetary(string="Saldo")

    # 🔥 CORREGIDO (sin readonly aquí)
    paid = fields.Boolean(string="Pagada")
    notified = fields.Boolean(string="Notificada", default=False, index=True)

    currency_id = fields.Many2one(
        related="expense_id.currency_id",
        store=True,
        readonly=True,
    )

    # ==========================================
    # VALIDACIONES
    # ==========================================

    @api.constrains('capital_amount', 'interest_amount')
    def _check_amounts(self):
        for rec in self:
            if rec.capital_amount and rec.capital_amount < 0:
                raise UserError("Los montos no pueden ser negativos.")
            if rec.interest_amount and rec.interest_amount < 0:
                raise UserError("Los montos no pueden ser negativos.")

    # ==========================================
    # BLOQUEO DE EDICIÓN FINANCIERA
    # ==========================================

    def write(self, vals):
        protected_fields = {
            'capital_amount',
            'interest_amount',
            'total_amount',
            'remaining_balance',
            'installment_number',
            'date',
        }

        # ✅ Permitir cambiar solo el boolean paid
        if list(vals.keys()) == ['paid']:
            return super().write(vals)

        # 🔒 Bloquear modificaciones manuales financieras
        if any(field in vals for field in protected_fields):
            raise UserError(
                "No puede modificar manualmente la tabla de amortización."
            )

        return super().write(vals)

    # ==========================================
    # CONTROL DE ELIMINACIÓN
    # ==========================================

    def unlink(self):
        # Permitir cuando el padre regenera
        if self.env.context.get("allow_amortization_unlink"):
            return super().unlink()

        # Bloquear eliminación manual desde UI
        raise UserError(
            "No está permitido eliminar líneas de amortización manualmente."
        )