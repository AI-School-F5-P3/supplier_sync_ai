# SupplierSync AI

Sistema de gestión inteligente de documentos de proveedores que utiliza OCR y procesamiento de lenguaje natural para automatizar la extracción de información de facturas y documentos de seguridad.

## Estructura del Proyecto

``` 
supplier_sync/
│
├── docs/                      # Documentación del proyecto
│   └── briefings              # Briefing del Proyecto
│
├── scripts/                   # Scripts útiles
│   ├── create_database.py    # Script para crear la base de datos
│   ├── create_database.sql   # SQL para crear la base de datos
│   └── generate_test_data.py # Generador de datos de prueba
│
├── src/                      # Código fuente principal
│   ├── __init__.py
│   ├── config/              # Configuración
│   │   ├── __init__.py
│   │   └── settings.py      # Configuraciones del proyecto
│   │
│   ├── core/               # Lógica central
│   │   ├── __init__.py
│   │   ├── document_processor.py
│   │   └── database.py
│   │
│   ├── models/            # Modelos de datos
│   │   ├── __init__.py
│   │   └── invoice.py
│   │
│   └── utils/            # Utilidades
│       ├── __init__.py
│       └── helpers.py
│
├── tests/                # Tests
│   ├── __init__.py
│   ├── test_document_processor.py
│   └── test_database.py
│
├── data/                # Datos de ejemplo y recursos
│   ├── sample_invoices/
│   └── sample_safety_docs/
│
├── requirements.txt     # Dependencias del proyecto
├── setup.py            # Configuración de instalación
├── .env.example        # Ejemplo de variables de entorno
└── README.md           # Documentación principal
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
streamlit run src/app.py
```

2. Acceder a la aplicación web en `http://localhost:8501`

## Características

- Procesamiento automático de facturas mediante OCR
- Extracción inteligente de datos de documentos
- Interfaz web intuitiva
- Gestión de documentos de seguridad
- Exportación de datos en múltiples formatos
- Sistema de búsqueda avanzado

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
