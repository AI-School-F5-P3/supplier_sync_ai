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

    def process_document(self, file_path, doc_type='invoice'):
        """Main document processing function"""
        try:
            # Handle PDF files
            if file_path.lower().endswith('.pdf'):
                images = pdf2image.convert_from_path(file_path)
                image = images[0]
                processed_img = preprocess_image(image)
            else:
                processed_img = preprocess_image(file_path)

            # Extract text
            text = extract_text(processed_img)
            
            # Process according to document type
            if doc_type in self.supported_types:
                return self.supported_types[doc_type](text)
            else:
                raise ValueError(f"Unsupported document type: {doc_type}")
                
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise