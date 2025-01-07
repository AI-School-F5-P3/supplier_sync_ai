import logging
import pytesseract
import os
import pdf2image
from PIL import Image
from ..utils.image_utils import preprocess_image
from ..utils.text_utils import extract_text
from .invoice_processor import process_invoice
from .safety_processor import process_safety_doc
from .insurance_processor import process_insurance_doc
from .personal_processor import process_personal_doc

# Configuración de Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configurar la variable TESSDATA_PREFIX directamente en Python
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

# Configurar el logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.supported_types = {
            'invoice': process_invoice,
            'safety': process_safety_doc,
            'insurance': process_insurance_doc,
            'personal': process_personal_doc
        }

    def verify_pdf(self, file_path):
        """Verifica si el archivo PDF tiene texto extraíble."""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                logger.info(f"PDF text extraction test: {text[:200]}")
                return bool(text.strip())
        except Exception as e:
            logger.warning(f"PDF verification failed: {str(e)}")
            return False
  
    def process_document(self, file_path, doc_type='invoice'):
        try:
            logger.info(f"Processing document: {file_path}")
            
            # Detectar el tipo de archivo (PDF o imagen)
            if file_path.lower().endswith('.pdf'):
                # Convertir PDF a imagen de alta resolución
                logger.info("Converting PDF to high-res image")
                images = pdf2image.convert_from_path(
                    file_path,
                    dpi=300,  # Aumentar DPI para mejor calidad
                    grayscale=True  # Convertir a escala de grises directamente
                )
                image = images[0]  # Tomar la primera página del PDF
                processed_img = preprocess_image(image)
            elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Si es una imagen, procesarla directamente
                logger.info("Processing image file")
                processed_img = preprocess_image(file_path)
            else:
                raise ValueError("Unsupported file type")

            # Usar múltiples configuraciones de OCR
            text = ""
            configs = [
                '--oem 3 --psm 6 -l eng',  # Asume un bloque uniforme de texto
                '--oem 3 --psm 3 -l eng',  # Segmentación completa
                '--oem 3 --psm 1 -l eng',  # Orientación y detección de script automática
            ]
            
            for config in configs:
                try:
                    current_text = pytesseract.image_to_string(processed_img, config=config)
                    if len(current_text) > len(text):
                        text = current_text
                except Exception as e:
                    logger.warning(f"OCR failed with config {config}: {str(e)}")
                    continue

            # Si no se extrae texto, lanzar un error
            if not text.strip():
                raise ValueError("No text could be extracted from the document")

            # Procesar el texto extraído según el tipo de documento
            return self.supported_types[doc_type](text)
                
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise
