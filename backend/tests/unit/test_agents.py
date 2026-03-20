"""Tests for the agentic AI framework."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agents.base import AgentExecutor, AgentResult, ToolDefinition
from app.llm.base import LLMResponse


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def mock_tool():
    """A simple mock tool."""

    async def execute(query: str = "default") -> str:
        return f"Tool result for: {query}"

    return ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters={"query": {"type": "string", "description": "The query"}},
        execute=execute,
    )


@pytest.fixture
def mock_llm():
    return AsyncMock()


# ── Tool definition tests ───────────────────────────────────────────────


class TestToolDefinition:
    def test_schema_text(self, mock_tool):
        schema = mock_tool.schema_text()
        assert "test_tool" in schema
        assert "A test tool" in schema

    @pytest.mark.asyncio
    async def test_execute(self, mock_tool):
        result = await mock_tool.execute(query="hello")
        assert result == "Tool result for: hello"


# ── Agent executor tests ────────────────────────────────────────────────


class TestAgentExecutor:
    @pytest.mark.asyncio
    async def test_direct_final_answer(self, mock_llm, mock_tool):
        """Agent should return immediately when LLM gives a FINAL ANSWER."""
        mock_llm.complete = AsyncMock(
            return_value=LLMResponse(
                content="THOUGHT: The user wants a simple answer.\nFINAL ANSWER: The portfolio risk is moderate at 45/100.",
                model="test",
            )
        )

        agent = AgentExecutor(llm=mock_llm, tools=[mock_tool])
        result = await agent.run("What is the portfolio risk?")

        assert isinstance(result, AgentResult)
        assert "portfolio risk is moderate" in result.answer
        assert result.iterations == 1
        assert result.tool_calls == 0

    @pytest.mark.asyncio
    async def test_tool_call_then_answer(self, mock_llm, mock_tool):
        """Agent should call a tool, then provide a final answer."""
        mock_llm.complete = AsyncMock(
            side_effect=[
                # First call: agent decides to use a tool
                LLMResponse(
                    content='THOUGHT: I need to look up the data.\nACTION: test_tool\nACTION_INPUT: {"query": "portfolio data"}',
                    model="test",
                ),
                # Second call: agent provides final answer
                LLMResponse(
                    content="THOUGHT: I now have the data.\nFINAL ANSWER: Based on the tool results, the risk is high.",
                    model="test",
                ),
            ]
        )

        agent = AgentExecutor(llm=mock_llm, tools=[mock_tool])
        result = await agent.run("Analyze the portfolio")

        assert result.tool_calls == 1
        assert result.iterations == 2
        assert "risk is high" in result.answer
        assert len(result.steps) == 2

    @pytest.mark.asyncio
    async def test_unknown_tool(self, mock_llm, mock_tool):
        """Agent should handle unknown tool names gracefully."""
        mock_llm.complete = AsyncMock(
            side_effect=[
                LLMResponse(
                    content='THOUGHT: Let me try a tool.\nACTION: nonexistent_tool\nACTION_INPUT: {"x": 1}',
                    model="test",
                ),
                LLMResponse(
                    content="THOUGHT: That tool doesn't exist.\nFINAL ANSWER: I couldn't find the right tool.",
                    model="test",
                ),
            ]
        )

        agent = AgentExecutor(llm=mock_llm, tools=[mock_tool])
        result = await agent.run("Do something")

        assert result.iterations == 2
        # The error observation should be in the steps
        assert any("Unknown tool" in s.observation for s in result.steps if s.observation)

    @pytest.mark.asyncio
    async def test_max_iterations(self, mock_llm, mock_tool):
        """Agent should stop after max iterations."""
        # LLM never gives a FINAL ANSWER
        mock_llm.complete = AsyncMock(
            return_value=LLMResponse(
                content='THOUGHT: Still thinking.\nACTION: test_tool\nACTION_INPUT: {"query": "more data"}',
                model="test",
            )
        )

        agent = AgentExecutor(llm=mock_llm, tools=[mock_tool], max_iterations=3)
        result = await agent.run("Endless analysis")

        assert result.iterations == 3
        assert "unable to complete" in result.answer.lower() or result.tool_calls == 3

    @pytest.mark.asyncio
    async def test_malformed_action_input(self, mock_llm, mock_tool):
        """Agent should handle malformed JSON in ACTION_INPUT."""
        mock_llm.complete = AsyncMock(
            side_effect=[
                LLMResponse(
                    content="THOUGHT: Let me try.\nACTION: test_tool\nACTION_INPUT: {invalid json}",
                    model="test",
                ),
                LLMResponse(
                    content="THOUGHT: Let me just answer.\nFINAL ANSWER: Here's my analysis.",
                    model="test",
                ),
            ]
        )

        agent = AgentExecutor(llm=mock_llm, tools=[mock_tool])
        result = await agent.run("Test")
        # Should still complete without crashing
        assert result.answer is not None

    @pytest.mark.asyncio
    async def test_parse_response_thought_only(self, mock_llm, mock_tool):
        """Parser should handle responses with only a THOUGHT."""
        agent = AgentExecutor(llm=mock_llm, tools=[mock_tool])
        thought, action, action_input, final = agent._parse_response(
            "THOUGHT: I need to think about this more."
        )
        assert thought == "I need to think about this more."
        assert action is None
        assert final is None

    @pytest.mark.asyncio
    async def test_parse_response_final_answer(self, mock_llm, mock_tool):
        """Parser should extract FINAL ANSWER correctly."""
        agent = AgentExecutor(llm=mock_llm, tools=[mock_tool])
        thought, action, action_input, final = agent._parse_response(
            "THOUGHT: I have all the data.\nFINAL ANSWER: The risk score is 72/100."
        )
        assert thought == "I have all the data."
        assert final == "The risk score is 72/100."
        assert action is None

    @pytest.mark.asyncio
    async def test_streaming_events(self, mock_llm, mock_tool):
        """Streaming should yield properly typed events."""
        mock_llm.complete = AsyncMock(
            return_value=LLMResponse(
                content="THOUGHT: Simple task.\nFINAL ANSWER: Done.",
                model="test",
            )
        )

        agent = AgentExecutor(llm=mock_llm, tools=[mock_tool])
        events = []
        async for event in agent.run_stream("Test"):
            events.append(event)

        event_types = [e["type"] for e in events]
        assert "status" in event_types
        assert "answer" in event_types

    @pytest.mark.asyncio
    async def test_system_context_in_prompt(self, mock_llm, mock_tool):
        """System context should be included in the prompt."""
        agent = AgentExecutor(
            llm=mock_llm,
            tools=[mock_tool],
            system_context="You are a climate expert.",
        )
        prompt = agent._build_system_prompt()
        assert "climate expert" in prompt
        assert "test_tool" in prompt
