import logging
from pathlib import Path
from datetime import datetime, timezone
import time

from config import settings

from .io import load_examples_dir, save_artifacts
from .aws import create_comprehend_client, analyze_text

logging.Formatter.converter = time.gmtime
if not settings.boto3_logging:
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
logging.basicConfig(level=settings.logging_level, format=settings.logging_format)

def get_next_run_id(output_root: str, date_str: str) -> int:
    """Find the next run number for today (e.g., 1, 2, 3...)."""
    base_path = Path(output_root)
    existing_runs = [
        d.name for d in base_path.iterdir()
        if d.is_dir() and d.name.startswith(date_str)
    ]
    if not existing_runs:
        return 1
    # Extract run numbers like "15_01_2026_3" -> 3
    run_numbers = []
    for name in existing_runs:
        try:
            run_num = int(name.split("_")[-1])
            run_numbers.append(run_num)
        except ValueError:
            logging.error(f"Format Error in an existed running name. File name: {name}")
            continue
    return max(run_numbers) + 1 if run_numbers else 1

def run_experiment():
    if not Path(settings.examples_path).exists():
        error_msg = f"Examples directory not found. Path in the config: {settings.examples_path}"
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logging.info("Initializing settings...")

    # === Prepare experiment directory ===
    today = datetime.now().strftime("%d_%m_%Y")  # e.g., "15_01_2026"
    output_root = Path(settings.aws_comp_output_path)
    run_id = get_next_run_id(output_root, today)
    experiment_dir = output_root / f"{today}_{run_id}"

    logging.info(f"Starting experiment: {experiment_dir.name}")

    examples = load_examples_dir(settings.examples_path)
    if not examples:
        error_msg = (f"No .txt files found in {settings.examples_path}/")
        logging.warning(error_msg)
        raise FileNotFoundError(error_msg)


    try:
        client = create_comprehend_client(settings.get_boto_kwargs())

        for idx, (name, text) in enumerate(examples, start=1):
            logging.info(f"Processing [{idx}/{len(examples)}]: {name}")

            if len(text) > settings.aws_comp_limit: 
                logging.warning(f"Text too long for {name} ({len(text)} chars). Truncating to {settings.aws_comp_limit}.")
                text = text[:settings.aws_comp_limit]

            try:
                response = analyze_text(client, text)
                out_dir = save_artifacts(name, idx, text, response, experiment_dir, settings.examples_path)
                logging.info(f"Saved artifacts to: {out_dir}")
            except Exception as e:
                logging.error(f"Failed on {name}: {e}")

        logging.info(f"Experiment completed. Results in: {experiment_dir}")

    except Exception as e:
        logging.error(f"An unexpected error occurred in main: {e}")
