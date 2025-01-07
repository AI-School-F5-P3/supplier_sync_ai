import cv2
import numpy as np
from PIL import Image

def preprocess_image(image):
    """Enhanced image preprocessing"""
    try:
        if isinstance(image, str):
            img = cv2.imread(image)
        elif isinstance(image, Image.Image):
            img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            raise ValueError("Invalid image input type")

        if img is None:
            raise ValueError("Could not process image")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply dilation to connect text components
        kernel = np.ones((1,1), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(dilated)
        
        return denoised
        
    except Exception as e:
        raise ValueError(f"Error preprocessing image: {str(e)}")