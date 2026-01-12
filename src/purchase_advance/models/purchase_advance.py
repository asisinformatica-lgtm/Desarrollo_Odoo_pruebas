# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseAdvance(models.Model):
    _name = 'purchase.advance'
    _description = 'Requisición de Compra'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # =================================================
    # DATOS GENERALES
    # =================================================

    name = fields.Char(
        string='Número',
        required=True,
        copy=False,
        readonly=True,
        default='Nueva'
    )

    date_request = fields.Date(
        string='Fecha',
        default=fields.Date.context_today,
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    requester_id = fields.Many2one(
        'res.users',
        string='Solicitante',
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True
    )

    requester_email = fields.Char(
        related='requester_id.login',
        store=True,
        readonly=True
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Departamento solicitante'
    )

    reason = fields.Text(string='Motivo')

    # =================================================
    # APROBADOR / FINANZAS
    # =================================================

    approver_employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado Aprobador (Finanzas)',
        tracking=True
    )

    approver_email = fields.Char(
        related='approver_employee_id.work_email',
        store=True,
        readonly=True
    )

    approver_department_id = fields.Many2one(
        related='approver_employee_id.department_id',
        store=True,
        readonly=True
    )

    # =================================================
    # ESTADOS
    # =================================================

    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('sent', 'Enviada'),
            ('approved', 'Aprobada'),
            ('rejected', 'Rechazada'),
            ('liquidated', 'Liquidada'),
        ],
        default='draft',
        tracking=True
    )

    # =================================================
    # ARCHIVADO
    # =================================================

    active = fields.Boolean(default=True, tracking=True)

    # =================================================
    # LÍNEAS
    # =================================================

    line_ids = fields.One2many(
        'purchase.advance.line',
        'advance_id',
        string='Detalle'
    )

    amount_total = fields.Monetary(
        string='Total',
        compute='_compute_amount_total',
        store=True,
        currency_field='currency_id'
    )

    @api.depends('line_ids.total')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('total'))

    # =================================================
    # LIQUIDACIÓN
    # =================================================

    liquidation_type = fields.Selection(
        [
            ('no_invoice', 'Sin factura'),
            ('with_invoice', 'Con factura'),
        ],
        string='Tipo de liquidación',
        tracking=True
    )

    invoice_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Factura (PDF)'
    )

    xml_attachment_id = fields.Many2one(
        'ir.attachment',
        string='XML SAT (Opcional)'
    )

    # =================================================
    # AUDITORÍA
    # =================================================

    sent_by_id = fields.Many2one(
        'res.users',
        string='Enviada por',
        readonly=True,
        copy=False,
        tracking=True
    )

    sent_date = fields.Datetime(
        string='Fecha de envío',
        readonly=True,
        copy=False,
        tracking=True
    )

    approved_by_id = fields.Many2one(
        'res.users',
        string='Aprobada por',
        readonly=True,
        copy=False,
        tracking=True
    )

    approved_date = fields.Datetime(
        string='Fecha de aprobación',
        readonly=True,
        copy=False,
        tracking=True
    )

    rejected_by_id = fields.Many2one(
        'res.users',
        string='Rechazada por',
        readonly=True,
        copy=False,
        tracking=True
    )

    rejected_date = fields.Datetime(
        string='Fecha de rechazo',
        readonly=True,
        copy=False,
        tracking=True
    )

    liquidated_by_id = fields.Many2one(
        'res.users',
        string='Liquidada por',
        readonly=True,
        copy=False,
        tracking=True
    )

    liquidated_date = fields.Datetime(
        string='Fecha de liquidación',
        readonly=True,
        copy=False,
        tracking=True
    )

    # =================================================
    # SECUENCIA
    # =================================================

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nueva') == 'Nueva':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'purchase.advance'
            ) or 'REQ-00001'

        rec = super().create(vals)
        rec.message_post(body='📝 Requisición creada.')
        return rec

    # =================================================
    # LINK DIRECTO
    # =================================================

    def get_portal_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/web#id={self.id}&model=purchase.advance&view_type=form"

    # =================================================
    # ENVÍO DE CORREO (ODOO 18 – CORRECTO)
    # =================================================

    def _send_approval_email(self):
        template = self.env.ref(
            'purchase_advance.mail_template_purchase_advance_to_approve',
            raise_if_not_found=False
        )

        for rec in self:
            if not template:
                return

            if not rec.approver_employee_id or not rec.approver_employee_id.work_email:
                raise UserError('❌ El aprobador no tiene correo configurado.')

            template.with_context(
                lang=self.env.user.lang
            ).send_mail(
                rec.id,
                force_send=True,
                raise_exception=True
            )

    # =================================================
    # ACCIONES
    # =================================================

    def action_send(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError('❌ Solo se puede enviar una requisición en borrador.')

            if not rec.approver_employee_id:
                raise UserError('❌ Debe seleccionar un aprobador.')

            if not rec.line_ids:
                raise UserError('❌ Debe agregar al menos una línea.')

            rec.write({
                'state': 'sent',
                'sent_by_id': self.env.user.id,
                'sent_date': fields.Datetime.now(),
            })

            rec._send_approval_email()

            rec.message_post(
                body='📤 Requisición enviada para aprobación.',
                message_type='comment'
            )

    def action_approve(self):
        for rec in self:
            if rec.state != 'sent':
                raise UserError('❌ Solo se puede aprobar una requisición enviada.')

            rec.write({
                'state': 'approved',
                'approved_by_id': self.env.user.id,
                'approved_date': fields.Datetime.now(),
            })
            rec.message_post(body='✅ Requisición aprobada.')

    def action_reject(self):
        for rec in self:
            if rec.state not in ('sent', 'approved'):
                raise UserError('❌ No se puede rechazar en este estado.')

            rec.write({
                'state': 'rejected',
                'rejected_by_id': self.env.user.id,
                'rejected_date': fields.Datetime.now(),
            })
            rec.message_post(body='❌ Requisición rechazada.')

    def action_liquidate(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError('❌ Solo se puede liquidar una requisición aprobada.')

            if rec.liquidation_type == 'with_invoice' and not rec.invoice_attachment_id:
                raise UserError('❌ Debe adjuntar factura PDF.')

            rec.write({
                'state': 'liquidated',
                'liquidated_by_id': self.env.user.id,
                'liquidated_date': fields.Datetime.now(),
            })
            rec.message_post(body='💰 Requisición liquidada.')

    # =================================================
    # ARCHIVAR / RESTAURAR
    # =================================================

    def action_archive(self):
        for rec in self:
            rec.active = False
            rec.message_post(body='📦 Requisición archivada.')

    def action_unarchive(self):
        for rec in self:
            rec.active = True
            rec.message_post(body='📂 Requisición restaurada.')

    # =================================================
    # BLOQUEOS DUROS
    # =================================================

    def write(self, vals):
        for rec in self:
            if rec.name == 'Nueva' and not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'purchase.advance'
                ) or 'REQ-00001'

            if rec.state in ('sent', 'approved', 'rejected', 'liquidated'):
                if 'line_ids' in vals:
                    raise UserError('❌ No puede modificar líneas fuera de borrador.')
                if 'approver_employee_id' in vals:
                    raise UserError('❌ No puede cambiar el aprobador después de enviar.')
                if 'department_id' in vals or 'reason' in vals:
                    raise UserError('❌ No puede modificar datos generales después de enviar.')

            if rec.state == 'liquidated':
                raise UserError('❌ Una requisición liquidada no puede modificarse.')

        return super().write(vals)

    # =================================================
    # ELIMINACIÓN BLOQUEADA
    # =================================================

    def unlink(self):
        raise UserError('❌ No se permite eliminar requisiciones. Use Archivar.')
