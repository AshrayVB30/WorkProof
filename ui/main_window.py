import sys
import os
import re
from typing import Dict
from ui.styles import get_modern_stylesheet
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor, QFont, QPixmap, QImage
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLabel, QPushButton, 
                             QStatusBar, QFileDialog, QSplitter, QFrame, QMessageBox,
                             QStackedWidget, QScrollArea, QFormLayout, QLineEdit,
                             QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox)

# Internal imports
from engine.field_validator import FieldValidator
from engine.business_rules import BusinessRulesEngine
from engine.monitor import ScreenMonitor
from storage.db_manager import DBManager
from reports.report_generator import ReportGenerator
from engine.web_scraper import WebScraper
import pytesseract
from PIL import Image
import tempfile
import requests
import shutil
import io


import logging

# Logger setup
logger = logging.getLogger("WorkProof.UI")

class WorkProofApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WorkProof - Data Entry Accuracy Monitor")
        self.resize(1000, 700)

        self.field_validator = FieldValidator()
        self.business_rules = BusinessRulesEngine()
        self.monitor = ScreenMonitor()
        self.db = DBManager()
        self.reporter = ReportGenerator()
        self.web_scraper = WebScraper()


        self.session_active = False
        self.session_id = None
        self.start_time = None
        self.last_screenshot = None
        self.web_data = {} # Store web-scraped data
        self.fields = [
            # 1. Personal Information
            "Full Name", "Gender", "DOB", "Address 1", "Address 2", 
            "City", "State", "Postal", "Country", "Email", "Contact", "SSN",

            # 2. Account Information
            "Customer ID", "A/C Type", "A/c Name", "A/c Number", "IBAN", "BIC", 
            "BTC Address", "ETH Address", "LTC Address", "CC_No", 
            "Last Txn Amount", "Last Txn Date",

            # 3. Investment Information
            "Company", "BS", "EIN", "Skill Description", "ISIN", 
            "Coupon", "Invested Amount", "Maturity Date", "Bond Name", "Bond Class",

            # 4. Assets & Last Purchase Information
            # Last Purchase Details
            "Department", "Ean13", "Product Name", "Unit Price", "User", 
            "Purchase Token", "Buying IPv4", "Buying IPv6",
            # Vehicle Detail
            "Type", "Model", "Manufacture", "VIN",
            # Insurance Detail
            "Beneficiary Identifier ID", "INS No",

            # 5. Legal Advisors
            # Account Advisor
            "Account Advisor - Advisor ID", "Account Advisor - Name", "Account Advisor - Contact", "Account Advisor - Address",
            # Assets Manager
            "Assets Manager - Advisor ID", "Assets Manager - Name", "Assets Manager - Contact", "Assets Manager - Address",
            # Investment Advisor
            "Investment Advisor - Manager ID", "Investment Advisor - Name", "Investment Advisor - Contact", "Investment Advisor - Address",
            # Insurance Manager
            "Insurance Manager - Manager ID", "Insurance Manager - Name", "Insurance Manager - Contact", "Insurance Manager - Address"
        ]  # Total fields updated
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_session_stats)

        self.init_ui()
        self.setStyleSheet(get_modern_stylesheet())

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Toolbar / Header
        header_container = QFrame()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        # URL Input for web scraping
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter website URL to scrape...")
        self.url_input.setMinimumWidth(400)
        
        self.btn_scrape = QPushButton("🌐 Get the data")
        self.btn_scrape.clicked.connect(self.scrape_website)
        
        self.btn_start = QPushButton("▶ Start Comparison")
        self.btn_start.setObjectName("activeAction")
        self.btn_start.clicked.connect(self.start_session)
        
        self.btn_stop = QPushButton("⏹ Stop Session")
        self.btn_stop.setObjectName("stopAction")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_session)
        
        self.btn_report = QPushButton("📄 Generate Report")
        self.btn_report.clicked.connect(self.generate_report)

        header_layout.addWidget(QLabel("Website URL:"))
        header_layout.addWidget(self.url_input)
        header_layout.addWidget(self.btn_scrape)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_start)
        header_layout.addWidget(self.btn_stop)
        header_layout.addWidget(self.btn_report)
        
        main_layout.addWidget(header_container)

        # Comparison Section Label
        labels_layout = QHBoxLayout()
        labels_layout.addWidget(QLabel("DATA VALIDATION VIEW (WEB REFERENCE VS USER INPUT)"))
        main_layout.addLayout(labels_layout)

        # Comparison View
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(3)
        self.comparison_table.setHorizontalHeaderLabels(["Field Name", "Reference Data", "Actual Data"])
        self.comparison_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.comparison_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.comparison_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.comparison_table.setAlternatingRowColors(True)
        self.comparison_table.verticalHeader().setVisible(False)
        
        # Initialize with field names
        self.comparison_table.setRowCount(len(self.fields))
        for idx, field in enumerate(self.fields):
            # Field name (Read-only)
            field_item = QTableWidgetItem(field)
            field_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            field_item.setFlags(field_item.flags() & ~Qt.ItemIsEditable)
            self.comparison_table.setItem(idx, 0, field_item)
            
            # Reference value (Manual entry if needed)
            web_item = QTableWidgetItem("")
            self.comparison_table.setItem(idx, 1, web_item)
            
            # Actual Data (Rich Widget)
            widget = self._create_field_widget(field)
            self.comparison_table.setCellWidget(idx, 2, widget)
            
            # Connect widget changes to highlighting
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda _: self.update_comparison_highlighting())
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.valueChanged.connect(lambda _: self.update_comparison_highlighting())
            elif isinstance(widget, QDateEdit):
                widget.dateChanged.connect(lambda _: self.update_comparison_highlighting())
            elif isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(lambda _: self.update_comparison_highlighting())

        main_layout.addWidget(self.comparison_table)
        
        # Connect signal for real-time validation
        self.comparison_table.itemChanged.connect(self.on_table_item_changed)


        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.lbl_accuracy = QLabel("Accuracy: 100%")
        self.lbl_errors = QLabel("Errors: 0")
        self.lbl_time = QLabel("Time: 00:00")
        
        self.status_bar.addPermanentWidget(self.lbl_accuracy)
        self.status_bar.addPermanentWidget(self.lbl_errors)
        self.status_bar.addPermanentWidget(self.lbl_time)

    def on_table_item_changed(self, item):
        """Triggered when any cell in the comparison table is edited"""
        # We only care about edits in the reference or input columns (1 and 2)
        if item.column() in [1, 2]:
            self.update_comparison_highlighting()

    def scrape_website(self):
        """Scrape data from the provided URL and update comparison table"""
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "No URL", "Please enter a website URL to scrape.")
            return
        
        try:
            self.status_bar.showMessage(f"Scraping website: {url}...", 0)
            QApplication.processEvents()
            
            # Perform web scraping
            self.web_data = self.web_scraper.scrape_url(url)
            
            logger.info(f"Successfully scraped {len(self.web_data)} fields from {url}")
            self.status_bar.showMessage(f"Scraped {len(self.web_data)} fields from website", 3000)
            
            # Block signals while updating table to prevent recursion
            self.comparison_table.blockSignals(True)
            self.update_comparison_table_web()
            self.comparison_table.blockSignals(False)
            
            # Update comparison highlighting
            self.update_comparison_highlighting()
            
        except ValueError as ve:
            if "IMAGE_URL_DETECTED" in str(ve):
                # Handle image URL
                try:
                    self.status_bar.showMessage(f"Image detected. Downloading and processing OCR...", 0)
                    QApplication.processEvents()
                    self.process_image_url(url)
                except Exception as e:
                    logger.error(f"OCR processing failed: {e}")
                    QMessageBox.critical(self, "OCR Error", f"Failed to process image from URL:\n{str(e)}")
                    self.status_bar.showMessage(f"OCR failed: {e}", 5000)
            else:
                logger.error(f"Web scraping input error: {ve}")
                QMessageBox.warning(self, "Input Error", str(ve))
                self.status_bar.showMessage(f"Input error: {ve}", 5000)

        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            QMessageBox.critical(self, "Scraping Error", 
                f"Failed to scrape website:\n{str(e)}\n\nPlease check:\n"
                "1. URL is correct and accessible\n"
                "2. Website is online\n"
                "3. No firewall blocking the request")
            self.status_bar.showMessage(f"Scraping failed: {e}", 5000)

    def process_image_url(self, url: str):
        """Download image from URL and process with OCR"""
        try:
            # Download image to temp file
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Read image into memory for preprocessing
            img = Image.open(io.BytesIO(response.content))
            
            # Preprocessing for better OCR
            # 1. Grayscale
            img = img.convert('L')
            # 2. Resize (x2) for better text recognition
            width, height = img.size
            img = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
            
            # Save processed image to temp file for Tesseract
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                img.save(tmp_file, format="PNG")
                tmp_path = tmp_file.name
            
            logger.info(f"Image downloaded and processed to {tmp_path}")
            
            # Process with OCR
            try:
                # Set tesseract path 
                tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                if os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                
                # Use PSM 6 (Assume a single uniform block of text) which works better for tables
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(Image.open(tmp_path), config=custom_config)
                logger.info(f"OCR extracted {len(text)} characters")
                
                # Parse text and populate reference data
                self.web_data = self._parse_ocr_text(text)
                
                logger.info(f"Parsed {len(self.web_data)} fields from OCR text")
                self.status_bar.showMessage(f"OCR Complete. Extracted {len(self.web_data)} fields.", 3000)
                
                # Update table
                self.comparison_table.blockSignals(True)
                self.update_comparison_table_web()
                self.comparison_table.blockSignals(False)
                self.update_comparison_highlighting()
                
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
        except Exception as e:
            raise Exception(f"Failed to download/process image: {e}")

    def _parse_ocr_text(self, text: str) -> Dict[str, str]:
        """
        Parse raw OCR text into key-value pairs.
        Handles "Key: Value" and "Key Value" formats.
        """
    def _parse_ocr_text(self, text: str) -> Dict[str, str]:
        """
        Parse raw OCR text into key-value pairs using section-aware logic.
        Handles repeated field names like 'Name' or 'Address' by tracking the current section.
        Also handles multi-line values (e.g., Address broken into two lines).
        """
        data = {}
        lines = text.splitlines()
        
        current_section = None
        current_sub_section = None # For Legal Advisors (Account Advisor, Assets Manager, etc.)
        last_field_key = None # To support multi-line values

        # Mappings for headers to sections
        section_map = {
            "personal information": "Personal",
            "account information": "Account",
            "investment information": "Investment",
            "assets & last purchase": "Assets",
            "legal advisors": "Legal"
        }
        
        # Implicit triggers: If header is missing, these keys force a section switch
        section_triggers = {
            "Full Name": "Personal",
            "Customer ID": "Account", 
            "Company": "Investment",
            "Department": "Assets",
            "Last Purchase Detail": "Assets", # Often appears as header
            "Account Advisor": "Legal",
            "Assets Manager": "Legal",
            "Investment Advisor": "Legal", 
            "Insurance Manager": "Legal"
        }

        # Sub-section mapping for Legal Advisors
        legal_sub_sections = [
            "Account Advisor", "Assets Manager", "Investment Advisor", "Insurance Manager"
        ]

        # Field aliases/mappings (Key in OCR -> Key in self.fields)
        # Note: We check if the line STARTS with these keys
        field_aliases = {
            "Personal": {
                "Full Name": "Full Name", "Gender": "Gender", "DOB": "DOB", 
                "Address 1": "Address 1", "Address 2": "Address 2", "City": "City", 
                "State": "State", "Postal": "Postal", "Country": "Country", 
                "Email": "Email", "Contact": "Contact", "SSN": "SSN" # Enable SSN
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
                # These depend on the sub-section
                "Advisor ID": "Advisor ID", "Manager ID": "Manager ID", 
                "Name": "Name", "Contact": "Contact", "Address": "Address"
            }
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Cleanup: Remove common OCR artifacts or section headers appearing on data lines
            # 'Last Purchase Detail', 'Vehicle Detail', 'Insurance Detail' often appear appended
            line = line.replace("Last Purchase Detail", "").replace("Vehicle Detail", "").replace("Insurance Detail", "")
            # Also clean 'Eanl3' or 'Fanl3' which often stick to previous fields
            line = line.replace("Eanl3", "").replace("Fanl3", "")
            
            line = line.strip()
            if not line:
                continue
            
            lower_line = line.lower()
            
            # 1. Detect Section Headers
            found_section = False
            for key, val in section_map.items():
                if key in lower_line:
                    current_section = val
                    current_sub_section = None # Reset sub-section on main section change
                    last_field_key = None # Reset multi-line tracking
                    found_section = True
                    break
            if found_section:
                continue
            
            # 1.5 Detect Implicit Section Triggers
            if not found_section:
                for trigger, section in section_triggers.items():
                    if line.lower().startswith(trigger.lower()):
                        if current_section != section:
                            current_section = section
                            current_sub_section = None
                            last_field_key = None
                            # Don't 'continue' here, as the line itself contains data
                        break

            # 2. Detect Sub-Sections (Specifically for Legal Advisors or Assets groups)
            if current_section == "Legal":
                for sub in legal_sub_sections:
                    if line.lower().startswith(sub.lower()):
                        if current_sub_section != sub:
                            current_sub_section = sub
                            last_field_key = None # Reset multi-line tracking
                            found_section = True
                        break
            if found_section:
                continue
                
            # 3. Parse Fields based on current context
            matched_field = False
            if current_section and current_section in field_aliases:
                aliases = field_aliases[current_section]
                
                # Special handling for Legal Advisors
                if current_section == "Legal" and current_sub_section:
                    prefix = f"{current_sub_section} - "
                    
                    for ocr_key, suffix_field in aliases.items():
                        if suffix_field is None: continue # Skip ignored fields
                        
                        if line.lower().startswith(ocr_key.lower()):
                            # Map "Name" -> "Account Advisor - Name"
                            # Handle exceptions where mapping isn't 1:1 string concat
                            # e.g. "Advisor ID" for Investment might be "Manager ID" in OCR
                            
                            # Clean up value: remove key, then remove colon/dot/space
                            value = line[len(ocr_key):].strip().lstrip(':. ').strip()
                            
                            full_field_name = f"{current_sub_section} - {suffix_field}"
                            
                            data[full_field_name] = value
                            last_field_key = full_field_name
                            matched_field = True
                            break

                else:
                    # Standard Sections
                    for ocr_key, target_field in aliases.items():
                        if target_field is None: continue # Skip ignored fields

                        if line.lower().startswith(ocr_key.lower()):
                            value = line[len(ocr_key):].strip().lstrip(':. ').strip()
                            
                            # SPECIAL FIELD CLEANING
                            # DOB: Remove "SSN"
                            if target_field == "DOB" and "ssn" in value.lower():
                                value = value.lower().split("ssn")[0].strip().upper()
                                # Fix OCR 'Q' -> '0' in dates like Q9-DEC
                                if len(value) > 1 and value[0] == 'Q':
                                    value = '0' + value[1:]

                            # Even if empty, we track it as last_field_key to potentially append next line
                            data[target_field] = value
                            last_field_key = target_field
                            matched_field = True
                            break
            
            # 4. Handle Multi-line values
            if not matched_field and last_field_key:
                # If we are here, the line didn't match a new key/header
                # So it belongs to the previous field value
                # Avoid appending if it looks like garbage or a separator or known keywords
                if len(line) > 1 and "---" not in line and not any(k.lower() in lower_line for k in ["ssn", "vehicle detail"]):
                    data[last_field_key] += " " + line

        return data
    
    def update_comparison_table_web(self):
        """Update comparison table with web-scraped data"""
        if not self.web_data:
            return
        
        # Update table - match web fields to our predefined fields
        for idx, field in enumerate(self.fields):
            # Try exact match first
            value = self.web_data.get(field, "")
            
            # If no exact match, try case-insensitive match
            if not value:
                for web_key, web_value in self.web_data.items():
                    if web_key.lower() == field.lower():
                        value = web_value
                        break
            
            if value and value.strip():
                # Column 1: Reference Data (Text item)
                item = self.comparison_table.item(idx, 1)
                item.setText(value)
                
                # Column 2: Actual Data (Rich Widget)
                widget = self.comparison_table.cellWidget(idx, 2)
                self._set_widget_value(widget, value)
        
        logger.info(f"Updated comparison table with web data for {len([v for v in self.web_data.values() if v])} fields")
    
    def update_comparison_highlighting(self):
        """Update row colors based on Web Reference vs User Input"""
        matches = 0
        mismatches = 0
        
        for idx in range(len(self.fields)):
            ref_item = self.comparison_table.item(idx, 1)
            widget = self.comparison_table.cellWidget(idx, 2)
            
            ref_value = ref_item.text().strip() if ref_item else ""
            actual_value = self._get_widget_value(widget)
            
            # Use field validator for intelligent comparison
            field_name = self.fields[idx]
            validation = self.field_validator.validate_field(field_name, ref_value, actual_value)
            
            # Determine row color and text color
            if not ref_value and not actual_value:
                # Neither has value - default (transparent/dark)
                bg_color = QColor("transparent")
                text_color = QColor("#e0e0e0")
            elif not ref_value or not actual_value:
                # Only one has value - professional amber/warning
                bg_color = QColor("#f57c00")
                text_color = QColor("white")
            elif validation["is_correct"]:
                # Match - professional green
                bg_color = QColor("#2e7d32")
                text_color = QColor("white")
                matches += 1
            else:
                # Mismatch - professional red
                bg_color = QColor("#c62828")
                text_color = QColor("white")
                mismatches += 1
            
            # Apply background and text color to all cells/widgets in row
            for col in range(3):
                item = self.comparison_table.item(idx, col)
                if item:
                    item.setBackground(bg_color)
                    item.setForeground(text_color)
            
            # Update widget appearance to match row highlighting
            if widget:
                # Use high-contrast colors and ensure font is visible
                border_style = "2px solid #4c6ef5" if validation["is_correct"] else "2px solid #fa5252"
                
                # Force white text on colorful backgrounds for maximum visibility
                text_color_str = "white" if bg_color != QColor("transparent") else "#e0e0e0"
                bg_color_str = bg_color.name() if bg_color != QColor("transparent") else "#1a1b1e"
                
                widget.setStyleSheet(f"""
                    QLineEdit {{
                        background-color: {bg_color_str}; 
                        color: {text_color_str}; 
                        border: {border_style};
                        border-radius: 2px;
                        padding: 0px 4px;
                        margin: 0px;
                        font-family: 'Segoe UI';
                        font-size: 14px;
                    }}
                """)
                
                widget.setProperty("validation_state", "correct" if validation["is_correct"] else "error")
                widget.style().unpolish(widget)
                widget.style().polish(widget)
        
        # Update status bar with comparison stats
        total = matches + mismatches
        accuracy = (matches / total * 100) if total > 0 else 0
        self.lbl_accuracy.setText(f"Accuracy: <b style='color:#4c6ef5'>{accuracy:.1f}%</b> ({matches}/{total} matches)")
        self.lbl_errors.setText(f"Mismatches: <b style='color:#fa5252'>{mismatches}</b>")
        
        # Update status bar stats label (Time is handled by timer)

    def _create_field_widget(self, field_name):
        """Create a simple QLineEdit for all fields to remove complex formatting"""
        widget = QLineEdit()
        widget.setPlaceholderText(f"Enter {field_name}...")
        return widget

    def _get_widget_value(self, widget) -> str:
        """Extract string value from QLineEdit"""
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        return ""

    def _set_widget_value(self, widget, value: str):
        """Set value for QLineEdit"""
        if isinstance(widget, QLineEdit):
            widget.setText(value)





    def start_session(self):
        """Start comparison session - requires web data (reference)"""
        # Check if we have any reference data in column 1
        has_ref = False
        for idx in range(len(self.fields)):
            item = self.comparison_table.item(idx, 1)
            if item and item.text().strip():
                has_ref = True
                break
        
        if not has_ref:
            logger.warning("Attempted to start session without reference data")
            QMessageBox.warning(self, "No Reference Data", 
                "Please scrape a website or enter reference data manually in the 'Web Data' column.")
            return

        self.session_active = True
        self.session_id = f"SESS_{int(sys.modules['time'].time())}"
        logger.info(f"Comparison session {self.session_id} started")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.start_time = sys.modules['time'].time()
        
        # Take initial screenshot
        try:
            rel_path = self.monitor.capture_screenshot()
            self.last_screenshot = os.path.abspath(rel_path)
            logger.info(f"Session screenshot saved: {self.last_screenshot}")
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            self.last_screenshot = None
        
        # Update comparison highlighting
        self.update_comparison_highlighting()
            
        self.timer.start(1000)
        self.status_bar.showMessage(f"Comparison Session {self.session_id} Started")

    def stop_session(self):
        self.session_active = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.timer.stop()
        
        # Save Session to DB
        stats = self.get_current_stats()
        logger.info(f"Session {self.session_id} stopped. Accuracy: {stats['accuracy']}%, Mismatches: {stats['error_count']}")
        
        try:
            self.db.save_session(stats)
            logger.info(f"Session {self.session_id} data saved to MongoDB.")
            self.status_bar.showMessage("Session Stopped and Saved", 5000)
        except Exception as e:
            logger.error(f"Failed to save session to MongoDB: {e}")
            self.status_bar.showMessage(f"Error saving session: {e}", 5000)

    def get_current_stats(self):
        """Generate statistics comparing Web Reference vs User Input"""
        matches = 0
        mismatches = 0
        errors = []
        field_results = []
        
        ref_data = {}
        user_data = {}

        for idx, field in enumerate(self.fields):
            ref_item = self.comparison_table.item(idx, 1)
            widget = self.comparison_table.cellWidget(idx, 2)
            
            ref_value = ref_item.text().strip() if ref_item else ""
            user_value = self._get_widget_value(widget)
            
            ref_data[field] = ref_value
            user_data[field] = user_value
            
            is_match = False
            if ref_value and user_value:
                if ref_value.lower() == user_value.lower():
                    is_match = True
                    matches += 1
                else:
                    mismatches += 1
                    errors.append({
                        "field": field,
                        "ref_value": ref_value,
                        "user_value": user_value,
                        "type": "mismatch"
                    })
            
            field_results.append({
                "field": field,
                "reference": ref_value,
                "user": user_value,
                "is_correct": is_match,
                "has_both": bool(ref_value and user_value)
            })
        
        # Calculate accuracy
        total = matches + mismatches
        accuracy = (matches / total * 100) if total > 0 else 0
        
        # Calculate time spent
        elapsed = int(sys.modules['time'].time() - self.start_time) if self.start_time else 0
        mins, secs = divmod(elapsed, 60)
        
        stats = {
            "session_id": self.session_id,
            "timestamp": sys.modules['time'].strftime("%Y-%m-%d %H:%M:%S"),
            "total_fields": total,
            "correct_fields": matches,
            "error_count": mismatches,
            "accuracy": round(accuracy, 2),
            "time_spent": f"{mins:02d}:{secs:02d}",
            "errors": errors,
            "field_results": field_results,
            "screenshot_path": self.last_screenshot,
            "reference_data": ref_data,
            "user_data": user_data
        }
        return stats

    def update_session_stats(self):
        """Update the time label in the status bar"""
        if self.start_time:
            elapsed = int(sys.modules['time'].time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            self.lbl_time.setText(f"Time: <b>{mins:02d}:{secs:02d}</b>")



    def generate_report(self):
        # Generate report for the LAST session or current if stopped
        stats = self.get_current_stats() if self.session_id else None
        if not stats:
            self.status_bar.showMessage("No session data to report!", 3000)
            return

        try:
            path = self.reporter.generate_pdf(stats)
            logger.info(f"PDF Report generated: {os.path.abspath(path)}")
            self.status_bar.showMessage(f"Report Generated: {path}", 5000)
            # Optionally open the PDF
            os.startfile(os.path.abspath(path))
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            self.status_bar.showMessage(f"Error generating report: {e}", 5000)


if __name__ == "__main__":
    import time # Ensure time is available for update_session_stats
    app = QApplication(sys.argv)
    window = WorkProofApp()
    window.show()
    sys.exit(app.exec())
