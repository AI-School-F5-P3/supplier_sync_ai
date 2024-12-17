import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
import json
import csv
import re
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime

@dataclass
class DocumentData:
    """Clase base para datos de documentos genéricos"""
    document_type: Optional[str] = None
    supplier_name: Optional[str] = None
    date: Optional[str] = None
    expiration_date: Optional[str] = None
    issuing_authority: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class InvoiceData(DocumentData):
    """Clase específica para datos de facturas"""
    invoice_number: Optional[str] = None
    due_date: Optional[str] = None
    currency: Optional[str] = None
    subtotal_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    payment_terms: Optional[str] = None

@dataclass
class SafetyDocumentData(DocumentData):
    """Clase específica para documentos de seguridad"""
    document_category: Optional[str] = None  # Compliance, Safety Certificate, etc.
    status: Optional[str] = None  # active, expired, etc.

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
        invoice_data = InvoiceData(document_type='invoice')
        
        # Buscar nombre del proveedor
        supplier_match = re.search(r'(?i)(compañía|empresa|proveedor|supplier|company):\s*(.+)', text, re.MULTILINE)
        if supplier_match:
            invoice_data.supplier_name = supplier_match.group(2).strip()
        
        # Buscar número de factura
        invoice_match = re.search(r'(?i)(?:invoice|factura)\s*(?:#|num|número)?\s*(\w+[-]?\d+)', text)
        if invoice_match:
            invoice_data.invoice_number = invoice_match.group(1)
        
        # Buscar fecha
        date_match = re.search(r'\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2}', text)
        if date_match:
            invoice_data.date = date_match.group(0)
        
        # Buscar monto total
        total_match = re.search(r'(?i)total[\s:]*\$?\s*([\d,]+\.?\d*)', text)
        if total_match:
            amount_str = total_match.group(1).replace(',', '')
            invoice_data.total_amount = float(amount_str)
        
        # Buscar impuestos
        tax_match = re.search(r'(?i)(?:tax|iva|impuesto)[\s:]*\$?\s*([\d,]+\.?\d*)', text)
        if tax_match:
            tax_str = tax_match.group(1).replace(',', '')
            invoice_data.tax_amount = float(tax_str)
        
        # Valores predeterminados
        invoice_data.supplier_name = invoice_data.supplier_name or "Desconocido"
        invoice_data.date = invoice_data.date or datetime.now().strftime('%Y-%m-%d')
        invoice_data.total_amount = invoice_data.total_amount or 0.0
        invoice_data.tax_amount = invoice_data.tax_amount or 0.0
        
        return invoice_data

    def extract_safety_document_data(self, text: str) -> SafetyDocumentData:
        """Extrae datos de documentos de seguridad"""
        safety_doc = SafetyDocumentData(document_type='safety')
        
        # Buscar nombre del proveedor/emisor
        supplier_match = re.search(r'(?i)(company|empresa|proveedor|issued by):\s*(.+)', text, re.MULTILINE)
        if supplier_match:
            safety_doc.supplier_name = supplier_match.group(2).strip()
        
        # Buscar fecha de emisión
        issue_date_match = re.search(r'(?i)(issue|fecha de emisión):\s*(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2})', text)
        if issue_date_match:
            safety_doc.date = issue_date_match.group(2)
        
        # Buscar fecha de vencimiento
        expiry_match = re.search(r'(?i)(expiration|vencimiento|válido hasta):\s*(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2})', text)
        if expiry_match:
            safety_doc.expiration_date = expiry_match.group(2)
        
        # Buscar autoridad emisora
        authority_match = re.search(r'(?i)(autoridad|authority):\s*(.+)', text, re.MULTILINE)
        if authority_match:
            safety_doc.issuing_authority = authority_match.group(2).strip()
        
        # Valores predeterminados
        safety_doc.supplier_name = safety_doc.supplier_name or "Desconocido"
        safety_doc.date = safety_doc.date or datetime.now().strftime('%Y-%m-%d')
        safety_doc.status = 'active'  # Predeterminado
        
        return safety_doc

    def export_to_json(self, document_data: DocumentData, output_path: str):
        """Exporta los datos del documento a un archivo JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(document_data), f, indent=2, ensure_ascii=False)

    def export_to_csv(self, document_data: List[DocumentData], output_path: str):
        """Exporta una lista de datos de documentos a un archivo CSV"""
        # Obtener todos los campos de los datos del documento
        all_fields = set()
        for doc in document_data:
            all_fields.update(doc.__annotations__.keys())
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(all_fields))
            writer.writeheader()
            for doc in document_data:
                writer.writerow(asdict(doc))