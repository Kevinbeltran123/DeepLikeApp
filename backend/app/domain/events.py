"""SSE event contract shared between backend modes and the frontend.

The frontend mirrors these types in src/types/events.ts.
Adding a new event type requires updating both sides.
"""

from typing import Any, Literal, TypedDict


class TokenEvent(TypedDict):
    type: Literal["token"]
    content: str


class DetectedLangEvent(TypedDict):
    type: Literal["detected_lang"]
    code: str
    display: str


class AgentStartEvent(TypedDict):
    type: Literal["agent_start"]
    agent: str
    icon: str
    message: str


class AgentActionEvent(TypedDict):
    """Mono-agent ReAct: the agent picks a tool to invoke."""
    type: Literal["agent_action"]
    step: int
    tool: str
    icon: str
    input: str


class AgentObservationEvent(TypedDict):
    """Mono-agent ReAct: the result returned by the tool."""
    type: Literal["agent_observation"]
    step: int
    tool: str
    result: str


class AgentDoneEvent(TypedDict):
    """Multi-agent: a specialized agent finished its step."""
    type: Literal["agent_done"]
    agent: str
    icon: str
    result: str
    metadata: dict[str, Any]


class FinalEvent(TypedDict):
    type: Literal["final"]
    translation: str
    metadata: dict[str, Any]


class ErrorEvent(TypedDict):
    type: Literal["error"]
    message: str
