
import requests
import pytesseract
from PIL import Image
import io
import tempfile
import time
from typing import Dict

# Helper parsing function (Copy of logic from main_window.py)
def _parse_ocr_text(text: str) -> Dict[str, str]:
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
    
    # Implicit triggers
    section_triggers = {
        "Full Name": "Personal",
        "Customer ID": "Account", 
        "Company": "Investment",
        "Department": "Assets",
        "Last Purchase Detail": "Assets",
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
            "Customer ID": "Customer ID", "A/c Type": "A/C Type", "A/c Name": "A/c Name",
            "A/c Number": "A/c Number",
            "IBAN": "IBAN", "BIC": "BIC", "BTC Address": "BTC Address", 
            "ETH Address": "ETH Address", "LTC Address": "LTC Address", 
            "CC_No": "CC_No", "Last Txn Amount": "Last Txn Amount", "Last Txn Date": "Last Txn Date"
        },
        "Investment": {
            "Company": "Company", "BS": "BS", "EIN": "EIN", "Skll Description": "Skill Description", "Skill Description": "Skill Description",
            "ISIN": "ISIN", "Coupon": "Coupon", "Invested Amount": "Invested Amount", 
            "Maturity Date": "Maturity Date", "Bond Name": "Bond Name", "Bond Class": "Bond Class"
        },
        "Assets": {
            "Department": "Department", "Ean13": "Ean13", "Product Name": "Product Name", 
            "Unit Price": "Unit Price", "User": "User", "Purchase Token": "Purchase Token",
            "Buying IPv4": "Buying IPv4", "Buying IPv6": "Buying IPv6",
            "Type": "Type", "Model": "Model", "Manufacturer": "Manufacture", "Manufacture": "Manufacture",
            "VIN": "VIN", "Beneficiary": "Beneficiary Identifier ID", "INS No": "INS No"
        },
        "Legal": {
            "Advisor ID": "Advisor ID", "Manager ID": "Manager ID", 
            "Name": "Name", "Contact": "Contact", "Address": "Address"
        }
    }

    print("DEBUG: Parsing Lines...")
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Cleanup: Remove common OCR artifacts or section headers appearing on data lines
        # 'Last Purchase Detail', 'Vehicle Detail', 'Insurance Detail' often appear appended
        line = line.replace("Last Purchase Detail", "").replace("Vehicle Detail", "").replace("Insurance Detail", "")
        # Also clean 'Eanl3' or 'Fanl3' which often stick to previous fields
        line = line.replace("Eanl3", "").replace("Fanl3", "")
        
        line = line.strip()
        if not line: continue

        lower_line = line.lower()
        
        # 1. Detect Explicit Section Headers
        found_section = False
        for key, val in section_map.items():
            if key in lower_line:
                print(f"DEBUG: Found Explicit Section: {val}")
                current_section = val
                current_sub_section = None
                last_field_key = None
                found_section = True
                break
        if found_section: continue

        # 1.5 Detect Implicit Section Triggers
        if not found_section:
            for trigger, section in section_triggers.items():
                if line.lower().startswith(trigger.lower()):
                    if current_section != section:
                        print(f"DEBUG: Found Implicit Section Trigger '{trigger}' -> {section}")
                        current_section = section
                        current_sub_section = None
                        last_field_key = None
                    break

        # 2. Detect Sub-Sections
        if current_section == "Legal":
            for sub in legal_sub_sections:
                if line.lower().startswith(sub.lower()):
                    if current_sub_section != sub:
                        print(f"DEBUG: Found Sub-Section: {sub}")
                        current_sub_section = sub
                        last_field_key = None
                        found_section = True
                    break
        if found_section: continue
            
        # 3. Parse Fields
        matched_field = False
        if current_section and current_section in field_aliases:
            aliases = field_aliases[current_section]
            
            if current_section == "Legal" and current_sub_section:
                for ocr_key, suffix_field in aliases.items():
                    if suffix_field is None: continue
                    if line.lower().startswith(ocr_key.lower()):
                        value = line[len(ocr_key):].strip().lstrip(':. ').strip()
                        full_field_name = f"{current_sub_section} - {suffix_field}"
                        data[full_field_name] = value
                        last_field_key = full_field_name
                        matched_field = True
                        print(f"DEBUG: Extracted {full_field_name} = {value}")
                        break
            else:
                for ocr_key, target_field in aliases.items():
                    if target_field is None: continue
                    if line.lower().startswith(ocr_key.lower()):
                        value = line[len(ocr_key):].strip().lstrip(':. ').strip()
                        
                        # SPECIAL FIELD CLEANING
                        # DOB: Remove "SSN"
                        if target_field == "DOB" and "ssn" in value.lower():
                            value = value.lower().split("ssn")[0].strip().upper()
                            # Fix OCR 'Q' -> '0' in dates like Q9-DEC
                            if len(value) > 1 and value[0] == 'Q':
                                value = '0' + value[1:]

                        data[target_field] = value
                        last_field_key = target_field
                        matched_field = True
                        print(f"DEBUG: Extracted {target_field} = {value}")
                        break
        
        # 4. Multi-line
        if not matched_field and last_field_key:
            if len(line) > 1 and "---" not in line and not any(k.lower() in lower_line for k in ["ssn", "vehicle detail"]):
                data[last_field_key] += " " + line
                print(f"DEBUG: Appended to {last_field_key}: {line}")

    return data

def run_debug():
    url = "http://109.199.108.38:2069/?q=QUNUQVNUeHg4MGltZzAwMDcuanBlZzs1NjY7MU4wZ01rSEg"
    print(f"Downloading {url}...")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        img = Image.open(io.BytesIO(response.content))
        
        # Preprocessing
        img = img.convert('L')
        width, height = img.size
        img = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        
        # Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(img, config=custom_config)
        
        print("\n" + "="*40)
        print("RAW OCR TEXT")
        print("="*40)
        print(text)
        print("="*40 + "\n")
        
        data = _parse_ocr_text(text)
        
        print("\n" + "="*40)
        print("PARSED DATA")
        print("="*40)
        for k, v in data.items():
            print(f"{k}: {v}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_debug()
