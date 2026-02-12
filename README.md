# WorkProof

WorkProof is a modular data validation platform designed to compare scraped or OCR-extracted data with a structured dashboard. It features a modern web-based dashboard, a powerful Python backend, and automated validation for 64 specific data fields.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)


## ✨ Features

- **Web Dashboard**: A clean, document-style interface using Times New Roman for a professional feel.
- **Intelligent Scraping & OCR**: Automatically detects if a URL is a webpage or an image. It uses BeautifulSoup for HTML scraping and Tesseract OCR for images.
- **64-Field Validation**: Automatically populates and validates 64 specific fields across Personal, Account, Investment, Asset, and Legal Advisor categories.
- **Plain Text Security**: Multi-layer protection against formatting injections; pasting text into fields automatically strips all styles.
- **Read-Only Reference**: Scraped data is presented in a non-editable but selectable format, ideal for referencing and copying.
- **Color-Coded Comparison**: Precise mapping of extracted data with visual match/mismatch indicators.
- **PDF Reports**: Generate detailed audit reports from validation sessions.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python), Uvicorn
- **Frontend**: HTML5, Vanilla CSS3, Javascript (ES6+)
- **Scraping**: Requests, BeautifulSoup4, Lxml
- **OCR Engine**: Tesseract OCR (pytesseract)
- **Database**: MongoDB (with SQLite fallback)
- **Design Reference**: Document-style, Times New Roman typography

## 🚀 Installation

### 1. Prerequisites
- **Python 3.8+**
- **Tesseract OCR**: Required for image-based URLs.
  - Windows: Install to `C:\Program Files\Tesseract-OCR\tesseract.exe`
- **MongoDB** (Optional): Falls back to SQLite if not found.

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/AshrayVB30/WorkProof.git
cd WorkProof

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Server
```bash
python server.py
```
After starting, open your browser and navigate to `http://localhost:8000`.

## 📖 Usage

1. **Enter URL**: Paste a website URL or a direct link to an image/scanned document.
2. **Get Data**: Click "🌐 Get Data". The system will automatically decide whether to scrape HTML or run OCR.
3. **Review**: Data will populate the 64 fields in the categorised sections.
4. **Validation**: Borders will highlight Green (Match) or Red (Mismatch) based on comparison logic.
5. **Copying**: Select any field value and copy it. It will copy as plain text without backgrounds.

## 📁 Project Structure

```text
WorkProof/
├── backend/
│   ├── engine/             # Web Scraping & OCR Logic
│   ├── storage/            # Multi-DB Management
│   ├── reports/            # PDF Generation
│   └── screenshots/        # Session Captures
├── frontend/
│   ├── index.html          # Main Dashboard Structure
│   ├── style.css           # Document-style Layout
│   ├── script.js           # Client-side Logic & API Connector
│   └── qt_ui/              # Legacy Desktop UI components
├── server.py               # Main FastAPI Entry Point
├── requirements.txt        # Backend dependencies
└── README.md
```

## 📊 Supported Fields (64 Total)

The platform tracks 5 major data groups:
1. **Personal Information** (12 fields): Full Name, DOB, SSN, etc.
2. **Account Information** (12 fields): IBAN, BIC, Crypto Addresses, etc.
3. **Investment Information** (10 fields): Bond Class, EIN, Maturity Date, etc.
4. **Assets & Last Purchase** (14 fields): VIN, Manufacture, IPv4/v6, etc.
5. **Legal Advisors** (16 fields): Account, Assets, Investment, and Insurance advisors.
