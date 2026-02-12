import os
import sys
import logging
import requests
import io
import tempfile
import pytesseract
from PIL import Image
from typing import Dict
from fastapi import FastAPI, HTTPException
import uvicorn
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add current directory to path for backend imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.engine.web_scraper import WebScraper
from backend.storage.db_manager import DBManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WorkProof.Server")

app = FastAPI(title="WorkProof API")

# Scraper instance
scraper = WebScraper()
db = DBManager()

# Configure Tesseract path
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

class ScrapeRequest(BaseModel):
    url: str

def parse_ocr_text(text: str) -> Dict[str, str]:
    """
    Parse raw OCR text into key-value pairs using section-aware logic.
    """
    data = {}
    lines = text.splitlines()
    
    current_section = None
    current_sub_section = None
    last_field_key = None

    section_map = {
        "personal information": "Personal",
        "account information": "Account",
        "investment information": "Investment",
        "assets & last purchase": "Assets",
        "legal advisors": "Legal"
    }
    
    section_triggers = {
        "Full Name": "Personal",
        "Customer ID": "Account", 
        "Company": "Investment",
        "Department": "Assets",
        "Account Advisor": "Legal",
        "Assets Manager": "Legal",
        "Investment Advisor": "Legal", 
        "Insurance Manager": "Legal"
    }

    legal_sub_sections = [
        "Account Advisor", "Assets Manager", "Investment Advisor", "Insurance Manager"
    ]

    field_aliases = {
        "Personal": {
            "Full Name": "Full Name", "Gender": "Gender", "DOB": "DOB", 
            "Address 1": "Address 1", "Address 2": "Address 2", "City": "City", 
            "State": "State", "Postal": "Postal", "Country": "Country", 
            "Email": "Email", "Contact": "Contact", "SSN": "SSN"
        },
        "Account": {
            "Customer ID": "Customer ID", "A/C Type": "A/C Type", "A/C Name": "A/C Name",
            "A/C Number": "A/C Number", "IBAN": "IBAN", "BIC": "BIC", 
            "BTC Address": "BTC Address", "ETH Address": "ETH Address", 
            "LTC Address": "LTC Address", "CC No": "CC No", 
            "Last Txn Amount": "Last Txn Amount", "Last Txn Date": "Last Txn Date"
        },
        "Investment": {
            "Company": "Company", "BS": "BS", "EIN": "EIN", "Skill Description": "Skill Description",
            "ISIN": "ISIN", "Coupon": "Coupon", "Invested Amount": "Invested Amount", 
            "Maturity Date": "Maturity Date", "Bond Name": "Bond Name", "Bond Class": "Bond Class"
        },
        "Assets": {
            "Department": "Department", "EAN 13": "EAN 13", "Product Name": "Product Name", 
            "Unit Price": "Unit Price", "User": "User", "Purchase Token": "Purchase Token",
            "Buying IPv4": "Buying IPv4", "Buying IPv6": "Buying IPv6",
            "Type": "Type", "Model": "Model", "Manufacture": "Manufacture", "VIN": "VIN",
            "Beneficiary Identifier ID": "Beneficiary Identifier ID", "INS No": "INS No"
        },
        "Legal": {
            "Advisor ID": "Advisor ID", "Manager ID": "Manager ID", 
            "Name": "Name", "Contact": "Contact", "Address": "Address"
        }
    }

    for line in lines:
        line = line.strip()
        if not line: continue
        
        lower_line = line.lower()
        
        # Section Detection
        found_section = False
        for key, val in section_map.items():
            if key in lower_line:
                current_section = val
                current_sub_section = None
                last_field_key = None
                found_section = True
                break
        if found_section: continue
        
        # Implicit triggers
        for trigger, section in section_triggers.items():
            if line.lower().startswith(trigger.lower()):
                current_section = section
                break

        if current_section == "Legal":
            for sub in legal_sub_sections:
                if line.lower().startswith(sub.lower()):
                    current_sub_section = sub
                    last_field_key = None
                    found_section = True
                    break
        if found_section: continue
            
        # Field Parsing
        matched_field = False
        if current_section and current_section in field_aliases:
            aliases = field_aliases[current_section]
            
            if current_section == "Legal" and current_sub_section:
                for ocr_key, suffix_field in aliases.items():
                    if line.lower().startswith(ocr_key.lower()):
                        value = line[len(ocr_key):].strip().lstrip(':. ').strip()
                        full_field_name = f"{current_sub_section} - {suffix_field}"
                        data[full_field_name] = value
                        last_field_key = full_field_name
                        matched_field = True
                        break
            else:
                for ocr_key, target_field in aliases.items():
                    if line.lower().startswith(ocr_key.lower()):
                        value = line[len(ocr_key):].strip().lstrip(':. ').strip()
                        data[target_field] = value
                        last_field_key = target_field
                        matched_field = True
                        break
        
        if not matched_field and last_field_key:
            if len(line) > 1 and "---" not in line:
                data[last_field_key] += " " + line

    return data

async def process_image_url(url: str):
    """Download image and process with OCR"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        
        # Preprocessing
        img = img.convert('L')
        width, height = img.size
        img = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            img.save(tmp_file, format="PNG")
            tmp_path = tmp_file.name
        
        try:
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(Image.open(tmp_path), config=custom_config)
            return parse_ocr_text(text)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        logger.error(f"OCR Failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR Processing failed: {str(e)}")

@app.post("/api/scrape")
async def scrape_endpoint(request: ScrapeRequest):
    """
    Trigger scraping for a given URL and return structured data.
    """
    try:
        data = scraper.scrape_url(request.url)
        return {"status": "success", "data": data}
    except ValueError as ve:
        if "IMAGE_URL_DETECTED" in str(ve):
             logger.info(f"Image detected at {request.url}. Starting OCR...")
             data = await process_image_url(request.url)
             return {"status": "success", "data": data, "method": "ocr"}
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

# Serve frontend static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    logger.info("Starting WorkProof Server at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
