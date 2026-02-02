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
        self._check_transaction_consistency(data)
        self._check_credit_card_logic(data)
        self._check_date_logic(data)
        self._check_loan_logic(data)
        self._check_data_sanity(data)
        
        return self.violations
    
    def _check_transaction_consistency(self, data: Dict):
        """
        Rule: Transaction type must match balance change direction.
        - Debit/Withdrawal → Balance decreases
        - Credit/Deposit → Balance increases
        """
        transaction_type = data.get("Transaction Type")
        account_balance = data.get("Account Balance")
        balance_after = data.get("Account Balance After Transaction")
        transaction_amount = data.get("Transaction Amount")
        
        # Guard: Skip if required fields are missing or not numeric
        if not all([transaction_type, account_balance is not None, balance_after is not None]):
            return
        if not isinstance(account_balance, (int, float)) or not isinstance(balance_after, (int, float)):
            return
        
        balance_change = balance_after - account_balance
        
        if transaction_type in ["Debit", "Withdrawal"]:
            if balance_change > 0:
                self.violations.append(BusinessRuleViolation(
                    "Transaction Consistency",
                    f"{transaction_type} transaction but balance increased by {abs(balance_change)}",
                    ["Transaction Type", "Account Balance", "Account Balance After Transaction"],
                    "error"
                ))
        
        elif transaction_type in ["Credit", "Deposit"]:
            if balance_change < 0:
                self.violations.append(BusinessRuleViolation(
                    "Transaction Consistency",
                    f"{transaction_type} transaction but balance decreased by {abs(balance_change)}",
                    ["Transaction Type", "Account Balance", "Account Balance After Transaction"],
                    "error"
                ))
        
        # Check if balance change matches transaction amount
        if transaction_amount is not None:
            expected_change = transaction_amount if transaction_type in ["Credit", "Deposit"] else -transaction_amount
            if abs(balance_change - expected_change) > 0.01:
                self.violations.append(BusinessRuleViolation(
                    "Balance Calculation",
                    f"Balance change ({balance_change}) doesn't match transaction amount ({transaction_amount})",
                    ["Transaction Amount", "Account Balance", "Account Balance After Transaction"],
                    "error"
                ))
    
    def _check_credit_card_logic(self, data: Dict):
        """
        Rules:
        - Credit Card Balance ≤ Credit Limit
        - Minimum Payment Due ≤ Credit Card Balance
        """
        credit_limit = data.get("Credit Limit")
        cc_balance = data.get("Credit Card Balance")
        min_payment = data.get("Minimum Payment Due")
        
        # Rule 1: Balance ≤ Limit
        if credit_limit is not None and cc_balance is not None:
            if isinstance(credit_limit, (int, float)) and isinstance(cc_balance, (int, float)) and cc_balance > credit_limit:
                self.violations.append(BusinessRuleViolation(
                    "Credit Limit Exceeded",
                    f"Credit Card Balance ({cc_balance}) exceeds Credit Limit ({credit_limit})",
                    ["Credit Card Balance", "Credit Limit"],
                    "error"
                ))
        
        # Rule 2: Minimum Payment ≤ Balance
        if min_payment is not None and cc_balance is not None:
            if isinstance(min_payment, (int, float)) and isinstance(cc_balance, (int, float)) and min_payment > cc_balance:
                self.violations.append(BusinessRuleViolation(
                    "Invalid Minimum Payment",
                    f"Minimum Payment Due ({min_payment}) exceeds Credit Card Balance ({cc_balance})",
                    ["Minimum Payment Due", "Credit Card Balance"],
                    "error"
                ))
    
    def _check_date_logic(self, data: Dict):
        """
        Rules:
        - Last Transaction Date ≥ Date Of Account Opening
        - Resolution Date required if Resolution Status = "Resolved"
        - Payment Due Date should be in future (warning only)
        """
        account_opening = data.get("Date Of Account Opening")
        last_transaction = data.get("Last Transaction Date")
        resolution_status = data.get("Resolution Status")
        resolution_date = data.get("Resolution Date")
        
        # Rule 1: Transaction date after account opening
        if account_opening and last_transaction:
            if last_transaction < account_opening:
                self.violations.append(BusinessRuleViolation(
                    "Invalid Transaction Date",
                    f"Last Transaction Date ({last_transaction}) is before Account Opening ({account_opening})",
                    ["Last Transaction Date", "Date Of Account Opening"],
                    "error"
                ))
        
        # Rule 2: Resolution date required if resolved
        if resolution_status == "Resolved" and not resolution_date:
            self.violations.append(BusinessRuleViolation(
                "Missing Resolution Date",
                "Resolution Status is 'Resolved' but Resolution Date is missing",
                ["Resolution Status", "Resolution Date"],
                "error"
            ))
    
    def _check_loan_logic(self, data: Dict):
        """
        Rules:
        - Loan Status = "Approved" → Approval Date must exist
        - Loan Status = "Rejected" → Rejection Date must exist
        """
        loan_status = data.get("Loan Status")
        approval_date = data.get("Approval/Rejection Date")
        
        if loan_status == "Approved" and not approval_date:
            self.violations.append(BusinessRuleViolation(
                "Missing Approval Date",
                "Loan Status is 'Approved' but Approval Date is missing",
                ["Loan Status", "Approval/Rejection Date"],
                "error"
            ))
        
        if loan_status == "Rejected" and not approval_date:
            self.violations.append(BusinessRuleViolation(
                "Missing Rejection Date",
                "Loan Status is 'Rejected' but Rejection Date is missing",
                ["Loan Status", "Approval/Rejection Date"],
                "error"
            ))
    
    def _check_data_sanity(self, data: Dict):
        """
        Rules:
        - Age: 0-150
        - Interest Rate: 0-100%
        - Loan Term: 1-360 months
        """
        age = data.get("Age")
        interest_rate = data.get("Interest Rate")
        loan_term = data.get("Loan Term")
        
        # Age check
        if age is not None and isinstance(age, (int, float)):
            if age < 0 or age > 150:
                self.violations.append(BusinessRuleViolation(
                    "Invalid Age",
                    f"Age ({age}) is outside reasonable range (0-150)",
                    ["Age"],
                    "error"
                ))
        
        # Interest rate check
        if interest_rate is not None and isinstance(interest_rate, (int, float)):
            if interest_rate < 0 or interest_rate > 100:
                self.violations.append(BusinessRuleViolation(
                    "Invalid Interest Rate",
                    f"Interest Rate ({interest_rate}%) is outside valid range (0-100%)",
                    ["Interest Rate"],
                    "error"
                ))
        
        # Loan term check
        if loan_term is not None and isinstance(loan_term, (int, float)):
            if loan_term < 1 or loan_term > 360:
                self.violations.append(BusinessRuleViolation(
                    "Invalid Loan Term",
                    f"Loan Term ({loan_term} months) is outside valid range (1-360 months)",
                    ["Loan Term"],
                    "warning"
                ))
