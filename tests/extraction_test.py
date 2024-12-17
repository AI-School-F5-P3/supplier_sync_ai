import pytesseract

# Configurar manualmente la ruta al archivo de Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configurar la variable TESSDATA_PREFIX directamente en Python
import os
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

# Verificar si pytesseract está funcionando correctamente
from PIL import Image

try:
    imagen = Image.open('tests/test2.png')  # Asegúrate de que esta imagen exista
    texto = pytesseract.image_to_string(imagen)
    print("Texto extraído:", texto)
except Exception as e:
    print(f"Error: {e}")
