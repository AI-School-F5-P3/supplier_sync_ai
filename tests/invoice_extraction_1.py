import pytesseract
from PIL import Image
import cv2
import re
import numpy as np
import os
from pathlib import Path
from pdf2image import convert_from_path
import tempfile

# Configuración de la ruta de Tesseract (ajústala según tu sistema)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configurar la variable TESSDATA_PREFIX (opcional si el OCR no encuentra los idiomas)
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

def convert_pdf_to_images(pdf_path):
    """Convierte un PDF a una lista de imágenes"""
    try:
        # Especifica la ruta a poppler
        poppler_path = r"C:\Program Files\poppler\Library\bin"  # Ajusta según tu instalación
        
        # Convertir PDF a imágenes
        images = convert_from_path(
            pdf_path,
            poppler_path=poppler_path,
            dpi=300  # Aumentar DPI para mejor calidad
        )
        return images
    except Exception as e:
        raise ValueError(f"Error al convertir PDF a imagen: {str(e)}")

def verify_file_path(file_path):
    """Verifica si el archivo existe y es accesible"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No se encontró el archivo en la ruta: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValueError(f"La ruta especificada no es un archivo: {file_path}")
    
    # Verificar si es PDF o imagen
    valid_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.pdf'}
    if Path(file_path).suffix.lower() not in valid_extensions:
        raise ValueError(f"El archivo no tiene una extensión válida: {file_path}")

def preprocess_image(image):
    """Preprocesa una imagen PIL o una ruta de imagen"""
    if isinstance(image, str):
        # Si es una ruta de archivo
        img = cv2.imread(image)
    else:
        # Si es una imagen PIL
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    if img is None:
        raise ValueError("No se pudo procesar la imagen")
    
    # Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar threshold adaptativo
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                 cv2.THRESH_BINARY, 11, 2)
    
    # Reducir ruido
    denoised = cv2.fastNlMeansDenoising(thresh)
    
    return denoised

def detect_letterhead(image):
    # Obtener el primer 25% de la imagen (donde suele estar el membrete)
    height = image.shape[0]
    letterhead_region = image[0:int(height*0.25), :]
    
    # Extraer texto del área del membrete
    letterhead_text = pytesseract.image_to_string(letterhead_region)
    return letterhead_text.strip()

def extract_invoice_data(file_path):
    """Extrae datos de una factura (PDF o imagen)"""
    # Verificar la ruta del archivo
    verify_file_path(file_path)
    
    # Si es PDF, convertir a imagen
    if file_path.lower().endswith('.pdf'):
        images = convert_pdf_to_images(file_path)
        # Procesar primera página del PDF
        image = images[0]
        processed_img = preprocess_image(image)
    else:
        # Procesar imagen directamente
        processed_img = preprocess_image(file_path)
    
    # Extraer texto usando Pytesseract
    text = pytesseract.image_to_string(processed_img)
    
    # Detectar membrete
    letterhead = detect_letterhead(processed_img)
    
    # Patrones expandidos para facturas en inglés
    patterns = {
        'invoice_number': r'(?i)Invoice\s*(?:#|No|Number|NUM)[:.]?\s*([A-Z0-9-]+)',
        'date': r'(?i)(?:Invoice\s+Date|Date)[:.]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        'due_date': r'(?i)(?:Due\s+Date|Payment\s+Due)[:.]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        'expiration_date': r'(?i)(?:Expiration\s+Date|Valid\s+Until)[:.]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        'po_number': r'(?i)(?:P\.?O\.?|Purchase\s+Order)[\s#:.]*([A-Z0-9-]+)',
        'total': r'(?i)Total\s*(?:Amount)?[:.]?\s*[\$€]?\s*([\d,]+\.?\d{0,2})',
        'subtotal': r'(?i)Subtotal[:.]?\s*[\$€]?\s*([\d,]+\.?\d{0,2})',
        'tax': r'(?i)(?:Tax|VAT)[:.]?\s*[\$€]?\s*([\d,]+\.?\d{0,2})',
        'payment_terms': r'(?i)(?:Payment\s+Terms|Terms)[:.]?\s*([^.\n]+)',
    }
    
    # Extraer información del destinatario (Bill To/Ship To)
    bill_to_pattern = r'(?i)(?:Bill\s+To|Sold\s+To)[:.]?\s*([^`]*)(?=(?:Ship\s+To|Invoice|P\.O\.|Date)|$)'
    ship_to_pattern = r'(?i)Ship\s+To[:.]?\s*([^`]*)(?=(?:Bill\s+To|Invoice|P\.O\.|Date)|$)'
    
    # Extraer notas
    notes_pattern = r'(?i)(?:Notes?|Remarks?|Comments?)[:.]?\s*([^`]*)(?=\n\n|$)'
    
    # Diccionario para almacenar los resultados
    extracted_data = {
        'letterhead': letterhead
    }
    
    # Buscar patrones en el texto
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            extracted_data[key] = match.group(1).strip()
        else:
            extracted_data[key] = None
    
    # Extraer información de dirección
    bill_to_match = re.search(bill_to_pattern, text, re.DOTALL)
    if bill_to_match:
        extracted_data['bill_to'] = clean_address(bill_to_match.group(1))
    
    ship_to_match = re.search(ship_to_pattern, text, re.DOTALL)
    if ship_to_match:
        extracted_data['ship_to'] = clean_address(ship_to_match.group(1))
    
    # Extraer notas
    notes_match = re.search(notes_pattern, text, re.DOTALL)
    if notes_match:
        extracted_data['notes'] = notes_match.group(1).strip()
    
    return extracted_data

def clean_address(address_text):
    # Limpiar el texto de la dirección
    cleaned = re.sub(r'\s+', ' ', address_text).strip()
    # Eliminar caracteres especiales comunes
    cleaned = re.sub(r'[`~]', '', cleaned)
    return cleaned

def format_extracted_data(data):
    """Formatea los datos extraídos para una mejor presentación"""
    formatted_output = []
    
    # Orden de presentación de los campos
    field_order = [
        ('letterhead', 'Letterhead'),
        ('invoice_number', 'Invoice Number'),
        ('date', 'Invoice Date'),
        ('due_date', 'Due Date'),
        ('expiration_date', 'Expiration Date'),
        ('po_number', 'Purchase Order Number'),
        ('bill_to', 'Bill To'),
        ('ship_to', 'Ship To'),
        ('subtotal', 'Subtotal'),
        ('tax', 'Tax'),
        ('total', 'Total'),
        ('payment_terms', 'Payment Terms'),
        ('notes', 'Notes')
    ]
    
    for field, label in field_order:
        if field in data and data[field]:
            formatted_output.append(f"{label}:\n{data[field]}\n")
    
    return "\n".join(formatted_output)

def main():
    # Obtener la ruta absoluta del directorio actual del script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construir la ruta al PDF (usar barras normales o dobles barras invertidas)
    invoice_path = os.path.join(current_dir, 'data_test', 'invoice_example.pdf')
    
    try:
        print(f"Intentando procesar archivo en: {invoice_path}")
        
        # Verificar que Tesseract está instalado y configurado
        if not pytesseract.get_tesseract_version():
            raise RuntimeError("Tesseract no está instalado o no se encuentra en el PATH")
        
        # Extraer datos
        data = extract_invoice_data(invoice_path)
        
        # Formatear y mostrar resultados
        formatted_output = format_extracted_data(data)
        print("Datos extraídos de la factura:")
        print("-" * 50)
        print(formatted_output)
            
    except FileNotFoundError as e:
        print(f"Error: No se encontró el archivo - {str(e)}")
    except ValueError as e:
        print(f"Error: Archivo inválido - {str(e)}")
    except RuntimeError as e:
        print(f"Error: Problema con Tesseract - {str(e)}")
    except Exception as e:
        print(f"Error inesperado al procesar la factura: {str(e)}")
        print(f"Tipo de error: {type(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()