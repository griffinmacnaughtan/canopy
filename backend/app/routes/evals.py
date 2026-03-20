"""Eval framework API endpoints.

Exposes the evaluation suite via HTTP so evals can be triggered from
the frontend dashboard or CI/CD pipelines.
"""

import structlog
from fastapi import APIRouter

from ..exceptions import LLMError, ValidationError
from ..llm import get_llm_client
from ..llm.prompts import SYSTEM_PROMPT
from ..models import EvalCaseResult, EvalRunRequest, EvalRunResponse

router = APIRouter(tags=["Evals"])
logger = structlog.get_logger()


@router.post("/evals/run", response_model=EvalRunResponse)
async def run_evals(body: EvalRunRequest):
    """Run an LLM evaluation suite.

    Executes test cases from the specified dataset, scores each response
    using the rubric scorer, and returns aggregated results.
    """
    from evals.datasets import DATASETS
    from evals.framework import EvalRunner
    from evals.scorers import RubricScorer

    if body.dataset not in DATASETS:
        raise ValidationError(
            f"Unknown dataset '{body.dataset}'. Available: {', '.join(DATASETS.keys())}"
        )

    cases = DATASETS[body.dataset]
    if body.max_cases:
        cases = cases[: body.max_cases]

    try:
        llm = get_llm_client()
        scorer = RubricScorer()
        runner = EvalRunner(llm=llm, scorer=scorer, system_prompt=SYSTEM_PROMPT)
        suite_result = await runner.run_suite(cases, dataset_name=body.dataset)
    except Exception as e:
        logger.error("eval_run_error", error=str(e))
        raise LLMError(f"Eval execution failed: {str(e)[:200]}") from e

    results = [
        EvalCaseResult(
            case_id=r.case_id,
            category=r.category,
            prompt=r.prompt,
            response=r.response[:500],  # Truncate for response size
            scores=r.scores,
            passed=r.passed,
            reasoning=r.reasoning,
        )
        for r in suite_result.results
    ]

    return EvalRunResponse(
        dataset=suite_result.dataset,
        total_cases=suite_result.total_cases,
        passed=suite_result.passed,
        failed=suite_result.failed,
        pass_rate=suite_result.pass_rate,
        avg_scores=suite_result.avg_scores,
        results=results,
        duration_ms=suite_result.duration_ms,
    )
