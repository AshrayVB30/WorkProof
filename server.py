import os
# Bypassing regressions in Paddle 3.3.0 on Windows
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_enable_new_ir_api'] = '0'
os.environ['FLAGS_enable_pir_in_executor'] = '0'
os.environ['FLAGS_new_executor'] = '0'

import sys
import paddle
paddle.device.set_device('cpu')
paddle.set_flags({
    'FLAGS_use_mkldnn': 0,
    'FLAGS_use_onednn': 0,
    'FLAGS_enable_pir_api': 0
})

import logging
import requests
import io
import tempfile
from typing import Dict, List, Union, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image
import numpy as np
import cv2
import re

# ✅ PaddleOCR
from paddleocr import PaddleOCR

# Add current directory to path for backend imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.engine.web_scraper import WebScraper

# ---------------------------------------------------
# Logging
# ---------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WorkProof.Server")

app = FastAPI(title="WorkProof API")
scraper = WebScraper()

# ---------------------------------------------------
# Initialize PaddleOCR ONCE (important)
# ---------------------------------------------------
ocr_engine = PaddleOCR(
    use_textline_orientation=True,
    lang='en'
)

# ---------------------------------------------------
# Request Model
# ---------------------------------------------------
class ScrapeRequest(BaseModel):
    url: str

# ---------------------------------------------------
# OCR USING PADDLE
# ---------------------------------------------------
def extract_text_with_paddle(image: Image.Image) -> str:
    try:
        img_np = np.array(image)

        # If grayscale convert to BGR
        if len(img_np.shape) == 2:
            img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)

        result = ocr_engine.predict(img_np)

        if not result:
            return ""

        lines = []

        for res in result:
            # Handle PaddleX OCRResult (which behaves like a dict)
            if hasattr(res, 'get'):
                texts = res.get('rec_texts', [])
                scores = res.get('rec_scores', [])
                for text, confidence in zip(texts, scores):
                    if confidence > 0.4:
                        lines.append(text)
            # Fallback for standard PaddleOCR result [[bbox, (text, conf)], ...]
            elif isinstance(res, list):
                for line in res:
                    if len(line) >= 2 and isinstance(line[1], (tuple, list)):
                        text, confidence = line[1]
                        if confidence > 0.4:
                            lines.append(text)

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return ""

# ---------------------------------------------------
# OCR CLEANING UTILITY
# ---------------------------------------------------
def clean_ocr_field(value: str, field_name: str) -> str:
    if not value:
        return ""
    
    # Remove common OCR artifacts
    cleaned = value.strip().replace('|', '').replace('[', '').replace(']', '')
    
    # Field specific cleaning
    field_lower = field_name.lower()
    if field_lower == "dob" or "date" in field_lower:
        # Keep alphanumeric and common separators for dates
        cleaned = re.sub(r'[^0-9a-zA-Z/\-\s]', '', cleaned)
    elif "amount" in field_lower or "price" in field_lower or "coupon" in field_lower:
        # Keep digits, dots, and common currency/number chars
        cleaned = re.sub(r'[^0-9.]', '', cleaned)
    elif "contact" in field_lower or "phone" in field_lower:
        # Keep digits, common phone symbols, and 'x' for masks
        cleaned = re.sub(r'[^0-9+\-\s()xX]', '', cleaned)
        
    return cleaned.strip()

