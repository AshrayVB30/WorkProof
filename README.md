# WorkProof

WorkProof is a complete stand-alone desktop application designed to compare OCR-extracted data with web-scraped reference data. It automatically validates data accuracy by comparing two automated sources, providing real-time visual feedback and detailed performance reports.

## Features

-   **Web Scraping**: Automatically extract reference data from websites using multiple HTML parsing strategies
-   **OCR Extraction**: Extract text from images using Tesseract OCR
-   **Automated Comparison**: Compare OCR data vs Web data with color-coded visual feedback
-   **Accuracy Calculation**: Real-time accuracy metrics based on field-by-field comparison
-   **Comparison Table**: Side-by-side view of OCR values vs Web values
-   **Color-Coded Feedback**: 
    - 🟢 Green: Values match
    - 🔴 Red: Values mismatch
    - 🟡 Yellow: Partial data (only one source has value)
-   **Session Monitoring**: Automatic screen capture and time tracking
-   **Local Storage**: All history stored locally in MongoDB for privacy
-   **PDF Reports**: Generate detailed comparison reports with accuracy metrics

## Tech Stack

-   **UI**: PySide6
-   **Web Scraping**: requests, BeautifulSoup4, lxml
-   **Screen Capture**: mss, Pillow
-   **OCR**: pytesseract
-   **Text Logic**: difflib, python-Levenshtein
-   **Reporting**: reportlab
-   **Database**: MongoDB

## Prerequisites

-   **Python 3.8+**
-   **MongoDB**: Must be installed and running on `localhost:27017`.
-   **Tesseract OCR**: Required for OCR extraction from images.

## Setup Instructions

1.  **Clone or Copy**:

    ```bash
    git clone https://github.com/AshrayVB30/WorkProof.git
    ```

2.  **Create Conda Environment**:

    ```bash
    conda create -n data_entry_monitor python=3.10 -y
    ```

    ```bash
    conda activate data_entry_monitor
    ```

3.  **Install Dependencies**:

    pip install -r requirements.txt

    
4.  **Run the Application**:
    ```bash
    python main.py
    ```

## Usage

1.  **Load Image**: Click "📁 Load Image" and select an image file (PNG, JPG, JPEG) containing data
2.  **OCR Extraction**: Application automatically extracts text using Tesseract OCR
3.  **Enter Website URL**: Type the URL of the website containing reference data
4.  **Scrape Website**: Click "🌐 Scrape Website" to extract data from the website
5.  **Review Comparison**: Check the comparison table for color-coded matches/mismatches
6.  **Start Session**: Click "▶ Start Comparison" to begin tracking the session
7.  **Monitor Stats**: Observe real-time accuracy and mismatch counts in the status bar
8.  **Stop & Report**: Click "⏹ Stop Session" to save data, and "📄 Generate Report" to create a PDF summary

## Project Structure

```text
WorkProof_Basic/
├── engine/
│   ├── monitor.py          # Screen capture logic
│   ├── validator.py        # Text comparison engine
│   ├── field_validator.py  # Field-level validation
│   ├── business_rules.py   # Business logic validation
│   └── web_scraper.py      # Web scraping engine
├── storage/
│   └── db_manager.py       # MongoDB integration
├── reports/
│   └── report_generator.py # PDF generation logic
├── ui/
│   ├── main_window.py      # GUI implementation
│   └── styles.py           # UI styling
├── main.py                 # Application entry point
├── requirements.txt        # Dependency list
└── README.md               # Documentation
```
