import streamlit as st
import tempfile
import os
from src.processor.document_processor import DocumentProcessor
from src.utils.export_utils import export_to_format

def main():
    st.set_page_config(page_title="Document Processor", layout="wide")
    st.title("Document Processor")

    # Document type selection
    doc_type = st.selectbox(
        "Select Document Type",
        ['invoice', 'safety', 'insurance', 'personal']
    )

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Supported formats: PDF, PNG, JPG, JPEG"
    )

    if uploaded_file:
        try:
            # Save uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_path = tmp.name

            # Process document
            processor = DocumentProcessor()
            with st.spinner('Processing document...'):
                data = processor.process_document(temp_path, doc_type)

            # Display results
            st.subheader("Extracted Information")
            
            # Create columns for better layout
            col1, col2 = st.columns(2)
            
            # Display general information
            with col1:
                for key, value in data.items():
                    if key != 'items' and value is not None:
                        st.text_input(key.replace('_', ' ').title(), value, disabled=True)

            # Display items if present
            if 'items' in data and data['items']:
                with col2:
                    st.subheader("Items")
                    st.table(data['items'])

            # Export options
            st.subheader("Export Options")
            export_format = st.radio("Select export format:", ('JSON', 'CSV'))
            
            if st.button("Download"):
                exported_data = export_to_format(data, export_format.lower())
                st.download_button(
                    label=f"Download {export_format}",
                    data=exported_data,
                    file_name=f"document_data.{export_format.lower()}",
                    mime=f"application/{export_format.lower()}"
                )

        except Exception as e:
            st.error(f"Error processing document: {str(e)}")

        finally:
            # Cleanup
            if 'temp_path' in locals():
                os.unlink(temp_path)

if __name__ == "__main__":
    main()