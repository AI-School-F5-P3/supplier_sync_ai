import re
from datetime import datetime

def parse_date(date_str):
    """Parse date string into datetime object"""
    date_formats = [
        '%m/%d/%Y', '%d/%m/%Y',  # Common US/International formats
        '%m-%d-%Y', '%d-%m-%Y',
        '%b %d, %Y', '%B %d, %Y',  # Month name formats
        '%Y/%m/%d', '%Y-%m-%d',    # ISO-like formats
        '%m/%d/%y', '%d/%m/%y'     # Two-digit year formats
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

def process_personal_doc(text, doc_type=None):
    """
    Process personal identification documents
    Supports: passports, driver's licenses, state IDs
    """
    data = {
        'document_type': doc_type,
        'id_number': None,
        'last_name': None,
        'first_name': None,
        'middle_name': None,
        'date_of_birth': None,
        'issue_date': None,
        'expiration_date': None,
        'issuing_authority': None,
        'nationality': None,
        'gender': None,
        'address': None,
        'height': None,
        'eye_color': None,
        'restrictions': [],
        'endorsements': []
    }
    
    # Detect document type if not provided
    if not doc_type:
        if re.search(r'passport', text, re.IGNORECASE):
            data['document_type'] = 'passport'
        elif re.search(r"driver'?s?\s*license", text, re.IGNORECASE):
            data['document_type'] = 'driver_license'
        elif re.search(r'identification\s*card|ID\s*card', text, re.IGNORECASE):
            data['document_type'] = 'state_id'
            
    # Extract ID number based on document type
    id_patterns = {
        'passport': r'Passport\s*(?:No|Number)[.:]?\s*([A-Z0-9]+)',
        'driver_license': r'(?:DL|License)\s*(?:No|Number|#)[.:]?\s*([A-Z0-9-]+)',
        'state_id': r'ID\s*(?:No|Number|#)[.:]?\s*([A-Z0-9-]+)'
    }
    
    if data['document_type'] in id_patterns:
        id_match = re.search(id_patterns[data['document_type']], text, re.IGNORECASE)
        if id_match:
            data['id_number'] = id_match.group(1).strip()
    
    # Extract names
    # Look for both "Last Name: Smith" and "Smith, John" formats
    name_pattern1 = re.search(r'(?:Last|Family|Sur)[- ]?name[:\s]*([^\n,]+)', text, re.IGNORECASE)
    name_pattern2 = re.search(r'(?:First|Given)[- ]?name[:\s]*([^\n,]+)', text, re.IGNORECASE)
    name_pattern3 = re.search(r'([A-Z]+),\s*([A-Z\s]+)(?:\s+([A-Z]+))?', text)
    
    if name_pattern1 and name_pattern2:
        data['last_name'] = name_pattern1.group(1).strip()
        data['first_name'] = name_pattern2.group(1).strip()
    elif name_pattern3:
        data['last_name'] = name_pattern3.group(1).strip()
        data['first_name'] = name_pattern3.group(2).strip()
        if name_pattern3.group(3):
            data['middle_name'] = name_pattern3.group(3).strip()
    
    # Extract dates
    dob_pattern = r'(?:Date\s+of\s+Birth|Birth\s+Date|DOB)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
    issue_pattern = r'(?:Issue|Issued)\s*(?:Date|On)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
    exp_pattern = r'(?:Expiration|Expiry|Expires)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
    
    dob_match = re.search(dob_pattern, text, re.IGNORECASE)
    if dob_match:
        data['date_of_birth'] = parse_date(dob_match.group(1))
        
    issue_match = re.search(issue_pattern, text, re.IGNORECASE)
    if issue_match:
        data['issue_date'] = parse_date(issue_match.group(1))
        
    exp_match = re.search(exp_pattern, text, re.IGNORECASE)
    if exp_match:
        data['expiration_date'] = parse_date(exp_match.group(1))
    
    # Extract issuing authority
    auth_match = re.search(r'(?:Issued\s+by|Issuing\s+Authority)[:\s]*([^\n]+)', text, re.IGNORECASE)
    if auth_match:
        data['issuing_authority'] = auth_match.group(1).strip()
    
    # Extract nationality (mainly for passports)
    nation_match = re.search(r'Nationality[:\s]*([^\n]+)', text, re.IGNORECASE)
    if nation_match:
        data['nationality'] = nation_match.group(1).strip()
    
    # Extract gender
    gender_match = re.search(r'(?:Gender|Sex)[:\s]*([MF]|Male|Female)', text, re.IGNORECASE)
    if gender_match:
        gender = gender_match.group(1).upper()
        data['gender'] = 'M' if gender in ['M', 'MALE'] else 'F'
    
    # Extract address (mainly for driver's licenses and state IDs)
    addr_match = re.search(r'(?:Address|ADD)[:\s]*([^\n]+(?:\n[^\n]+)*)', text, re.IGNORECASE)
    if addr_match:
        data['address'] = ' '.join(addr_match.group(1).split())
    
    # Extract physical characteristics (mainly for driver's licenses)
    height_match = re.search(r'HGT[:\s]*(\d{1,2}\'?\s*\d{1,2}\"?|\d{3}\s*cm)', text, re.IGNORECASE)
    if height_match:
        data['height'] = height_match.group(1).strip()
        
    eye_match = re.search(r'(?:Eyes|Eye\s+Color)[:\s]*([A-Z]{3}|[A-Za-z]+)', text, re.IGNORECASE)
    if eye_match:
        data['eye_color'] = eye_match.group(1).strip().upper()
    
    # Extract restrictions and endorsements (for driver's licenses)
    if data['document_type'] == 'driver_license':
        rest_match = re.search(r'REST[:\s]*([^\n]+)', text, re.IGNORECASE)
        if rest_match:
            data['restrictions'] = [r.strip() for r in rest_match.group(1).split(',')]
            
        end_match = re.search(r'END[:\s]*([^\n]+)', text, re.IGNORECASE)
        if end_match:
            data['endorsements'] = [e.strip() for e in end_match.group(1).split(',')]
    
    return data