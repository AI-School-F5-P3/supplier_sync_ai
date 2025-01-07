import re
from datetime import datetime

def process_safety_doc(text):
    """Process safety documents"""
    data = {
        'document_type': 'safety',
        'document_number': None,
        'date': None,
        'expiry_date': None,
        'issuer': None,
        'safety_category': None,
        'compliance_status': None,
        'inspection_details': None,
        'safety_measures': []
    }
    
    # Extract document number
    doc_patterns = [
        r'Certificate\s*(?:No|Number)[.:]?\s*([A-Z0-9-]+)',
        r'Safety\s*Doc[.:]?\s*([A-Z0-9-]+)',
        r'Document\s*ID[.:]?\s*([A-Z0-9-]+)'
    ]
    
    for pattern in doc_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data['document_number'] = match.group(1).strip()
            break
    
    # Extract dates
    date_pattern = r'(?:Date|Issued)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
    expiry_pattern = r'(?:Expiry|Valid Until)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
    
    date_match = re.search(date_pattern, text, re.IGNORECASE)
    if date_match:
        data['date'] = parse_date(date_match.group(1))
    
    expiry_match = re.search(expiry_pattern, text, re.IGNORECASE)
    if expiry_match:
        data['expiry_date'] = parse_date(expiry_match.group(1))
    
    # Extract issuer
    issuer_match = re.search(r'(?:Issued By|Certifier)[:\s]*([^\n]+)', text, re.IGNORECASE)
    if issuer_match:
        data['issuer'] = issuer_match.group(1).strip()
    
    # Extract safety category
    category_match = re.search(r'(?:Category|Type)[:\s]*([^\n]+)', text, re.IGNORECASE)
    if category_match:
        data['safety_category'] = category_match.group(1).strip()
    
    # Extract compliance status
    status_match = re.search(r'(?:Status|Compliance)[:\s]*([^\n]+)', text, re.IGNORECASE)
    if status_match:
        data['compliance_status'] = status_match.group(1).strip()
    
    # Extract inspection details
    inspection_match = re.search(r'(?:Inspection|Assessment)[:\s]*([^\n]+(?:\n[^\n]+)*)', text, re.IGNORECASE)
    if inspection_match:
        data['inspection_details'] = inspection_match.group(1).strip()
    
    # Extract safety measures
    measures_section = re.findall(r'(?:•|\d+\.)\s*([^\n]+)', text)
    data['safety_measures'] = [measure.strip() for measure in measures_section if len(measure.strip()) > 5]
    
    return data

def parse_date(date_str):
    """Parse date string into standard format"""
    formats = [
        '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y',
        '%d/%m/%y', '%y-%m-%d', '%d-%m-%y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None