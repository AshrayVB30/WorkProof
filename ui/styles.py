
def get_modern_stylesheet():
    return """
    QMainWindow {
        background-color: #1a1b1e;
    }
    
    QWidget {
        color: #e0e0e0;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 14px;
    }
    
    QSplitter::handle {
        background-color: #2c2e33;
        width: 2px;
    }
    
    QTableWidget {
        background-color: #25262b;
        border: 1px solid #373a40;
        border-radius: 8px;
        gridline-color: #373a40;
        selection-background-color: #3b5bdb;
        selection-color: white;
        outline: none;
    }
    
    QTableWidget::item {
        padding: 5px;
    }

    QHeaderView::section {
        background-color: #2c2e33;
        color: #a1a1aa;
        padding: 8px;
        border: none;
        border-right: 1px solid #373a40;
        border-bottom: 1px solid #373a40;
        font-weight: bold;
    }

    QHeaderView::section:last {
        border-right: none;
    }

    QTextEdit, QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {
        background-color: #25262b;
        border: 1px solid #373a40;
        border-radius: 6px;
        padding: 8px;
        color: #e0e0e0;
        selection-background-color: #4c6ef5;
    }

    QTextEdit:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
        border: 1px solid #4c6ef5;
    }
    
    QLabel {
        font-weight: 600;
        color: #a1a1aa;
        margin-bottom: 4px;
    }
    
    QPushButton {
        background-color: #2c2e33;
        border: 1px solid #373a40;
        padding: 8px 16px;
        border-radius: 6px;
        color: #e0e0e0;
        font-weight: 500;
    }
    
    QPushButton:hover {
        background-color: #373a40;
        border-color: #4b4e54;
    }
    
    QPushButton:pressed {
        background-color: #25262b;
    }
    
    QPushButton:disabled {
        background-color: #1a1b1e;
        color: #5c5f66;
        border-color: #2c2e33;
    }
    
    QPushButton#activeAction {
        background-color: #4c6ef5;
        border-color: #4c6ef5;
        color: white;
    }
    
    QPushButton#activeAction:hover {
        background-color: #5c7cfa;
    }
    
    QPushButton#stopAction {
        background-color: #fa5252;
        border-color: #fa5252;
        color: white;
    }
    
    QPushButton#stopAction:hover {
        background-color: #ff6b6b;
    }
    
    QStatusBar {
        background-color: #1a1b1e;
        border-top: 1px solid #2c2e33;
        color: #a1a1aa;
    }
    
    QStatusBar QLabel {
        font-weight: normal;
        margin-right: 15px;
        color: #a1a1aa;
    }
    
    QScrollBar:vertical {
        border: none;
        background: #1a1b1e;
        width: 10px;
        margin: 0px;
    }
    
    QScrollBar::handle:vertical {
        background: #373a40;
        min-height: 20px;
        border-radius: 5px;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    """
