import re
from datetime import datetime

# Extraer montos ajustados
def extract_final_total(text):
    """
    Extract the second occurrence of 'Total' (or the last one).
    """
    total_matches = list(re.finditer(r'(?:Total|Amount|Sum)[^0-9]*?(\d+\.?\d*)', text, re.IGNORECASE))
    if len(total_matches) > 1:
        # Return the value from the last match (the second 'Total')
        return float(total_matches[-1].group(1).replace(',', ''))
    elif total_matches:
        # Return the first match if only one is found
        return float(total_matches[0].group(1).replace(',', ''))
    return None

def process_invoice(text):
    """Process invoice documents with enhanced field extraction"""
    data = {
        'document_type': 'invoice',
        'invoice_number': None,
        'date': None,
        'due_date': None,
        'total': None,
        'subtotal': None,
        'tax': None,
        'items': [],
        'vendor': None,
        'bill_to': None
    }
    
    # Extract invoice number (multiple patterns)
    invoice_patterns = [
        r'(?:Invoice|Bill|Receipt|Invoice #).*?[:#]?\s*([A-Z0-9-]+)',
        r'Document\s*(?:No|Number)[.:]?\s*([A-Z0-9-]+)',
        r'TD(\d+)',
        r'No[.:]\s*(\d+)',
    ]
    
    for pattern in invoice_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data['invoice_number'] = match.group(1).strip()
            break
    
    # Extract dates
    date_patterns = [
        r'(?:Date|Invoice Date|Due Date)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # MM/DD/YYYY or MM/DD/YY
        r'(?:Date|Invoice Date|Due Date)[:\s]*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',  # January 7, 2025
        r'(?:Date|Invoice Date|Due Date)[:\s]*(\d{4}[-/]\d{2}[-/]\d{2})',  # YYYY-MM-DD
        r'(?:Date|Invoice Date|Due Date)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2})'  # M/D/YY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                date_str = match.group(1)
                parsed_date = parse_date(date_str)
                if 'Due Date' in pattern:
                    data['due_date'] = parsed_date
                else:
                    data['date'] = parsed_date
            except ValueError:
                continue
    
    # Extract total using the new function
    data['total'] = extract_final_total(text)

    # Extract subtotal and tax as before
    amount_patterns = {
        'subtotal': r'(?:Subtotal|Net)[^0-9]*?(\d+\.?\d*)',
        'tax': r'(?:Tax|VAT|GST)[^)]*\)\s*[^0-9]*?(\d+\.?\d*)'  # Look for tax after percentage
    }
    
    for key, pattern in amount_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                data[key] = float(match.group(1).replace(',', ''))
            except ValueError:
                continue
    
    # Extract vendor information
    vendor_patterns = [
        r'(?:Vendor|Seller|Company):\s*([^\n]+)',
        r'^([A-Z\s&]+)(?:\n|$)',
        r'([A-Z][A-Za-z\s&]+)\nAddress'
    ]
    
    for pattern in vendor_patterns:
        match = re.search(pattern, text)
        if match:
            data['vendor'] = match.group(1).strip()
            break
    
    # Extract items
    items_patterns = [
        r'(\d+)\s+([A-Za-z\s]+)\s+(\d+\.?\d*)\s+(\d+\.?\d*)',
        r'([A-Za-z\s]+)\s+(\d+)\s+(?:@\s*)?(\d+\.?\d*)\s+(\d+\.?\d*)'
    ]
    
    for pattern in items_patterns:
        items = re.finditer(pattern, text)
        for item in items:
            try:
                if len(item.groups()) == 4:
                    data['items'].append({
                        'quantity': int(item.group(1)),
                        'description': item.group(2).strip(),
                        'unit_price': float(item.group(3)),
                        'total': float(item.group(4))
                    })
            except (ValueError, IndexError):
                continue
    
    return data

def parse_date(date_str):
    """Parse date string into standard format"""
    formats = [
        '%B %d, %Y',  # January 7, 2025
        '%m/%d/%Y', '%m/%d/%y',  # MM/DD/YYYY, MM/DD/YY
        '%m-%d-%Y', '%m-%d-%y',  # MM-DD-YYYY, MM-DD-YY
        '%Y-%m-%d',  # YYYY-MM-DD
        '%d %b %Y', '%d %B %Y'  # 07 Jan 2025, 07 January 2025
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None
