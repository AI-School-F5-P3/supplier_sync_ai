# SupplierSync AI

Sistema de gestión inteligente de documentos de proveedores que utiliza OCR y procesamiento de lenguaje natural para automatizar la extracción de información de facturas y documentos de seguridad.

## Estructura del Proyecto

``` 
supplier_sync/
│
├── docs/                                               # Documentación del proyecto
│   └── SupplierSyncAI_english_version.odt              # Briefing del Proyecto
│
├── scripts/                   # Scripts útiles
│   ├── generated_invoices/    # Facturas generadas para testing
│   ├── templates/             # Templates para la generación de documentos de testing
│   └── invoice_generator.py   # Generador automatizado de facturas de testing
│
├── src/                        # Código fuente principal
│   ├── __init__.py
│   │
│   ├── core/                   # Lógica central
│   │   ├── __init__.py
│   │   └── invoice_extraction.py
│   │
├── tests/                      # Tests
│   ├── __init__.py
│   ├── data_test/              #Documentación de testing    
│   ├──outputs/                 #Output de la app.py en formato json y csv
│   └── extraction_test.py      #Archivo de prueba del funcionamiento pytesseract ocr  
│
├── data/                # Datos de ejemplo y recursos
│   ├── sample_invoices/
│   └── sample_safety_docs/
│
├── requirements.txt     # Dependencias del proyecto
├── .env                 # Ejemplo de variables de entorno
└── README.md            # Documentación principal
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
