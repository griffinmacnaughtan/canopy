"""LLM evaluation framework for systematic quality assessment.

Evaluates copilot and agent responses against curated test cases
covering good prompts, bad prompts, adversarial inputs, and
domain-specific accuracy requirements.
"""

from .framework import EvalCase, EvalResult, EvalRunner
from .scorers import LLMJudgeScorer, RubricScorer

__all__ = [
    "EvalCase",
    "EvalResult",
    "EvalRunner",
    "LLMJudgeScorer",
    "RubricScorer",
]
