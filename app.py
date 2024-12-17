import sys
import subprocess
import os
from pathlib import Path
import streamlit as st
import psycopg2
from psycopg2.extras import DictCursor
import tempfile
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Import the updated DocumentProcessor
from src.core.document_processor import DocumentProcessor, InvoiceData, SafetyDocumentData

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.db_params = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }
        self.create_tables()

    def get_connection(self):
        return psycopg2.connect(**self.db_params)

    def create_tables(self):
        """Ensure necessary tables exist when app starts"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Verify if tables exist
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public'
                            AND table_name = 'suppliers'
                        )
                    """)
                    tables_exist = cur.fetchone()[0]
                    
                    if not tables_exist:
                        # If tables don't exist, run create_database.py
                        script_path = os.path.join(
                            os.path.dirname(os.path.abspath(__file__)), 
                            'scripts', 
                            'create_database.py'
                        )
                        subprocess.run([sys.executable, script_path], check=True)
                        print("Database tables created successfully")
                    else:
                        print("Database tables already exist")
        except Exception as e:
            print(f"Error checking/creating tables: {str(e)}")
            raise

    def get_or_create_supplier(self, supplier_name):
        """Get existing supplier or create a new one"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # First, try to find existing supplier
                cur.execute("SELECT id FROM suppliers WHERE supplier_name = %s", (supplier_name,))
                result = cur.fetchone()
                
                if result:
                    return result['id']
                
                # If not found, create new supplier
                cur.execute("""
                    INSERT INTO suppliers (supplier_name) 
                    VALUES (%s) 
                    RETURNING id
                """, (supplier_name,))
                
                supplier_id = cur.fetchone()['id']
                conn.commit()
                return supplier_id

    def save_invoice(self, invoice_data: InvoiceData, original_filename: str, file_content: str):
        """Save invoice to database"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Get or create supplier
                supplier_id = self.get_or_create_supplier(invoice_data.supplier_name)

                # Insert invoice
                cur.execute("""
                    INSERT INTO invoices (
                        supplier_id, supplier_name, invoice_number, file_name, file_content, 
                        date, due_date, currency, subtotal_amount, total_amount,
                            payment_terms, notes, tax_amount, bill_to, send_to
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    supplier_id, 
                    invoice_data.supplier_name,
                    invoice_data.invoice_number, 
                    original_filename, 
                    file_content,
                    invoice_data.issue_date, 
                    invoice_data.expiration_date,
                    invoice_data.currency,
                    invoice_data.subtotal_amount,
                    invoice_data.total_amount, 
                    invoice_data.payment_terms,
                    invoice_data.notes,                    
                    invoice_data.tax_amount,
                    invoice_data.bill_to,
                    invoice_data.sent_to,

                ))
                
                invoice_id = cur.fetchone()['id']
                conn.commit()
                return invoice_id

    def save_safety_document(self, safety_doc: SafetyDocumentData, original_filename: str, file_content: str):
        """Save safety document to database"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Get or create supplier
                supplier_id = self.get_or_create_supplier(safety_doc.supplier_name)

                # Insert safety document
                cur.execute("""
                    INSERT INTO safety_documents (
                        supplier_id, document_type, file_name, file_content, 
                        issue_date, expiration_date, issuing_authority, 
                        supplier_name, status, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    supplier_id, 
                    safety_doc.document_type or 'Unspecified', 
                    original_filename, 
                    file_content,
                    safety_doc.issue_date, 
                    safety_doc.expiration_date,
                    safety_doc.issuing_authority,
                    safety_doc.supplier_name,
                    safety_doc.status or 'review',
                    safety_doc.notes
                ))
                
                doc_id = cur.fetchone()['id']
                conn.commit()
                return doc_id

    def get_all_invoices(self):
        """Retrieve all invoices"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM invoices
                    ORDER BY date DESC
                """)
                return cur.fetchall()

    def get_all_safety_documents(self):
        """Retrieve all safety documents"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT * FROM safety_documents
                    ORDER BY issue_date DESC
                """)
                return cur.fetchall()

def initialize_session_state():
    """Initialize session state variables"""
    if 'processor' not in st.session_state:
        st.session_state.processor = DocumentProcessor()
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager()

def main():
    st.title("SupplierSync AI")
    initialize_session_state()

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Process Documents", "View Records"])

    if page == "Process Documents":
        show_upload_page()
    else:
        show_records_page()

def show_upload_page():
    st.header("Process Documents")
    
    # Document type selector
    doc_type = st.selectbox(
        "Document Type",
        ["Invoice", "Safety Document"]
    )
    
    uploaded_file = st.file_uploader("Upload document", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{uploaded_file.name.split(".")[-1]}') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            if doc_type == "Invoice":
                process_invoice(tmp_path, uploaded_file.name)
            else:
                process_safety_document(tmp_path, uploaded_file.name)
                
        finally:
            os.unlink(tmp_path)  # Delete temporary file

def process_invoice(file_path: str, original_filename: str):
    """Process and save invoice"""
    with st.spinner('Processing invoice...'):
        # Extract text from document
        text = st.session_state.processor.extract_text_from_pdf(file_path)
        
        # Extract invoice data
        invoice_data = st.session_state.processor.extract_invoice_data(text)
        
        # Show extracted data and allow editing
        with st.form("invoice_form"):
            st.write("Extracted Invoice Data (you can edit if needed):")
            invoice_data.supplier_name = st.text_input("Supplier Name", value=invoice_data.supplier_name or "")
            invoice_data.invoice_number = st.text_input("Invoice Number", value=invoice_data.invoice_number or "")
            invoice_data.date = st.date_input("Date", value=datetime.strptime(invoice_data.date, '%Y-%m-%d') if invoice_data.date else datetime.now())
            invoice_data.total_amount = st.number_input("Total Amount", value=invoice_data.total_amount or 0.0)
            invoice_data.tax_amount = st.number_input("Tax Amount", value=invoice_data.tax_amount or 0.0)
            
            submitted = st.form_submit_button("Save")
            
            if submitted:
                try:
                    # Convert date to string for database
                    invoice_data.date = invoice_data.date.strftime('%Y-%m-%d') if isinstance(invoice_data.date, datetime) else invoice_data.date
                    
                    # Save to database with scanned content
                    invoice_id = st.session_state.db.save_invoice(invoice_data, original_filename, text)
                    st.success(f"Invoice saved successfully with ID: {invoice_id}")
                except Exception as e:
                    st.error(f"Error saving invoice: {str(e)}")

def process_safety_document(file_path: str, original_filename: str):
    """Process and save safety document"""
    with st.spinner('Processing safety document...'):
        # Extract text from document
        text = st.session_state.processor.extract_text_from_pdf(file_path)
        
        # Extract safety document data
        safety_doc_data = st.session_state.processor.extract_safety_document_data(text)
        
        # Show extracted data and allow editing
        with st.form("safety_doc_form"):
            st.write("Extracted Safety Document Data (you can edit if needed):")
            safety_doc_data.supplier_name = st.text_input("Supplier Name", value=safety_doc_data.supplier_name or "")
            safety_doc_data.document_category = st.selectbox(
                "Document Category", 
                ["Compliance", "Safety Certificate", "Quality Assurance", "Other"],
                index=0 if not safety_doc_data.document_category else 
                       ["Compliance", "Safety Certificate", "Quality Assurance", "Other"].index(safety_doc_data.document_category)
            )
            safety_doc_data.date = st.date_input(
                "Issue Date", 
                value=datetime.strptime(safety_doc_data.date, '%Y-%m-%d') if safety_doc_data.date else datetime.now()
            )
            safety_doc_data.expiration_date = st.date_input(
                "Expiration Date", 
                value=datetime.strptime(safety_doc_data.expiration_date, '%Y-%m-%d') if safety_doc_data.expiration_date else None
            )
            safety_doc_data.issuing_authority = st.text_input("Issuing Authority", value=safety_doc_data.issuing_authority or "")
            safety_doc_data.status = st.selectbox(
                "Status", 
                ["active", "expired", "pending"],
                index=0 if not safety_doc_data.status else ["active", "expired", "pending"].index(safety_doc_data.status)
            )
            
            submitted = st.form_submit_button("Save")
            
            if submitted:
                try:
                    # Convert dates to string for database
                    safety_doc_data.date = safety_doc_data.date.strftime('%Y-%m-%d') if isinstance(safety_doc_data.date, datetime) else safety_doc_data.date
                    safety_doc_data.expiration_date = safety_doc_data.expiration_date.strftime('%Y-%m-%d') if isinstance(safety_doc_data.expiration_date, datetime) else safety_doc_data.expiration_date
                    
                    # Save to database with scanned content
                    doc_id = st.session_state.db.save_safety_document(safety_doc_data, original_filename, text)
                    st.success(f"Safety document saved successfully with ID: {doc_id}")
                except Exception as e:
                    st.error(f"Error saving safety document: {str(e)}")

def show_records_page():
    """Show records page"""
    st.header("Records")
    
    # Tabs for different document types
    tab1, tab2 = st.tabs(["Invoices", "Safety Documents"])
    
    with tab1:
        show_invoices_table()
    
    with tab2:
        show_safety_documents_table()

def show_invoices_table():
    """Show invoices table"""
    invoices = st.session_state.db.get_all_invoices()
    
    if not invoices:
        st.write("No invoices registered")
        return
    
    # Convert data for table display
    invoice_data = []
    for inv in invoices:
        invoice_data.append({
            "ID": inv['id'],
            "Supplier": inv['supplier_name'],
            "Invoice Number": inv['invoice_number'],
            "Date": inv['date'].strftime('%Y-%m-%d') if inv['date'] else '',
            "Total Amount": f"${inv['total_amount']:,.2f}",
            "Tax": f"${inv['tax_amount']:,.2f}",
            "File": inv['file_name']
        })
    
    st.table(invoice_data)

def show_safety_documents_table():
    """Show safety documents table"""
    safety_docs = st.session_state.db.get_all_safety_documents()
    
    if not safety_docs:
        st.write("No safety documents registered")
        return
    
    # Convert data for table display
    safety_doc_data = []
    for doc in safety_docs:
        safety_doc_data.append({
            "ID": doc['id'],
            "Supplier": doc['supplier_name'],
            "Document Type": doc['document_type'],
            "Issue Date": doc['issue_date'].strftime('%Y-%m-%d') if doc['issue_date'] else '',
            "Expiration Date": doc['expiration_date'].strftime('%Y-%m-%d') if doc['expiration_date'] else '',
            "Issuing Authority": doc['issuing_authority'],
            "Status": doc['status'],
            "File": doc['file_name']
        })
    
    st.table(safety_doc_data)

if __name__ == "__main__":
    main()