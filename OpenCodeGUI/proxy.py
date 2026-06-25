import asyncio
import json
from dataclasses import dataclass, field
from typing import Optional

import httpx

CONTEXT_WINDOW = 128_000
TARGET_BASE = "https://api.freemodel.dev/v1"

HOP_BY_HOP = {
    "host", "content-length", "connection", "transfer-encoding",
    "x-session-id", "x-forwarded-for", "x-forwarded-proto",
    "x-forwarded-host", "x-forwarded-port",
}


class SSEEventBus:
    def __init__(self):
        self._queues: dict[str, list[asyncio.Queue]] = {"a": [], "b": []}

    def subscribe(self, session_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.setdefault(session_id, []).append(q)
        return q

    def unsubscribe(self, session_id: str, q: asyncio.Queue):
        self._queues[session_id].remove(q)

    async def publish(self, session_id: str, event: str, data: dict):
        payload = f"event: {event}\ndata: {json.dumps(data)}\n\n"
        for q in self._queues.get(session_id, []):
            await q.put(payload)


event_bus = SSEEventBus()


@dataclass
class SessionState:
    session_id: str
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    actions: int = 0
    messages: list = field(default_factory=list)

    @property
    def avg_tokens_per_action(self) -> float:
        return self.total_tokens / max(self.actions, 1)

    @property
    def context_fill_pct(self) -> float:
        return min(100.0, self.total_tokens / CONTEXT_WINDOW * 100)

    def reset(self):
        self.model = ""
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.actions = 0
        self.messages = []

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "actions": self.actions,
            "avg_tpa": round(self.avg_tokens_per_action, 1),
            "pct": round(self.context_fill_pct, 1),
        }


sessions: dict[str, SessionState] = {
    "a": SessionState(session_id="a"),
    "b": SessionState(session_id="b"),
}


def _build_forward_headers(raw_headers: dict) -> dict:
    return {
        k: v for k, v in raw_headers.items()
        if k.lower() not in HOP_BY_HOP
    }


async def _emit_message_events(data: dict, body: Optional[dict], session_id: str):
    choices = data.get("choices", [])
    if not choices or not isinstance(choices, list) or len(choices) == 0:
        return
    choice = choices[0]
    if "message" not in choice:
        return

    if body and isinstance(body, dict):
        msgs = body.get("messages", [])
        if msgs and isinstance(msgs, list) and msgs[-1].get("role") == "user":
            await event_bus.publish(session_id, "message", {
                "session": session_id,
                "role": "user",
                "content": msgs[-1]["content"],
            })

    msg = choice["message"]
    await event_bus.publish(session_id, "message", {
        "session": session_id,
        "role": msg.get("role", "assistant"),
        "content": msg.get("content", ""),
    })


async def _emit_metrics(session_id: str):
    await event_bus.publish(session_id, "metrics", sessions[session_id].to_dict())


async def proxy_non_streaming(
    method: str, path: str, raw_headers: dict,
    body: Optional[dict], session_id: str,
):
    url = f"{TARGET_BASE}/{path}"
    headers = _build_forward_headers(raw_headers)

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.request(method, url, headers=headers, json=body)

            data = None
            try:
                data = resp.json()
            except Exception:
                pass

            if data and isinstance(data, dict) and resp.status_code < 400:
                usage = data.get("usage")
                if usage:
                    state = sessions[session_id]
                    state.prompt_tokens += usage.get("prompt_tokens", 0)
                    state.completion_tokens += usage.get("completion_tokens", 0)
                    state.total_tokens += usage.get("total_tokens", 0)
                    state.actions += 1
                    if "model" in data:
                        state.model = data["model"]
                    await _emit_metrics(session_id)

                await _emit_message_events(data, body, session_id)

            return resp.status_code, data if data else resp.text, resp.headers.get("content-type", "application/json")

    except httpx.ConnectError:
        return 502, {"error": "upstream_unreachable", "detail": f"Cannot connect to {TARGET_BASE}"}, "application/json"
    except httpx.TimeoutException:
        return 504, {"error": "upstream_timeout", "detail": "Request to upstream API timed out"}, "application/json"
    except Exception as e:
        return 500, {"error": "proxy_error", "detail": str(e)}, "application/json"


async def proxy_streaming(
    method: str, path: str, raw_headers: dict,
    body: Optional[dict], session_id: str,
):
    url = f"{TARGET_BASE}/{path}"
    headers = _build_forward_headers(raw_headers)

    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            req = client.build_request(method, url, headers=headers, json=body)
            resp = await client.send(req, stream=True)

            model_name = ""
            last_usage = None
            collected_content = ""

            async def generate():
                nonlocal model_name, last_usage, collected_content

                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line.strip() != "data: [DONE]":
                        try:
                            chunk = json.loads(line[6:])
                            if chunk.get("model"):
                                model_name = chunk["model"]
                            if chunk.get("usage") and chunk["usage"]:
                                last_usage = chunk["usage"]
                            choices = chunk.get("choices", [])
                            if choices and choices[0].get("delta", {}).get("content"):
                                collected_content += choices[0]["delta"]["content"]
                        except json.JSONDecodeError:
                            pass
                    yield line + "\n"

                if last_usage:
                    state = sessions[session_id]
                    state.prompt_tokens += last_usage.get("prompt_tokens", 0)
                    state.completion_tokens += last_usage.get("completion_tokens", 0)
                    state.total_tokens += last_usage.get("total_tokens", 0)
                    state.actions += 1
                    if model_name:
                        state.model = model_name
                    await _emit_metrics(session_id)

                if model_name:
                    sessions[session_id].model = model_name

                if collected_content and last_usage:
                    if body and isinstance(body, dict):
                        msgs = body.get("messages", [])
                        if msgs and isinstance(msgs, list) and msgs[-1].get("role") == "user":
                            await event_bus.publish(session_id, "message", {
                                "session": session_id,
                                "role": "user",
                                "content": msgs[-1]["content"],
                            })
                    await event_bus.publish(session_id, "message", {
                        "session": session_id,
                        "role": "assistant",
                        "content": collected_content,
                    })

            return (
                resp.status_code,
                generate(),
                resp.headers.get("content-type", "text/event-stream"),
                dict(resp.headers),
            )

        except httpx.ConnectError:
            async def err_gen():
                yield json.dumps({"error": "upstream_unreachable", "detail": f"Cannot connect to {TARGET_BASE}"})
            return 502, err_gen(), "application/json", {}
        except httpx.TimeoutException:
            async def err_gen():
                yield json.dumps({"error": "upstream_timeout", "detail": "Request to upstream API timed out"})
            return 504, err_gen(), "application/json", {}
        except Exception as e:
            async def err_gen():
                yield json.dumps({"error": "proxy_error", "detail": str(e)})
            return 500, err_gen(), "application/json", {}
