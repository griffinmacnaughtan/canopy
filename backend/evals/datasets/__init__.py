"""Eval datasets for Canopy LLM quality assessment."""

from .climate_copilot import CLIMATE_COPILOT_CASES
from .safety import SAFETY_CASES

DATASETS: dict[str, list] = {
    "climate_copilot": CLIMATE_COPILOT_CASES,
    "safety": SAFETY_CASES,
    "all": CLIMATE_COPILOT_CASES + SAFETY_CASES,
}

__all__ = ["CLIMATE_COPILOT_CASES", "DATASETS", "SAFETY_CASES"]
