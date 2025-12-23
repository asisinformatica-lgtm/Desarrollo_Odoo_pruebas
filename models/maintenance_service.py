from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FleetMaintenanceTireService(models.Model):
    _name = "fleet.maintenance.tire.service"
    _description = "Servicio de Llantas"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Referencia",
        default="Nuevo",
        required=True,
        tracking=True
    )

    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehículo",
        required=True,
        tracking=True
    )

    date = fields.Date(
        string="Fecha",
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("confirmed", "Confirmado"),
            ("done", "Finalizado"),
        ],
        default="draft",
        string="Estado",
        tracking=True
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    line_ids = fields.One2many(
        "fleet.maintenance.tire.service.line",
        "service_id",
        string="Líneas de servicio"
    )

    amount_total = fields.Monetary(
        string="Total",
        compute="_compute_amount_total",
        store=True
    )

    @api.depends("line_ids.price")
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(record.line_ids.mapped("price"))

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_done(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError(
                    "No puedes finalizar un servicio sin líneas de llantas."
                )
        self.write({"state": "done"})