# ---------------------------------------------------
# KNOWN FIELDS & SECTION HEADERS
# ---------------------------------------------------
KNOWN_FIELDS = [
    "Full Name", "Gender", "DOB", "SSN", "Address 1", "Address 2", "City", "State", "Postal", "Country", 
    "Email", "Contact", "Customer ID", "Account Type", "Account Name", "Account Number", "IBAN", "BIC", 
    "BTC Address", "ETH Address", "LTC Address", "CC No", "Last Txn Amount", "Last Txn Date", 
    "Account Status", "Account Currency", "Company", "BS", "EIN", "Skill Description", "ISIN", 
    "Coupon", "Invested Amount", "Maturity Date", "Bond Name", "Bond Class", "Department", "Ean13", 
    "Product Name", "Unit Price", "User", "Purchase Token", "Buying IPv4", "Buying IPv6", 
    "Purchase Status", "Purchase Category", "Type", "Model", "Manufacturer", "VIN", 
    "Beneficiary Identifier ID", "INS No", "Insurance Status", "Account Advisor - Advisor ID", 
    "Account Advisor - Name", "Account Advisor - Contact", "Account Advisor - Address", 
    "Assets Manager - Advisor ID", "Assets Manager - Name", "Assets Manager - Contact", 
    "Assets Manager - Address", "Investment Advisor - Manager ID", "Investment Advisor - Name", 
    "Investment Advisor - Contact", "Investment Advisor - Address", "Insurance Manager - Manager ID", 
    "Insurance Manager - Name", "Insurance Manager - Contact", "Insurance Manager - Address",
    "A/c Name", "A/C Name", "A/c Number", "A/C Number", "A/c Type", "A/C Type", "CC_No", 
    "INS No.", "IN", "VIN No.", "Total Amount", "Price", "Dob", "Beneficiary", "Identifier ID",
    "Skll Description", "SKLL Description", "Skill Description",
    "Advisor ID", "Manager ID", "Name", "Contact", "Address", "IPv6", "IPv4"
]

# Define mapping from possible field labels (aliases) to canonical schema keys
ALIAS_MAP = {
    "A/c Name": "Account Name", "A/C Name": "Account Name",
    "A/c Number": "Account Number", "A/C Number": "Account Number",
    "A/c Type": "Account Type", "A/C Type": "Account Type",
    "CC_No": "CC No",
    "INS No.": "INS No",
    "IN": "VIN", "VIN No.": "VIN",
    "Dob": "DOB",
    "Total Amount": "Last Txn Amount", "Price": "Unit Price",
    "Beneficiary": "Beneficiary Identifier ID", "Identifier ID": "Beneficiary Identifier ID",
    "Skll Description": "Skill Description", "SKLL Description": "Skill Description",
    "Purchase Token": "Purchase Token", "purchase Token": "Purchase Token",
    "IPv4": "Buying IPv4", "IPv6": "Buying IPv6"
}

SECTION_HEADERS = [
    "Personal Information", "Account Information", "Investment Information", 
    "Assets & Last Purchase Information", "Last Purchase Detail", "Vehicle Detail", 
    "Insurance Detail", "Legal Advisors", "Account Advisor", "Assets Manager", 
    "Investment Advisor", "Insurance Manager", "Detail", "Insurance"
]

