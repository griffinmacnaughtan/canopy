"""Scoring strategies for LLM evaluation.

Provides rule-based (``RubricScorer``), LLM-as-judge (``LLMJudgeScorer``),
and ground-truth (``FactualAccuracyScorer``) approaches.
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


class FactualAccuracyScorer(Scorer):
    """Scorer that checks factual accuracy against ground-truth values.

    Unlike ``RubricScorer`` (formatting heuristics) and ``LLMJudgeScorer``
    (semantic LLM evaluation), this scorer compares extracted numeric
    values and entity mentions against **known correct answers** computed
    from the seed data.

    Scoring methodology:

    1. **Numeric accuracy** -- extract all numbers from the LLM response,
       check whether each expected value appears within a configurable
       tolerance (default ±10 %).
    2. **Entity recall** -- verify that required entity names (companies,
       sectors) appear in the response.
    3. **Combined score** -- weighted average of numeric accuracy (60 %)
       and entity recall (40 %).
    """

    def __init__(self, tolerance: float = 0.10) -> None:
        self._tolerance = tolerance

    async def score(
        self,
        prompt: str,
        response: str,
        criteria: dict[str, str],
        max_score: int = 5,
    ) -> tuple[dict[str, float], str]:
        """Fall back to rubric scoring when no ground-truth is provided."""
        fallback = RubricScorer()
        return await fallback.score(prompt, response, criteria, max_score)

    async def score_with_ground_truth(
        self,
        prompt: str,
        response: str,
        criteria: dict[str, str],
        max_score: int = 5,
        expected_values: dict[str, float] | None = None,
        expected_entities: list[str] | None = None,
    ) -> tuple[dict[str, float], str]:
        """Score a response against ground-truth numeric values and entities.

        Args:
            prompt: The original prompt.
            response: The LLM response to evaluate.
            criteria: Scoring dimensions (used for output keys).
            max_score: Maximum score per dimension.
            expected_values: ``{label: numeric_value}`` pairs to check.
            expected_entities: Entity names that must appear in the response.

        Returns:
            ``(scores_dict, reasoning_string)``
        """
        reasons: list[str] = []
        expected_values = expected_values or {}
        expected_entities = expected_entities or []

        # ── Numeric accuracy ────────────────────────────────────────
        numeric_score = max_score  # Start perfect, deduct for misses
        response_numbers = self._extract_numbers(response)

        value_hits = 0
        value_misses: list[str] = []

        for label, expected in expected_values.items():
            if self._number_found(expected, response_numbers):
                value_hits += 1
            else:
                value_misses.append(f"{label}={expected:,.0f}")
                numeric_score -= max_score / max(len(expected_values), 1)

        numeric_score = max(0.0, numeric_score)

        if expected_values:
            reasons.append(f"Numeric: {value_hits}/{len(expected_values)} values found")
            if value_misses:
                reasons.append(f"Missing: {', '.join(value_misses)}")

        # ── Entity recall ───────────────────────────────────────────
        entity_score = max_score
        resp_lower = response.lower()

        entity_hits = 0
        entity_misses: list[str] = []

        for entity in expected_entities:
            if entity.lower() in resp_lower:
                entity_hits += 1
            else:
                entity_misses.append(entity)
                entity_score -= max_score / max(len(expected_entities), 1)

        entity_score = max(0.0, entity_score)

        if expected_entities:
            reasons.append(f"Entities: {entity_hits}/{len(expected_entities)} found")
            if entity_misses:
                reasons.append(f"Missing entities: {', '.join(entity_misses)}")

        # ── Combine into per-criterion scores ───────────────────────
        # Weight: 60% numeric, 40% entity
        has_values = bool(expected_values)
        has_entities = bool(expected_entities)

        if has_values and has_entities:
            combined = numeric_score * 0.6 + entity_score * 0.4
        elif has_values:
            combined = numeric_score
        elif has_entities:
            combined = entity_score
        else:
            combined = max_score * 0.5

        combined = round(min(max_score, combined), 1)

        scores = dict.fromkeys(criteria, combined)
        return scores, "; ".join(reasons)

    def _extract_numbers(self, text: str) -> list[float]:
        """Extract all numeric values from text, handling commas."""
        # Match numbers with optional commas and decimals
        raw = re.findall(r"[\d,]+\.?\d*", text)
        results = []
        for r in raw:
            try:
                results.append(float(r.replace(",", "")))
            except ValueError:
                continue
        return results

    def _number_found(
        self,
        expected: float,
        found_numbers: list[float],
    ) -> bool:
        """Check if the expected value appears in the extracted numbers."""
        if expected == 0:
            return 0.0 in found_numbers

        return any(abs(num - expected) / abs(expected) <= self._tolerance for num in found_numbers)
