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

import pytesseract
from PIL import Image as PILImage
import logging

# Configure Tesseract path if provided in .env
tesseract_cmd = os.getenv("TESSERACT_CMD")
if not tesseract_cmd:
    # Try default Windows installation paths
    default_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Tesseract-OCR\tesseract.exe"
    ]
    for p in default_paths:
        p_expanded = os.path.expandvars(p)
        if os.path.exists(p_expanded):
            tesseract_cmd = p_expanded
            break

if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    # Set TESSDATA_PREFIX environment variable
    # This tells Tesseract where to find language data files (e.g., eng.traineddata)
    tesseract_dir = os.path.dirname(tesseract_cmd)
    tessdata_path = os.path.join(tesseract_dir, "tessdata")
    
    # Only set if tessdata directory exists
    if os.path.exists(tessdata_path):
        os.environ["TESSDATA_PREFIX"] = tessdata_path
        logging.getLogger("WorkProof").info(f"Using Tesseract executable: {tesseract_cmd}")
        logging.getLogger("WorkProof").info(f"TESSDATA_PREFIX set to: {tessdata_path}")
    else:
        logging.getLogger("WorkProof").warning(f"Tesseract found at {tesseract_cmd}, but tessdata directory not found at {tessdata_path}")

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

        self.session_active = False
        self.session_id = None
        self.start_time = None
        self.last_screenshot = None
        self.reference_text = "" # Store OCR text for validation
        self.reference_path = None # Store path for report
        self.form_inputs = {} # Store field widgets
        self.field_hints = {} # Store hint labels for expected values
        self.current_field_index = 0 # Track current field for progress indicator
        self.fields = [
            # Customer Information (9 fields)
            "Customer ID", "First Name", "Last Name", "Age", "Gender", 
            "Address", "City", "Contact Number", "Email",
            
            # Account Information (6 fields)
            "Account Type", "Account Balance", "Date Of Account Opening", 
            "Last Transaction Date", "Branch ID", "Transaction ID",
            
            # Transaction Information (4 fields - Branch ID already counted)
            "Transaction Date", "Transaction Type", "Transaction Amount", 
            "Account Balance After Transaction",
            
            # Loan Information (8 fields)
            "Loan ID", "Loan Amount", "Loan Type", "Interest Rate", 
            "Loan Term", "Approval/Rejection Date", "Loan Status", "Anomaly",
            
            # Credit Card Information (9 fields)
            "Card ID", "Card Type", "Credit Limit", "Credit Card Balance", 
            "Minimum Payment Due", "Payment Due Date", 
            "Last Credit Card Payment Date", "Rewards Points",
            
            # Feedback/QA Information (5 fields)
            "Feedback ID", "Feedback Date", "Feedback Type", 
            "Resolution Status", "Resolution Date"
        ]  # Total: 41 fields
        self.zoom_factor = 1.0 # 1.0 = 100%
        self.original_pixmap = None
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
        
        self.btn_load = QPushButton("Load Reference")
        self.btn_load.clicked.connect(self.load_reference)
        
        self.btn_start = QPushButton("Start Session")
        self.btn_start.setObjectName("activeAction")
        self.btn_start.clicked.connect(self.start_session)
        
        self.btn_stop = QPushButton("Stop Session")
        self.btn_stop.setObjectName("stopAction")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_session)
        
        self.btn_report = QPushButton("Generate Report")
        self.btn_report.clicked.connect(self.generate_report)

        header_layout.addWidget(self.btn_load)
        header_layout.addWidget(self.btn_start)
        header_layout.addWidget(self.btn_stop)
        header_layout.addWidget(self.btn_report)
        header_layout.addStretch()
        
        main_layout.addWidget(header_container)

        # Labels for Panels
        labels_layout = QHBoxLayout()
        labels_layout.addWidget(QLabel("SOURCE REFERENCE"))
        labels_layout.addWidget(QLabel("DATA ENTRY PANEL"))
        main_layout.addLayout(labels_layout)

        # Panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel (Stacked: Text or Image)
        self.ref_stack = QStackedWidget()
        
        # Page 0: Text View
        self.txt_reference = QTextEdit()
        self.txt_reference.setReadOnly(True)
        self.txt_reference.setPlaceholderText("Load data to see reference text here...")
        self.txt_reference.setFont(QFont("Consolas", 12))
        self.ref_stack.addWidget(self.txt_reference)
        
        # Page 1: Image View with Controls
        img_container = QWidget()
        img_vbox = QVBoxLayout(img_container)
        img_vbox.setContentsMargins(0, 0, 0, 0)
        img_vbox.setSpacing(5)
        
        # Zoom Toolbar
        zoom_bar = QHBoxLayout()
        btn_zoom_in = QPushButton("+")
        btn_zoom_in.setFixedWidth(40)
        btn_zoom_in.clicked.connect(lambda: self.apply_zoom(1.2))
        
        btn_zoom_out = QPushButton("-")
        btn_zoom_out.setFixedWidth(40)
        btn_zoom_out.clicked.connect(lambda: self.apply_zoom(0.8))
        
        btn_zoom_reset = QPushButton("Reset Zoom")
        btn_zoom_reset.clicked.connect(self.reset_zoom)
        
        zoom_bar.addWidget(btn_zoom_in)
        zoom_bar.addWidget(btn_zoom_out)
        zoom_bar.addWidget(btn_zoom_reset)
        zoom_bar.addStretch()
        img_vbox.addLayout(zoom_bar)
        
        self.img_scroll = QScrollArea()
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_scroll.setWidget(self.img_label)
        self.img_scroll.setWidgetResizable(True)
        img_vbox.addWidget(self.img_scroll)
        
        self.ref_stack.addWidget(img_container)
        
        # Right Panel (Entry Form with Type-Specific Widgets)
        self.form_scroll = QScrollArea()
        self.form_scroll.setWidgetResizable(True)
        form_container = QWidget()
        self.form_layout = QFormLayout(form_container)
        self.form_layout.setSpacing(15)
        self.form_layout.setLabelAlignment(Qt.AlignRight)
        
        for field in self.fields:
            # Create container for field + hint + copy button
            field_container = QWidget()
            field_vbox = QVBoxLayout(field_container)
            field_vbox.setContentsMargins(0, 0, 0, 0)
            field_vbox.setSpacing(3)
            
            # Top row: Input widget + Copy button
            input_row = QHBoxLayout()
            input_row.setSpacing(5)
            
            # Create appropriate widget based on field type
            widget = self._create_field_widget(field)
            widget.setFont(QFont("Segoe UI", 10))
            self.form_inputs[field] = widget
            
            # Connect validation on focus-out instead of every keystroke
            if hasattr(widget, 'editingFinished'):
                widget.editingFinished.connect(self.on_field_changed)
            elif hasattr(widget, 'currentIndexChanged'):
                widget.currentIndexChanged.connect(self.on_field_changed)
            
            # Add focus event to track current field
            widget.installEventFilter(self)
            
            input_row.addWidget(widget, stretch=1)
            
            # Add "Copy from Reference" button
            btn_copy = QPushButton("📋")
            btn_copy.setFixedSize(30, 30)
            btn_copy.setToolTip("Copy value from reference")
            btn_copy.clicked.connect(lambda checked, f=field: self.copy_from_reference(f))
            input_row.addWidget(btn_copy)
            
            field_vbox.addLayout(input_row)
            
            # Expected value hint label
            hint_label = QLabel("")
            hint_label.setStyleSheet("color: #888; font-style: italic; font-size: 9pt;")
            hint_label.setWordWrap(True)
            self.field_hints[field] = hint_label
            field_vbox.addWidget(hint_label)
            
            self.form_layout.addRow(QLabel(field + ":"), field_container)
            
        self.form_scroll.setWidget(form_container)

        splitter.addWidget(self.ref_stack)
        splitter.addWidget(self.form_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)


        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.lbl_accuracy = QLabel("Accuracy: 100%")
        self.lbl_errors = QLabel("Errors: 0")
        self.lbl_time = QLabel("Time: 00:00")
        
        self.status_bar.addPermanentWidget(self.lbl_accuracy)
        self.status_bar.addPermanentWidget(self.lbl_errors)
        self.status_bar.addPermanentWidget(self.lbl_time)

    def load_reference(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Reference File", "", 
            "All Supported (*.txt *.csv *.png *.jpg *.jpeg);;Text Files (*.txt);;CSV Files (*.csv);;Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            ext = file_path.lower().split('.')[-1]
            try:
                if ext in ['png', 'jpg', 'jpeg']:
                    logger.info(f"Loading image reference: {file_path}")
                    # Check if tesseract is configured
                    try:
                        pytesseract.get_tesseract_version()
                    except pytesseract.TesseractNotFoundError:
                        QMessageBox.critical(self, "OCR Missing", 
                            "Tesseract OCR is not installed or configured.\n\n"
                            "1. Download it from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                            "2. Install it to default path\n"
                            "3. Or set TESSERACT_CMD in your .env file.")
                        return

                    self.status_bar.showMessage("Performing OCR on image... Please wait", 0)
                    QApplication.processEvents() 
                    
                    # Display Image
                    self.original_pixmap = QPixmap(file_path)
                    self.zoom_factor = 1.0
                    self.reset_zoom()
                    self.ref_stack.setCurrentIndex(1)
                    
                    # Process OCR in background (or foreground for now)
                    text = pytesseract.image_to_string(PILImage.open(file_path))
                    self.reference_text = text.strip()
                    self.reference_path = os.path.abspath(file_path)
                    logger.info(f"OCR completed. Characters extracted: {len(text)}")
                else:
                    logger.info(f"Loading text reference: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.txt_reference.setPlainText(content)
                        self.reference_text = content
                    self.reference_path = None # If text file, maybe no image to show
                    self.ref_stack.setCurrentIndex(0)
                
                self.status_bar.showMessage(f"Loaded: {file_path}", 3000)
                
                # Update expected value hints after loading reference
                self.update_expected_hints()
            except Exception as e:
                logger.error(f"Failed to load reference data: {e}")
                self.status_bar.showMessage(f"Error loading file: {e}", 5000)

    def _create_field_widget(self, field_name):
        """Create appropriate widget based on field type from metadata"""
        from engine.field_validator import FieldMetadata
        
        config = FieldMetadata.get_field_config(field_name)
        field_type = config.get("type", "text")
        
        if field_type == "number":
            widget = QSpinBox()
            widget.setMinimum(config.get("min", 0))
            widget.setMaximum(config.get("max", 999999999))
            widget.setSpecialValueText("")  # Allow empty
            widget.setValue(widget.minimum())
            return widget
            
        elif field_type == "currency":
            widget = QDoubleSpinBox()
            widget.setMinimum(0.0)
            widget.setMaximum(999999999.99)
            widget.setDecimals(2)
            widget.setPrefix("$ ")
            widget.setSpecialValueText("")
            widget.setValue(0.0)
            return widget
            
        elif field_type == "percentage":
            widget = QDoubleSpinBox()
            widget.setMinimum(config.get("min", 0.0))
            widget.setMaximum(config.get("max", 100.0))
            widget.setDecimals(2)
            widget.setSuffix(" %")
            widget.setSpecialValueText("")
            widget.setValue(0.0)
            return widget
            
        elif field_type == "date":
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("MM/dd/yyyy")
            widget.setSpecialValueText("")
            return widget
            
        elif field_type == "enum":
            widget = QComboBox()
            widget.addItem("")  # Empty option
            values = config.get("values", [])
            widget.addItems(values)
            widget.setEditable(False)
            return widget
            
        elif field_type == "phone":
            widget = QLineEdit()
            widget.setPlaceholderText("e.g., 555-1234")
            widget.setInputMask("999-9999;_")  # Simple phone mask
            return widget
            
        elif field_type == "email":
            widget = QLineEdit()
            widget.setPlaceholderText("e.g., user@example.com")
            return widget
            
        else:  # text
            widget = QLineEdit()
            widget.setPlaceholderText(f"Enter {field_name}...")
            return widget

    def update_expected_hints(self):
        """Update hint labels with expected values from reference data"""
        if not self.reference_text:
            return
            
        reference_data = self._parse_reference_to_fields()
        
        for field, hint_label in self.field_hints.items():
            ref_value = reference_data.get(field, "")
            if ref_value and ref_value.strip():
                hint_label.setText(f"Expected: {ref_value[:50]}")
                hint_label.setStyleSheet("color: #4c6ef5; font-style: italic; font-size: 9pt;")
            else:
                hint_label.setText("(No reference value)")
                hint_label.setStyleSheet("color: #ccc; font-style: italic; font-size: 9pt;")

    def copy_from_reference(self, field_name):
        """Copy reference value into the field"""
        if not self.reference_text:
            return
            
        reference_data = self._parse_reference_to_fields()
        ref_value = reference_data.get(field_name, "")
        
        if not ref_value or not ref_value.strip():
            return
            
        widget = self.form_inputs.get(field_name)
        if not widget:
            return
            
        # Set value based on widget type
        if isinstance(widget, QSpinBox):
            try:
                widget.setValue(int(float(ref_value)))
            except ValueError:
                pass
        elif isinstance(widget, QDoubleSpinBox):
            try:
                # Remove currency symbols and parse
                cleaned = ref_value.replace('$', '').replace(',', '').strip()
                widget.setValue(float(cleaned))
            except ValueError:
                pass
        elif isinstance(widget, QDateEdit):
            from datetime import datetime
            # Try to parse date
            for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"]:
                try:
                    date_obj = datetime.strptime(ref_value.strip(), fmt)
                    widget.setDate(date_obj.date())
                    break
                except ValueError:
                    continue
        elif isinstance(widget, QComboBox):
            index = widget.findText(ref_value, Qt.MatchFixedString)
            if index >= 0:
                widget.setCurrentIndex(index)
        elif isinstance(widget, QLineEdit):
            widget.setText(ref_value)

    def eventFilter(self, obj, event):
        """Track field focus for progress indicator and highlighting"""
        from PySide6.QtCore import QEvent
        
        if event.type() == QEvent.FocusIn:
            # Find which field got focus
            for idx, (field_name, widget) in enumerate(self.form_inputs.items()):
                if obj == widget:
                    self.current_field_index = idx
                    # Update progress indicator in status bar
                    self.lbl_time.setText(f"Field {idx + 1}/{len(self.fields)}")
                    # TODO: Highlight corresponding field in reference panel
                    break
        
        return super().eventFilter(obj, event)

    def on_field_changed(self):
        """Called when a field value changes (on blur, not keystroke)"""
        if not self.session_active:
            return
            
        # Run validation
        stats = self.get_current_stats()
        
        # Update UI
        correct = stats.get('correct_fields', 0)
        total = stats.get('total_fields', 0)
        accuracy = stats.get('accuracy', 0)
        
        self.lbl_accuracy.setText(f"Accuracy: <b style='color:#4c6ef5'>{accuracy}%</b> ({correct}/{total} fields)")
        self.lbl_errors.setText(f"Field Errors: <b style='color:#fa5252'>{stats['error_count']}</b>")
        
        # Show business violations if any
        violations = stats.get('business_violations', [])
        if violations and self.current_field_index < len(self.fields):
            # Only show if not on progress indicator
            pass
        
        self.highlight_errors(stats.get('field_results', []))


    def start_session(self):
        if not self.reference_text.strip():
            logger.warning("Attempted to start session without reference data")
            self.status_bar.showMessage("Error: No reference data loaded!", 3000)
            return

        self.session_active = True
        self.session_id = f"SESS_{int(sys.modules['time'].time())}"
        logger.info(f"Session {self.session_id} started at {sys.modules['time'].ctime()}")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        # Clear form - handle all widget types
        for widget in self.form_inputs.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QSpinBox):
                widget.setValue(widget.minimum())
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(0.0)
            elif isinstance(widget, QDateEdit):
                widget.setDate(widget.minimumDate())
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)  # Select empty option
        self.start_time = sys.modules['time'].time()
        
        # Take initial screenshot
        try:
            rel_path = self.monitor.capture_screenshot()
            self.last_screenshot = os.path.abspath(rel_path)
            logger.info(f"Session initial screenshot saved: {self.last_screenshot}")
        except Exception as e:
            logger.error(f"Failed to capture initial screenshot: {e}")
            self.last_screenshot = None
            
        self.timer.start(1000)
        self.status_bar.showMessage(f"Session {self.session_id} Started")

    def stop_session(self):
        self.session_active = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.timer.stop()
        
        # Save Session to DB
        stats = self.get_current_stats()
        logger.info(f"Session {self.session_id} stopped. Accuracy: {stats['accuracy']}%, Mistakes: {stats['error_count']}")
        
        try:
            self.db.save_session(stats)
            logger.info(f"Session {self.session_id} data saved to MongoDB.")
            self.status_bar.showMessage("Session Stopped and Saved", 5000)
        except Exception as e:
            logger.error(f"Failed to save session to MongoDB: {e}")
            self.status_bar.showMessage(f"Error saving session: {e}", 5000)

    def get_current_stats(self):
        # Extract reference data from OCR text (parse it into fields)
        reference_data = self._parse_reference_to_fields()
        
        # ✅ Guard: Detect "REFERENCE NOT PARSED" state
        # If no reference fields have values, don't run validation
        non_empty_refs = [
            v for v in reference_data.values()
            if v not in ("", None)
        ]
        
        if not non_empty_refs:
            # No reference data available - return empty stats
            return {
                "total_fields": 0,
                "correct_fields": 0,
                "error_count": 0,
                "accuracy": 0.0,
                "errors": [],
                "field_results": [],
                "business_violations": [],
                "screenshot_path": self.last_screenshot,
                "reference_path": self.reference_path,
                "form_data": {}
            }
        
        # Get user data from form - handle all widget types
        user_data = {}
        for field, widget in self.form_inputs.items():
            if isinstance(widget, QLineEdit):
                user_data[field] = widget.text()
            elif isinstance(widget, QSpinBox):
                val = widget.value()
                user_data[field] = str(val) if val != widget.minimum() else ""
            elif isinstance(widget, QDoubleSpinBox):
                val = widget.value()
                user_data[field] = str(val) if val != 0.0 else ""
            elif isinstance(widget, QDateEdit):
                user_data[field] = widget.date().toString("MM/dd/yyyy")
            elif isinstance(widget, QComboBox):
                user_data[field] = widget.currentText()
            else:
                user_data[field] = ""
        
        # Field-by-field validation
        validation_result = self.field_validator.validate_all_fields(reference_data, user_data)
        
        # Get normalized data for business rules
        normalized_data = {}
        for field_result in validation_result["field_results"]:
            normalized_data[field_result["field"]] = field_result["normalized_user"]
        
        # Business logic validation
        business_violations = self.business_rules.validate_all_rules(normalized_data)
        
        elapsed = int(sys.modules['time'].time() - self.start_time) if self.start_time else 0
        mins, secs = divmod(elapsed, 60)

        stats = {
            "session_id": self.session_id,
            "timestamp": sys.modules['time'].strftime("%Y-%m-%d %H:%M:%S"),
            "total_fields": validation_result["total_fields"],
            "correct_fields": validation_result["correct_fields"],
            "error_count": len(validation_result["errors"]),
            "accuracy": validation_result["accuracy"],
            "time_spent": f"{mins:02d}:{secs:02d}",
            "field_results": validation_result["field_results"],
            "errors": validation_result["errors"],
            "business_violations": [v.to_dict() for v in business_violations],
            "screenshot_path": self.last_screenshot,
            "reference_path": self.reference_path,
            "form_data": user_data
        }
        return stats

    def on_text_changed(self):
        if not self.session_active:
            return
            
        stats = self.get_current_stats()
        
        # Field-based accuracy display
        correct = stats.get('correct_fields', 0)
        total = stats.get('total_fields', 0)
        accuracy = stats.get('accuracy', 0)
        
        self.lbl_accuracy.setText(f"Accuracy: <b style='color:#4c6ef5'>{accuracy}%</b> ({correct}/{total} fields)")
        self.lbl_errors.setText(f"Field Errors: <b style='color:#fa5252'>{stats['error_count']}</b>")
        
        # Show business violations if any
        violations = stats.get('business_violations', [])
        if violations:
            self.lbl_time.setText(f"⚠️ {len(violations)} Logic Violations")
        
        self.highlight_errors(stats.get('field_results', []))
    
    def _parse_reference_to_fields(self) -> Dict[str, str]:
        """
        Robust OCR parser:
        - Handles table-style OCR (Key Value)
        - Handles colon-style OCR (Key: Value)
        - Skips section headers
        """
        data = {f: "" for f in self.fields}
        if not self.reference_text:
            return data

        lines = [l.strip() for l in self.reference_text.splitlines() if l.strip()]

        SECTION_HEADERS = {
            "customer information",
            "account information",
            "transaction information",
            "loan information",
            "card information",
            "feedback information",
        }

        for line in lines:
            # Skip section headers
            if line.lower() in SECTION_HEADERS:
                continue

            for field in self.fields:
                if line.lower().startswith(field.lower()):
                    remainder = line[len(field):].strip()

                    # Case 1: "Field: Value"
                    if remainder.startswith(":"):
                        value = remainder[1:].strip()

                    # Case 2: "Field   Value"
                    else:
                        value = remainder.strip()

                    if value:
                        data[field] = value
                    break

        return data

    def highlight_errors(self, field_results):
        # Field-by-field highlighting based on validation results
        for field_result in field_results:
            field_name = field_result["field"]
            widget = self.form_inputs.get(field_name)
            
            if not widget:
                continue
            
            # Check if field has value
            has_value = False
            if isinstance(widget, QLineEdit):
                has_value = bool(widget.text().strip())
            elif isinstance(widget, QSpinBox):
                has_value = widget.value() != widget.minimum()
            elif isinstance(widget, QDoubleSpinBox):
                has_value = widget.value() != 0.0
            elif isinstance(widget, QDateEdit):
                has_value = True  # Date always has a value
            elif isinstance(widget, QComboBox):
                has_value = bool(widget.currentText().strip())
            
            if not has_value:
                widget.setStyleSheet("")
                widget.setToolTip("")
                continue
            
            if field_result["is_correct"]:
                # Green border for correct
                widget.setStyleSheet("border: 2px solid #51cf66; border-radius: 3px;")
                widget.setToolTip("✅ Correct")
            else:
                # Red border for error
                widget.setStyleSheet("border: 2px solid #ff6b6b; border-radius: 3px;")
                error_msg = field_result.get("message", "Value mismatch")
                tooltip = f"❌ {error_msg}\nExpected: {field_result['reference']}\nEntered: {field_result['user']}"
                widget.setToolTip(tooltip)


    def update_session_stats(self):
        if self.start_time:
            elapsed = int(sys.modules['time'].time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            self.lbl_time.setText(f"Time: <b>{mins:02d}:{secs:02d}</b>")

    def apply_zoom(self, multiplier):
        if self.original_pixmap:
            self.zoom_factor *= multiplier
            # Clamp zoom between 0.1 and 10.0
            self.zoom_factor = max(0.1, min(self.zoom_factor, 10.0))
            new_width = self.original_pixmap.width() * self.zoom_factor
            new_height = self.original_pixmap.height() * self.zoom_factor
            
            scaled_pixmap = self.original_pixmap.scaled(
                new_width, new_height, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.img_label.setPixmap(scaled_pixmap)
            # Ensure label resizes to fit scaled pixmap so scrollbars work
            self.img_label.resize(scaled_pixmap.size())

    def reset_zoom(self):
        if self.original_pixmap:
            self.zoom_factor = 1.0
            # Fit to scroll area width initially
            avail_width = self.img_scroll.width() - 30
            self.zoom_factor = avail_width / self.original_pixmap.width()
            self.apply_zoom(1.0)

    def wheelEvent(self, event):
        # Ctrl + Mouse Wheel for zoom
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.apply_zoom(1.1) # Zoom in
            else:
                self.apply_zoom(0.9) # Zoom out
            event.accept()
        else:
            super().wheelEvent(event)


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
