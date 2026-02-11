# WorkProof

WorkProof is a complete stand-alone desktop application designed to compare OCR-extracted data with web-scraped reference data. It automatically validates data accuracy by comparing two automated sources, providing real-time visual feedback and detailed performance reports.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Local Setup](#local-setup)
  - [Docker Setup](#docker-setup)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## ✨ Features

-   **Web Scraping**: Automatically extract reference data from websites using multiple HTML parsing strategies
-   **OCR Extraction**: Extract text from images using Tesseract OCR with advanced preprocessing
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
-   **Field-Specific Validation**: Custom validation rules for DOB, VIN, SSN, and other fields

## 🛠️ Tech Stack

-   **UI Framework**: PySide6 (Qt for Python)
-   **Web Scraping**: requests, BeautifulSoup4, lxml
-   **Screen Capture**: mss, Pillow
-   **OCR Engine**: pytesseract (Tesseract OCR wrapper)
-   **Text Comparison**: difflib, python-Levenshtein
-   **Report Generation**: reportlab
-   **Database**: MongoDB (pymongo)
-   **Containerization**: Docker

## 📦 Prerequisites

### For Local Setup:
-   **Python 3.8+** (Python 3.10 recommended)
-   **MongoDB**: Must be installed and running on `localhost:27017`
-   **Tesseract OCR**: Required for OCR extraction from images
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`

### For Docker Setup:
-   **Docker**: Version 20.10+
-   **Docker Compose**: Version 2.0+ (optional, for multi-container setup)

## 🚀 Installation

### Local Setup

1.  **Clone the Repository**:

    ```bash
    git clone https://github.com/AshrayVB30/WorkProof.git
    cd WorkProof
    ```

2.  **Create Virtual Environment** (Choose one):

    **Using Conda:**
    ```bash
    conda create -n workproof python=3.10 -y
    conda activate workproof
    ```

    **Using venv:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**:

    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

4.  **Start MongoDB**:

    Make sure MongoDB is running on `localhost:27017`. 
    
    ```bash
    # Windows (if installed as service)
    net start MongoDB
    
    # macOS/Linux
    mongod --dbpath /path/to/data/directory
    ```

5.  **Run the Application**:

    ```bash
    python main.py
    ```

### Docker Setup (Browser-based Access)

The easiest way to run the application with all dependencies (including MongoDB and Tesseract) is using Docker Compose. This setup allows you to access the GUI directly through your web browser.

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/AshrayVB30/WorkProof.git
    cd WorkProof
    ```

2.  **Start the Environment**:
    ```bash
    docker-compose up -d --build
    ```

3.  **Access the Application**:
    Open your web browser and go to:
    [http://localhost:6080/vnc.html](http://localhost:6080/vnc.html)

4.  **How it works**:
    - The application runs inside a headless container using a virtual display (Xvfb).
    - A VNC server exports this display.
    - NoVNC provides a web interface to the VNC server.
    - MongoDB data, screenshots, and reports are persisted in your local directory.

## 📖 Usage

1.  **Load Image**: Click "📁 Load Image" and select an image file (PNG, JPG, JPEG) containing data to extract
2.  **OCR Extraction**: Application automatically extracts text using Tesseract OCR with preprocessing
3.  **Enter Website URL**: Type the URL of the website containing reference data
4.  **Scrape Website**: Click "🌐 Scrape Website" to extract data from the website
5.  **Review Comparison**: Check the comparison table for color-coded matches/mismatches
6.  **Start Session**: Click "▶ Start Comparison" to begin tracking the session with screenshots
7.  **Monitor Stats**: Observe real-time accuracy and mismatch counts in the status bar
8.  **Stop & Report**: Click "⏹ Stop Session" to save data, and "📄 Generate Report" to create a PDF summary

### Supported Data Fields

The application can extract and validate the following fields:
- **Name** (First Name, Last Name, Full Name)
- **Date of Birth (DOB)**
- **Social Security Number (SSN)**
- **Vehicle Identification Number (VIN)**
- **License Number**
- **Address** (Street, City, State, ZIP)
- **Custom Fields** (configurable)

## 📁 Project Structure

```text
WorkProof/
├── engine/
│   ├── monitor.py              # Screen capture and session monitoring
│   ├── field_validator.py      # Field-level validation logic
│   ├── business_rules.py       # Business logic validation rules
│   ├── web_scraper.py          # Web scraping engine with multiple strategies
│   └── new_field_definitions.py # Extended field definitions and mappings
├── storage/
│   └── db_manager.py           # MongoDB integration and data persistence
├── reports/
│   └── report_generator.py     # PDF report generation with charts
├── ui/
│   ├── main_window.py          # Main GUI implementation (contains OCR parsing)
│   └── styles.py               # UI styling and themes
├── debug_*.py                  # Debug utilities for testing components
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── .dockerignore               # Docker ignore patterns
├── .gitignore                  # Git ignore patterns
└── README.md                   # This file
```

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Getting Started

1.  **Fork the Repository**: Click the "Fork" button at the top right of this page

2.  **Clone Your Fork**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/WorkProof.git
    cd WorkProof
    ```

3.  **Create a Branch**:
    ```bash
    git checkout -b feature/your-feature-name
    ```

4.  **Make Your Changes**: 
    - Write clean, documented code
    - Follow existing code style and conventions
    - Add comments for complex logic
    - Update documentation if needed

5.  **Test Your Changes**:
    ```bash
    python main.py
    # Test the specific functionality you modified
    ```

6.  **Commit Your Changes**:
    ```bash
    git add .
    git commit -m "Add: Brief description of your changes"
    ```

7.  **Push to Your Fork**:
    ```bash
    git push origin feature/your-feature-name
    ```

8.  **Create a Pull Request**: 
    - Go to the original repository
    - Click "New Pull Request"
    - Select your fork and branch
    - Describe your changes in detail

### Contribution Guidelines

-   **Code Style**: Follow PEP 8 guidelines for Python code
-   **Commit Messages**: Use clear, descriptive commit messages
    - `Add:` for new features
    - `Fix:` for bug fixes
    - `Update:` for improvements to existing features
    - `Refactor:` for code refactoring
    - `Docs:` for documentation changes
-   **Documentation**: Update README and code comments as needed
-   **Testing**: Test your changes thoroughly before submitting
-   **Issues**: Check existing issues before creating new ones

### Areas for Contribution

-   🐛 Bug fixes and error handling improvements
-   ✨ New features (e.g., additional OCR engines, new validation rules)
-   📝 Documentation improvements
-   🎨 UI/UX enhancements
-   ⚡ Performance optimizations
-   🧪 Test coverage improvements
-   🌐 Internationalization (i18n) support

## 🔧 Troubleshooting

### Common Issues

#### 1. **Tesseract Not Found**
```
Error: Tesseract is not installed or not in PATH
```
**Solution**: 
- Install Tesseract OCR (see Prerequisites)
- Add Tesseract to your system PATH
- On Windows, verify installation path (usually `C:\Program Files\Tesseract-OCR`)

#### 2. **MongoDB Connection Error**
```
Error: Could not connect to MongoDB
```
**Solution**:
- Ensure MongoDB is running: `mongod` or `net start MongoDB`
- Check if MongoDB is listening on `localhost:27017`
- Verify MongoDB service is started

#### 3. **Module Import Errors**
```
ModuleNotFoundError: No module named 'PySide6'
```
**Solution**:
- Activate your virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

#### 4. **OCR Extraction Returns Empty Results**
**Solution**:
- Ensure image quality is good (high resolution, clear text)
- Check if Tesseract is properly installed
- Try preprocessing the image (increase contrast, remove noise)

#### 5. **GUI Not Displaying on Docker**
**Solution**:
- Docker GUI support requires X11 forwarding (Linux/macOS)
- For best experience, run the application locally
- Alternatively, use VNC or remote desktop solutions

### Debug Tools

The project includes several debug utilities:

```bash
# Test OCR extraction
python debug_ocr_raw.py

# Test web scraping
python debug_scraper.py

# Test application logic
python debug_app_logic.py

# Verify Tesseract installation
python verify_tesseract.py
```

### Getting Help

-   📫 **Issues**: [Create an issue](https://github.com/AshrayVB30/WorkProof/issues)
-   💬 **Discussions**: Use GitHub Discussions for questions
-   📧 **Email**: Contact the maintainers (see GitHub profile)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

-   **Tesseract OCR** - Google's open-source OCR engine
-   **PySide6** - Qt for Python framework
-   **MongoDB** - NoSQL database for data storage
-   **ReportLab** - PDF generation library

---

**Made by the WorkProof Team**

If you find this project useful, please consider giving it a ⭐ on GitHub!
