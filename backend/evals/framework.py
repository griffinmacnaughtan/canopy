"""Core evaluation framework.

Defines the data structures and execution engine for running LLM
evaluation suites. Each ``EvalCase`` specifies an input prompt,
expected behaviour criteria, and scoring rubric. The ``EvalRunner``
orchestrates execution and scoring across a dataset.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import structlog

from app.llm.base import LLMClient

from .scorers import RubricScorer, Scorer

logger = structlog.get_logger()


@dataclass
class EvalCase:
    """A single evaluation test case.

    Attributes:
        id: Unique identifier for the case.
        category: Classification — ``good_prompt``, ``bad_prompt``,
                  ``adversarial``, ``edge_case``, ``domain_accuracy``.
        prompt: The input prompt to send to the LLM.
        criteria: Dict of scoring dimensions to expected behaviour
                  descriptions.  Passed to the scorer for evaluation.
        context: Optional portfolio/document context to inject.
        expected_keywords: Keywords that SHOULD appear in a good response.
        forbidden_keywords: Keywords that must NOT appear in a response.
        max_score: Maximum possible score per dimension (default 5).
        pass_threshold: Minimum average score to pass (default 3.0).
    """

    id: str
    category: str
    prompt: str
    criteria: dict[str, str]
    context: str | None = None
    expected_keywords: list[str] = field(default_factory=list)
    forbidden_keywords: list[str] = field(default_factory=list)
    max_score: int = 5
    pass_threshold: float = 3.0
    # Ground-truth fields for domain accuracy evaluation
    expected_answer: str | None = None
    expected_values: dict[str, float] = field(default_factory=dict)
    expected_entities: list[str] = field(default_factory=list)


@dataclass
class EvalResult:
    """Result of evaluating a single case."""

    case_id: str
    category: str
    prompt: str
    response: str
    scores: dict[str, float]
    avg_score: float
    passed: bool
    reasoning: str
    duration_ms: float = 0
    keyword_hits: list[str] = field(default_factory=list)
    keyword_violations: list[str] = field(default_factory=list)


@dataclass
class EvalSuiteResult:
    """Aggregated results for an entire eval suite."""

    dataset: str
    total_cases: int
    passed: int
    failed: int
    pass_rate: float
    avg_scores: dict[str, float]
    results: list[EvalResult]
    duration_ms: float

    def summary(self) -> str:
        """Human-readable summary of the eval run."""
        lines = [
            f"## Eval Results: {self.dataset}",
            f"- Total: {self.total_cases} | Passed: {self.passed} | Failed: {self.failed}",
            f"- Pass rate: {self.pass_rate:.1%}",
            f"- Duration: {self.duration_ms:.0f}ms",
            "",
            "### Average Scores",
        ]
        for dim, score in sorted(self.avg_scores.items()):
            lines.append(f"- {dim}: {score:.2f}/5.0")

        lines.append("")
        lines.append("### Failed Cases")
        for r in self.results:
            if not r.passed:
                lines.append(f"- [{r.case_id}] ({r.category}): avg={r.avg_score:.2f}")
                lines.append(f"  Prompt: {r.prompt[:80]}...")

        return "\n".join(lines)


class EvalRunner:
    """Executes eval cases against an LLM and scores the responses.

    The runner manages the full lifecycle: generating LLM responses,
    scoring them against criteria, checking keyword requirements,
    and aggregating results.
    """

    def __init__(
        self,
        llm: LLMClient,
        scorer: Scorer | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._llm = llm
        self._scorer = scorer or RubricScorer()
        self._system_prompt = system_prompt

    async def _generate_response(self, case: EvalCase) -> str:
        """Generate an LLM response for an eval case."""
        user_content = case.prompt
        if case.context:
            user_content = f"{case.context}\n\n{case.prompt}"

        messages = [{"role": "user", "content": user_content}]
        response = await self._llm.complete(
            messages=messages,
            system_prompt=self._system_prompt,
            max_tokens=1500,
            temperature=0.3,
        )
        return response.content

    def _check_keywords(self, response: str, case: EvalCase) -> tuple[list[str], list[str]]:
        """Check expected and forbidden keywords."""
        response_lower = response.lower()
        hits = [kw for kw in case.expected_keywords if kw.lower() in response_lower]
        violations = [kw for kw in case.forbidden_keywords if kw.lower() in response_lower]
        return hits, violations

    async def run_case(self, case: EvalCase) -> EvalResult:
        """Execute and score a single eval case."""
        start = time.perf_counter()

        try:
            response = await self._generate_response(case)
        except Exception as e:
            logger.error("eval_generation_error", case_id=case.id, error=str(e))
            return EvalResult(
                case_id=case.id,
                category=case.category,
                prompt=case.prompt,
                response=f"ERROR: {e}",
                scores=dict.fromkeys(case.criteria, 0),
                avg_score=0,
                passed=False,
                reasoning=f"LLM generation failed: {e}",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        # Score with the configured scorer.
        # If the scorer supports ground-truth checking and the case has
        # expected values, use the extended interface.
        if hasattr(self._scorer, "score_with_ground_truth") and (
            case.expected_values or case.expected_entities
        ):
            scores, reasoning = await self._scorer.score_with_ground_truth(
                prompt=case.prompt,
                response=response,
                criteria=case.criteria,
                max_score=case.max_score,
                expected_values=case.expected_values,
                expected_entities=case.expected_entities,
            )
        else:
            scores, reasoning = await self._scorer.score(
                prompt=case.prompt,
                response=response,
                criteria=case.criteria,
                max_score=case.max_score,
            )

        # Keyword checks
        hits, violations = self._check_keywords(response, case)

        # Apply keyword penalties
        if violations:
            for dim in scores:
                scores[dim] = max(0, scores[dim] - 1.0)
            reasoning += f" | Keyword violations: {violations}"

        avg_score = sum(scores.values()) / len(scores) if scores else 0
        passed = avg_score >= case.pass_threshold and len(violations) == 0

        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "eval_case_complete",
            case_id=case.id,
            category=case.category,
            avg_score=round(avg_score, 2),
            passed=passed,
            duration_ms=round(duration_ms, 1),
        )

        return EvalResult(
            case_id=case.id,
            category=case.category,
            prompt=case.prompt,
            response=response,
            scores=scores,
            avg_score=round(avg_score, 2),
            passed=passed,
            reasoning=reasoning,
            duration_ms=round(duration_ms, 1),
            keyword_hits=hits,
            keyword_violations=violations,
        )

    async def run_suite(
        self,
        cases: list[EvalCase],
        dataset_name: str = "unnamed",
    ) -> EvalSuiteResult:
        """Run a complete evaluation suite.

        Args:
            cases: List of eval cases to execute.
            dataset_name: Name for reporting.

        Returns:
            Aggregated ``EvalSuiteResult``.
        """
        start = time.perf_counter()
        results: list[EvalResult] = []

        for case in cases:
            result = await self.run_case(case)
            results.append(result)

        # Aggregate scores
        all_dims: dict[str, list[float]] = {}
        for r in results:
            for dim, score in r.scores.items():
                all_dims.setdefault(dim, []).append(score)

        avg_scores = {dim: sum(vals) / len(vals) for dim, vals in all_dims.items()}

        passed = sum(1 for r in results if r.passed)
        total = len(results)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "eval_suite_complete",
            dataset=dataset_name,
            total=total,
            passed=passed,
            pass_rate=round(passed / total, 2) if total > 0 else 0,
            duration_ms=round(duration_ms, 1),
        )

        return EvalSuiteResult(
            dataset=dataset_name,
            total_cases=total,
            passed=passed,
            failed=total - passed,
            pass_rate=round(passed / total, 4) if total > 0 else 0,
            avg_scores={k: round(v, 2) for k, v in avg_scores.items()},
            results=results,
            duration_ms=round(duration_ms, 1),
        )
