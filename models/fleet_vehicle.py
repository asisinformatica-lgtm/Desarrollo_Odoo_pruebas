from odoo import models, fields, api


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    tire_service_count = fields.Integer(
        string="Servicios de Llantas",
        compute="_compute_tire_service_count"
    )

    def _compute_tire_service_count(self):
        service_model = self.env["fleet.maintenance.tire.service"]
        for vehicle in self:
            vehicle.tire_service_count = service_model.search_count([
                ("vehicle_id", "=", vehicle.id)
            ])
#test