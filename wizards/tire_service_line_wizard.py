from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import os


class FleetMaintenanceTireServiceLineWizard(models.TransientModel):
    _name = "fleet.maintenance.tire.service.line.wizard"
    _description = "Crear líneas de reparación de llantas"

    # =========================
    # UNIDAD
    # =========================
    unit_type = fields.Selection(
        [
            ("truck", "Camión"),
            ("trailer_2", "Remolque 2 Ejes"),
            ("trailer_3", "Remolque 3 Ejes"),
        ],
        string="Unidad",
        default="truck",
        required=True
    )

    unit_image = fields.Binary(
        string="Diagrama",
        compute="_compute_unit_image"
    )

    # =========================
    # RELACIÓN
    # =========================
    service_id = fields.Many2one(
        "fleet.maintenance.tire.service",
        required=True
    )

    mechanic_id = fields.Many2one(
        "res.partner",
        string="Mecánico"
    )

    # =========================
    # POSICIONES (MÚLTIPLES)
    # =========================
    position_ids = fields.Many2many(
        comodel_name="fleet.maintenance.tire.position",
        relation="tire_srv_line_wiz_pos_rel", #esto es para un nombre corto
        column1="wizard_id",
        column2="position_id",
        string="Posiciones",
        required=True
    )

    # =========================
    # DATOS TÉCNICOS
    # =========================
    size = fields.Char(string="Medida")
    brand = fields.Char(string="Marca")
    model = fields.Char(string="Modelo")

    wear_type = fields.Selection(
        [
            ("normal", "Desgaste normal"),
            ("irregular", "Desgaste irregular"),
            ("explosion", "Explosión"),
        ],
        string="Tipo de desgaste"
    )

    change_date = fields.Date(string="Fecha de cambio")

    supplier_id = fields.Many2one("res.partner", string="Proveedor")
    invoice = fields.Char(string="Factura")
    price = fields.Monetary(string="Precio")

    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id
    )

    # =========================
    # IMAGEN SEGÚN UNIDAD
    # =========================
    @api.depends("unit_type")
    def _compute_unit_image(self):
        for wizard in self:
            wizard.unit_image = False
            image_map = {
                "truck": "truck.png",
                "trailer_2": "trailer_2.png",
                "trailer_3": "trailer_3.png",
            }
            filename = image_map.get(wizard.unit_type)
            if filename:
                wizard.unit_image = self._load_image(filename)

    def _load_image(self, filename):
        path = os.path.join(
            os.path.dirname(__file__),
            "..", "static", "img", filename
        )
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read())
        return False

    # =========================
    # CREAR LÍNEAS
    # =========================
    def action_create_lines(self):
        self.ensure_one()

        if not self.position_ids:
            raise ValidationError("Debes seleccionar al menos una posición.")

        for position in self.position_ids:
            self.env["fleet.maintenance.tire.service.line"].create({
                "service_id": self.service_id.id,
                "position_id": position.id,
                "brand": self.brand,
                "model": self.model,
                "size": self.size,
                "wear_type": self.wear_type,
                "change_date": self.change_date,
                "mechanic_id": self.mechanic_id.id,
                "supplier_id": self.supplier_id.id,
                "invoice": self.invoice,
                "price": self.price,
            })

        return {"type": "ir.actions.act_window_close"}
