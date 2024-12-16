-- create_database.sql

-- Crear la base de datos
CREATE DATABASE supplier_sync
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'es_ES.UTF-8'
    LC_CTYPE = 'es_ES.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;



-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Crear esquema principal
CREATE SCHEMA IF NOT EXISTS supplier_sync;

-- Configurar el path de búsqueda
SET search_path TO supplier_sync, public;

-- Crear tipos enumerados
CREATE TYPE document_status AS ENUM ('active', 'expired', 'pending_review');
CREATE TYPE document_type AS ENUM ('invoice', 'safety', 'tax', 'legal');

-- Crear tabla de proveedores
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_name VARCHAR(255) NOT NULL,
    ein VARCHAR(20),
    contact_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    country VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_supplier_ein UNIQUE (ein)
);

-- Crear tabla de documentos
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID NOT NULL REFERENCES suppliers(id),
    document_type document_type NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    mime_type VARCHAR(100),
    file_size BIGINT,
    hash_md5 VARCHAR(32),
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_document_supplier FOREIGN KEY (supplier_id) 
        REFERENCES suppliers(id) ON DELETE CASCADE
);

-- Crear tabla de facturas
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id),
    invoice_number VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    due_date DATE,
    currency VARCHAR(3) DEFAULT 'USD',
    subtotal_amount DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    total_amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    payment_terms VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_invoice_document FOREIGN KEY (document_id) 
        REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT uk_invoice_number UNIQUE (invoice_number, document_id)
);

-- Crear tabla de documentos de seguridad
CREATE TABLE safety_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id),
    document_type VARCHAR(50) NOT NULL,
    issue_date DATE,
    expiration_date DATE,
    issuing_authority VARCHAR(255),
    status document_status DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_safety_document FOREIGN KEY (document_id) 
        REFERENCES documents(id) ON DELETE CASCADE
);

-- Crear índices
CREATE INDEX idx_supplier_name ON suppliers(supplier_name);
CREATE INDEX idx_document_type ON documents(document_type);
CREATE INDEX idx_invoice_number ON invoices(invoice_number);
CREATE INDEX idx_invoice_date ON invoices(date);
CREATE INDEX idx_safety_status ON safety_documents(status);
CREATE INDEX idx_safety_expiration ON safety_documents(expiration_date);

-- Crear función para actualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Crear triggers para actualizar timestamps
CREATE TRIGGER update_supplier_modtime
    BEFORE UPDATE ON suppliers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_modtime
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_invoice_modtime
    BEFORE UPDATE ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_safety_document_modtime
    BEFORE UPDATE ON safety_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Crear vistas útiles
CREATE VIEW v_invoice_summary AS
SELECT 
    i.id,
    i.invoice_number,
    i.date,
    i.total_amount,
    i.status,
    s.supplier_name,
    s.ein
FROM invoices i
JOIN documents d ON i.document_id = d.id
JOIN suppliers s ON d.supplier_id = s.id;

CREATE VIEW v_expired_safety_documents AS
SELECT 
    sd.id,
    sd.document_type,
    sd.expiration_date,
    s.supplier_name,
    s.contact_name,
    s.email
FROM safety_documents sd
JOIN documents d ON sd.document_id = d.id
JOIN suppliers s ON d.supplier_id = s.id
WHERE sd.expiration_date < CURRENT_DATE
AND sd.status = 'active';

-- Crear roles y permisos básicos
CREATE ROLE supplier_sync_admin;
CREATE ROLE supplier_sync_user;

-- Asignar permisos
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA supplier_sync TO supplier_sync_admin;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA supplier_sync TO supplier_sync_user;