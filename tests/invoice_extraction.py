import pytesseract
import re
from PIL import Image
import os

# Configuración de la ruta de Tesseract (ajústala según tu sistema)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configurar la variable TESSDATA_PREFIX (opcional si el OCR no encuentra los idiomas)
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

# Función para extraer texto de la imagen
def extract_text_from_image(image_path):
    """Extrae todo el texto de una imagen usando OCR."""
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

# Función para extraer los campos clave de la factura
def extract_invoice_fields(text):
    """Extrae los campos clave del texto de la factura."""
    extracted_data = {}

    # Extraer el supplier_name (por ejemplo, la primera línea del texto)
    supplier_name_match = re.search(r'Supplier Name[:\s]*(.*)', text, re.IGNORECASE)
    extracted_data['supplier_name'] = supplier_name_match.group(1).strip() if supplier_name_match else None

    # Extraer supplier_tax_id (por ejemplo, una secuencia de números)
    supplier_tax_id_match = re.search(r'Supplier Tax ID[:\s]*(\w+)', text, re.IGNORECASE)
    extracted_data['supplier_tax_id'] = supplier_tax_id_match.group(1).strip() if supplier_tax_id_match else None

    # Extraer Bill To (a quién va dirigida la factura)
    bill_to_match = re.search(r'Bill To[:\s]*(.*)', text, re.IGNORECASE)
    extracted_data['bill_to'] = bill_to_match.group(1).strip() if bill_to_match else None

    # Extraer Send To (dónde se envía)
    send_to_match = re.search(r'Send To[:\s]*(.*)', text, re.IGNORECASE)
    extracted_data['send_to'] = send_to_match.group(1).strip() if send_to_match else None

    # Extraer la fecha de emisión (issue_date)
    issue_date_match = re.search(r'Issue Date[:\s]*([\d]{2,4}[-/][\d]{2}[-/][\d]{2,4})', text, re.IGNORECASE)
    extracted_data['issue_date'] = issue_date_match.group(1).strip() if issue_date_match else None

    # Extraer la fecha de expiración (expiration_date)
    expiration_date_match = re.search(r'Expiration Date[:\s]*([\d]{2,4}[-/][\d]{2}[-/][\d]{2,4})', text, re.IGNORECASE)
    extracted_data['expiration_date'] = expiration_date_match.group(1).strip() if expiration_date_match else None

    # Extraer términos de pago (payment_terms)
    payment_terms_match = re.search(r'Payment Terms[:\s]*(.*)', text, re.IGNORECASE)
    extracted_data['payment_terms'] = payment_terms_match.group(1).strip() if payment_terms_match else None

    # Extraer la orden de compra (purchase_order)
    purchase_order_match = re.search(r'Purchase Order[:\s]*(\w+)', text, re.IGNORECASE)
    extracted_data['purchase_order'] = purchase_order_match.group(1).strip() if purchase_order_match else None

    # Extraer notas (puede estar al final de la factura)
    notes_match = re.search(r'Notes[:\s]*(.*)', text, re.IGNORECASE)
    extracted_data['notes'] = notes_match.group(1).strip() if notes_match else None

    return extracted_data

# Función principal para extraer los datos de la factura
def process_invoice(image_path):
    """Extrae texto y campos clave de una imagen de factura."""
    print(f'Procesando la imagen: {image_path}')
    text = extract_text_from_image(image_path)
    print(f'Texto extraído:\n{text}')
    
    extracted_fields = extract_invoice_fields(text)
    print(f'Campos extraídos de la factura:\n{extracted_fields}')
    
    return extracted_fields


# Ejecutar la extracción de una imagen de factura (cambia el nombre del archivo por el tuyo)
image_path = 'data/sample_invoices/invoice_1.pdf'  # Reemplaza con la ruta de tu imagen
extracted_fields = process_invoice(image_path)
