import json
import csv
import io

def export_to_format(data, format_type):
    """Export data to specified format"""
    if format_type == 'json':
        return json.dumps(data, indent=2)
    elif format_type == 'csv':
        output = io.StringIO()
        
        # Handle nested data
        flattened_data = flatten_dict(data)
        
        writer = csv.DictWriter(output, fieldnames=flattened_data.keys())
        writer.writeheader()
        writer.writerow(flattened_data)
        
        return output.getvalue()
    else:
        raise ValueError(f"Unsupported export format: {format_type}")

def flatten_dict(d, parent_key='', sep='_'):
    """Flatten nested dictionary for CSV export"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            if v and isinstance(v[0], dict):
                # For list of dictionaries, concatenate values
                for i, item in enumerate(v):
                    items.extend(flatten_dict(item, f"{new_key}{sep}{i}", sep=sep).items())
            else:
                items.append((new_key, ','.join(map(str, v))))
        else:
            items.append((new_key, v))
    return dict(items)