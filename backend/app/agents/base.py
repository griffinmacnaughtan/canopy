"""Core agent executor implementing the ReAct loop.

The agent alternates between THOUGHT → ACTION → OBSERVATION steps until
it reaches a FINAL ANSWER or exceeds the maximum iteration count.  This
mirrors the ReAct paper (Yao et al., 2022) pattern used in production
agent systems.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any

import structlog

from ..llm.base import LLMClient

logger = structlog.get_logger()

# ── Data classes ─────────────────────────────────────────────────────────


@dataclass
class ToolDefinition:
    """Schema for a tool the agent can invoke."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for the parameters
    execute: Callable[..., Coroutine[Any, Any, str]]  # async callable

    def schema_text(self) -> str:
        """Human-readable schema for the system prompt."""
        params = json.dumps(self.parameters, indent=2)
        return f"**{self.name}**: {self.description}\nParameters: {params}"


@dataclass
class ToolCall:
    """A single tool invocation during the agent loop."""

    tool_name: str
    arguments: dict[str, Any]
    result: str = ""
    duration_ms: float = 0


@dataclass
class AgentStep:
    """One iteration of the ReAct loop."""

    thought: str
    action: ToolCall | None = None
    observation: str = ""


@dataclass
class AgentResult:
    """Final result of an agent execution."""

    answer: str
    steps: list[AgentStep] = field(default_factory=list)
    total_duration_ms: float = 0
    tool_calls: int = 0
    iterations: int = 0


# ── System prompt builder ────────────────────────────────────────────────

_REACT_SYSTEM = """You are an autonomous AI agent that solves complex analytical tasks by reasoning step-by-step and using tools.

## Available Tools

{tool_schemas}

## How to Operate

You MUST follow this exact format for each step:

THOUGHT: <your reasoning about what to do next>
ACTION: <tool_name>
ACTION_INPUT: <JSON object with the tool parameters>

After each action, you will receive an OBSERVATION with the tool result.

When you have enough information to provide a comprehensive answer, respond with:

THOUGHT: <your final reasoning>
FINAL ANSWER: <your complete, well-structured answer in markdown>

## Rules

1. Always start with a THOUGHT about what information you need.
2. Use tools to gather real data — never fabricate numbers or facts.
3. You may call multiple tools across iterations to build a complete picture.
4. Reference specific data points from tool results in your final answer.
5. If a tool returns an error, reason about alternatives and try a different approach.
6. Limit yourself to {max_iterations} iterations maximum.
7. Your final answer should be executive-ready: structured, quantitative, and actionable.
"""


# ── Agent executor ───────────────────────────────────────────────────────


