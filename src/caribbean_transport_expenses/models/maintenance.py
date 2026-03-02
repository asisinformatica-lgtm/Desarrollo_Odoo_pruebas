# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class CaribbeanFleetMaintenance(models.Model):
    _name = "caribbean.fleet.maintenance"
    _description = "Control de Mantenimiento de Flota Caribbean"
    _order = "maintenance_date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # ==================================================
    # DATOS GENERALES
    # ==================================================

    name = fields.Char(
        string="Referencia",
        readonly=True,
        copy=False,
        default="Nuevo",
        tracking=True,
    )

    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Camión",
        required=True,
        tracking=True,
    )

    license_plate = fields.Char(
        string="Placa",
        readonly=True,
    )

    maintenance_date = fields.Date(
        string="Fecha de mantenimiento",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )

    odometer = fields.Float(
        string="Kilometraje",
        required=True,
        tracking=True,
        help="Kilometraje del vehículo al momento del mantenimiento",
    )

    maintenance_type = fields.Selection(
        [
            ("preventivo", "Preventivo"),
            ("correctivo", "Correctivo"),
            ("emergencia", "Emergencia"),
        ],
        string="Tipo de mantenimiento",
        required=True,
        tracking=True,
    )

    description = fields.Text(
        string="Detalle del mantenimiento",
    )

    responsible_id = fields.Many2one(
        "hr.employee",
        string="Responsable",
        tracking=True,
    )

    # ==================================================
    # CONTROL
    # ==================================================

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("done", "Realizado"),
            ("cancel", "Cancelado"),
        ],
        default="draft",
        string="Estado",
        tracking=True,
    )

    active = fields.Boolean(default=True)

    # ==================================================
    # AUTOCOMPLETAR PLACA
    # ==================================================

    @api.onchange("vehicle_id")
    def _onchange_vehicle_set_plate(self):
        for record in self:
            record.license_plate = record.vehicle_id.license_plate or False

    # ==================================================
    # CORRELATIVO
    # ==================================================

    @api.model
    def create(self, vals):
        if vals.get("name", "Nuevo") == "Nuevo":
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "caribbean.fleet.maintenance"
            ) or "Nuevo"
        return super().create(vals)

    # ==================================================
    # ACCIONES
    # ==================================================

    def action_done(self):
        for record in self:
            if record.odometer <= 0:
                raise UserError("El kilometraje debe ser mayor a cero.")
            record.state = "done"

    def action_cancel(self):
        for record in self:
            record.state = "cancel"
