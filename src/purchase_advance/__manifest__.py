{
    'name': 'Requisiciones',
    'version': '18.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Gestión de requisiciones internas',
    'description': """
Gestión de requisiciones internas.
Permite solicitar, aprobar y controlar requisiciones.
""",
    'author': 'Grupo Caribbean Port',
    'license': 'LGPL-3',

    'depends': [
        'purchase',
        'hr',
        'mail',
    ],
    # ⚠️ ORDEN CRÍTICO
    'data': [
    # =========================
    # SEGURIDAD (SIEMPRE PRIMERO)
    # =========================
    'security/groups.xml',                  # 1️⃣ Grupos
    'security/ir.model.access.csv',         # 2️⃣ Permisos
    'security/purchase_advance_rules.xml',  # 3️⃣ Reglas de visibilidad

    # =========================
    # DATA
    # =========================
    'data/sequence.xml',                    # Secuencia de requisiciones
    'data/mail_template.xml',               # Correos

    # =========================
    # VISTAS
    # =========================
    'views/purchase_advance_search_views.xml',
    'views/menus.xml',                      # 🔹 MENÚ DESPLEGABLE
    'views/purchase_advance_views.xml',     # Formularios y listas
],
    'installable': True,
    'application': False,
}
