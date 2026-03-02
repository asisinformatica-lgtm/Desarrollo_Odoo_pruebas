# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class HrExpense(models.Model):
    _inherit = "hr.expense"

    # ==================================================
    # CORRELATIVO
    # ==================================================

    expense_sequence = fields.Char(
        string="Correlativo",
        readonly=True,
        copy=False,
    )

    # ==================================================
    # CATEGORÍA DE GASTO
    # ==================================================

    expense_category = fields.Selection(
        [
            ("operativo", "Operativo"),
            ("administrativo", "Administrativo"),
            ("legal", "Legal"),
            ("financiamiento", "Financiamiento Interno"),
        ],
        string="Categoría de Gasto",
    )

    operative_expense = fields.Selection(
        [
            ("reparacion", "Reparación"),
            ("servicios", "Servicios"),
            ("combustible", "Combustible"),
        ],
        string="Tipo Operativo",
    )

    admin_expense = fields.Selection(
        [
            ("energia", "Energía eléctrica"),
            ("alquiler", "Alquiler"),
            ("internet", "Internet"),
            ("insumos", "Insumos"),
        ],
        string="Tipo Administrativo",
    )

    legal_expense = fields.Selection(
        [
            ("seguros", "Seguros"),
            ("impuestos", "Impuestos"),
            ("multas", "Multas"),
        ],
        string="Tipo Legal",
    )

    # ==================================================
    # LÍNEAS DE DETALLE
    # ==================================================

    detail_line_ids = fields.One2many(
        "hr.expense.detail.line",
        "expense_id",
        string="Detalle de gasto",
    )

    detail_total = fields.Monetary(
        string="Total Detalle",
        compute="_compute_detail_total",
        store=True,
    )

    @api.depends("detail_line_ids.subtotal")
    def _compute_detail_total(self):
        for rec in self:
            if rec.detail_line_ids:
                total = sum(rec.detail_line_ids.mapped("subtotal"))
                rec.detail_total = total
                if rec.expense_category != "financiamiento":
                    rec.total_amount = total
            else:
                rec.detail_total = 0.0

    @api.onchange(
        "detail_line_ids",
        "detail_line_ids.quantity",
        "detail_line_ids.unit_price",
    )
    def _onchange_sync_total(self):
        for rec in self:
            if rec.detail_line_ids and rec.expense_category != "financiamiento":
                rec.total_amount = sum(rec.detail_line_ids.mapped("subtotal"))

    @api.onchange("expense_category", "admin_expense", "legal_expense")
    def _onchange_reset_lines_for_notes(self):
        for rec in self:
            if rec.expense_category == "administrativo":
                if rec.admin_expense in ("energia", "alquiler", "internet"):
                    rec.detail_line_ids = [(5, 0, 0)]
            if rec.expense_category == "legal":
                rec.detail_line_ids = [(5, 0, 0)]

    # ==================================================
    # COMBUSTIBLE / FLOTA
    # ==================================================

    fuel_type = fields.Selection(
        [
            ("diesel", "Diesel"),
            ("super", "Súper"),
            ("regular", "Regular"),
        ],
        string="Tipo de combustible",
    )

    fuel_gallons = fields.Float(string="Galonaje", digits=(12, 2))

    vehicle_id = fields.Many2one("fleet.vehicle", string="Camión")

    vehicle_plate = fields.Char(
        string="Placa",
        related="vehicle_id.license_plate",
        store=True,
        readonly=True,
    )

    # ==================================================
    # FINANCIAMIENTO
    # ==================================================

    loan_amount = fields.Monetary(string="Monto del préstamo")

    loan_term = fields.Selection(
        [
            ("6", "6 cuotas"),
            ("12", "12 cuotas"),
            ("18", "18 cuotas"),
            ("24", "24 cuotas"),
            ("36", "36 cuotas"),
            ("48", "48 cuotas"),
            ("60", "60 cuotas"),
        ],
        string="Plazo",
    )

    loan_interest = fields.Boolean(string="¿Aplica interés?")
    annual_interest_rate = fields.Float(string="Interés anual (%)")

    amortization_line_ids = fields.One2many(
        "hr.expense.amortization.line",
        "expense_id",
        string="Tabla de amortización",
    )

    extra_payment_amount = fields.Monetary(string="Abono Extraordinario")

    total_interest_amount = fields.Monetary(
        compute="_compute_loan_summary",
        store=True,
        string="Intereses Totales",
    )

    remaining_loan_balance = fields.Monetary(
        compute="_compute_loan_summary",
        store=True,
        string="Saldo Pendiente",
    )

    loan_closed = fields.Boolean(
        compute="_compute_loan_closed",
        store=True,
        string="Préstamo Cerrado",
    )

    # ==================================================
    # CREATE
    # ==================================================

    @api.model
    def create(self, vals):
        record = super().create(vals)

        if (
            record.expense_category == "financiamiento"
            and record.loan_amount
            and record.loan_term
        ):
            record._generate_amortization_lines()

        return record

    # ==================================================
    # WRITE
    # ==================================================

    def write(self, vals):

        trigger_fields = {
            "loan_amount",
            "loan_term",
            "loan_interest",
            "annual_interest_rate",
        }

        need_regenerate = bool(trigger_fields.intersection(vals.keys()))

        res = super().write(vals)

        if need_regenerate:
            for rec in self:
                if (
                    rec.expense_category == "financiamiento"
                    and rec.loan_amount
                    and rec.loan_term
                ):
                    rec._generate_amortization_lines()

        return res

    # ==================================================
    # ONCHANGE DINÁMICO
    # ==================================================

    @api.onchange("loan_amount", "loan_term", "loan_interest", "annual_interest_rate")
    def _onchange_preview_amortization(self):
        for rec in self:
            if (
                rec.expense_category == "financiamiento"
                and rec.loan_amount
                and rec.loan_term
            ):
                lines = rec._prepare_amortization_lines()

                rec.amortization_line_ids = [(5, 0, 0)]
                rec.amortization_line_ids = [
                    (0, 0, vals) for vals in lines
                ]

    # ==================================================
    # GENERAR TABLA
    # ==================================================

    def _generate_amortization_lines(self):
        self.ensure_one()

        if self.amortization_line_ids:
            self.with_context(
                allow_amortization_unlink=True
            ).amortization_line_ids.unlink()

        lines = self._prepare_amortization_lines()

        if lines:
            self.amortization_line_ids = [(0, 0, vals) for vals in lines]

    def _prepare_amortization_lines(self):
        self.ensure_one()

        total_installments = int(self.loan_term)
        loan_amount = self.loan_amount
        start_date = self.date or fields.Date.today()

        monthly_interest = 0.0
        if self.loan_interest and self.annual_interest_rate:
            monthly_interest = (self.annual_interest_rate / 100.0) / 12.0

        balance = loan_amount
        lines = []

        for i in range(1, total_installments + 1):

            interest_amount = balance * monthly_interest if monthly_interest else 0.0
            capital = loan_amount / total_installments
            total_payment = capital + interest_amount
            balance -= capital

            lines.append({
                "installment_number": i,
                "date": start_date + relativedelta(months=i),
                "capital_amount": capital,
                "interest_amount": interest_amount,
                "total_amount": total_payment,
                "remaining_balance": balance if balance > 0 else 0.0,
            })

        return lines

    # ==================================================
    # RESUMEN
    # ==================================================

    @api.depends(
        "amortization_line_ids.interest_amount",
        "amortization_line_ids.remaining_balance",
        "amortization_line_ids.paid",
    )
    def _compute_loan_summary(self):
        for rec in self:
            rec.total_interest_amount = sum(
                rec.amortization_line_ids.mapped("interest_amount")
            )

            unpaid = rec.amortization_line_ids.filtered(lambda l: not l.paid)

            rec.remaining_loan_balance = sum(
                unpaid.mapped("capital_amount")
            )

    @api.depends("amortization_line_ids.paid")
    def _compute_loan_closed(self):
        for rec in self:
            rec.loan_closed = bool(
                rec.amortization_line_ids and
                all(rec.amortization_line_ids.mapped("paid"))
            )

    # ==================================================
    # ABONO EXTRA
    # ==================================================

    def action_apply_extra_payment(self):
        self.ensure_one()

        if self.loan_closed:
            raise UserError("El préstamo ya está cerrado.")

        if not self.extra_payment_amount or self.extra_payment_amount <= 0:
            raise UserError("Debe ingresar un monto válido.")

        currency = self.currency_id
        remaining = currency.round(self.extra_payment_amount)

        pending_lines = self.amortization_line_ids.filtered(
            lambda l: not l.paid
        ).sorted("installment_number")

        for line in pending_lines:
            if remaining <= 0:
                break

            if remaining >= line.total_amount:
                remaining -= line.total_amount
                line.paid = True
            else:
                break

        self.extra_payment_amount = 0.0
        self._compute_loan_summary()

    # ==================================================
    # CRON AUTOMATIZACIÓN FINANCIAMIENTO
    # ==================================================

    def cron_internal_financing_automation(self):
        """
        Se ejecuta diariamente desde el cron.
        - Detecta cuotas vencidas
        - Marca como notificadas
        - Deja mensaje en el chatter
        """

        today = fields.Date.today()

        loans = self.search([
            ('expense_category', '=', 'financiamiento'),
            ('loan_closed', '=', False)
        ])

        for loan in loans:

            overdue_lines = loan.amortization_line_ids.filtered(
                lambda l: not l.paid and l.date and l.date < today
            )

            for line in overdue_lines:
                if not line.notified:
                    line.notified = True

                    loan.message_post(
                        body=f"La cuota #{line.installment_number} está vencida."
                    )