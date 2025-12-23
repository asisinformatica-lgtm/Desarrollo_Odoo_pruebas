from odoo import models, fields, api
from datetime import date


class FleetMaintenanceTirePosition(models.Model):
    _name = "fleet.maintenance.tire.position"
    _description = "Posición de Llanta"
    _order = "alert_level desc, sequence asc, name"


    # =========================
    # CAMPOS BÁSICOS
    # =========================
    name = fields.Char(
        string="Código",
        required=True
    )

    description = fields.Char(
        string="Descripción"
    )

    unit_type = fields.Selection(
        [
            ("truck", "Camión"),
            ("trailer_2", "Remolque 2 Ejes"),
            ("trailer_3", "Remolque 3 Ejes"),
        ],
        string="Tipo de Unidad",
        required=True
    )

    axle = fields.Integer(
        string="Eje"
    )

    side = fields.Selection(
        [
            ("left", "Izquierda"),
            ("right", "Derecha"),
            ("single", "Sencilla"),
        ],
        string="Lado"
    )
    
    sequence = fields.Integer(
        string="Secuencia",
        default=10
    )

    active = fields.Boolean(default=True)

    # =========================
    # RELACIÓN CON SERVICIOS
    # =========================
    service_line_ids = fields.Many2many(
        comodel_name="fleet.maintenance.tire.service.line",
        relation="fleet_tire_position_service_line_rel",
        column1="position_id",
        column2="service_line_id",
        string="Historial de servicios"
    )

    # =========================
    # MÉTRICAS
    # =========================
    service_count = fields.Integer(
        string="Servicios",
        compute="_compute_metrics",
        store=True
    )

    last_change_date = fields.Date(
        string="Último cambio",
        compute="_compute_metrics",
        store=True
    )

    total_cost = fields.Monetary(
        string="Costo acumulado",
        compute="_compute_metrics",
        currency_field="currency_id",
        store=True
    )

    alert_level = fields.Selection(
        [
            ("ok", "OK"),
            ("warning", "Advertencia"),
            ("danger", "Crítico"),
        ],
        string="Alerta",
        compute="_compute_metrics",
        store=True
    )

    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id
    )

    # =========================
    # COMPUTE CENTRAL
    # =========================
    @api.depends(
        "service_line_ids.change_date",
        "service_line_ids.price"
    )
    def _compute_metrics(self):
        for position in self:
            lines = position.service_line_ids

            position.service_count = len(lines)
            position.total_cost = sum(lines.mapped("price"))

            if lines:
                last_line = lines.sorted(
                    lambda l: l.change_date or date.today(),
                    reverse=True
                )[0]
                position.last_change_date = last_line.change_date
            else:
                position.last_change_date = False

            if position.service_count >= 5:
                position.alert_level = "danger"
            elif position.service_count >= 3:
                position.alert_level = "warning"
            else:
                position.alert_level = "ok"
