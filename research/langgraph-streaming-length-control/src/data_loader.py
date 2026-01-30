import logging
from pathlib import Path
from typing import Dict, List, NamedTuple

import numpy as np
import pandas as pd

from config import settings

logger = logging.getLogger(__name__)


class PromptSample(NamedTuple):

    prompt_id: str
    category: str
    prompt: str
    complexity: str  # 'Low', 'Medium', 'High'


class DataLoader:
    def __init__(self, data_path: str = "data/mtbench_prompts.parquet") -> None:
        self.data_path = Path(data_path)
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found at {self.data_path}")

    def _process_text(self, text: object) -> str:
        """Helper to convert prompt content to string."""
        if isinstance(text, (list, pd.Series, np.ndarray)):
            return " ".join([str(t) for t in text])
        return str(text) if text is not None else ""

    def _categorize_complexity(self, text: str, category: str) -> str:
        """
        Categorize prompt complexity based on category and length using config.
        """
        # Simple estimation based on config factor
        approx_tokens = (
            len(text.split()) * settings.data_loader.tokens_per_word_estimate
        )

        # Check explicit category mappings first (High priority)
        if category in settings.data_loader.complexity_categories_map.get("High", []):
            return "High"
        if category in settings.data_loader.complexity_categories_map.get("Medium", []):
            return "Medium"

        # Fallback to length-based thresholds
        thresholds = settings.data_loader.complexity_thresholds
        if approx_tokens > thresholds.get("Medium", 100):
            return "High"
        elif approx_tokens >= thresholds.get("Low", 50):
            return "Medium"
        else:
            return "Low"

    def load_prompts(self) -> Dict[str, List[PromptSample]]:
        """
        Load prompts from parquet and categorize them.
        Returns a dictionary mapping complexity levels to lists of PromptSamples.
        """
        try:
            df = pd.read_parquet(self.data_path)
            logger.info(f"Loaded {len(df)} prompts from {self.data_path}")

            # Ensure required columns exist
            required_cols = ["category", "prompt", "prompt_id"]
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"Missing required columns. Found: {df.columns}")

            samples = {"Low": [], "Medium": [], "High": []}

            for _, row in df.iterrows():
                raw_text = row["prompt"]
                category = row["category"]

                # Process text first to ensure it is a string
                prompt_text = self._process_text(raw_text)

                complexity = self._categorize_complexity(prompt_text, category)

                sample = PromptSample(
                    prompt_id=str(row["prompt_id"]),
                    category=category,
                    prompt=prompt_text,
                    complexity=complexity,
                )
                samples[complexity].append(sample)

            logger.info(
                f"Categorization results: Low={len(samples['Low'])}, "
                "Medium={len(samples['Medium'])}, High={len(samples['High'])}"
            )
            return samples

        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            raise


if __name__ == "__main__":
    loader = DataLoader()
    data = loader.load_prompts()
    print("Example Low complexity prompt:", data["Low"][0].prompt[:50] + "...")
