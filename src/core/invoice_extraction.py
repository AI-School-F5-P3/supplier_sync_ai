import pytesseract
from PIL import Image
import cv2
import re
import numpy as np
import os
import json
import csv
from pathlib import Path
from pdf2image import convert_from_path, pdfinfo_from_path
import io
import tempfile
import logging

# Configuración de la ruta de Tesseract (ajústala según tu sistema)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configurar la variable TESSDATA_PREFIX (opcional si el OCR no encuentra los idiomas)
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_pdf(pdf_path):
    """Verifies if a PDF file is valid and readable"""
    try:
        # Check if file is empty
        if os.path.getsize(pdf_path) == 0:
            raise ValueError("PDF file is empty")
        
        # Try to get PDF info
        try:
            pdf_info = pdfinfo_from_path(pdf_path)
            if pdf_info['Pages'] < 1:
                raise ValueError("PDF contains no pages")
        except Exception as e:
            raise ValueError(f"Invalid PDF format: {str(e)}")
            
        return True
    except Exception as e:
        raise ValueError(f"PDF verification failed: {str(e)}")

def convert_pdf_to_images(pdf_path):
    """Converts a PDF to a list of images with enhanced error handling"""
    try:
        # Verify PDF first
        verify_pdf(pdf_path)
        
        # Define possible poppler paths
        poppler_paths = [
            None,  # Try system's poppler first
            r"C:\Program Files\poppler\Library\bin",
            r"C:\Program Files\poppler-23.11.0\Library\bin",
            r"C:\poppler\bin",
            os.getenv('POPPLER_PATH')
        ]
        
        # Remove None and empty values
        poppler_paths = [p for p in poppler_paths if p]
        
        last_error = None
        # Try each poppler path
        for poppler_path in poppler_paths:
            try:
                logger.info(f"Attempting PDF conversion with poppler path: {poppler_path}")
                conversion_args = {
                    'pdf_path': pdf_path,
                    'dpi': 300,
                    'fmt': 'ppm'  # More reliable format
                }
                
                if poppler_path:
                    conversion_args['poppler_path'] = poppler_path
                
                images = convert_from_path(**conversion_args)
                
                if not images:
                    raise ValueError("No images extracted from PDF")
                
                logger.info(f"Successfully converted PDF using poppler path: {poppler_path}")
                return images
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Failed with poppler path {poppler_path}: {str(e)}")
                continue
        
        # If we get here, all attempts failed
        raise ValueError(f"All PDF conversion attempts failed. Last error: {last_error}")
        
    except Exception as e:
        raise ValueError(f"Error in PDF conversion: {str(e)}")

