import streamlit as st
import psycopg2
from psycopg2.extras import DictCursor
import tempfile
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json
from dataclasses import asdict

# Importar la clase DocumentProcessor del código anterior
from src.core.document_processor import DocumentProcessor, InvoiceData

class DatabaseManager:
    def __init__(self, db_params: Dict[str, str]):
        self.db_params = db_params
        self.create_tables()

    def get_connection(self):
        return psycopg2.connect(**self.db_params)

    def create_tables(self):
        """Crear las tablas necesarias si no existen"""
        commands = [
            """
            CREATE TABLE IF NOT EXISTS suppliers (
                id SERIAL PRIMARY KEY,
                supplier_name VARCHAR(255),
                ein VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                supplier_id INTEGER REFERENCES suppliers(id),
                document_type VARCHAR(50),
                file_name VARCHAR(255),
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id),
                invoice_number VARCHAR(100),
                date DATE,
                total_amount DECIMAL(15,2),
                tax_amount DECIMAL(15,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS safety_documents (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id),
                document_type VARCHAR(50),
                expiration_date DATE,
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for command in commands:
                    cur.execute(command)

    def save_invoice(self, invoice_data: InvoiceData, file_name: str) -> int:
        """Guardar datos de factura en la base de datos"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Insertar o actualizar proveedor
                cur.execute(
                    """
                    INSERT INTO suppliers (supplier_name)
                    VALUES (%s)
                    RETURNING id
                    """,
                    (invoice_data.supplier_name or 'Unknown Supplier',)
                )
                supplier_id = cur.fetchone()[0]

                # Insertar documento
                cur.execute(
                    """
                    INSERT INTO documents (supplier_id, document_type, file_name)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (supplier_id, 'invoice', file_name)
                )
                document_id = cur.fetchone()[0]

                # Insertar factura
                cur.execute(
                    """
                    INSERT INTO invoices (document_id, invoice_number, date, total_amount, tax_amount)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (document_id, 
                     invoice_data.invoice_number,
                     invoice_data.date,
                     invoice_data.total_amount,
                     invoice_data.tax_amount)
                )
                return cur.fetchone()[0]

    def get_all_invoices(self):
        """Obtener todas las facturas de la base de datos"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(
                    """
                    SELECT i.*, d.file_name, s.supplier_name
                    FROM invoices i
                    JOIN documents d ON i.document_id = d.id
                    JOIN suppliers s ON d.supplier_id = s.id
                    ORDER BY i.created_at DESC
                    """
                )
                return [dict(row) for row in cur.fetchall()]

def initialize_session_state():
    """Inicializar variables de estado de la sesión"""
    if 'processor' not in st.session_state:
        st.session_state.processor = DocumentProcessor()
    if 'db' not in st.session_state:
        # Configuración de la base de datos
        db_params = {
            'dbname': 'supplier_sync',
            'user': 'postgres',
            'password': 'your_password',  # Cambiar por tu contraseña
            'host': 'localhost',
            'port': '5432'
        }
        st.session_state.db = DatabaseManager(db_params)

def main():
    st.title("SupplierSync AI")
    initialize_session_state()

    # Sidebar para navegación
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Ir a", ["Procesar Documentos", "Ver Registros"])

    if page == "Procesar Documentos":
        show_upload_page()
    else:
        show_records_page()

def show_upload_page():
    st.header("Procesar Documentos")
    
    # Selector de tipo de documento
    doc_type = st.selectbox(
        "Tipo de Documento",
        ["Factura", "Documento de Seguridad"]
    )
    
    uploaded_file = st.file_uploader("Cargar documento", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{uploaded_file.name.split(".")[-1]}') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            if doc_type == "Factura":
                process_invoice(tmp_path, uploaded_file.name)
            else:
                process_safety_document(tmp_path, uploaded_file.name)
                
        finally:
            os.unlink(tmp_path)  # Eliminar archivo temporal

def process_invoice(file_path: str, original_filename: str):
    """Procesar y guardar factura"""
    with st.spinner('Procesando factura...'):
        # Extraer texto del documento
        text = st.session_state.processor.extract_text_from_pdf(file_path)
        
        # Extraer datos de la factura
        invoice_data = st.session_state.processor.extract_invoice_data(text)
        
        # Mostrar datos extraídos y permitir edición
        with st.form("invoice_form"):
            st.write("Datos extraídos (puedes editarlos si es necesario):")
            invoice_data.invoice_number = st.text_input("Número de Factura", value=invoice_data.invoice_number or "")
            invoice_data.date = st.date_input("Fecha", value=datetime.now() if not invoice_data.date else datetime.strptime(invoice_data.date, '%Y-%m-%d'))
            invoice_data.total_amount = st.number_input("Monto Total", value=invoice_data.total_amount or 0.0)
            invoice_data.tax_amount = st.number_input("Monto de Impuestos", value=invoice_data.tax_amount or 0.0)
            invoice_data.supplier_name = st.text_input("Nombre del Proveedor", value=invoice_data.supplier_name or "")
            
            submitted = st.form_submit_button("Guardar")
            
            if submitted:
                try:
                    # Guardar en la base de datos
                    invoice_id = st.session_state.db.save_invoice(invoice_data, original_filename)
                    st.success(f"Factura guardada exitosamente con ID: {invoice_id}")
                except Exception as e:
                    st.error(f"Error al guardar la factura: {str(e)}")

def process_safety_document(file_path: str, original_filename: str):
    """Procesar y guardar documento de seguridad"""
    st.write("Procesamiento de documentos de seguridad - En desarrollo")
    # Aquí irá la lógica para procesar documentos de seguridad

def show_records_page():
    """Mostrar página de registros"""
    st.header("Registros")
    
    # Pestañas para diferentes tipos de documentos
    tab1, tab2 = st.tabs(["Facturas", "Documentos de Seguridad"])
    
    with tab1:
        show_invoices_table()
    
    with tab2:
        st.write("Registros de documentos de seguridad - En desarrollo")

def show_invoices_table():
    """Mostrar tabla de facturas"""
    invoices = st.session_state.db.get_all_invoices()
    
    if not invoices:
        st.write("No hay facturas registradas")
        return
    
    # Convertir los datos para mostrarlos en una tabla
    invoice_data = []
    for inv in invoices:
        invoice_data.append({
            "ID": inv['id'],
            "Proveedor": inv['supplier_name'],
            "Número de Factura": inv['invoice_number'],
            "Fecha": inv['date'].strftime('%Y-%m-%d'),
            "Monto Total": f"${inv['total_amount']:,.2f}",
            "Impuestos": f"${inv['tax_amount']:,.2f}",
            "Archivo": inv['file_name']
        })
    
    st.table(invoice_data)

if __name__ == "__main__":
    main()