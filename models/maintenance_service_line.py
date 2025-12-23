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

    # POSICIÓN (D1, T2, C3, etc.)
    description = fields.Char(
        string="Posición",
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

    mechanic_id = fields.Many2one("res.partner", string="Mecánico")
    supplier_id = fields.Many2one("res.partner", string="Proveedor")
    invoice = fields.Char(string="Factura")

    price = fields.Monetary(string="Costo", required=True)

    currency_id = fields.Many2one(
        related="service_id.currency_id",
        store=True,
        readonly=True
    )

    @api.constrains("description", "service_id")
    def _check_unique_position_per_service(self):
        for line in self:
            if not line.description or not line.service_id:
                continue

            duplicated = self.search([
                ("service_id", "=", line.service_id.id),
                ("description", "=", line.description),
                ("id", "!=", line.id),
            ], limit=1)

            if duplicated:
                raise ValidationError(
                    f"La posición '{line.description}' ya fue utilizada en este servicio."
                )
