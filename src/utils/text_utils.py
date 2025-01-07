import pytesseract
import logging

logger = logging.getLogger(__name__)

def extract_text(image):
    """Extract text using multiple OCR configurations"""
    configs = [
        '--oem 3 --psm 6 -l eng',  # Standard processing
        '--oem 3 --psm 4 -l eng',  # Assume vertical text
        '--oem 3 --psm 1 -l eng'   # Auto page segmentation
    ]
    
    text = ""
    for config in configs:
        try:
            text += pytesseract.image_to_string(image, config=config) + "\n"
        except Exception as e:
            logger.warning(f"OCR failed with config {config}: {str(e)}")
            
    return text

def clean_text(text):
    """Clean extracted text"""
    if not text:
        return ""
    
    # Remove multiple spaces
    text = ' '.join(text.split())
    
    # Remove special characters but keep basic punctuation
    text = ''.join(char for char in text if char.isalnum() or char in ' .,:-@\n')
    
    return text.strip()