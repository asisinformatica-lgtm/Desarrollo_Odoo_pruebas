from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FleetMaintenanceTireServiceLine(models.Model):
    _name = "fleet.maintenance.tire.service.line"
    _description = "Detalle Servicio de Llantas"

    service_id = fields.Many2one(
        "fleet.maintenance.tire.service",
        string="Servicio",
        required=True,
        ondelete="cascade"
    )

    position_ids = fields.Many2many(
        "fleet.maintenance.tire.position",
        string="Posiciones",
        required=True
    )

    brand = fields.Char(string="Marca")
    model = fields.Char(string="Modelo")
    size = fields.Char(string="Medida")

    wear_type = fields.Selection(
        [
            ("normal", "Desgaste normal"),
            ("irregular", "Desgaste irregular"),
            ("explosion", "Explosión"),
        ],
        string="Tipo de desgaste"
    )

    change_date = fields.Date(string="Fecha de cambio")

    price = fields.Monetary(string="Costo")
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id
    )

    # =========================
    # VALIDACIÓN CRÍTICA
    # =========================
    @api.constrains("position_ids", "service_id")
    def _check_unique_positions_per_service(self):
        for line in self:
            if not line.service_id or not line.position_ids:
                continue

            other_lines = self.env["fleet.maintenance.tire.service.line"].search([
                ("service_id", "=", line.service_id.id),
                ("id", "!=", line.id),
            ])

            used_positions = other_lines.mapped("position_ids")
            duplicated = line.position_ids & used_positions

            if duplicated:
                raise ValidationError(
                    "Las siguientes posiciones ya fueron usadas en este servicio:\n- "
                    + "\n- ".join(duplicated.mapped("name"))
                )
