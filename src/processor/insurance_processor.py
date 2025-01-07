import re
from datetime import datetime

def parse_date(date_str):
    """Parse date string into datetime object"""
    date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%m-%d-%Y', 
                   '%d/%m/%y', '%d-%m-%y', '%m/%d/%y', '%m-%d-%y']
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

def process_insurance_doc(text):
    """Process insurance documents"""
    data = {
        'document_type': 'insurance',
        'policy_number': None,
        'insurer': None,
        'insured': None,
        'coverage_type': None,
        'start_date': None,
        'end_date': None,
        'premium': None,
        'coverage_amount': None,
        'beneficiaries': [],
        'terms': []
    }
    
    # Extract policy number
    policy_patterns = [
        r'Policy\s*(?:No|Number)[.:]?\s*([A-Z0-9-]+)',
        r'Insurance\s*ID[.:]?\s*([A-Z0-9-]+)',
        r'Certificate\s*Number[.:]?\s*([A-Z0-9-]+)'
    ]
    
    for pattern in policy_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data['policy_number'] = match.group(1).strip()
            break
    
    # Extract insurer
    insurer_match = re.search(r'(?:Insurer|Insurance Company)[:\s]*([^\n]+)', text, re.IGNORECASE)
    if insurer_match:
        data['insurer'] = insurer_match.group(1).strip()
    
    # Extract insured
    insured_match = re.search(r'(?:Insured|Policy Holder)[:\s]*([^\n]+)', text, re.IGNORECASE)
    if insured_match:
        data['insured'] = insured_match.group(1).strip()
    
    # Extract coverage type
    coverage_match = re.search(r'(?:Coverage|Insurance Type)[:\s]*([^\n]+)', text, re.IGNORECASE)
    if coverage_match:
        data['coverage_type'] = coverage_match.group(1).strip()
    
    # Extract dates
    start_pattern = r'(?:Start Date|Effective From)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
    end_pattern = r'(?:End Date|Valid Until|Expiry)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
    
    start_match = re.search(start_pattern, text, re.IGNORECASE)
    if start_match:
        data['start_date'] = parse_date(start_match.group(1))
    
    end_match = re.search(end_pattern, text, re.IGNORECASE)
    if end_match:
        data['end_date'] = parse_date(end_match.group(1))
    
    # Extract premium
    premium_match = re.search(r'Premium[:\s]*\$?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
    if premium_match:
        try:
            data['premium'] = float(premium_match.group(1).replace(',', ''))
        except ValueError:
            pass
    
    # Extract coverage amount
    coverage_amount_match = re.search(r'(?:Coverage Amount|Sum Insured)[:\s]*\$?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
    if coverage_amount_match:
        try:
            data['coverage_amount'] = float(coverage_amount_match.group(1).replace(',', ''))
        except ValueError:
            pass
    
    # Extract beneficiaries
    beneficiaries_section = re.search(r'Beneficiaries:(.*?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
    if beneficiaries_section:
        beneficiaries = re.findall(r'([^\n,]+)(?:,|\n|$)', beneficiaries_section.group(1))
        data['beneficiaries'] = [b.strip() for b in beneficiaries if b.strip()]
    
    # Extract terms and conditions
    terms_section = re.search(r'(?:Terms|Conditions|Terms and Conditions):(.*?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
    if terms_section:
        terms = re.findall(r'[\d\.\-\*]\s*([^\n]+)', terms_section.group(1))
        data['terms'] = [t.strip() for t in terms if t.strip()]
    
    return data