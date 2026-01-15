import json
from pathlib import Path
import logging
from typing import Any, Dict
import time
from datetime import datetime, timezone

import boto3

from config import settings

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

def load_examples_dir(dir_path: str = "examples") -> list[tuple[str, str]]:
    """Load .txt files sorted by name, return [(stem, content), ...]."""
    examples = []
    for file in sorted(Path(dir_path).glob("*.txt")):
        with open(file, encoding="utf-8") as f:
            examples.append((file.stem, f.read().strip()))
    return examples

def sanitize_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name)

def save_artifacts(
    example_name: str,
    index: int,
    text: str,
    response: Dict[Any, Any],
    experiment_dir: Path
):
    """Save input.json and output.json into a subfolder named {index}_{example_name}."""
    safe_name = sanitize_name(example_name)
    out_dir = experiment_dir / f"{index}_{safe_name}"
    out_dir.mkdir(parents=True, exist_ok=True)

    input_data = {
        "text": text,
        "metadata": {
            "source_file": f"examples/{example_name}.txt",
            "character_count": len(text),
            "language": "en",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "api_method": "DetectEntitiesV2"
        }
    }

    with open(out_dir / "input.json", "w", encoding="utf-8") as f:
        json.dump(input_data, f, indent=2, ensure_ascii=False)

    with open(out_dir / "output.json", "w", encoding="utf-8") as f:
        json.dump(response, f, indent=2, default=str)

    logging.info(f"Saved: {out_dir}")


def main():
    if not Path(settings.examples_path).exists():
        logging.error(f"Examples directory not found: {settings.examples_path}")
        return
    
    logging.info("Initializing settings...")
    
    # === Prepare experiment directory ===
    today = datetime.now().strftime("%d_%m_%Y")  # e.g., "15_01_2026"
    output_root = Path(settings.aws_comp_output_path)
    run_id = get_next_run_id(output_root, today)
    experiment_dir = output_root / f"{today}_{run_id}"

    logging.info(f"Starting experiment: {experiment_dir.name}")
    
    examples = load_examples_dir()
    if not examples:
        logging.warning(f"No .txt files found in {settings.examples_path}/")
        return

    try:
        boto_kwargs = settings.get_boto_kwargs()
        client = boto3.client("comprehendmedical", **boto_kwargs)

        for idx, (name, text) in enumerate(examples, start=1):
            logging.info(f"Processing [{idx}/{len(examples)}]: {name}")

            if len(text) > settings.aws_comp_limit:  # AWS Comprehend Medical limit
                logging.warning(f"Text too long ({len(text)} chars). Truncating to 10KB.")
                text = text[:settings.aws_comp_limit]

            try:
                response = client.detect_entities_v2(Text=text)
                save_artifacts(name, idx, text, response, experiment_dir)
            except Exception as e:
                logging.error(f"Failed on {name}: {e}")

        logging.info(f"Experiment completed. Results in: {experiment_dir}")

    except Exception as e:
        logging.error(f"An unexpected error occurred in main: {e}")

if __name__ == "__main__":
    main()
