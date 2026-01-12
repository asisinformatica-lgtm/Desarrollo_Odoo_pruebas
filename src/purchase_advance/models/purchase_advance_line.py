from odoo import models, fields, api


class PurchaseAdvanceLine(models.Model):
    _name = 'purchase.advance.line'
    _description = 'Detalle de Requisición'

    advance_id = fields.Many2one(
        'purchase.advance',
        string='Requisición',
        ondelete='cascade',
        required=True
    )
    
    #MONEDA HEREDADA DE LA CABECERA
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='advance_id_currency_id',
        store=True,
        readonly=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor'
    )

    quantity = fields.Float(
        string='Cantidad',
        default=1.0
    )

    price_unit = fields.Float(
        string='Precio Unitario'
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='advance_id.currency_id',
        store=True,
        readonly=True
    )

    # 🔥 ESTE ERA EL CAMPO QUE FALTABA
    tax_ids = fields.Many2many(
        'account.tax',
        string='Impuestos',
        domain="[('type_tax_use', 'in', ('purchase', 'none'))]"
    )

    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        currency_field='currency_id',
        store=True
    )

    total = fields.Monetary(
        string='Total',
        compute='_compute_total',
        currency_field='currency_id',
        store=True
    )

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

    @api.depends('subtotal', 'tax_ids')
    def _compute_total(self):
        for line in self:
            if line.tax_ids:
                taxes = line.tax_ids.compute_all(
                    line.subtotal,
                    currency=line.currency_id,
                    quantity=1.0,
                    product=line.product_id,
                    partner=line.partner_id
                )
                line.total = taxes['total_included']
            else:
                line.total = line.subtotal
