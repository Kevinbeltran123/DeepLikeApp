"""Mono-agent translator built with the LangChain ReAct pattern.

Unlike the pipeline, the LLM itself decides which tool to invoke and when to
stop. The orchestration logic in this file just runs the agent and streams its
intermediate steps to the frontend after execution finishes.

A future improvement would be to use AgentExecutor.astream_events to push events
in real time. The post-hoc emission below is closer to the PDF reference and is
easier to follow when learning the ReAct loop.
"""

import asyncio
import json
import re
from typing import Any, AsyncIterator

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama

from app.config import get_settings
from app.domain.languages import english_name

from .tools import (
    check_translation_quality,
    detect_language,
    lookup_technical_terms,
    translate_text,
)


_TOOL_ICONS = {
    "detect_language": "search",
    "lookup_technical_terms": "book",
    "translate_text": "globe",
    "check_translation_quality": "check",
}


_REACT_PROMPT = PromptTemplate.from_template("""You are an expert professional translator agent. You have access to tools to help you translate text accurately.

You must follow this EXACT format for every step:

Thought: [your reasoning about what to do next]
Action: [tool name]
Action Input: [input for the tool, see formats below]
Observation: [tool result - this will be filled in automatically]
... (repeat Thought/Action/Action Input/Observation as needed)

Thought: I now have everything I need to provide the final translation
Final Answer: [ONLY the translated text, nothing else]

Available tools:
{tools}

Tool names: {tool_names}

INPUT FORMATS (READ CAREFULLY):
- detect_language: pass the raw text as a string (no JSON).
- lookup_technical_terms: pass the raw text as a string (no JSON).
- translate_text: pass a JSON object: {{"text": "<original>", "source_language": "<English name>", "target_language": "<English name>"}}
- check_translation_quality: pass a JSON object: {{"original": "<original>", "translation": "<translated>"}}

IMPORTANT RULES:
- Always start by detecting the language
- Always check for technical terms before translating
- Always verify quality after translating
- Your Final Answer must contain ONLY the translated text, no explanations
- Never skip the quality check

Begin!

Task: Translate the following text to {target_language}.
Text: "{text}"

{agent_scratchpad}""")


def _build_executor() -> AgentExecutor:
    settings = get_settings()
    llm = ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=settings.llm_temperature,
    )
    tools = [detect_language, lookup_technical_terms, translate_text, check_translation_quality]
    agent = create_react_agent(llm, tools, _REACT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        max_iterations=8,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )


def _clean_final_answer(output: str) -> str:
    cleaned = output.strip()
    for prefix in ("Final Answer:", "Translation:", "Translated text:"):
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
    return cleaned.strip('"').strip("'").strip()


def _truncate(value: Any, limit: int) -> str:
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "..."


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def stream_translation(text: str, target_lang: str) -> AsyncIterator[str]:
    target_name = english_name(target_lang)
    yield _sse({"type": "agent_start", "agent": "translator", "icon": "robot",
                "message": "Iniciando agente ReAct..."})

    executor = _build_executor()
    loop = asyncio.get_event_loop()

    try:
        result = await loop.run_in_executor(
            None,
            lambda: executor.invoke({"text": text, "target_language": target_name}),
        )
    except Exception as exc:
        yield _sse({"type": "error", "message": f"Agent error: {exc}"})
        yield "data: [DONE]\n\n"
        return

    steps = result.get("intermediate_steps", [])
    for i, (action, observation) in enumerate(steps):
        tool_name = getattr(action, "tool", "unknown")
        tool_input = getattr(action, "tool_input", "")
        icon = _TOOL_ICONS.get(tool_name, "spark")

        yield _sse({
            "type": "agent_action",
            "step": i + 1,
            "tool": tool_name,
            "icon": icon,
            "input": _truncate(tool_input, 200),
        })
        await asyncio.sleep(0.05)

        yield _sse({
            "type": "agent_observation",
            "step": i + 1,
            "tool": tool_name,
            "result": _truncate(observation, 300),
        })
        await asyncio.sleep(0.05)

    final_translation = _clean_final_answer(result.get("output", ""))

    # If the agent returned junk, try to recover the translation from the last
    # successful translate_text observation.
    if not final_translation and steps:
        for action, observation in reversed(steps):
            if getattr(action, "tool", "") == "translate_text":
                final_translation = str(observation).strip()
                break

    yield _sse({
        "type": "final",
        "translation": final_translation,
        "metadata": {
            "target": target_lang,
            "target_name": target_name,
            "iterations": len(steps),
            "model": get_settings().llm_model,
        },
    })
    yield "data: [DONE]\n\n"
