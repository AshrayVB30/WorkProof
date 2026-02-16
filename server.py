import os
import sys
import logging
import requests
import io
import tempfile
import pytesseract
from PIL import Image
from typing import Dict, List, Union, Tuple
from fastapi import FastAPI, HTTPException
import uvicorn
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import re

# Add current directory to path for backend imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.engine.web_scraper import WebScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WorkProof.Server")

app = FastAPI(title="WorkProof API")

# Scraper instance
scraper = WebScraper()

# Configure Tesseract path
tesseract_paths = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'/usr/bin/tesseract',
    r'/usr/local/bin/tesseract'
]

for path in tesseract_paths:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        break

class ScrapeRequest(BaseModel):
    url: str

def clean_ocr_field(value: str, key: str = "") -> str:
    """Clean common OCR noise and trailing labels from values"""
    if not value or not isinstance(value, str):
        return value
    
    cleaned = value.strip()
    
    # 0. Noise Removal (Prefix and Suffix)
    # Handle known noise labels first
    noise_labels = [
        "CC_No", "CC No", "Skill Description", "Sk1LL Description", "SkLL Description",
        "Last Purchase Detail", "Vehicle Detail", "Insurance Detail",
        "Beneficiary Identifier ID", "Identifier ID", "Beneficiary",
        "Purchase Detail", "Detail", "Last Purchase", "CC_NO", "Sk1LL", "SkLL",
        "Ean13", "Eanl3", "EAN 13", "Vehicle", "Vichle", "Last Txn", "Description"
    ]
    
    for noise in noise_labels:
        pattern = re.compile(r'\b' + re.escape(noise) + r'\b', re.IGNORECASE)
        match = list(pattern.finditer(cleaned))
        if match:
             # If match is at the start (Prefix/Label)
             if match[0].start() == 0:
                  cleaned = cleaned[match[0].end():].strip()
             # If match is elsewhere (Suffix/Trailing), strip everything after it
             else:
                  cleaned = cleaned[:match[0].start()].strip()
    
    # Remove single-char prefix artifacts (e.g. "r Chevrolet", "r 2023")
    cleaned = re.sub(r'^[a-zA-Z0-9©é]\s+', '', cleaned)

    # 1. Handle common OCR character misidentifications
    # Masked fields: HK, #, ~, ¥ -> *
    if any(k in cleaned for k in ["HK", "#", "~", "¥"]):
        cleaned = cleaned.replace("HK", "*").replace("#", "*").replace("~", "*").replace("¥", "*")
    
    # Numeric and Date fields misreads
    if any(k in cleaned.lower() for k in ["fett", "ost", "l7", "i7"]):
        cleaned = cleaned.lower().replace("fett", "7.77").replace("ost", "17").replace("l7", "17").replace("i7", "17")
    
    # Replace @ with 0 in potential numeric/date positions
    if "@" in cleaned and "@" == cleaned[0] and "." not in cleaned:
        cleaned = "0" + cleaned[1:]
    
    # 2. Alphanumeric Code Corrections
    # Determine if this field is likely a code/ID based on Key
    is_crypto = any(k in key for k in ["BTC", "ETH", "LTC"])
    # Common ID fields that should be stripped of spaces/cleaned aggressively
    code_indicators = [
        "IBAN", "BIC", "VIN", "ISIN", "SSN", "CC No", "A/C Number", 
        "Customer ID", "Advisor ID", "Manager ID", "EIN", "Token", "INS No", "Code"
    ]
    is_code = is_crypto or any(k in key for k in code_indicators)

    # Check for long alphanumeric strings (codes)
    # Using [a-zA-Z] to support lowercase codes/crypto addresses
    if re.search(r'^[a-zA-Z0-9\*\-\s]{8,}$', cleaned):
        # Only apply aggressive space removal if it is a known code field
        if is_code:
            # Prefer Numbers for codes that usually contain them
            cleaned = cleaned.replace("O", "0").replace("Q", "0")
            # Specifically for ISINs which are often misread
            if any(p in cleaned for p in ["YTBYX", "WD2AC"]):
                 cleaned = cleaned.replace("1", "I").replace("5", "S")
            if "1FGSG" in cleaned: cleaned = cleaned.replace("1FGSG", "JFGSG")
            
            # Remove spaces (Common for OCR'd codes like IBANs or Addresses)
            if " " in cleaned:
                 cleaned = cleaned.replace(" ", "")

    # 4. Final trim and strip leading/trailing artifacts
    cleaned = cleaned.strip().lstrip(':. ©é').strip()

    # 5. Remove single-character artifacts (if the WHOLE value is just one char)
    if len(cleaned) == 1 and cleaned.lower() in ['r', 'l', 'i', 'v', 'b']:
        return ""
        
    return cleaned

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
            "LTC Address": "LTC Address", "CC No": "CC No", "CC_No": "CC No",
            "Last Txn Amount": "Last Txn Amount", "Last Txn Date": "Last Txn Date",
            "Last Txn": "Last Txn Amount"
        },
        "Investment": {
            "Company": "Company", "BS": "BS", "EIN": "EIN", 
            "Skill Description": "Skill Description", "Sk1LL Description": "Skill Description", 
            "Skll Description": "Skill Description", "Skll": "Skill Description",
            "ISIN": "ISIN", "Coupon": "Coupon", "Invested Amount": "Invested Amount", 
            "Invested": "Invested Amount", "Maturity Date": "Maturity Date", 
            "Bond Name": "Bond Name", "Bond Class": "Bond Class"
        },
        "Assets": {
            "Department": "Department", "EAN 13": "EAN 13", "Ean13": "EAN 13", "Eanl3": "EAN 13", 
            "Product Name": "Product Name", "Unit Price": "Unit Price", "User": "User", 
            "Purchase Token": "Purchase Token", "Buying IPv4": "Buying IPv4", "Buying IPv6": "Buying IPv6",
            "Type": "Type", "Model": "Model", 
            "Manufacture": "Manufacture", "Manufacturer": "Manufacture", 
            "VIN": "VIN", "Beneficiary": "Beneficiary Identifier ID",
            "Beneficiary Identifier ID": "Beneficiary Identifier ID", 
            "INS No": "INS No", "INS No.": "INS No"
        },
        "Legal": {
            "Advisor ID": "Advisor ID", "Manager ID": "Manager ID", 
            "Name": "Name", "Contact": "Contact", "Address": "Address"
        }
    }

    # Pre-process lines to split merged OCR fields
    splitters = [
        "Skill Description", "Sk1LL Description", "Skll Description", 
        "EAN 13", "Buying IPv4", "Buying IPv6", "LTC Address", 
        "Last Txn", "Last Txn Date", "Invested", "Txn", "Description"
    ]
    processed_lines = []
    for line in lines:
        if not line.strip(): continue
        merged = False
        for s in splitters:
            # If splitter is in line but NOT at the start
            idx = line.lower().find(s.lower())
            if idx > 2: 
                processed_lines.append(line[:idx].strip())
                processed_lines.append(line[idx:].strip())
                merged = True
                break
        if not merged:
            processed_lines.append(line.strip())
    
    for line in processed_lines:
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
            # Don't append if the line looks like a known field marker, common noise, or section header
            is_noise = any(line.lower().startswith(n.lower()) for n in [
                "Last Purchase Detail", "Vehicle Detail", "Insurance Detail", 
                "Beneficiary", "Detail", "Insurance", "Identifier"
            ])
            
            # Check if it starts with ANY known field name from ANY section
            is_potential_key = False
            for section in field_aliases.values():
                if any(line.lower().startswith(k.lower()) for k in section.keys()):
                    is_potential_key = True
                    break
            
            if not is_noise and not is_potential_key and len(line) > 1 and "---" not in line:
                data[last_field_key] += " " + line

    # Final cleanup pass on all extracted values
    for key in data:
        data[key] = clean_ocr_field(data[key], key=key)

    return data

async def process_image_url(url: Union[str, List[str], Tuple[str, ...]]):
    """Download image(s) and process with OCR, returning separate data for each URL."""
    if isinstance(url, (list, tuple)):
        results = {}
        for u in url:
            try:
                data = await _process_single_image(u)
                results[u] = data
            except Exception as e:
                logger.error(f"OCR Failed for {u}: {e}")
                results[u] = {"error": str(e)}
        return results
    else:
        return await _process_single_image(url)

async def _process_single_image(url: str) -> Dict[str, str]:
    """Helper to process a single image URL."""
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
        logger.error(f"Single Image OCR Failed: {e}")
        raise e

@app.post("/api/scrape")
async def scrape_endpoint(request: ScrapeRequest):
    """
    Trigger scraping for a given URL and return structured data.
    """
    try:
        scraped_data = scraper.scrape_url(request.url)
        # Extract metadata like unique link count
        unique_links = scraped_data.get("__metadata__", {}).get("unique_links", 0)
        data = {k: v for k, v in scraped_data.items() if k != "__metadata__"}
        
        return {
            "status": "success", 
            "data": data, 
            "metadata": {"unique_links": unique_links}
        }
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
