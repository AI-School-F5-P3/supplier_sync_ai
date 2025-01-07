# SupplierSync AI

Sistema de gestión inteligente de documentos de proveedores que utiliza OCR y procesamiento de lenguaje natural para automatizar la extracción de información de facturas y documentos de seguridad.

## Estructura del Proyecto

``` 
supplier_sync/
│
├── app.py                    # Main Streamlit application
├── requirements.txt          # Project dependencies
│
├── src/
│   ├── __init__.py
│   ├── processor/
│   │   ├── __init__.py
│   │   ├── document_processor.py   # DocumentProcessor class
│   │   ├── invoice_processor.py    # Invoice-specific processing
│   │   ├── safety_processor.py     # Safety document processing
│   │   ├── insurance_processor.py  # Insurance document processing
│   │   └── personal_processor.py   # Personal document processing
│   │
│   └── utils/
│       ├── __init__.py
│       ├── image_utils.py          # Image processing utilities
│       ├── text_utils.py           # Text processing utilities
│       └── export_utils.py         # Export functionality
│
└── tests/                    # Unit tests
|   ├── __init__.py
|   └── test_processor.py
|
├── docs/                                               # Project documentation
│   └── SupplierSyncAI_english_version.odt              # Project briefing
│
├── data/                # Example data and resources
│   ├── sample_invoices/
│   └── sample_safety_docs/

├── .gitignore           # Specifies files and directories to be excluded from version control
├── .env                 # Contains environment-specific configuration variables (e.g., API keys, database credentials)
├── venv                 # Virtual environment
└── README.md            # Main documentation


```

## Requisitos

- Python 3.8+
- PostgreSQL 12+
- Tesseract OCR
- Dependencias de Python (ver requirements.txt)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tuusuario/supplier_sync.git
cd supplier_sync
```

2. Crear un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Crear el archivo .env basado en .env.example y configurar las variables de entorno

5. Crear la base de datos:
```bash
python scripts/create_database.py
```

## Uso

1. Iniciar la aplicación:
```bash
streamlit run app.py
```

2. Acceder a la aplicación web en `http://localhost:8501`

## Características

- Procesamiento automático de facturas mediante OCR
- Extracción inteligente de datos de documentos
- Interfaz web intuitiva
- Gestión de documentos de seguridad - en progreso
- Exportación de datos en múltiples formatos
- Sistema de búsqueda avanzado - en progreso

## Desarrollo

Para configurar el entorno de desarrollo:

1. Instalar dependencias de desarrollo:
```bash
pip install -r requirements-dev.txt
```

2. Ejecutar tests:
```bash
pytest
```

## Contribuir

1. Fork del repositorio
2. Crear una rama para tu característica (`git checkout -b feature/AmazingFeature`)
3. Commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.
