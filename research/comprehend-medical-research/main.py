import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import app

if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        logging.critical("The application failed unexpectedly.", exc_info=True)
        sys.exit(1)