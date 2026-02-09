"""
NOTE:
Business rule violations are NON-SCORING.
They must NOT affect data entry accuracy or field error counts.
They are reported separately for logical and compliance validation.
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger("WorkProof.BusinessRules")


class BusinessRuleViolation:
    """Represents a business rule violation"""
    
    def __init__(self, rule_name: str, description: str, fields_involved: List[str], severity: str = "error"):
        self.rule_name = rule_name
        self.description = description
        self.fields_involved = fields_involved
        self.severity = severity  # "error", "warning"
    
    def to_dict(self) -> Dict:
        return {
            "rule": self.rule_name,
            "description": self.description,
            "fields": self.fields_involved,
            "severity": self.severity
        }


class BusinessRulesEngine:
    """
    Validates business logic rules across related fields.
    """
    
    def __init__(self):
        self.violations = []
    
    def validate_all_rules(self, data: Dict[str, any]) -> List[BusinessRuleViolation]:
        """
        Run all business rule validations.
        
        Args:
            data: Dictionary of field_name -> normalized_value
        
        Returns:
            List of BusinessRuleViolation objects
        """
        self.violations = []
        
        # Run all rule checks
        self._check_data_sanity(data)
        self._check_cross_field_validity(data)
        
        return self.violations

    def _check_data_sanity(self, data: Dict[str, str]):
        """
        Check for logical consistency in the new data model.
        Currently a placeholder as specific business rules for the new fields are not yet defined.
        """
        # Example of a generic check (if needed in future)
        # if "Age" in data: ...
        
        pass

    def _check_cross_field_validity(self, data: Dict[str, str]):
        """
        Check relationships between fields.
        """
        pass
