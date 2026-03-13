"""AI Copilot endpoints with streaming and RAG."""

from typing import AsyncIterator, Optional
import structlog

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database.connection import get_db, async_session_factory
from ..database.seed import SECTOR_BASELINES
from ..database.pipeline_models import EmissionsData, ClimateData
from ..models import CopilotRequest, CopilotResponse, CopilotStreamRequest
from ..risk import score_portfolio
from ..documents import get_combined_document_text
from ..llm import get_llm_client, SYSTEM_PROMPT, build_portfolio_context
from ..llm.prompts import build_user_message
from ..exceptions import ValidationError, LLMError
from .portfolios import get_portfolio_by_id, db_asset_to_pydantic
from .scoring import get_scenarios_dict

router = APIRouter()
logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)


async def get_pipeline_context(db: AsyncSession) -> Optional[str]:
    """Get summary of pipeline data for copilot context."""
    try:
        # Get emissions summary by sector
        sector_query = await db.execute(
            select(
                EmissionsData.sector,
                func.sum(EmissionsData.total_emissions_mt_co2e).label("total"),
                func.count().label("count"),
            )
            .where(EmissionsData.sector.isnot(None))
            .group_by(EmissionsData.sector)
            .order_by(desc("total"))
            .limit(10)
        )
        sector_rows = sector_query.all()

        if not sector_rows:
            return None

        # Get top emitters
        top_emitters_query = await db.execute(
            select(EmissionsData)
            .where(EmissionsData.total_emissions_mt_co2e.isnot(None))
            .order_by(desc(EmissionsData.total_emissions_mt_co2e))
            .limit(5)
        )
        top_emitters = top_emitters_query.scalars().all()

        # Build context
        context_parts = [
            "## Real EPA Emissions Data (GHGRP)",
            "",
            "### Emissions by Sector:",
        ]

        for row in sector_rows:
            total_mt = row.total or 0
            context_parts.append(
                f"- {row.sector}: {total_mt:,.0f} MT CO2e ({row.count} facilities)"
            )

        context_parts.append("")
        context_parts.append("### Top Emitting Facilities:")

        for e in top_emitters:
            context_parts.append(
                f"- {e.facility_name or 'Unknown'} ({e.state}): "
                f"{e.total_emissions_mt_co2e:,.0f} MT CO2e - {e.sector}"
            )

        return "\n".join(context_parts)

    except Exception as e:
        logger.warning("pipeline_context_error", error=str(e))
        return None


def calculate_confidence_score(
    question: str,
    has_documents: bool,
    portfolio_size: int,
) -> float:
    """
    Calculate confidence score for the response based on context quality.

    Factors:
    - Question specificity (longer questions tend to be more specific)
    - Document availability (more context = higher confidence)
    - Portfolio size (more data = higher confidence)

    Returns:
        Float between 0.0 and 1.0
    """
    base_score = 0.5

    # Question length factor (0-0.15)
    question_words = len(question.split())
    question_factor = min(0.15, question_words * 0.01)

    # Document factor (0-0.2)
    doc_factor = 0.2 if has_documents else 0.0

    # Portfolio size factor (0-0.15)
    portfolio_factor = min(0.15, portfolio_size * 0.02)

    confidence = base_score + question_factor + doc_factor + portfolio_factor

    return round(min(1.0, confidence), 2)


def get_source_attribution(
    has_documents: bool,
    document_count: int = 0,
    has_pipeline_data: bool = False,
) -> list:
    """
    Generate source attribution for the response.

    Returns:
        List of source citations
    """
    sources = [
        "Portfolio asset inventory",
        "Sector baseline risk factors (NGFS-aligned)",
        "Scenario library (NGFS-inspired)",
    ]

    if has_pipeline_data:
        sources.append("EPA GHGRP emissions data")

    if has_documents:
        sources.append(f"Uploaded documents ({document_count} files)")

    return sources


@router.post("/copilot", response_model=CopilotResponse)
async def copilot(
    request: CopilotRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a copilot response (non-streaming) using the configured LLM with RAG context."""
    portfolio = await get_portfolio_by_id(request.portfolio_id, db)
    pydantic_assets = [db_asset_to_pydantic(a) for a in portfolio.assets]
    scenarios = await get_scenarios_dict(db)

    # Build the same rich context as the streaming endpoint
    overall, climate, transition, physical, opportunity, top_risks, quick_wins, sector = score_portfolio(
        pydantic_assets, SECTOR_BASELINES
    )

    scores = {
        "overall_score": overall,
        "climate_risk": climate,
        "transition_risk": transition,
        "physical_risk": physical,
        "opportunity_score": opportunity,
        "top_risks": top_risks,
        "quick_wins": quick_wins,
        "sector_breakdown": sector,
    }

    assets_data = [
        {
            "name": a.name,
            "sector": a.sector,
            "region": a.region,
            "revenue_usd_m": a.revenue_usd_m,
            "scope1_tco2e": a.scope1_tco2e,
            "scope2_tco2e": a.scope2_tco2e,
            "green_revenue_pct": a.green_revenue_pct,
            "controversies": a.controversies,
        }
        for a in pydantic_assets
    ]

    context = build_portfolio_context(assets_data, scores, scenarios)
    document_context = get_combined_document_text()
    pipeline_context = await get_pipeline_context(db)
    if pipeline_context:
        context = context + "\n\n" + pipeline_context

    user_message = build_user_message(request.question, context, document_context)
    messages = [{"role": "user", "content": user_message}]

    try:
        client = get_llm_client()
        response = await client.complete(
            messages=messages,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=2048,
            temperature=0.7,
        )
        answer = response.content
    except Exception as e:
        logger.error("copilot_llm_error", error=str(e))
        raise LLMError(f"LLM request failed: {str(e)[:200]}")

    has_pipeline = pipeline_context is not None
    confidence = calculate_confidence_score(
        request.question,
        has_documents=document_context is not None or has_pipeline,
        portfolio_size=len(pydantic_assets),
    )

    citations = get_source_attribution(
        has_documents=document_context is not None,
        document_count=len(document_context.split("### Document:")) - 1 if document_context else 0,
        has_pipeline_data=has_pipeline,
    )

    return CopilotResponse(
        portfolio_id=str(portfolio.id),
        answer=answer,
        citations=citations,
        confidence=confidence,
    )


async def generate_stream(
    question: str,
    portfolio_id: Optional[str] = None,
) -> AsyncIterator[str]:
    """Generate streaming response from LLM with RAG context."""
    async with async_session_factory() as db:
        portfolio = await get_portfolio_by_id(portfolio_id, db)
        pydantic_assets = [db_asset_to_pydantic(a) for a in portfolio.assets]
        scenarios = await get_scenarios_dict(db)

        # Build portfolio context
        overall, climate, transition, physical, opportunity, top_risks, quick_wins, sector = score_portfolio(
            pydantic_assets, SECTOR_BASELINES
        )

        scores = {
            "overall_score": overall,
            "climate_risk": climate,
            "transition_risk": transition,
            "physical_risk": physical,
            "opportunity_score": opportunity,
            "top_risks": top_risks,
            "quick_wins": quick_wins,
            "sector_breakdown": sector,
        }

        assets_data = [
            {
                "name": a.name,
                "sector": a.sector,
                "region": a.region,
                "revenue_usd_m": a.revenue_usd_m,
                "scope1_tco2e": a.scope1_tco2e,
                "scope2_tco2e": a.scope2_tco2e,
                "green_revenue_pct": a.green_revenue_pct,
                "controversies": a.controversies,
            }
            for a in pydantic_assets
        ]

        context = build_portfolio_context(assets_data, scores, scenarios)
        document_context = get_combined_document_text()

        # Get pipeline data context (real EPA emissions data)
        pipeline_context = await get_pipeline_context(db)
        if pipeline_context:
            context = context + "\n\n" + pipeline_context

        # Calculate and emit confidence metadata first
        has_pipeline_data = pipeline_context is not None
        confidence = calculate_confidence_score(
            question,
            has_documents=document_context is not None or has_pipeline_data,
            portfolio_size=len(pydantic_assets),
        )

        # Emit metadata event
        yield f"event: metadata\ndata: {{\"confidence\": {confidence}, \"portfolio\": \"{portfolio.name}\"}}\n\n"

        # Log context info
        doc_size = len(document_context) if document_context else 0
        logger.info(
            "copilot_stream_started",
            portfolio_id=str(portfolio.id),
            portfolio_name=portfolio.name,
            question_preview=question[:50],
            context_chars=len(context),
            document_chars=doc_size,
            confidence=confidence,
        )

        user_message = build_user_message(question, context, document_context)
        messages = [{"role": "user", "content": user_message}]

    try:
        client = get_llm_client()
        chunk_count = 0

        async for chunk in client.stream(
            messages=messages,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=2048,
            temperature=0.7,
        ):
            chunk_count += 1
            yield f"data: {chunk}\n\n"

        logger.info(
            "copilot_stream_complete",
            chunk_count=chunk_count,
        )

    except Exception as e:
        logger.error("copilot_stream_error", error=str(e))
        yield f"event: error\ndata: {{\"error\": \"{str(e)[:200]}\"}}\n\n"

    yield "data: [DONE]\n\n"


@router.post("/copilot/stream")
@limiter.limit("20/minute")
async def copilot_stream(request: Request, body: CopilotStreamRequest):
    """Stream a copilot response using Server-Sent Events."""
    if not body.question.strip():
        raise ValidationError("Question cannot be empty")

    return StreamingResponse(
        generate_stream(body.question, body.portfolio_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
