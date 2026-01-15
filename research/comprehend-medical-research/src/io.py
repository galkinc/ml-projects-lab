from pathlib import Path
from typing import List, Tuple
import json
from datetime import datetime, timezone

def load_examples_dir(dir_path: str) -> List[Tuple[str, str]]:
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
    response: dict,
    experiment_dir: Path,
    examples_root_path: str
):
    safe_name = sanitize_name(example_name)
    out_dir = experiment_dir / f"{index}_{safe_name}"
    out_dir.mkdir(parents=True, exist_ok=True)

    input_data = {
        "text": text,
        "metadata": {
            "source_file": f"{examples_root_path}/{example_name}.txt",
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
    
    return out_dir