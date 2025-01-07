import logging
from ..utils.image_utils import preprocess_image
from ..utils.text_utils import extract_text
from .invoice_processor import process_invoice
from .safety_processor import process_safety_doc
from .insurance_processor import process_insurance_doc
from .personal_processor import process_personal_doc
import pdf2image

# Configure logging
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

    def verify_pdf(file_path):
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
            
            if file_path.lower().endswith('.pdf'):
                # Aumentar la resolución de la conversión
                logger.info("Converting PDF to high-res image")
                images = pdf2image.convert_from_path(
                    file_path,
                    dpi=300,  # Aumentar DPI para mejor calidad
                    grayscale=True  # Convertir a escala de grises directamente
                )
                image = images[0]
                processed_img = preprocess_image(image)
            else:
                processed_img = preprocess_image(file_path)

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

            if not text.strip():
                raise ValueError("No text could be extracted from the document")

            return self.supported_types[doc_type](text)
                
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise