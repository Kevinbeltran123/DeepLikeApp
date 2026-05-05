"""Mono-agent translator built with the LangChain ReAct pattern.

The LLM itself decides which tool to invoke and when to stop. This module
streams the agent's lifecycle in real time using AgentExecutor.astream_events:

    on_chat_model_stream  -> the LLM is producing Thought/Action text
    on_tool_start         -> Action + Action Input fully parsed, tool fires
    on_tool_end           -> tool returned, observation emitted
    on_chain_end          -> agent finished, Final Answer ready

Tokens from on_chat_model_stream are accumulated into a buffer; _extract_thoughts
slices that buffer into discrete Thought blocks that are pushed to the frontend
as agent_thought events. That way the user sees the model reasoning live, not
just the actions it decided to take.
"""

import json
import re
from typing import Any, AsyncIterator

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.exceptions import OutputParserException
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
        max_iterations=12,
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


# ---------------------------------------------------------------------------
# TODO(tú): implementar _extract_thoughts
# ---------------------------------------------------------------------------
# Esta es LA decisión que define el feel del agente en vivo.
#
# Contexto:
#   on_chat_model_stream nos entrega el texto del LLM en chunks pequeños
#   (a veces tokens sueltos, a veces frases completas). Lo vamos acumulando en
#   un buffer. Tu trabajo es sacar de ese buffer las "Thoughts" terminadas y
#   devolver el resto para que se siga acumulando.
#
# Una Thought se ve así dentro del buffer:
#
#   "Thought: Necesito detectar el idioma primero.\nAction: detect_language\n..."
#
#   Empieza con el literal "Thought:" y termina cuando aparece "\nAction:" o
#   "\nFinal Answer:" — eso significa que el modelo dejó de pensar y pasó a
#   actuar (o a entregar el resultado).
#
# Trade-offs a considerar:
#   - Si emites cada chunk parcial como Thought, el UI vibra muy rápido pero
#     se ve "vivo". Si esperas a tener la Thought completa, es más limpio
#     pero el usuario espera más entre eventos.
#   - Una sola Thought, varias Thoughts en el mismo buffer, o ninguna —
#     todos son posibles dependiendo de qué tan rápido te llamen.
#   - "Final Answer:" también cierra una Thought (el modelo termina de pensar
#     y entrega resultado).
#
# Firma:
#   Input:  buffer acumulado de texto crudo del LLM
#   Output: (lista de Thoughts completas como strings, buffer restante por procesar)
#
# Ejemplo:
#   _extract_thoughts("Thought: Detecto idioma.\nAction: detect_language\nAction Input: hola")
#     -> (["Detecto idioma."], "Action: detect_language\nAction Input: hola")
#
#   _extract_thoughts("Thought: Sigo pensan")
#     -> ([], "Thought: Sigo pensan")        # incompleta, no emitir
#
#   _extract_thoughts("hola sin marcadores")
#     -> ([], "hola sin marcadores")          # nada que emitir
#
# Pista: re.search con un patrón "Thought:(.*?)(\\n\\s*(?:Action|Final Answer):)"
# en modo DOTALL te resuelve casi todo. Recuerda devolver el buffer "podado".
# Implementa abajo.
# ---------------------------------------------------------------------------


_THOUGHT_PATTERN = re.compile(
    r"Thought:\s*(.*?)(?=\n\s*(?:Action|Final Answer):)",
    re.DOTALL,
)


def _extract_thoughts(buffer: str) -> tuple[list[str], str]:
    """Pull complete Thought blocks out of the running LLM buffer.

    Conservative: only emit a Thought when its terminator (\\nAction: or
    \\nFinal Answer:) is present. Anything after the last terminator is
    discarded — LangChain emits it as on_tool_start.
    """
    thoughts = [m.strip() for m in _THOUGHT_PATTERN.findall(buffer) if m.strip()]
    if not thoughts:
        return [], buffer

    last = list(_THOUGHT_PATTERN.finditer(buffer))[-1]
    return thoughts, buffer[last.end():].lstrip("\n")


