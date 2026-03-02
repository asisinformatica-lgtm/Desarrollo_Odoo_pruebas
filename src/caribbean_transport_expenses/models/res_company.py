# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    expense_account_operativo_id = fields.Many2one(
        "account.account",
        string="Cuenta Gastos Operativos",
        domain="[('internal_group', '=', 'expense')]",
    )

    expense_account_administrativo_id = fields.Many2one(
        "account.account",
        string="Cuenta Gastos Administrativos",
        domain="[('internal_group', '=', 'expense')]",
    )

    expense_account_legal_id = fields.Many2one(
        "account.account",
        string="Cuenta Gastos Legales",
        domain="[('internal_group', '=', 'expense')]",
    )