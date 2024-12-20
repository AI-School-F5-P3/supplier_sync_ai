from fpdf import FPDF
from PIL import Image


# Clase para crear la factura en PDF
class InvoicePDF(FPDF):
    def header(self):
        """Encabezado de la factura."""
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'INVOICE Nº 28922', align='C', ln=True)
        self.ln(5)
    
    def footer(self):
        """Pie de página de la factura."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')
    
    def invoice_body(self, invoice_data):
        """Cuerpo de la factura con los datos proporcionados."""
        self.set_font('Arial', '', 12)

        # Datos del proveedor
        self.cell(0, 10, f"Supplier Name: {invoice_data['supplier_name']}", ln=True)
        self.cell(0, 10, f"Supplier Tax ID: {invoice_data['supplier_tax_id']}", ln=True)
        
        self.ln(5)  # Espacio
        
        # Información de facturación
        self.cell(0, 10, f"Bill To: {invoice_data['bill_to']}", ln=True)
        self.cell(0, 10, f"Send To: {invoice_data['send_to']}", ln=True)
        
        self.ln(5)  # Espacio

        # Fechas y términos
        self.cell(0, 10, f"Issue Date: {invoice_data['issue_date']}", ln=True)
        self.cell(0, 10, f"Expiration Date: {invoice_data['expiration_date']}", ln=True)
        self.cell(0, 10, f"Payment Terms: {invoice_data['payment_terms']}", ln=True)
        self.cell(0, 10, f"Purchase Order: {invoice_data['purchase_order']}", ln=True)
        
        self.ln(10)  # Espacio grande

        # Tabla de productos
        self.set_font('Arial', 'B', 12)
        self.cell(50, 10, 'Description', 1, 0, 'C')
        self.cell(30, 10, 'Quantity', 1, 0, 'C')
        self.cell(40, 10, 'Unit Price', 1, 0, 'C')
        self.cell(40, 10, 'Total', 1, 1, 'C')

        self.set_font('Arial', '', 12)
        for item in invoice_data['items']:
            self.cell(50, 10, item['description'], 1, 0, 'C')
            self.cell(30, 10, str(item['quantity']), 1, 0, 'C')
            self.cell(40, 10, f"${item['unit_price']:.2f}", 1, 0, 'C')
            self.cell(40, 10, f"${item['total']:.2f}", 1, 1, 'C')

        self.ln(10)  # Espacio

        # Notas
        self.set_font('Arial', 'I', 10)
        self.multi_cell(0, 10, f"Notes: {invoice_data['notes']}")

# Datos de la factura de ejemplo
invoice_data = {
    'supplier_name': 'Reddingtong Corporation',
    'supplier_tax_id': '23342343',
    'bill_to': 'Belmont Enterprises',
    'send_to': '456 Main St, Springfield',
    'issue_date': '2024-02-12',
    'expiration_date': '2026-03-12',
    'payment_terms': 'Net 45',
    'purchase_order': 'ABD22222',
    'items': [
        {'description': 'Product A', 'quantity': 10, 'unit_price': 50.00, 'total': 500.00},
        {'description': 'Product B', 'quantity': 5, 'unit_price': 100.00, 'total': 500.00},
    ],
    'notes': 'Thank you for your business. Please remit payment by the due date.'
}

# Crear la factura en PDF
pdf = InvoicePDF()
pdf.add_page()
pdf.invoice_body(invoice_data)

# Guardar la factura como archivo PDF
pdf_output_path = 'scripts/generated_invoices/invoice_example2.pdf'
pdf.output(pdf_output_path)

# Convertir el PDF en una imagen PNG
from pdf2image import convert_from_path

# Convertir la primera página del PDF en una imagen PNG
images = convert_from_path(pdf_output_path, dpi=150)
png_output_path = 'scripts/generated_invoices/invoice_example.png'
images[0].save(png_output_path, 'PNG')


# Confirmación de las rutas de salida
pdf_output_path, png_output_path
