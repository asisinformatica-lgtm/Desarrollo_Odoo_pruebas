# -*- coding: utf-8 -*-
from odoo import models, fields
import base64
import io
import xlsxwriter


class PurchaseAdvanceExportExcel(models.TransientModel):
    _name = 'purchase.advance.export.excel'
    _description = 'Exportar Requisiciones a Excel'

    date_from = fields.Date(string='Fecha inicio', required=True)
    date_to = fields.Date(string='Fecha fin', required=True)

    file_data = fields.Binary(string='Archivo', readonly=True)
    file_name = fields.Char(string='Nombre de archivo')

    def action_export(self):
        requisitions = self.env['purchase.advance'].search([
            ('date_request', '>=', self.date_from),
            ('date_request', '<=', self.date_to),
        ])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Requisiciones')

        headers = [
            'Número',
            'Fecha',
            'Solicitante',
            'Departamento',
            'Estado',
            'Total',
        ]

        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        row = 1
        for rec in requisitions:
            sheet.write(row, 0, rec.name)
            sheet.write(row, 1, str(rec.date_request))
            sheet.write(row, 2, rec.requester_id.name or '')
            sheet.write(row, 3, rec.department_id.name or '')
            sheet.write(row, 4, rec.state)
            sheet.write(row, 5, rec.amount_total)
            row += 1

        workbook.close()
        output.seek(0)

        self.file_data = base64.b64encode(output.read())
        self.file_name = f'Requisiciones_{self.date_from}_a_{self.date_to}.xlsx'

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