def nest_data(flat_data: Dict[str, str]) -> Dict:
    """Transforms flat field-value pairs into the 64-field nested schema with alias support"""

    def g(key, default=""):
        # Case-insensitive lookup with alias support
        key_lower = key.lower()
        
        # 1. Try exact/case-insensitive match for the primary key
        for k, v in flat_data.items():
            if k.lower() == key_lower:
                return v
        
        # 2. Check for aliases that map to this key
        for alias, canonical in ALIAS_MAP.items():
            if canonical.lower() == key_lower:
                # If alias is found in flat_data, return its value
                for k, v in flat_data.items():
                    if k.lower() == alias.lower():
                        return v
        return default

    return {
        "personal_information": {
            "full_name": g("Full Name"),
            "gender": g("Gender"),
            "dob": g("DOB"),
            "ssn": g("SSN"),
            "address_1": g("Address 1"),
            "address_2": g("Address 2"),
            "city": g("City"),
            "state": g("State"),
            "postal": g("Postal"),
            "country": g("Country"),
            "email": g("Email"),
            "contact": g("Contact")
        },
        "account_information": {
            "customer_id": g("Customer ID"),
            "account_type": g("Account Type"),
            "account_name": g("Account Name"),
            "account_number": g("Account Number"),
            "iban": g("IBAN"),
            "bic": g("BIC"),
            "btc_address": g("BTC Address"),
            "eth_address": g("ETH Address"),
            "ltc_address": g("LTC Address"),
            "cc_no": g("CC No"),
            "last_txn_amount": g("Last Txn Amount"),
            "last_txn_date": g("Last Txn Date"),
            "account_status": g("Account Status"),
            "account_currency": g("Account Currency")
        },
        "investment_information": {
            "company": g("Company"),
            "bs": g("BS"),
            "ein": g("EIN"),
            "skill_description": g("Skill Description"),
            "isin": g("ISIN"),
            "coupon": g("Coupon"),
            "invested_amount": g("Invested Amount"),
            "maturity_date": g("Maturity Date"),
            "bond_name": g("Bond Name"),
            "bond_class": g("Bond Class")
        },
        "assets_last_purchase_information": {
            "department": g("Department"),
            "ean13": g("Ean13"),
            "product_name": g("Product Name"),
            "unit_price": g("Unit Price"),
            "user": g("User"),
            "purchase_token": g("Purchase Token"),
            "buying_ipv4": g("Buying IPv4"),
            "buying_ipv6": g("Buying IPv6"),
            "purchase_status": g("Purchase Status"),
            "purchase_category": g("Purchase Category")
        },
        "vehicle_detail": {
            "type": g("Type"),
            "model": g("Model"),
            "manufacturer": g("Manufacturer"),
            "vin": g("VIN")
        },
        "insurance_detail": {
            "beneficiary_identifier_id": g("Beneficiary Identifier ID"),
            "ins_no": g("INS No"),
            "insurance_status": g("Insurance Status")
        },
        "legal_advisors": {
            "account_advisor": {
                "advisor_id": g("Account Advisor - Advisor ID"),
                "name": g("Account Advisor - Name"),
                "contact": g("Account Advisor - Contact"),
                "address": g("Account Advisor - Address")
            },
            "assets_manager": {
                "advisor_id": g("Assets Manager - Advisor ID"),
                "name": g("Assets Manager - Name"),
                "contact": g("Assets Manager - Contact"),
                "address": g("Assets Manager - Address")
            },
            "investment_advisor": {
                "manager_id": g("Investment Advisor - Manager ID"),
                "name": g("Investment Advisor - Name"),
                "contact": g("Investment Advisor - Contact"),
                "address": g("Investment Advisor - Address")
            },
            "insurance_manager": {
                "manager_id": g("Insurance Manager - Manager ID"),
                "name": g("Insurance Manager - Name"),
                "contact": g("Insurance Manager - Contact"),
                "address": g("Insurance Manager - Address")
            }
        }
    }

