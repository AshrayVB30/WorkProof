"""
Field-by-Field Validation Engine
Replaces character-based comparison with intelligent field-level validation.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional
import logging

logger = logging.getLogger("WorkProof.FieldValidator")

class FieldMetadata:
    """Defines metadata and validation rules for each field"""
    
    # All 41 fields with validation rule types (A-F)
    # Rule A: Numeric (Exact Match) - Customer ID, Age, Branch ID, Transaction ID, Loan ID, Loan Term, Card ID, Rewards Points, Anomaly
    # Rule B: Decimal/Amount (Float) - Account Balance, Transaction Amount, Account Balance After Transaction, Loan Amount, Credit Limit, Credit Card Balance, Minimum Payment Due
    # Rule C: Text (Case-Insensitive) - First Name, Last Name, Gender, Address, City, Account Type, Transaction Type, Loan Type, Loan Status, Card Type, Feedback Type, Resolution Status
    # Rule D: Email (Strict) - Email
    # Rule E: Contact Number (Exact Digits) - Contact Number
    # Rule F: Date (Normalized) - Date Of Account Opening, Last Transaction Date, Transaction Date, Approval/Rejection Date, Payment Due Date, Last Credit Card Payment Date, Feedback Date, Resolution Date
    
    FIELD_DEFINITIONS = {
        # 1. Personal Information
        "Full Name": {"type": "text", "rule": "C", "required": True},
        "Gender": {"type": "text", "rule": "C", "required": False},
        "DOB": {"type": "date", "rule": "F", "format": "%m/%d/%Y"},
        # "SSN": {"type": "text", "rule": "C", "required": False},
        "Address 1": {"type": "text", "rule": "C", "required": False},
        "Address 2": {"type": "text", "rule": "C", "required": False},
        "City": {"type": "text", "rule": "C", "required": False},
        "State": {"type": "text", "rule": "C", "required": False},
        "Postal": {"type": "text", "rule": "C", "required": False},
        "Country": {"type": "text", "rule": "C", "required": False},
        "Email": {"type": "email", "rule": "D", "required": False},
        "Contact": {"type": "phone", "rule": "E", "required": False},

        # 2. Account Information
        "Customer ID": {"type": "number", "rule": "A", "required": True},
        "A/C Type": {"type": "text", "rule": "C", "required": False},
        "A/c Name": {"type": "text", "rule": "C", "required": False},
        # "A/c Number": {"type": "text", "rule": "C", "required": False},
        "IBAN": {"type": "text", "rule": "C", "required": False}, # Add validation later
        "BIC": {"type": "text", "rule": "C", "required": False},
        "BTC Address": {"type": "text", "rule": "C", "required": False},
        "ETH Address": {"type": "text", "rule": "C", "required": False},
        "LTC Address": {"type": "text", "rule": "C", "required": False},
        "CC_No": {"type": "number", "rule": "A", "required": False},
        "Last Txn Amount": {"type": "currency", "rule": "B", "required": False},
        "Last Txn Date": {"type": "date", "rule": "F", "format": "%m/%d/%Y"},

        # 3. Investment Information
        "Company": {"type": "text", "rule": "C", "required": False},
        "BS": {"type": "text", "rule": "C", "required": False},
        "EIN": {"type": "text", "rule": "C", "required": False},
        "Skill Description": {"type": "text", "rule": "C", "required": False},
        "ISIN": {"type": "text", "rule": "C", "required": False},
        "Coupon": {"type": "currency", "rule": "B", "required": False},
        "Invested Amount": {"type": "currency", "rule": "B", "required": False},
        "Maturity Date": {"type": "date", "rule": "F", "format": "%m/%d/%Y"},
        "Bond Name": {"type": "text", "rule": "C", "required": False},
        "Bond Class": {"type": "text", "rule": "C", "required": False},

        # 4. Assets & Last Purchase Information
        # 4.1 Last Purchase Detail
        "Department": {"type": "text", "rule": "C", "required": False},
        "Ean13": {"type": "text", "rule": "C", "required": False},
        "Product Name": {"type": "text", "rule": "C", "required": False},
        "Unit Price": {"type": "currency", "rule": "B", "required": False},
        "User": {"type": "text", "rule": "C", "required": False},
        "Purchase Token": {"type": "text", "rule": "C", "required": False},
        "Buying IPv4": {"type": "text", "rule": "C", "required": False},
        "Buying IPv6": {"type": "text", "rule": "C", "required": False},
        # 4.2 Vehicle Detail
        "Type": {"type": "text", "rule": "C", "required": False},
        "Model": {"type": "text", "rule": "C", "required": False},
        "Manufacture": {"type": "text", "rule": "C", "required": False},
        "VIN": {"type": "text", "rule": "C", "required": False},
        # 4.3 Insurance Detail
        "Beneficiary Identifier ID": {"type": "text", "rule": "C", "required": False},
        "INS No": {"type": "text", "rule": "C", "required": False},

        # 5. Legal Advisors
        # 5.1 Account Advisor
        "Account Advisor - Advisor ID": {"type": "text", "rule": "C", "required": False},
        "Account Advisor - Name": {"type": "text", "rule": "C", "required": False},
        "Account Advisor - Contact": {"type": "phone", "rule": "E", "required": False},
        "Account Advisor - Address": {"type": "text", "rule": "C", "required": False},
        # 5.2 Assets Manager
        "Assets Manager - Advisor ID": {"type": "text", "rule": "C", "required": False},
        "Assets Manager - Name": {"type": "text", "rule": "C", "required": False},
        "Assets Manager - Contact": {"type": "phone", "rule": "E", "required": False},
        "Assets Manager - Address": {"type": "text", "rule": "C", "required": False},
        # 5.3 Investment Advisor
        "Investment Advisor - Manager ID": {"type": "text", "rule": "C", "required": False},
        "Investment Advisor - Name": {"type": "text", "rule": "C", "required": False},
        "Investment Advisor - Contact": {"type": "phone", "rule": "E", "required": False},
        "Investment Advisor - Address": {"type": "text", "rule": "C", "required": False},
        # 5.4 Insurance Manager
        "Insurance Manager - Manager ID": {"type": "text", "rule": "C", "required": False},
        "Insurance Manager - Name": {"type": "text", "rule": "C", "required": False},
        "Insurance Manager - Contact": {"type": "phone", "rule": "E", "required": False},
        "Insurance Manager - Address": {"type": "text", "rule": "C", "required": False},
    }
    
    @classmethod
    def get_field_type(cls, field_name: str) -> str:
        """Get the type of a field"""
        return cls.FIELD_DEFINITIONS.get(field_name, {}).get("type", "text")
    
    @classmethod
    def get_field_config(cls, field_name: str) -> Dict:
        """Get full configuration for a field"""
        return cls.FIELD_DEFINITIONS.get(field_name, {"type": "text"})


class FieldNormalizer:
    """Normalizes field values based on their type"""
    
    @staticmethod
    def normalize_number(value: str) -> Optional[float]:
        """Normalize numeric values: remove commas, convert to float"""
        if not value or value.strip() == "":
            return None
        try:
            # Remove commas, spaces, currency symbols
            cleaned = re.sub(r'[,$\s]', '', value.strip())
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def normalize_currency(value: str) -> Optional[float]:
        """Normalize currency values"""
        return FieldNormalizer.normalize_number(value)
    
    @staticmethod
    def normalize_percentage(value: str) -> Optional[float]:
        """Normalize percentage values"""
        if not value:
            return None
        try:
            cleaned = value.strip().replace('%', '').strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def normalize_text(value: str) -> str:
        """Normalize text: trim, normalize spaces (Keep Case)"""
        if not value:
            return ""
        # Trim and collapse multiple spaces, but KEEP CASE
        normalized = ' '.join(value.strip().split())
        return normalized
    
    @staticmethod
    def normalize_date(value: str, date_format: str = "%m/%d/%Y") -> Optional[datetime]:
        """Parse and normalize date values (Strict Format)"""
        if not value or value.strip() == "":
            return None
        try:
            # Strict format check as requested
            return datetime.strptime(value.strip(), date_format)
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def normalize_enum(value: str, allowed_values: List[str]) -> Optional[str]:
        """Normalize enum values: case-insensitive match"""
        if not value:
            return None
        normalized = value.strip().lower()
        for allowed in allowed_values:
            if normalized == allowed.lower():
                return allowed  # Return the canonical form
        return None
    
    @staticmethod
    def normalize_phone(value: str) -> str:
        """Normalize phone numbers: keep only digits"""
        if not value:
            return ""
        return re.sub(r'\D', '', value)
    
    @staticmethod
    def normalize_email(value: str) -> str:
        """Normalize email: lowercase, trim"""
        if not value:
            return ""
        return value.strip().lower()


class FieldValidator:
    """
    Field-by-field validation engine.
    Compares reference and user data at the field level, not character level.
    """
    
    def __init__(self):
        self.metadata = FieldMetadata()
        self.normalizer = FieldNormalizer()
    
    def validate_field(self, field_name: str, reference_value: str, user_value: str) -> Dict:
        """
        Validate a single field using rule-based validation (A-F).
        
        Returns:
            {
                "field": str,
                "is_correct": bool,
                "reference": str,
                "user": str,
                "normalized_reference": Any,
                "normalized_user": Any,
                "error_type": str,  # "correct", "value_error", "type_error", "format_warning"
                "message": str,
                "rule": str  # A, B, C, D, E, or F
            }
        """
        config = self.metadata.get_field_config(field_name)
        field_type = config.get("type", "text")
        validation_rule = config.get("rule", "C")  # Default to Rule C (text)
        
        result = {
            "field": field_name,
            "reference": reference_value,
            "user": user_value,
            "normalized_reference": None,
            "normalized_user": None,
            "is_correct": False,
            "error_type": "correct",
            "message": "",
            "rule": validation_rule
        }
        
        # Handle empty reference values - skip validation
        if not reference_value or reference_value.strip() == "":
            result["is_correct"] = True  # Don't penalize for missing reference
            return result
        
        # Handle empty user values
        if not user_value or user_value.strip() == "":
            result["error_type"] = "value_error"
            result["message"] = "Field is empty"
            return result
        
        # RULE A: Numeric (Exact Match) - No tolerance for integer fields
        if validation_rule == "A" or field_type == "number":
            ref_norm = self.normalizer.normalize_number(reference_value)
            user_norm = self.normalizer.normalize_number(user_value)
            result["normalized_reference"] = ref_norm
            result["normalized_user"] = user_norm
            
            if ref_norm is None or user_norm is None:
                result["error_type"] = "type_error"
                result["message"] = "Invalid number format"
            else:
                # Exact integer comparison (no tolerance)
                ref_int = int(ref_norm)
                user_int = int(user_norm)
                result["is_correct"] = (ref_int == user_int)
                if not result["is_correct"]:
                    result["error_type"] = "value_error"
                    result["message"] = f"Expected {ref_int}, got {user_int}"
        
        # RULE B: Decimal/Amount (Float Comparison with penny tolerance)
        elif validation_rule == "B" or field_type == "currency":
            ref_norm = self.normalizer.normalize_currency(reference_value)
            user_norm = self.normalizer.normalize_currency(user_value)
            result["normalized_reference"] = ref_norm
            result["normalized_user"] = user_norm
            
            if ref_norm is None or user_norm is None:
                result["error_type"] = "type_error"
                result["message"] = "Invalid currency format"
            else:
                # Float comparison with 0.01 tolerance
                result["is_correct"] = abs(ref_norm - user_norm) < 0.01
                if not result["is_correct"]:
                    result["error_type"] = "value_error"
                    result["message"] = f"Expected ${ref_norm:.2f}, got ${user_norm:.2f}"
        
        # RULE C: Text (Case-Sensitive Exact Match)
        elif validation_rule == "C" or field_type == "text":
            ref_norm = self.normalizer.normalize_text(reference_value)
            user_norm = self.normalizer.normalize_text(user_value)
            result["normalized_reference"] = ref_norm
            result["normalized_user"] = user_norm
            result["is_correct"] = (ref_norm == user_norm)
            
            if not result["is_correct"]:
                result["error_type"] = "value_error"
                result["message"] = f"Expected '{reference_value}', got '{user_value}' (Case-Sensitive)"
        
        # RULE D: Email (Strict Match)
        elif validation_rule == "D" or field_type == "email":
            ref_norm = self.normalizer.normalize_email(reference_value)
            user_norm = self.normalizer.normalize_email(user_value)
            result["normalized_reference"] = ref_norm
            result["normalized_user"] = user_norm
            result["is_correct"] = (ref_norm == user_norm)
            
            if not result["is_correct"]:
                result["error_type"] = "value_error"
                result["message"] = f"Expected '{reference_value}', got '{user_value}'"
        
        # RULE E: Contact Number (Exact Digits OR Masked)
        elif validation_rule == "E" or field_type == "phone":
            ref_digits = self.normalizer.normalize_phone(reference_value)
            user_digits = self.normalizer.normalize_phone(user_value)

            result["normalized_reference"] = ref_digits
            result["normalized_user"] = user_digits

            # --- Case 1: Fully visible number ---
            if re.fullmatch(r"\d+", user_value.strip()):
                is_valid_length = len(user_digits) == 11
                result["is_correct"] = (ref_digits == user_digits) and is_valid_length

                if not is_valid_length:
                    result["error_type"] = "value_error"
                    result["message"] = "Phone number must be exactly 11 digits"
                elif not result["is_correct"]:
                    result["error_type"] = "value_error"
                    result["message"] = f"Expected '{ref_digits}', got '{user_digits}'"

            # --- Case 2: Masked number (xxx allowed, last 4 must match) ---
            elif re.fullmatch(r"\+?\d?\s*\([xX]{3}\)\s*[xX]{3}\s*\d{4}", user_value.strip()):
                result["is_correct"] = ref_digits[-4:] == user_digits[-4:]

                if not result["is_correct"]:
                    result["error_type"] = "value_error"
                    result["message"] = "Last 4 digits do not match"

            # --- Case 3: Invalid format ---
            else:
                result["error_type"] = "type_error"
                result["message"] = "Invalid phone number format"

        # RULE F: Date (Normalized Comparison)
        elif validation_rule == "F" or field_type == "date":
            date_format = config.get("format", "%m/%d/%Y")
            ref_norm = self.normalizer.normalize_date(reference_value, date_format)
            user_norm = self.normalizer.normalize_date(user_value, date_format)
            result["normalized_reference"] = ref_norm
            result["normalized_user"] = user_norm
            
            if ref_norm is None or user_norm is None:
                result["error_type"] = "type_error"
                result["message"] = "Invalid date format"
            else:
                result["is_correct"] = (ref_norm == user_norm)
                if not result["is_correct"]:
                    result["error_type"] = "value_error"
                    result["message"] = f"Expected {ref_norm.strftime(date_format)}, got {user_norm.strftime(date_format)}"
        
        return result

    
    def validate_all_fields(self, reference_data: Dict[str, str], user_data: Dict[str, str]) -> Dict:
        """
        Validate all fields and calculate accuracy.
        
        Returns:
            {
                "total_fields": int,
                "correct_fields": int,
                "accuracy": float,
                "field_results": List[Dict],
                "errors": List[Dict]
            }
        """
        field_results = []
        correct_count = 0
        total_count = 0
        
        for field_name in reference_data.keys():
            ref_value = reference_data.get(field_name, "")
            user_value = user_data.get(field_name, "")
            
            # Always validate the field (for completeness in field_results)
            result = self.validate_field(field_name, ref_value, user_value)
            field_results.append(result)
            
            # ✅ ONLY count fields with non-empty reference values
            # Fields without reference data don't affect accuracy
            if not ref_value or ref_value.strip() == "":
                continue  # DO NOT COUNT in totals
            
            total_count += 1
            if result["is_correct"]:
                correct_count += 1
        
        # ✅ NEVER default to 100% when nothing is validated
        if total_count == 0:
            accuracy = 0.0  # No fields validated = 0% accuracy
        else:
            accuracy = round((correct_count / total_count) * 100, 2)
        
        errors = [r for r in field_results if not r["is_correct"] and reference_data.get(r["field"], "").strip() != ""]
        
        return {
            "total_fields": total_count,
            "correct_fields": correct_count,
            "accuracy": round(accuracy, 2),
            "field_results": field_results,
            "errors": errors
        }
