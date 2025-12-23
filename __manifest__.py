{
    "name": "Fleet Maintenance Extended",
    "version": "1.8.0",
    "category": "Fleet",
    "summary": "Extensión de mantenimiento para Fleet (Llantas - Fase 1)",
    "description": """
Módulo de mantenimiento extendido para Fleet.
FASE 1:
- Estructura base
- Modelos iniciales de llantas
- Vistas mínimas
    """,
    "author": "Grupo Caribbean Port",
    "website": "https://www.caribbeanport.com.gt",
    "depends": [
        "fleet",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/tire_service_line_wizard_views.xml",
        "views/tire_service_line_wizard_action.xml",
        "views/maintenance_position_views.xml",
        "views/maintenance_service_views.xml",
        "views/fleet_vehicle_views.xml",
    ],
    "installable": True,
    "application": False,
}