# ---------------------------------------------------
# PARSER (Improved Context-Aware & Multi-line Support)
# ---------------------------------------------------
def parse_ocr_text(text: str) -> Dict[str, str]:
    data = {}
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Keywords that should never be treated as values
    SKIPPABLE_HEADERS = set([h.lower() for h in SECTION_HEADERS] + ["detail", "information", "beneficiary", "insurance"])
    STOP_LABELS = sorted(list(set([f.lower() for f in KNOWN_FIELDS] + [a.lower() for a in ALIAS_MAP.keys()] + 
                      ["name", "contact", "address", "advisor id", "manager id", "identifier id"])), key=len, reverse=True)

    def should_skip(line):
        l_low = line.lower()
        return l_low in SKIPPABLE_HEADERS or len(l_low) < 2

    def should_stop(line, val_parts=None):
        l_low = line.strip().lower()
        if not l_low:
            return False
            
        # 1. Advisor Headers MUST ALWAYS stop collection (strong boundaries)
        if l_low in [h.lower() for h in ["account advisor", "assets manager", "investment advisor", "insurance manager"]]:
            return True
        
        # 2. General Section Headers only stop if we already have a value
        # But we must be careful not to stop on values that contain words like "Personal"
        if l_low in [h.lower() for h in SECTION_HEADERS] or l_low in SKIPPABLE_HEADERS:
            if val_parts and len(val_parts) > 0:
                return True
            return False 
            
        if len(l_low) < 2:
            return False 
        
        # 3. Label Check: Stop if the line is a label or starts with one
        for f in sorted(KNOWN_FIELDS + list(ALIAS_MAP.keys()) + ["advisor id", "manager id", "name", "contact", "address"], key=len, reverse=True):
            f_low = f.lower()
            if l_low == f_low:
                return True
            if l_low.startswith(f_low):
                # Check character immediately after the label
                if len(l_low) > len(f_low):
                    next_char = l_low[len(f_low)]
                    if next_char in [' ', ':', '|', '-']:
                        return True
                else:
                    # Exactly matches
                    return True
                
        return False

    # ---------------------------------------------------
    # LINE SPLITTING PRE-PROCESSOR
    # ---------------------------------------------------
    final_lines = []
    # Labels that might be on the same line as a value (like EIN/Skill Description)
    # We AVOID adding generic words like 'name' here to prevent splitting 'Full Name'
    SPLIT_LABELS = [
        "skill description", "skll description", "isin", "coupon", "ein", "ipv6", "ipv4"
    ]

    for line in [l.strip() for l in text.splitlines() if l.strip()]:
        l_low = line.lower()
        found_split = False
        
        # Split on labels that ARE NOT at the start (intra-line splitting)
        for label in SPLIT_LABELS:
            idx = l_low.find(label)
            # If label is present and NOT at start
            if idx > 1 and (l_low[idx-1] in [' ', ':', '|', '-']):
                # Special cases for fields that often follow values
                if label in ["skill description", "skll description", "isin", "coupon", "name", "contact", "address", "company"]:
                    part1 = line[:idx].strip()
                    part2 = line[idx:].strip()
                    if part1: final_lines.append(part1)
                    if part2: final_lines.append(part2)
                    found_split = True
                    break
        
        if not found_split:
            final_lines.append(line)
    
    lines = final_lines
    
    # Sort KNOWN_FIELDS by length (desc) for matching logic
    FIELDS_DESC = sorted(KNOWN_FIELDS, key=len, reverse=True)


    current_section = None
    i = 0
    while i < len(lines):
        line = lines[i]
        line_low = line.lower()
        
        # Track Section Header for Advisors
        matched_section = None
        for h in ["Account Advisor", "Assets Manager", "Investment Advisor", "Insurance Manager"]:
            # Use fuzzy check but avoid collision with "Assets & Last Purchase Information"
            if h.lower() in line_low and "last purchase" not in line_low:
                matched_section = h
                break
        
        if matched_section:
            current_section = matched_section
            i += 1
            continue

        # Skip other general section headers
        if any(line_low == h.lower() for h in SECTION_HEADERS):
            # Reset current_section if we hit a different general section
            # (Advisors are handled above)
            current_section = None
            i += 1
            continue

        # 1. Try Colon Match (label: value)
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip()
            
            # If value is empty, collect subsequent lines
            if not value:
                val_parts = []
                j = i + 1
                while j < len(lines):
                    if should_stop(lines[j], val_parts):
                        break
                    if not should_skip(lines[j]):
                        val_parts.append(lines[j])
                    j += 1
                value = " ".join(val_parts)
                i = j - 1
            
            if current_section and key in ["Advisor ID", "Manager ID", "Name", "Contact", "Address"]:
                key = f"{current_section} - {key}"
                
            data[key] = clean_ocr_field(value, key)
            i += 1
            continue

        # 2. Try Exact Match with known fields
        found_field = None
        # Special check for Advisor fields
        if current_section:
            for field_part in ["Advisor ID", "Manager ID", "Name", "Contact", "Address"]:
                if line_low == field_part.lower():
                    found_field = f"{current_section} - {field_part}"
                    break
        
        # General check
        if not found_field:
            for field in FIELDS_DESC:
                if line_low == field.lower():
                    found_field = field
                    break
        
        if found_field:
            val_parts = []
            j = i + 1
            while j < len(lines):
                if should_stop(lines[j], val_parts):
                    break
                if not should_skip(lines[j]):
                    val_parts.append(lines[j])
                j += 1
            value = " ".join(val_parts)
            data[found_field] = clean_ocr_field(value, found_field)
            i = j - 1 
            i += 1 
            continue
        
        # 3. Fuzzy search for field within line
        for field in FIELDS_DESC:
            if len(field) > 2 and field.lower() in line_low:
                idx = line_low.find(field.lower())
                # Boundary check: label must be at start or preceded by separator
                if idx > 0 and (line_low[idx-1] not in [' ', ':', '|', '-']):
                    continue
                
                # Further check: if it looks like a section header, skip
                if field.lower() in [h.lower() for h in SECTION_HEADERS]:
                    continue
                    
                val_candidate = line[idx + len(field):].strip().lstrip(':').strip()
                if val_candidate:
                    key = field
                    if current_section and key in ["Advisor ID", "Manager ID", "Name", "Contact", "Address"]:
                        key = f"{current_section} - {key}"
                    
                    canonical_key = ALIAS_MAP.get(key, key)
                    if canonical_key not in data or not data[canonical_key]:
                        val_parts = [val_candidate]
                        j = i + 1
                        while j < len(lines):
                            if should_stop(lines[j], val_parts):
                                break
                            if not should_skip(lines[j]):
                                val_parts.append(lines[j])
                            j += 1
                        
                        full_val = " ".join(val_parts)
                        data[key] = clean_ocr_field(full_val, key)
                        i = j - 1
                        break
        
        i += 1

    return data

