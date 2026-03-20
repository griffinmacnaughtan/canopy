"""Agent execution API endpoints.

Provides both synchronous and streaming endpoints for the agentic
climate risk analyst, exposing the ReAct loop to the frontend.
"""

import json
from collections.abc import AsyncIterator

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..agents import create_climate_agent
from ..exceptions import LLMError, ValidationError
from ..models import AgentRequest, AgentResponse, AgentStepResponse

router = APIRouter(tags=["Agent"])
logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)


@router.post("/agent", response_model=AgentResponse)
async def run_agent(body: AgentRequest):
    """Execute the climate risk analyst agent (non-streaming).

    The agent autonomously reasons, calls tools, and synthesises a
    comprehensive answer over multiple iterations.
    """
    if not body.query.strip():
        raise ValidationError("Query cannot be empty")

    try:
        agent = create_climate_agent(max_iterations=body.max_iterations)
        result = await agent.run(body.query)
    except Exception as e:
        logger.error("agent_execution_error", error=str(e))
        raise LLMError(f"Agent execution failed: {str(e)[:200]}") from e

    steps = [
        AgentStepResponse(
            thought=s.thought,
            tool_name=s.action.tool_name if s.action else None,
            tool_input=s.action.arguments if s.action else None,
            observation=s.observation if s.observation else None,
        )
        for s in result.steps
    ]

    return AgentResponse(
        answer=result.answer,
        steps=steps,
        tool_calls=result.tool_calls,
        iterations=result.iterations,
        duration_ms=result.total_duration_ms,
    )


async def _stream_agent(query: str, max_iterations: int) -> AsyncIterator[str]:
    """Generate SSE events from the agent's ReAct loop."""
    try:
        agent = create_climate_agent(max_iterations=max_iterations)
        async for event in agent.run_stream(query):
            yield f"data: {json.dumps(event)}\n\n"
    except Exception as e:
        logger.error("agent_stream_error", error=str(e))
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)[:200]})}\n\n"

    yield "data: [DONE]\n\n"


@router.post("/agent/stream")
@limiter.limit("10/minute")
async def run_agent_stream(request: Request, body: AgentRequest):
    """Stream the agent's reasoning process via Server-Sent Events.

    Emits events for each step: thought, tool_call, observation, answer.
    """
    if not body.query.strip():
        raise ValidationError("Query cannot be empty")

    return StreamingResponse(
        _stream_agent(body.query, body.max_iterations),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
