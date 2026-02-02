import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("WorkProof")
logger.info("Initializing WorkProof Application...")

# Add the project root to sys.path so we can import from engine, storage, etc.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from ui.main_window import WorkProofApp

def main():
    app = QApplication(sys.argv)
    window = WorkProofApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
