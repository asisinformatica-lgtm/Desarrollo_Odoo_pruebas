# -*- coding: utf-8 -*-
import base64
import io
from odoo import models, fields
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class RequisitionExportWizard(models.TransientModel):
    _name = 'purchase.advance.export.wizard'
    _description = 'Exportar Requisiciones por Fecha'

    date_from = fields.Date(
        string='Fecha inicio',
        required=True
    )

    date_to = fields.Date(
        string='Fecha fin',
        required=True
    )

    file_data = fields.Binary('Archivo')
    file_name = fields.Char('Nombre de archivo')

    def action_export_excel(self):
        if self.date_from > self.date_to:
            raise UserError('❌ La fecha inicio no puede ser mayor a la fecha fin.')

        requisitions = self.env['purchase.advance'].search([
            ('date_request', '>=', self.date_from),
            ('date_request', '<=', self.date_to),
        ])

        if not requisitions:
            raise UserError('❌ No hay requisiciones en ese rango de fechas.')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Requisiciones')

        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center'
        })

        row_format = workbook.add_format({'border': 1})

        headers = [
            'Número',
            'Fecha',
            'Solicitante',
            'Departamento',
            'Estado',
            'Aprobador',
            'Total'
        ]

        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        row = 1
        for req in requisitions:
            sheet.write(row, 0, req.name or '', row_format)
            sheet.write(row, 1, str(req.date_request or ''), row_format)
            sheet.write(row, 2, req.requester_id.name or '', row_format)
            sheet.write(row, 3, req.approver_department_id.name or '', row_format)
            sheet.write(row, 4, dict(req._fields['state'].selection).get(req.state), row_format)
            sheet.write(row, 5, req.approver_employee_id.name or '', row_format)
            sheet.write(row, 6, req.amount_total or 0.0, row_format)
            row += 1

        workbook.close()
        output.seek(0)

        self.file_data = base64.b64encode(output.read())
        self.file_name = f'Requisiciones_{self.date_from}_a_{self.date_to}.xlsx'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.advance.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
