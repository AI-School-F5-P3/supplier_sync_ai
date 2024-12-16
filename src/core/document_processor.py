import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
import json
import csv
import re
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class InvoiceData:
    """Clase para almacenar los datos extraídos de una factura"""
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    supplier_name: Optional[str] = None
    supplier_id: Optional[str] = None

class DocumentProcessor:
    """Clase principal para procesar documentos"""
    
    def __init__(self):
        self.ocr_engine = pytesseract

    def preprocess_image(self, image):
        """Preprocesa la imagen para mejorar la calidad del OCR"""
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Aplicar threshold adaptativo
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Reducir ruido
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        return denoised

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrae texto de un archivo PDF"""
        try:
            # Convertir PDF a imágenes
            images = convert_from_path(pdf_path)
            
            full_text = ""
            for image in images:
                # Convertir imagen de PIL a formato numpy para OpenCV
                opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                # Preprocesar imagen
                processed_image = self.preprocess_image(opencv_image)
                
                # Extraer texto
                text = self.ocr_engine.image_to_string(processed_image)
                full_text += text + "\n"
                
            return full_text
        except Exception as e:
            print(f"Error al procesar PDF: {str(e)}")
            return ""

    def extract_invoice_data(self, text: str) -> InvoiceData:
        """Extrae datos específicos de la factura del texto"""
        invoice_data = InvoiceData()
        
        # Buscar número de factura (patrón común: "Invoice #" seguido de números)
        invoice_match = re.search(r'(?i)(?:invoice|factura)\s*(?:#|num|número)?\s*(\w+[-]?\d+)', text)
        if invoice_match:
            invoice_data.invoice_number = invoice_match.group(1)
        
        # Buscar fecha (formato común: DD/MM/YYYY o YYYY-MM-DD)
        date_match = re.search(r'\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2}', text)
        if date_match:
            invoice_data.date = date_match.group(0)
        
        # Buscar monto total (precedido por "Total" y seguido por números)
        total_match = re.search(r'(?i)total[\s:]*\$?\s*([\d,]+\.?\d*)', text)
        if total_match:
            amount_str = total_match.group(1).replace(',', '')
            invoice_data.total_amount = float(amount_str)
        
        # Buscar impuestos (IVA, Tax, etc.)
        tax_match = re.search(r'(?i)(?:tax|iva|impuesto)[\s:]*\$?\s*([\d,]+\.?\d*)', text)
        if tax_match:
            tax_str = tax_match.group(1).replace(',', '')
            invoice_data.tax_amount = float(tax_str)
        
        return invoice_data

    def export_to_json(self, invoice_data: InvoiceData, output_path: str):
        """Exporta los datos de la factura a un archivo JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(invoice_data.__dict__, f, indent=2, ensure_ascii=False)

    def export_to_csv(self, invoice_data: List[InvoiceData], output_path: str):
        """Exporta una lista de datos de facturas a un archivo CSV"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=InvoiceData.__annotations__.keys())
            writer.writeheader()
            for invoice in invoice_data:
                writer.writerow(invoice.__dict__)

def main():
    # Ejemplo de uso
    processor = DocumentProcessor()
    
    # Procesar un PDF de ejemplo
    pdf_path = "ejemplo_factura.pdf"
    try:
        # Extraer texto del PDF
        text = processor.extract_text_from_pdf(pdf_path)
        
        # Extraer datos de la factura
        invoice_data = processor.extract_invoice_data(text)
        
        # Exportar a JSON
        processor.export_to_json(invoice_data, "factura_procesada.json")
        
        # Exportar a CSV (ejemplo con una sola factura)
        processor.export_to_csv([invoice_data], "facturas_procesadas.csv")
        
        print("Procesamiento completado exitosamente")
        print(f"Datos extraídos: {invoice_data}")
        
    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")

if __name__ == "__main__":
    main()