def _flush_trailing_thought(buffer: str) -> str:
    """When the agent finishes, the buffer may end with an unterminated
    'Thought: ...' (no trailing Action because we're at Final Answer).
    Return the trailing thought text or '' if there is none.
    """
    match = re.search(r"Thought:\s*(.+?)(?=\n\s*Final Answer:|$)", buffer, re.DOTALL)
    return match.group(1).strip() if match else ""


async def stream_translation(text: str, target_lang: str) -> AsyncIterator[str]:
    target_name = english_name(target_lang)
    yield _sse({"type": "agent_start", "agent": "translator", "icon": "robot",
                "message": "Iniciando agente ReAct..."})

    executor = _build_executor()
    step = 0
    llm_buffer = ""
    last_action_step = 0
    intermediate_steps: list[tuple[Any, Any]] = []

    try:
        async for ev in executor.astream_events(
            {"text": text, "target_language": target_name},
            version="v2",
        ):
            kind = ev.get("event")

            if kind == "on_chat_model_stream":
                chunk = ev["data"].get("chunk")
                content = getattr(chunk, "content", "") if chunk else ""
                if not content:
                    continue
                llm_buffer += content

                thoughts, llm_buffer = _extract_thoughts(llm_buffer)
                for t in thoughts:
                    if t.strip():
                        yield _sse({
                            "type": "agent_thought",
                            "step": last_action_step + 1,
                            "content": _truncate(t.strip(), 500),
                        })

            elif kind == "on_tool_start":
                step += 1
                last_action_step = step
                tool_name = ev.get("name", "unknown")
                tool_input = ev["data"].get("input", "")
                if isinstance(tool_input, dict):
                    tool_input = tool_input.get("input", tool_input)
                yield _sse({
                    "type": "agent_action",
                    "step": step,
                    "tool": tool_name,
                    "icon": _TOOL_ICONS.get(tool_name, "spark"),
                    "input": _truncate(tool_input, 200),
                })
                # Reset buffer — anything past Action: belongs to LangChain's parser.
                llm_buffer = ""

            elif kind == "on_tool_end":
                tool_name = ev.get("name", "unknown")
                output = ev["data"].get("output", "")
                yield _sse({
                    "type": "agent_observation",
                    "step": step,
                    "tool": tool_name,
                    "result": _truncate(output, 300),
                })
                intermediate_steps.append((tool_name, output))

            elif kind == "on_chain_end" and ev.get("name") == "AgentExecutor":
                output_payload = ev["data"].get("output", {})
                raw_final = output_payload.get("output", "") if isinstance(output_payload, dict) else str(output_payload)
                final_translation = _clean_final_answer(raw_final)

                tail_thought = _flush_trailing_thought(llm_buffer)
                if tail_thought:
                    yield _sse({
                        "type": "agent_thought",
                        "step": last_action_step + 1,
                        "content": _truncate(tail_thought, 500),
                    })

                # Recovery: if the agent didn't produce a clean Final Answer,
                # fall back to the last successful translate_text observation.
                if not final_translation:
                    for tool_name, observation in reversed(intermediate_steps):
                        if tool_name == "translate_text":
                            final_translation = str(observation).strip()
                            break

                yield _sse({
                    "type": "final",
                    "translation": final_translation,
                    "metadata": {
                        "target": target_lang,
                        "target_name": target_name,
                        "iterations": step,
                        "model": get_settings().llm_model,
                    },
                })

    except OutputParserException as exc:
        yield _sse({
            "type": "agent_warning",
            "step": step,
            "message": f"El modelo se salió del formato ReAct: {exc}",
        })
        yield _sse({"type": "error", "message": "Parsing del agente falló. Reintenta o reformula el texto."})
    except Exception as exc:
        yield _sse({"type": "error", "message": f"Agent error: {exc}"})
    finally:
        yield "data: [DONE]\n\n"
