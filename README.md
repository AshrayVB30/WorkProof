# WorkProof

WorkProof is a complete stand-alone desktop application designed to monitor data entry accuracy in real-time. It validates user input against reference data, monitors screen content for session logging, and generates detailed performance reports.

## Features

-   **Live Validation**: Real-time accuracy calculation using Levenshtein distance.
-   **Mistake Detection**: Highlights and counts insertions, deletions, and substitutions.
-   **Two-Panel Interface**: Source panel (left) and entry panel (right) for efficient work tracking.
-   **Session Monitoring**: Automatic screen capture at session start.
-   **Local Storage**: All history is stored locally in MongoDB for privacy and offline use.
-   **PDF Reports**: Generate detailed accuracy reports including time spent and mismatch logs.

## Tech Stack

-   **UI**: PySide6
-   **Screen Capture**: mss, Pillow
-   **OCR**: pytesseract (Optional)
-   **Text Logic**: difflib, python-Levenshtein
-   **Reporting**: reportlab
-   **Database**: MongoDB

## Prerequisites

-   **Python 3.8+**
-   **MongoDB**: Must be installed and running on `localhost:27017`.
-   **Tesseract OCR**: (Optional) Required if OCR features are enabled.

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

1.  **Load Reference**: Click "Load Reference Data" and select a `.txt` or `.csv` file.
2.  **Start Session**: Click "Start Session" to begin monitoring.
3.  **Data Entry**: Type the reference text into the right panel.
4.  **Monitor Stats**: Observe real-time accuracy and error counts in the status bar.
5.  **Stop & Report**: Click "Stop Session" to save data, and "Generate Report" to create a PDF summary.

## Project Structure

```text
WorkProof_Basic/
├── engine/
│   ├── monitor.py      # Screen capture logic
│   └── validator.py    # Text comparison engine
├── storage/
│   └── db_manager.py   # MongoDB integration
├── reports/
│   └── report_generator.py # PDF generation logic
├── ui/
│   └── main_window.py  # GUI implementation
├── main.py             # Application entry point
├── requirements.txt    # Dependency list
└── README.md           # Documentation
```