# ---------------------------------------------------
# IMAGE PROCESSING
# ---------------------------------------------------
async def process_image_url(url: Union[str, List[str], Tuple[str, ...]]):

    if isinstance(url, (list, tuple)):
        results = {}
        for u in url:
            try:
                results[u] = await _process_single_image(u)
            except Exception as e:
                results[u] = {"error": str(e)}
        return results
    else:
        return await _process_single_image(url)


async def _process_single_image(url: str) -> Dict[str, str]:
    try:
        # Extreme timeout for slow servers
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        img = Image.open(io.BytesIO(response.content)).convert("RGB")

        text = extract_text_with_paddle(img)

        if not text.strip():
            raise Exception("No text detected by OCR")

        parsed_data = parse_ocr_text(text)
        print(f"DEBUG: Final Flat Data: {parsed_data}")
        return parsed_data

    except Exception as e:
        logger.error(f"OCR Failed: {e}")
        raise e

# ---------------------------------------------------
# API ENDPOINT
# ---------------------------------------------------
@app.post("/api/scrape")
async def scrape_endpoint(request: ScrapeRequest):
    try:
        scraped_data = scraper.scrape_url(request.url)
        unique_links = scraped_data.get("__metadata__", {}).get("unique_links", 0)
        data = {k: v for k, v in scraped_data.items() if k != "__metadata__"}
        
        print(f"DEBUG: Scraped flat data keys: {list(data.keys())}")
        nested_response = nest_data(data)
        print("DEBUG: Final Nested JSON generated.")
        
        return {
            "status": "success",
            "data": nested_response,
            "metadata": {"unique_links": unique_links}
        }

    except ValueError as ve:
        if "IMAGE_URL_DETECTED" in str(ve) or "image" in str(ve).lower():
            print(f"DEBUG: Image detected via ValueError: {ve}")
            try:
                data = await process_image_url(request.url)
                print(f"DEBUG: OCR completed. Fields found: {list(data.keys())}")
                nested_response = nest_data(data)
                return {"status": "success", "data": nested_response, "method": "paddleocr"}
            except Exception as e:
                print(f"DEBUG: OCR Processing Exception: {e}")
                return JSONResponse(
                    status_code=400,
                    content={"error": str(e)}
                )
        print(f"DEBUG: Other ValueError: {ve}")
        return JSONResponse(
            status_code=400,
            content={"error": str(ve)}
        )

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )

# ---------------------------------------------------
# Serve Frontend
# ---------------------------------------------------
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# ---------------------------------------------------
# RUN
# ---------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting WorkProof Server at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)