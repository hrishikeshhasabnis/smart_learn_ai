import json
import logging
from typing import Any, Dict, List

from openai import OpenAI
from openai import RateLimitError, APITimeoutError, APIConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.schemas.itinerary import Itinerary
from app.services.tools.fetch_page import fetch_page

log = logging.getLogger("itinerary_agent")

SYSTEM_INSTRUCTIONS = """
You are a learning itinerary agent.

Goal:
Create a day-wise itinerary to learn ONE concept step-by-step with minimal, high-signal links.

Hard rules:
- Free sources only. If unsure, mark UNKNOWN and do not include it when free_only=true.
- 1–2 links per day maximum.
- Keep total links minimal.
- Provide a short free_evidence snippet for each link.
- Prefer practical, hands-on material (docs, tutorials, code, videos).
- Do not include ML basics unless the user explicitly asks.

Agentic process:
1) Create a micro-syllabus (subtopics) for the concept.
2) Use web_search to find candidate sources.
3) Use fetch_page only when necessary to confirm free-ness or reduce uncertainty.
4) Select the minimum set that covers the micro-syllabus and fits the link limits.
Return ONLY JSON that matches the schema.
""".strip()

def _tool_schema_fetch_page() -> dict:
    # With strict=True, OpenAI expects required to include ALL properties.
    return {
        "type": "function",
        "name": "fetch_page",
        "description": (
            "Fetch a web page URL and return a short excerpt plus paywall signals. "
            "Use ONLY to verify free-ness/relevance when needed. Keep calls minimal."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch"},
                "max_chars": {"type": "integer", "description": "Max characters of excerpt to return"},
            },
            "required": ["url", "max_chars"],
            "additionalProperties": False,
        },
    }

def _as_dict(item: Any) -> Dict[str, Any]:
    if isinstance(item, dict):
        return item
    if hasattr(item, "model_dump"):
        return item.model_dump()
    d: Dict[str, Any] = {}
    for k in ("type", "name", "arguments", "call_id", "content", "role"):
        if hasattr(item, k):
            d[k] = getattr(item, k)
    return d

def _extract_function_calls(resp: Any) -> List[Dict[str, Any]]:
    calls: List[Dict[str, Any]] = []
    for item in getattr(resp, "output", []) or []:
        d = _as_dict(item)
        if d.get("type") == "function_call":
            calls.append(d)
    return calls

def _append_response_output_to_input(input_list: List[Dict[str, Any]], resp: Any) -> None:
    for item in getattr(resp, "output", []) or []:
        input_list.append(_as_dict(item))

def _make_function_call_output(call_id: str, output_obj: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "function_call_output",
        "call_id": call_id,
        "output": json.dumps(output_obj, ensure_ascii=False),
    }

# Retry only transient errors (do NOT retry 400/BadRequest)
@retry(
    retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=6),
)
def generate_itinerary(
    *,
    concept: str,
    level: str,
    days: int,
    hours_per_day: int,
    prefer_format: str,
    free_only: bool,
    max_links_per_day: int,
    max_total_links: int,
) -> Itinerary:
    client = OpenAI(api_key=settings.openai_api_key)

    user_prompt = f"""
Concept: {concept}
Level: {level}
Days: {days}
Hours per day: {hours_per_day}
Preferred format: {prefer_format} (videos | blogs | mix)
Free only: {free_only}

Output requirements:
- Day 1..Day {days}
- Each day: objective + 1–{max_links_per_day} links (NO MORE)
- Total links: keep <= {max_total_links}
- Each link must include:
  title, url, content_type (blog/video/docs/course/repo/other),
  minutes, why,
  free_label (FREE_FULL/FREE_AUDIT/FREEMIUM/PAID/UNKNOWN),
  free_evidence (short snippet).
- Include a single short project for the week.
Return ONLY JSON that matches the schema.
""".strip()

    tools: List[Dict[str, Any]] = [{"type": "web_search"}]
    if settings.enable_fetch_tool:
        tools.append(_tool_schema_fetch_page())

    input_list: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
        {"role": "user", "content": user_prompt},
    ]

    resp = client.responses.parse(
        model=settings.openai_model,
        input=input_list,
        tools=tools,
        text_format=Itinerary,
        max_tool_calls=settings.max_tool_calls,
    )

    # Execute custom function tool calls if any (web_search is handled by OpenAI)
    for _ in range(8):
        function_calls = _extract_function_calls(resp)
        if not function_calls:
            break

        _append_response_output_to_input(input_list, resp)

        for call in function_calls:
            name = call.get("name")
            call_id = call.get("call_id")
            args_raw = call.get("arguments") or "{}"
            if not call_id:
                continue

            if name != "fetch_page":
                input_list.append(_make_function_call_output(call_id, {"error": f"Unknown tool: {name}"}))
                continue

            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                url = args["url"]
                max_chars = int(args.get("max_chars", 4000))
                result = fetch_page(url=url, max_chars=max_chars)
            except Exception as e:
                result = {"error": str(e)}

            input_list.append(_make_function_call_output(call_id, result))

        resp = client.responses.parse(
            model=settings.openai_model,
            input=input_list,
            tools=tools,
            text_format=Itinerary,
            max_tool_calls=settings.max_tool_calls,
        )

    plan = getattr(resp, "output_parsed", None)
    if plan is None:
        out_text = getattr(resp, "output_text", "") or ""
        raise RuntimeError(
            "Model did not return a valid Itinerary JSON. "
            f"Raw output_text (truncated): {out_text[:800]}"
        )
    return plan
