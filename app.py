import streamlit as st
import os
import tempfile
from src.core.invoice_extraction import extract_invoice_data, export_data_to_json, export_data_to_csv
import pandas as pd
import shutil

st.set_page_config(page_title="Invoice Data Extractor", layout="wide")

st.title("Invoice Data Extractor")

def validate_uploaded_file(uploaded_file):
    """Validates the uploaded file content"""
    if uploaded_file.size == 0:
        raise ValueError("El archivo subido está vacío")
    
    if uploaded_file.size > 10 * 1024 * 1024:  # 10MB limit
        raise ValueError("El archivo es demasiado grande. Por favor, suba un archivo menor a 10MB")
    
    return True

def save_uploaded_file(uploaded_file):
    """Safely saves the uploaded file to a temporary location"""
    try:
        # Create a temporary directory that will be cleaned up automatically
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create full path for the temporary file
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            temp_path = os.path.join(tmp_dir, f"invoice{file_extension}")
            
            # Save uploaded file content
            with open(temp_path, 'wb') as f:
                # Read in chunks to handle larger files
                CHUNK_SIZE = 64 * 1024  # 64KB chunks
                file_content = uploaded_file.getvalue()
                
                # Verify we have content
                if not file_content:
                    raise ValueError("No se encontró contenido en el archivo subido")
                
                # Write content
                f.write(file_content)
            
            # Verify the file was written correctly
            if os.path.getsize(temp_path) == 0:
                raise ValueError("Error al escribir el contenido del archivo")
            
            # Create a copy of the file that will persist beyond the with block
            final_temp_path = tempfile.mktemp(suffix=file_extension)
            shutil.copy2(temp_path, final_temp_path)
            
            return final_temp_path
            
    except Exception as e:
        raise ValueError(f"Error al guardar el archivo: {str(e)}")

# File upload - added accepted file types and help text
uploaded_file = st.file_uploader(
    "Upload an invoice (PDF or image)",
    type=['pdf', 'png', 'jpg', 'jpeg'],
    help="Supported formats: PDF, PNG, JPG, JPEG"
)

if uploaded_file is not None:
    try:
        # Validate uploaded file
        validate_uploaded_file(uploaded_file)
        
        # Save file and get path
        temp_path = save_uploaded_file(uploaded_file)

        # Extract data
        with st.spinner('Processing invoice...'):
            data = extract_invoice_data(temp_path)

        # Display results in two columns
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("General Information")
            fields = [
                ('Invoice Number', 'invoice_number'),
                ('Date', 'date'),
                ('Due Date', 'due_date'),
                ('PO Number', 'po_number'),
                ('Payment Terms', 'payment_terms')
            ]
            for label, key in fields:
                if key in data and data[key]:
                    st.text_input(label, data[key], disabled=True)

        with col2:
            st.subheader("Addresses")
            if data.get('bill_to'):
                st.text_area("Bill To", data['bill_to'], disabled=True)
            if data.get('send_to'):
                st.text_area("Send To", data['send_to'], disabled=True)

        # Display items in a table if present
        if data.get('items') and len(data['items']) > 0:
            st.subheader("Items")
            items_df = pd.DataFrame(data['items'])
            st.dataframe(items_df, use_container_width=True)

        # Display totals if present
        col3, col4, col5 = st.columns(3)
        with col3:
            if data.get('subtotal'):
                st.metric("Subtotal", f"${data['subtotal']}")
        with col4:
            if data.get('tax'):
                st.metric("Tax", f"${data['tax']}")
        with col5:
            if data.get('total'):
                st.metric("Total", f"${data['total']}")

        # Export buttons
        st.subheader("Export Data")
        col6, col7 = st.columns(2)
        
        # JSON export
        with col6:
            json_data = export_data_to_json(data, None)  # Modified to return string
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name="invoice_data.json",
                mime="application/json"
            )
        
        # CSV export
        with col7:
            csv_data = export_data_to_csv(data, None)  # Modified to return string
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="invoice_data.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Error processing invoice: {str(e)}")
        st.info("Please make sure your file is not corrupted and try uploading again.")

    finally:
        # Clean up temporary file
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except Exception as e:
                st.warning(f"Could not delete temporary file: {str(e)}")

st.sidebar.markdown("""
## Instructions
1. Upload an invoice file (PDF or image format)
2. Wait for the file to be processed
3. Review the extracted data
4. Export results in JSON or CSV format

**Note**: All data is processed locally and no information is stored.
""")