class AgentExecutor:
    """ReAct agent executor with tool use.

    The executor manages the agent loop, parsing LLM output for tool calls,
    executing tools, and feeding observations back until the agent produces
    a final answer.
    """

    def __init__(
        self,
        llm: LLMClient,
        tools: list[ToolDefinition],
        system_context: str = "",
        max_iterations: int = 8,
    ) -> None:
        self._llm = llm
        self._tools = {t.name: t for t in tools}
        self._system_context = system_context
        self._max_iterations = max_iterations

    def _build_system_prompt(self) -> str:
        tool_schemas = "\n\n".join(t.schema_text() for t in self._tools.values())
        prompt = _REACT_SYSTEM.format(
            tool_schemas=tool_schemas,
            max_iterations=self._max_iterations,
        )
        if self._system_context:
            prompt += f"\n\n## Domain Context\n\n{self._system_context}"
        return prompt

    def _parse_response(self, text: str) -> tuple[str, str | None, dict | None, str | None]:
        """Parse the LLM response into thought, action, input, and final answer.

        Returns:
            (thought, action_name, action_input, final_answer)
        """
        thought = ""
        action_name = None
        action_input = None
        final_answer = None

        # Extract THOUGHT
        thought_match = re.search(r"THOUGHT:\s*(.+?)(?=\nACTION:|\nFINAL ANSWER:|\Z)", text, re.DOTALL)
        if thought_match:
            thought = thought_match.group(1).strip()

        # Check for FINAL ANSWER
        final_match = re.search(r"FINAL ANSWER:\s*(.+)", text, re.DOTALL)
        if final_match:
            final_answer = final_match.group(1).strip()
            return thought, None, None, final_answer

        # Extract ACTION and ACTION_INPUT
        action_match = re.search(r"ACTION:\s*(\S+)", text)
        input_match = re.search(r"ACTION_INPUT:\s*(\{.+?\})", text, re.DOTALL)

        if action_match:
            action_name = action_match.group(1).strip()

        if input_match:
            try:
                action_input = json.loads(input_match.group(1))
            except json.JSONDecodeError:
                action_input = {}

        return thought, action_name, action_input, final_answer

    async def _execute_tool(self, name: str, arguments: dict) -> str:
        """Execute a tool and return the result string."""
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Unknown tool '{name}'. Available tools: {', '.join(self._tools.keys())}"

        try:
            start = time.perf_counter()
            result = await tool.execute(**arguments)
            duration = (time.perf_counter() - start) * 1000
            logger.info("agent_tool_executed", tool=name, duration_ms=round(duration, 1))
            return result
        except Exception as e:
            logger.error("agent_tool_error", tool=name, error=str(e))
            return f"Error executing {name}: {str(e)}"

    async def run(self, query: str) -> AgentResult:
        """Execute the agent loop for a given query.

        Args:
            query: The user's question or task.

        Returns:
            ``AgentResult`` with the final answer and execution trace.
        """
        start_time = time.perf_counter()
        system_prompt = self._build_system_prompt()

        messages: list[dict[str, str]] = [
            {"role": "user", "content": f"Task: {query}"},
        ]

        steps: list[AgentStep] = []
        tool_call_count = 0

        for iteration in range(self._max_iterations):
            logger.info("agent_iteration", iteration=iteration + 1)

            response = await self._llm.complete(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.2,  # Low temp for reliable tool use
            )

            thought, action_name, action_input, final_answer = self._parse_response(
                response.content
            )

            step = AgentStep(thought=thought)

            if final_answer:
                step.observation = "Agent reached final answer."
                steps.append(step)
                total_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    "agent_complete",
                    iterations=iteration + 1,
                    tool_calls=tool_call_count,
                    duration_ms=round(total_ms, 1),
                )
                return AgentResult(
                    answer=final_answer,
                    steps=steps,
                    total_duration_ms=round(total_ms, 1),
                    tool_calls=tool_call_count,
                    iterations=iteration + 1,
                )

            if action_name and action_input is not None:
                tool_call = ToolCall(
                    tool_name=action_name,
                    arguments=action_input,
                )

                observation = await self._execute_tool(action_name, action_input)
                tool_call.result = observation
                tool_call_count += 1

                step.action = tool_call
                step.observation = observation
                steps.append(step)

                # Feed the full exchange back to the LLM
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": f"OBSERVATION: {observation}",
                })
            else:
                # LLM didn't produce a valid action or final answer — nudge it
                step.observation = "No valid action parsed. Please use the THOUGHT/ACTION/FINAL ANSWER format."
                steps.append(step)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": "Please respond with either an ACTION or a FINAL ANSWER using the required format.",
                })

        # Max iterations reached — synthesise from what we have
        total_ms = (time.perf_counter() - start_time) * 1000
        logger.warning("agent_max_iterations", iterations=self._max_iterations)

        return AgentResult(
            answer="I was unable to complete the analysis within the iteration limit. "
            "Here is what I found so far:\n\n"
            + "\n".join(f"- {s.thought}" for s in steps if s.thought),
            steps=steps,
            total_duration_ms=round(total_ms, 1),
            tool_calls=tool_call_count,
            iterations=self._max_iterations,
        )

    async def run_stream(self, query: str) -> AsyncIterator[dict]:
        """Execute the agent loop, yielding events for real-time streaming.

        Yields dicts with ``type`` key:
        - ``thought``: Agent's reasoning
        - ``tool_call``: Tool being invoked
        - ``observation``: Tool result
        - ``answer``: Final answer
        - ``error``: Error message
        """
        start_time = time.perf_counter()
        system_prompt = self._build_system_prompt()

        messages: list[dict[str, str]] = [
            {"role": "user", "content": f"Task: {query}"},
        ]

        for iteration in range(self._max_iterations):
            yield {"type": "status", "iteration": iteration + 1, "max": self._max_iterations}

            response = await self._llm.complete(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.2,
            )

            thought, action_name, action_input, final_answer = self._parse_response(
                response.content
            )

            if thought:
                yield {"type": "thought", "content": thought}

            if final_answer:
                total_ms = (time.perf_counter() - start_time) * 1000
                yield {
                    "type": "answer",
                    "content": final_answer,
                    "duration_ms": round(total_ms, 1),
                    "iterations": iteration + 1,
                }
                return

            if action_name and action_input is not None:
                yield {"type": "tool_call", "tool": action_name, "arguments": action_input}

                observation = await self._execute_tool(action_name, action_input)
                yield {"type": "observation", "tool": action_name, "content": observation}

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": f"OBSERVATION: {observation}"})
            else:
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": "Please respond with either an ACTION or a FINAL ANSWER.",
                })

        yield {"type": "error", "content": "Maximum iterations reached."}
