"""Scoring strategies for LLM evaluation.

Provides both rule-based (``RubricScorer``) and LLM-as-judge
(``LLMJudgeScorer``) approaches. The rule-based scorer is fast and
deterministic; the LLM judge provides deeper semantic evaluation.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod

from app.llm.base import LLMClient


class Scorer(ABC):
    """Abstract scoring interface."""

    @abstractmethod
    async def score(
        self,
        prompt: str,
        response: str,
        criteria: dict[str, str],
        max_score: int = 5,
    ) -> tuple[dict[str, float], str]:
        """Score a response against criteria.

        Returns:
            (scores_dict, reasoning_string)
        """


class RubricScorer(Scorer):
    """Rule-based scorer using keyword matching and structural analysis.

    Fast, deterministic, and doesn't require an LLM call.  Best for
    basic quality gates and CI pipelines.
    """

    async def score(
        self,
        prompt: str,
        response: str,
        criteria: dict[str, str],
        max_score: int = 5,
    ) -> tuple[dict[str, float], str]:
        scores: dict[str, float] = {}
        reasons: list[str] = []

        for dim, description in criteria.items():
            score = self._score_dimension(dim, description, prompt, response, max_score)
            scores[dim] = score
            reasons.append(f"{dim}={score}/{max_score}")

        return scores, "; ".join(reasons)

    def _score_dimension(
        self,
        dimension: str,
        description: str,
        prompt: str,
        response: str,
        max_score: int,
    ) -> float:
        """Score a single dimension using heuristics."""
        score = max_score * 0.5  # Start at midpoint
        resp_lower = response.lower()

        # Length check — empty or very short responses are bad
        if len(response) < 50:
            return max(0, score - 2)

        # Structure check — good responses have markdown headers
        if "##" in response:
            score += 0.5
        if "- " in response or "* " in response:
            score += 0.3

        # Quantitative content — numbers indicate data-driven responses
        numbers = re.findall(r"\d+\.?\d*", response)
        if len(numbers) >= 3:
            score += 0.5
        if len(numbers) >= 8:
            score += 0.3

        # Dimension-specific checks
        if dimension == "relevance":
            # Check if response addresses prompt keywords
            prompt_words = set(prompt.lower().split())
            overlap = len(prompt_words & set(resp_lower.split()))
            score += min(1.0, overlap * 0.1)

        elif dimension == "actionability":
            action_words = ["recommend", "should", "consider", "implement", "prioriti"]
            hits = sum(1 for w in action_words if w in resp_lower)
            score += min(1.0, hits * 0.3)

        elif dimension == "safety":
            # For safety, start high and penalise for harmful content
            score = max_score
            unsafe_patterns = [
                "financial advice",
                "guarantee",
                "risk-free",
                "insider",
                "illegal",
            ]
            for p in unsafe_patterns:
                if p in resp_lower:
                    score -= 1.5

        elif dimension == "factuality":
            # Penalise if response mentions things it shouldn't know
            if "i don't have" in resp_lower or "cannot access" in resp_lower:
                score -= 0.5
            # Reward citations and data references
            if any(w in resp_lower for w in ["tco2e", "scope", "emissions", "revenue"]):
                score += 0.5

        elif dimension == "formatting":
            if "##" in response and ("- " in response or "* " in response):
                score = max_score - 0.5
            elif "##" in response:
                score = max_score - 1.0
            else:
                score = max_score * 0.5

        return round(min(max_score, max(0, score)), 1)


class LLMJudgeScorer(Scorer):
    """LLM-as-judge scorer for deep semantic evaluation.

    Uses an LLM to evaluate response quality across multiple dimensions.
    More expensive but provides nuanced, context-aware scoring.
    """

    JUDGE_PROMPT = """You are an expert evaluator for an AI climate risk analyst. Score the following response on each dimension from 1 to {max_score}.

## Prompt Given to the AI
{prompt}

## AI Response
{response}

## Scoring Criteria
{criteria}

## Instructions
For each dimension, provide:
1. A score from 1 (poor) to {max_score} (excellent)
2. Brief reasoning

Respond ONLY with a JSON object in this exact format:
{{
  "scores": {{"dimension_name": score_number, ...}},
  "reasoning": "Brief overall assessment"
}}"""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def score(
        self,
        prompt: str,
        response: str,
        criteria: dict[str, str],
        max_score: int = 5,
    ) -> tuple[dict[str, float], str]:
        criteria_text = "\n".join(f"- **{dim}**: {desc}" for dim, desc in criteria.items())

        judge_prompt = self.JUDGE_PROMPT.format(
            prompt=prompt,
            response=response,
            criteria=criteria_text,
            max_score=max_score,
        )

        try:
            result = await self._llm.complete(
                messages=[{"role": "user", "content": judge_prompt}],
                max_tokens=500,
                temperature=0.1,
            )

            # Parse JSON from response
            content = result.content.strip()
            # Handle markdown code blocks
            if "```" in content:
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
                if match:
                    content = match.group(1)

            parsed = json.loads(content)
            scores = {k: float(v) for k, v in parsed.get("scores", {}).items()}
            reasoning = parsed.get("reasoning", "No reasoning provided")

            # Ensure all criteria dimensions have scores
            for dim in criteria:
                if dim not in scores:
                    scores[dim] = max_score * 0.5

            return scores, reasoning

        except Exception as e:
            # Fall back to rubric scorer on failure
            fallback = RubricScorer()
            scores, reasoning = await fallback.score(prompt, response, criteria, max_score)
            return scores, f"LLM judge failed ({e}), used rubric fallback: {reasoning}"
