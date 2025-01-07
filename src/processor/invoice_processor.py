import re
from datetime import datetime

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
        r'(?:Invoice|Bill|Receipt).*?[:#]?\s*([A-Z0-9-]+)',
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
        r'(?:Date|Invoice Date)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        r'(\d{4}[-/]\d{2}[-/]\d{2})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                date_str = match.group(1)
                data['date'] = parse_date(date_str)
                break
            except ValueError:
                continue
    
    # Extract amounts
    amount_patterns = {
        'total': r'(?:Total|Amount|Sum)[^0-9]*?(\d+\.?\d*)',
        'subtotal': r'(?:Subtotal|Net)[^0-9]*?(\d+\.?\d*)',
        'tax': r'(?:Tax|VAT|GST)[^0-9]*?(\d+\.?\d*)'
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
        '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y',
        '%d/%m/%y', '%y-%m-%d', '%d-%m-%y',
        '%d %b %Y', '%d %B %Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None