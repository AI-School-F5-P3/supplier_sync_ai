# scripts/create_database.py

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import random
from datetime import datetime, timedelta
from faker import Faker
from psycopg2.extras import DictCursor
import uuid
import shutil

# Configurar Faker para datos en inglés
fake = Faker(['en_US'])

def create_database():
    """Crear la base de datos y las tablas"""
    load_dotenv()

    # Conexión inicial para crear la base de datos
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            # Verificar si la base de datos existe
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'supplier_sync'")
            exists = cur.fetchone()
            
            if not exists:
                cur.execute("CREATE DATABASE supplier_sync")
                print("Base de datos creada exitosamente")
            else:
                print("La base de datos ya existe")

    finally:
        conn.close()

    # Ejecutar el script SQL
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
        database="supplier_sync"
    )

    try:
        with conn.cursor() as cur:
            # Leer y ejecutar el script SQL
            sql_file = Path(__file__).parent / "create_database.sql"
            with open(sql_file, 'r', encoding='utf-8') as f:
                cur.execute(f.read())
            conn.commit()
            print("Estructura de la base de datos creada exitosamente")

    except Exception as e:
        print(f"Error al crear la estructura de la base de datos: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def generate_sample_files():
    """Generar archivos de ejemplo"""
    data_dir = Path(__file__).parent.parent / "data"
    sample_invoices_dir = data_dir / "sample_invoices"
    sample_safety_dir = data_dir / "sample_safety_docs"

    # Crear directorios si no existen
    for dir_path in [sample_invoices_dir, sample_safety_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Generar facturas de ejemplo
    for i in range(5):
        source = Path(__file__).parent / "templates" / "invoice_template.pdf"
        if source.exists():
            shutil.copy(source, sample_invoices_dir / f"invoice_{i+1}.pdf")

    # Generar documentos de seguridad de ejemplo
    for i in range(3):
        source = Path(__file__).parent / "templates" / "safety_doc_template.pdf"
        if source.exists():
            shutil.copy(source, sample_safety_dir / f"safety_doc_{i+1}.pdf")

def generate_supplier_data():
    """Generar datos de prueba para la tabla suppliers"""
    suppliers = []
    for _ in range(10):
        supplier = {
            'supplier_name': fake.company(),
            'ein': f'{random.randint(10,99)}-{random.randint(1000000,9999999)}',
            'contact_name': fake.name(),
            'email': fake.company_email(),
            'phone': fake.phone_number(),
            'address': fake.address(),
            'country': 'España',
            'status': random.choice(['active', 'inactive', 'pending'])
        }
        suppliers.append(supplier)
    return suppliers

def generate_document_data(supplier_ids, doc_type):
    """Generar datos de prueba para la tabla documents"""
    documents = []
    base_path = f"data/sample_{'invoices' if doc_type == 'invoice' else 'safety_docs'}"
    
    for supplier_id in supplier_ids:
        num_docs = random.randint(1, 3)
        for i in range(num_docs):
            doc_number = random.randint(1, 5 if doc_type == 'invoice' else 3)
            documents.append({
                'supplier_id': supplier_id,
                'document_type': doc_type,
                'file_name': f"{'invoice' if doc_type == 'invoice' else 'safety_doc'}_{doc_number}.pdf",
                'file_path': f"{base_path}/{'invoice' if doc_type == 'invoice' else 'safety_doc'}_{doc_number}.pdf",
                'mime_type': 'application/pdf',
                'file_size': random.randint(100000, 1000000),
                'hash_md5': uuid.uuid4().hex[:32]
            })
    return documents

def generate_invoice_data(document_ids):
    """Generar datos de prueba para la tabla invoices"""
    invoices = []
    for doc_id in document_ids:
        date = fake.date_between(start_date='-1y', end_date='today')
        total = round(random.uniform(1000, 50000), 2)
        tax = round(total * 0.21, 2)  # 21% IVA
        subtotal = round(total - tax, 2)
        
        invoices.append({
            'document_id': doc_id,
            'invoice_number': f"INV-{fake.unique.random_number(digits=6)}",
            'date': date,
            'due_date': date + timedelta(days=30),
            'currency': 'EUR',
            'subtotal_amount': subtotal,
            'tax_amount': tax,
            'total_amount': total,
            'status': random.choice(['pending', 'paid', 'overdue']),
            'payment_terms': 'Net 30',
            'notes': fake.text(max_nb_chars=200)
        })
    return invoices

def generate_safety_document_data(document_ids):
    """Generar datos de prueba para la tabla safety_documents"""
    safety_docs = []
    doc_types = ['Certificado ISO', 'Evaluación de Riesgos', 'Plan de Prevención']
    
    for doc_id in document_ids:
        issue_date = fake.date_between(start_date='-2y', end_date='-1y')
        safety_docs.append({
            'document_id': doc_id,
            'document_type': random.choice(doc_types),
            'issue_date': issue_date,
            'expiration_date': issue_date + timedelta(days=365),
            'issuing_authority': fake.company(),
            'status': random.choice(['active', 'expired', 'pending_review']),
            'notes': fake.text(max_nb_chars=200)
        })
    return safety_docs

def generate_test_data():
    """Generar datos de prueba para la base de datos"""
    load_dotenv()

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
        database="supplier_sync"
    )

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Generar y insertar proveedores
            suppliers = generate_supplier_data()
            supplier_ids = []
            for supplier in suppliers:
                cur.execute("""
                    INSERT INTO supplier_sync.suppliers 
                    (supplier_name, ein, contact_name, email, phone, address, country, status)
                    VALUES (%(supplier_name)s, %(ein)s, %(contact_name)s, %(email)s, 
                            %(phone)s, %(address)s, %(country)s, %(status)s)
                    RETURNING id
                """, supplier)
                supplier_ids.append(cur.fetchone()['id'])

            # Generar y insertar documentos de facturas
            invoice_docs = generate_document_data(supplier_ids, 'invoice')
            invoice_doc_ids = []
            for doc in invoice_docs:
                cur.execute("""
                    INSERT INTO supplier_sync.documents 
                    (supplier_id, document_type, file_name, file_path, mime_type, file_size, hash_md5)
                    VALUES (%(supplier_id)s, %(document_type)s, %(file_name)s, %(file_path)s,
                            %(mime_type)s, %(file_size)s, %(hash_md5)s)
                    RETURNING id
                """, doc)
                invoice_doc_ids.append(cur.fetchone()['id'])

            # Generar y insertar facturas
            invoices = generate_invoice_data(invoice_doc_ids)
            for invoice in invoices:
                cur.execute("""
                    INSERT INTO supplier_sync.invoices 
                    (document_id, invoice_number, date, due_date, currency,
                    subtotal_amount, tax_amount, total_amount, status, payment_terms, notes)
                    VALUES (%(document_id)s, %(invoice_number)s, %(date)s, %(due_date)s,
                            %(currency)s, %(subtotal_amount)s, %(tax_amount)s, %(total_amount)s,
                            %(status)s, %(payment_terms)s, %(notes)s)
                """, invoice)

            # Generar y insertar documentos de seguridad
            safety_docs = generate_document_data(supplier_ids, 'safety')
            safety_doc_ids = []
            for doc in safety_docs:
                cur.execute("""
                    INSERT INTO supplier_sync.documents 
                    (supplier_id, document_type, file_name, file_path, mime_type, file_size, hash_md5)
                    VALUES (%(supplier_id)s, %(document_type)s, %(file_name)s, %(file_path)s,
                            %(mime_type)s, %(file_size)s, %(hash_md5)s)
                    RETURNING id
                """, doc)
                safety_doc_ids.append(cur.fetchone()['id'])

            # Generar y insertar documentos de seguridad
            safety_records = generate_safety_document_data(safety_doc_ids)
            for record in safety_records:
                cur.execute("""
                    INSERT INTO supplier_sync.safety_documents 
                    (document_id, document_type, issue_date, expiration_date,
                    issuing_authority, status, notes)
                    VALUES (%(document_id)s, %(document_type)s, %(issue_date)s, %(expiration_date)s,
                            %(issuing_authority)s, %(status)s, %(notes)s)
                """, record)

            conn.commit()
            print("Datos de prueba generados exitosamente")

    except Exception as e:
        print(f"Error al generar datos de prueba: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_database()
    generate_sample_files()
    generate_test_data()