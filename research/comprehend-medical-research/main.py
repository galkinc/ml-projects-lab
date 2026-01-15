import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import run_experiment

if __name__ == "__main__":
    try:
        run_experiment()
    except Exception as e:
        logging.critical("Experiment failed", exc_info=True)
        sys.exit(1)