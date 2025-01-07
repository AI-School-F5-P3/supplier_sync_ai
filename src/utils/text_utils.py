import pytesseract
import logging


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

logger = logging.getLogger(__name__)

def extract_text(image):
    """Extract text using multiple OCR configurations"""
    configs = [
        '--oem 3 --psm 6 -l eng',  # Standard processing
        '--oem 3 --psm 3 -l eng',  # Fully automatic page segmentation
        '--oem 3 --psm 4 -l eng',  # Assume single column of text
        '--oem 3 --psm 11 -l eng'  # Sparse text. Finds as much text as possible in no particular order
    ]
    
    best_text = ""
    max_length = 0
    
    for config in configs:
        try:
            logger.info(f"Trying OCR with config: {config}")
            current_text = pytesseract.image_to_string(image, config=config)
            logger.info(f"Extracted {len(current_text)} characters")
            
            if len(current_text) > max_length:
                best_text = current_text
                max_length = len(current_text)
                
        except Exception as e:
            logger.warning(f"OCR failed with config {config}: {str(e)}")
    
    if not best_text.strip():
        logger.error("No text could be extracted with any configuration")
        
    return best_text

def clean_text(text):
    """Clean extracted text"""
    if not text:
        return ""
    
    # Remove multiple spaces
    text = ' '.join(text.split())
    
    # Remove special characters but keep basic punctuation
    text = ''.join(char for char in text if char.isalnum() or char in ' .,:-@\n')
    
    return text.strip()