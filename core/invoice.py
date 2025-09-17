from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from datetime import datetime
import os

def generate_invoice_pdf(invoice_number, customer_name, items, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    c.setFont('Helvetica-Bold', 16)
    c.drawString(margin, height - margin, 'Painel Vendas - Fatura / Recibo')
    c.setFont('Helvetica', 10)
    c.drawString(margin, height - margin - 18, f'Número: {invoice_number if invoice_number else "-"}')
    c.drawString(margin, height - margin - 32, f'Cliente: {customer_name}')
    c.drawString(margin, height - margin - 46, f'Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
    y = height - margin - 90
    c.setFont('Helvetica-Bold', 10)
    c.drawString(margin, y, 'Descrição')
    c.drawString(margin + 280, y, 'Qtd')
    c.drawString(margin + 330, y, 'Preço Unit.')
    c.drawString(margin + 420, y, 'Subtotal')
    c.line(margin, y - 4, width - margin, y - 4)
    c.setFont('Helvetica', 10)
    y -= 18
    total = 0.0
    for it in items:
        desc = str(it.get('description',''))
        qty = float(it.get('quantity',0))
        unit = float(it.get('unit_price',0.0))
        subtotal = qty*unit
        c.drawString(margin, y, desc[:40])
        c.drawRightString(margin + 300, y, f"{qty:g}")
        c.drawRightString(margin + 380, y, f"R$ {unit:,.2f}")
        c.drawRightString(margin + 480, y, f"R$ {subtotal:,.2f}")
        y -= 16
        total += subtotal
        if y < margin + 80:
            c.showPage()
            y = height - margin - 40
    c.setFont('Helvetica-Bold', 12)
    c.drawRightString(width - margin, margin + 60, f'Total: R$ {total:,.2f}')
    c.save()
    return output_path
