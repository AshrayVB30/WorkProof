import requests
import pytesseract
from PIL import Image
import io
import os

# Set Tesseract path
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

url = "http://109.199.108.38:2069/?q=QUNUQVNUeHg4MGltZzAwMDcuanBlZzs1NjY7MU4wZ01rSEg"

def debug_ocr():
    print(f"Downloading image from {url}...")
    try:
        response = requests.get(url, timeout=30)
        img = Image.open(io.BytesIO(response.content))
        
        # Preprocessing
        print("Preprocessing image...")
        # 1. Grayscale
        img = img.convert('L')
        # 2. Resize (x2)
        width, height = img.size
        img = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        
        # Save debug image
        # img.save("debug_processed.png")
        
        print("Running OCR with --psm 6...")
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(img, config=custom_config)
        
        print("-" * 40)
        print("RAW OCR OUTPUT (Processed):")
        print("-" * 40)
        print(text)
        print("-" * 40)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_ocr()
