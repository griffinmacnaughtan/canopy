"""CLI entry point for running LLM evaluations.

Usage:
    python -m evals.run_evals                          # Run all datasets
    python -m evals.run_evals --dataset climate_copilot  # Specific dataset
    python -m evals.run_evals --dataset safety --scorer llm  # LLM-as-judge
    python -m evals.run_evals --max-cases 5            # Limit cases
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.llm import get_llm_client
from app.llm.prompts import SYSTEM_PROMPT

from .datasets import DATASETS
from .framework import EvalRunner
from .scorers import LLMJudgeScorer, RubricScorer


async def main(
    dataset: str = "all",
    scorer_type: str = "rubric",
    max_cases: int | None = None,
) -> int:
    """Run evaluation suite and print results."""
    if dataset not in DATASETS:
        print(f"Unknown dataset '{dataset}'. Available: {', '.join(DATASETS.keys())}")
        return 1

    cases = DATASETS[dataset]
    if max_cases:
        cases = cases[:max_cases]

    llm = get_llm_client()

    if scorer_type == "llm":
        scorer = LLMJudgeScorer(llm=llm)
    else:
        scorer = RubricScorer()

    runner = EvalRunner(llm=llm, scorer=scorer, system_prompt=SYSTEM_PROMPT)
    result = await runner.run_suite(cases, dataset_name=dataset)

    print(result.summary())
    print()

    if result.pass_rate < 0.7:
        print(f"FAIL: Pass rate {result.pass_rate:.1%} is below 70% threshold")
        return 1

    print(f"PASS: {result.pass_rate:.1%} pass rate")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Canopy LLM evaluations")
    parser.add_argument(
        "--dataset",
        default="all",
        choices=list(DATASETS.keys()),
        help="Which eval dataset to run",
    )
    parser.add_argument(
        "--scorer",
        default="rubric",
        choices=["rubric", "llm"],
        help="Scoring strategy (rubric=fast/deterministic, llm=deep/semantic)",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="Maximum number of cases to run",
    )

    args = parser.parse_args()
    exit_code = asyncio.run(main(args.dataset, args.scorer, args.max_cases))
    sys.exit(exit_code)
