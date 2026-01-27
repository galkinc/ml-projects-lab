from typing import Dict, List

import numpy as np


class MetricsCalculator:
    @staticmethod
    def calculate_percentiles(latencies: List[float]) -> Dict[str, float]:
        """Calculates p50, p90, p95, p99 and other stats."""
        if not latencies:
            return {}
        return {
            "p50": float(np.percentile(latencies, 50)),
            "p90": float(np.percentile(latencies, 90)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99)),
            "mean": float(np.mean(latencies)),
            "min": float(np.min(latencies)),
            "max": float(np.max(latencies)),
            "count": len(latencies),
        }