def verify_file_path(file_path):
    """Verifies if the file exists and is accessible"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at path: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValueError(f"Specified path is not a file: {file_path}")
    
    # Check if file is empty
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"File is empty: {file_path}")
    
    valid_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.pdf'}
    if Path(file_path).suffix.lower() not in valid_extensions:
        raise ValueError(f"Invalid file extension: {file_path}")

def preprocess_image(image):
    """Preprocesses an image for better OCR results"""
    try:
        if isinstance(image, str):
            img = cv2.imread(image)
        elif isinstance(image, Image.Image):
            img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            raise ValueError("Invalid image input type")
        
        if img is None:
            raise ValueError("Could not process image")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Reduce noise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        return denoised
    except Exception as e:
        raise ValueError(f"Error preprocessing image: {str(e)}")

def extract_invoice_data(file_path):
    """Extracts data from an invoice"""
    logger.info(f"Starting invoice data extraction from: {file_path}")
    
    try:
        # Verify file path and basic file properties
        verify_file_path(file_path)
        
        # Process PDF or image
        if file_path.lower().endswith('.pdf'):
            logger.info("Processing PDF file")
            images = convert_pdf_to_images(file_path)
            if not images:
                raise ValueError("No images extracted from PDF")
            image = images[0]
            processed_img = preprocess_image(image)
        else:
            logger.info("Processing image file")
            processed_img = preprocess_image(file_path)
        
        # Extract text using Tesseract
        try:
            custom_config = r'--oem 3 --psm 6 -l eng'
            text = pytesseract.image_to_string(processed_img, config=custom_config)
        except Exception as e:
            raise RuntimeError(f"Tesseract OCR error: {str(e)}")
        
        # Initialize extracted data
        extracted_data = {
            'items': [],
            'invoice_number': None,
            'date': None,
            'due_date': None,
            'po_number': None,
            'payment_terms': None,
            'bill_to': None,
            'send_to': None,
            'total': None,
            'subtotal': None,
            'tax': None,
            'notes': None
        }
        
        # Extract invoice number
        invoice_patterns = [
            r'Invoice\s*(?:No\.?|Number|#)?\s*:?\s*([A-Z0-9-]+)',
            r'(?:No\.?|Number|#)\s*:?\s*([A-Z0-9-]+)',
            r'(?<=INVOICE\s)([A-Z0-9-]+)',
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_data['invoice_number'] = match.group(1).strip()
                break
        
        # Extract dates
        date_match = re.search(r'(?:Issue|Invoice)\s*Date[:.]?\s*(\d{4}[-/]\d{2}[-/]\d{2})', text, re.IGNORECASE)
        if date_match:
            extracted_data['date'] = date_match.group(1)
        
        due_date_match = re.search(r'(?:Due|Expiration)\s*Date[:.]?\s*(\d{4}[-/]\d{2}[-/]\d{2})', text, re.IGNORECASE)
        if due_date_match:
            extracted_data['due_date'] = due_date_match.group(1)
        
        # Extract PO number
        po_match = re.search(r'(?:Purchase\s*Order|PO)[:.]?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if po_match:
            extracted_data['po_number'] = po_match.group(1)
        
        # Extract payment terms
        payment_terms_match = re.search(r'Payment\s*Terms[:.]?\s*([^\n]+)', text, re.IGNORECASE)
        if payment_terms_match:
            extracted_data['payment_terms'] = payment_terms_match.group(1).strip()
        
        # Extract addresses
        bill_to_match = re.search(r'Bill\s*To[:.]?\s*([^\n]+(?:\n[^\n]+)*)', text, re.IGNORECASE)
        if bill_to_match:
            extracted_data['bill_to'] = clean_address(bill_to_match.group(1))
        
        send_to_match = re.search(r'Send\s*To[:.]?\s*([^\n]+(?:\n[^\n]+)*)', text, re.IGNORECASE)
        if send_to_match:
            extracted_data['send_to'] = clean_address(send_to_match.group(1))
        
        # Extract amounts
        amount_patterns = {
            'total': r'Total[:.]?\s*\$?\s*([\d,]+\.?\d{0,2})',
            'subtotal': r'Subtotal[:.]?\s*\$?\s*([\d,]+\.?\d{0,2})',
            'tax': r'Tax[:.]?\s*\$?\s*([\d,]+\.?\d{0,2})'
        }
        
        for key, pattern in amount_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_data[key] = match.group(1).replace(',', '')
        
        # Extract items
        lines = text.split('\n')
        item_pattern = re.compile(r'^(.*?)\s+(\d+)\s+\$?([\d,.]+)\s+\$?([\d,.]+)')
        
        for line in lines:
            match = item_pattern.match(line.strip())
            if match and not any(keyword in match.group(1).lower() for keyword in ['total', 'subtotal', 'tax']):
                item = {
                    'description': match.group(1).strip(),
                    'quantity': int(match.group(2)),
                    'unit_price': float(match.group(3).replace(',', '')),
                    'total': float(match.group(4).replace(',', ''))
                }
                extracted_data['items'].append(item)
        
        # Extract notes
        notes_match = re.search(r'Notes?[:.]?\s*([^\n]+)', text, re.IGNORECASE)
        if notes_match:
            extracted_data['notes'] = notes_match.group(1).strip()
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error in invoice data extraction: {str(e)}")
        raise Exception(f"Error extracting invoice data: {str(e)}")

def clean_address(address_text):
    """Cleans and consolidates address information"""
    if not address_text:
        return None
    
    # Remove multiple spaces and special characters
    cleaned = re.sub(r'\s+', ' ', address_text).strip()
    cleaned = re.sub(r'[`~]', '', cleaned)
    
    # Remove address prefixes
    cleaned = re.sub(r'^(?:Bill\s+To|Send\s+To|Ship\s+To)[:.]?\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Remove text after keywords that might indicate the end of the address
    cleaned = re.split(r'\b(?:Invoice|Date|P\.O\.|Total)\b', cleaned)[0].strip()
    
    return cleaned

def export_data_to_json(data, output_path=None):
    """Exports extracted data to JSON"""
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
    
    return json_str

def export_data_to_csv(data, output_path=None):
    """Exports extracted data to CSV"""
    # StringIO for in-memory CSV
    output = io.StringIO()
    
    # Write general data
    fieldnames = ['invoice_number', 'date', 'due_date', 'po_number', 'payment_terms',
                 'bill_to', 'send_to', 'subtotal', 'tax', 'total', 'notes']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Filter only the fields we want
    row_data = {k: data.get(k, '') for k in fieldnames}
    writer.writerow(row_data)
    
    csv_str = output.getvalue()
    output.close()
    
    if output_path:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_str)
        
        # Write items to separate file if present
        if data.get('items'):
            items_path = output_path.replace('.csv', '_items.csv')
            with open(items_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['description', 'quantity', 'unit_price', 'total'])
                writer.writeheader()
                writer.writerows(data['items'])
    
    return csv_str

if __name__ == "__main__":
    try:
        # Get the current script directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build path to test invoice
        invoice_path = os.path.join(current_dir, 'data_test', 'invoice_example.pdf')
        
        print(f"Attempting to process file at: {invoice_path}")
        
        # Verify Tesseract installation
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise RuntimeError("Tesseract is not installed or not found in PATH")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(current_dir, 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract data
        data = extract_invoice_data(invoice_path)
        
        # Print formatted results
        print("\nExtracted Invoice Data:")
        print("-" * 50)
        
        # Print general information
        fields = ['invoice_number', 'date', 'due_date', 'po_number', 'payment_terms']
        for field in fields:
            if data.get(field):
                print(f"{field.replace('_', ' ').title()}: {data[field]}")
        
        # Print addresses
        if data.get('bill_to'):
            print(f"\nBill To:\n{data['bill_to']}")
        if data.get('send_to'):
            print(f"\nSend To:\n{data['send_to']}")
        
        # Print items
        if data.get('items'):
            print("\nItems:")
            print("-" * 30)
            for item in data['items']:
                print(f"Description: {item['description']}")
                print(f"Quantity: {item['quantity']}")
                print(f"Unit Price: ${item['unit_price']}")
                print(f"Total: ${item['total']}")
                print("-" * 30)
        
        # Print totals
        if data.get('subtotal'):
            print(f"\nSubtotal: ${data['subtotal']}")
        if data.get('tax'):
            print(f"Tax: ${data['tax']}")
        if data.get('total'):
            print(f"Total: ${data['total']}")
        
        # Export to JSON
        json_output_path = os.path.join(output_dir, 'invoice_data.json')
        export_data_to_json(data, json_output_path)
        print(f"\nData exported to JSON: {json_output_path}")
        
        # Export to CSV
        csv_output_path = os.path.join(output_dir, 'invoice_data.csv')
        export_data_to_csv(data, csv_output_path)
        print(f"Data exported to CSV: {csv_output_path}")
            
    except FileNotFoundError as e:
        print(f"Error: File not found - {str(e)}")
    except ValueError as e:
        print(f"Error: Invalid file - {str(e)}")
    except RuntimeError as e:
        print(f"Error: Tesseract issue - {str(e)}")
    except Exception as e:
        print(f"Unexpected error while processing invoice: {str(e)}")
        import traceback
        print(traceback.format_exc())