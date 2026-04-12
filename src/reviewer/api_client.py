from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request


class OllamaClientError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OllamaGenerateDiagnostics:
    endpoint: str
    request_payload: dict[str, Any]
    raw_http_response_body: str
    extracted_text: str
    response_field_used: str
    thinking_present: bool
    prompt_eval_count: int | None
    eval_count: int | None
    status: str  # ok | transport_error | timeout | empty_response | thinking_only_no_answer | parse_error
    error_message: str | None
    timeout: bool
    retry_count: int
    latency_ms: float


def _is_timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    if isinstance(exc, error.URLError):
        reason = getattr(exc, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return True
    return "timed out" in str(exc).lower()


def _extract_text_and_thinking(parsed: dict[str, Any]) -> tuple[str, str, bool]:
    message = parsed.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        thinking = message.get("thinking")
        content_text = content if isinstance(content, str) else ""
        thinking_text = thinking if isinstance(thinking, str) else ""
        return content_text, "message.content", bool(thinking_text.strip())
    response = parsed.get("response")
    content_text = response if isinstance(response, str) else ""
    thinking = parsed.get("thinking")
    thinking_text = thinking if isinstance(thinking, str) else ""
    return content_text, "response", bool(thinking_text.strip())


@dataclass(slots=True)
class OllamaClient:
    base_url: str
    timeout_seconds: float
    retry_count: int = 1

    def generate_with_diagnostics(
        self,
        *,
        model: str,
        prompt: str,
        timeout_seconds: float | None = None,
        retry_count: int | None = None,
        output_json_schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
        num_predict: int = 384,
        num_ctx: int = 8192,
        think: bool = False,
    ) -> OllamaGenerateDiagnostics:
        endpoint = "/api/chat"
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "think": bool(think),
            "options": {
                "temperature": float(temperature),
                "num_predict": int(num_predict),
                "num_ctx": int(num_ctx),
            },
            # Keep each review call isolated; no carry-over chat session state.
            "keep_alive": 0,
        }
        if output_json_schema is not None:
            payload["format"] = output_json_schema
        else:
            payload["format"] = "json"

        url = f"{self.base_url.rstrip('/')}{endpoint}"
        req = request.Request(
            url=url,
            data=json.dumps(payload, ensure_ascii=True).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        effective_timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds
        effective_retries = self.retry_count if retry_count is None else retry_count
        max_attempts = max(1, effective_retries + 1)

        call_started = time.perf_counter()
        last_error: Exception | None = None
        for attempt_idx in range(max_attempts):
            try:
                with request.urlopen(req, timeout=effective_timeout) as resp:
                    raw_http = resp.read().decode("utf-8", errors="replace")
                try:
                    parsed = json.loads(raw_http)
                except json.JSONDecodeError as exc:
                    latency_ms = round((time.perf_counter() - call_started) * 1000.0, 3)
                    return OllamaGenerateDiagnostics(
                        endpoint=endpoint,
                        request_payload=payload,
                        raw_http_response_body=raw_http,
                        extracted_text="",
                        response_field_used="unknown",
                        thinking_present=False,
                        prompt_eval_count=None,
                        eval_count=None,
                        status="parse_error",
                        error_message=f"invalid transport envelope JSON: {exc}",
                        timeout=False,
                        retry_count=attempt_idx,
                        latency_ms=latency_ms,
                    )
                if not isinstance(parsed, dict):
                    latency_ms = round((time.perf_counter() - call_started) * 1000.0, 3)
                    return OllamaGenerateDiagnostics(
                        endpoint=endpoint,
                        request_payload=payload,
                        raw_http_response_body=raw_http,
                        extracted_text="",
                        response_field_used="unknown",
                        thinking_present=False,
                        prompt_eval_count=None,
                        eval_count=None,
                        status="parse_error",
                        error_message="ollama response envelope is not object",
                        timeout=False,
                        retry_count=attempt_idx,
                        latency_ms=latency_ms,
                    )

                extracted, field_used, thinking_present = _extract_text_and_thinking(parsed)
                prompt_eval_count = (
                    int(parsed["prompt_eval_count"])
                    if isinstance(parsed.get("prompt_eval_count"), int)
                    else None
                )
                eval_count = (
                    int(parsed["eval_count"])
                    if isinstance(parsed.get("eval_count"), int)
                    else None
                )
                latency_ms = round((time.perf_counter() - call_started) * 1000.0, 3)
                if not extracted.strip():
                    status = "thinking_only_no_answer" if thinking_present else "empty_response"
                    return OllamaGenerateDiagnostics(
                        endpoint=endpoint,
                        request_payload=payload,
                        raw_http_response_body=raw_http,
                        extracted_text=extracted,
                        response_field_used=field_used,
                        thinking_present=thinking_present,
                        prompt_eval_count=prompt_eval_count,
                        eval_count=eval_count,
                        status=status,
                        error_message="thinking present but answer field empty"
                        if status == "thinking_only_no_answer"
                        else "empty model response text",
                        timeout=False,
                        retry_count=attempt_idx,
                        latency_ms=latency_ms,
                    )
                return OllamaGenerateDiagnostics(
                    endpoint=endpoint,
                    request_payload=payload,
                    raw_http_response_body=raw_http,
                    extracted_text=extracted,
                    response_field_used=field_used,
                    thinking_present=thinking_present,
                    prompt_eval_count=prompt_eval_count,
                    eval_count=eval_count,
                    status="ok",
                    error_message=None,
                    timeout=False,
                    retry_count=attempt_idx,
                    latency_ms=latency_ms,
                )
            except (error.URLError, error.HTTPError, TimeoutError, socket.timeout) as exc:
                last_error = exc
                timeout = _is_timeout_error(exc)
                if attempt_idx + 1 < max_attempts:
                    continue
                latency_ms = round((time.perf_counter() - call_started) * 1000.0, 3)
                return OllamaGenerateDiagnostics(
                    endpoint=endpoint,
                    request_payload=payload,
                    raw_http_response_body="",
                    extracted_text="",
                    response_field_used="unknown",
                    thinking_present=False,
                    prompt_eval_count=None,
                    eval_count=None,
                    status="timeout" if timeout else "transport_error",
                    error_message=f"ollama request failed: {exc}",
                    timeout=timeout,
                    retry_count=attempt_idx,
                    latency_ms=latency_ms,
                )

        latency_ms = round((time.perf_counter() - call_started) * 1000.0, 3)
        return OllamaGenerateDiagnostics(
            endpoint=endpoint,
            request_payload=payload,
            raw_http_response_body="",
            extracted_text="",
            response_field_used="unknown",
            thinking_present=False,
            prompt_eval_count=None,
            eval_count=None,
            status="transport_error",
            error_message=f"ollama request failed: {last_error}",
            timeout=False,
            retry_count=max_attempts - 1,
            latency_ms=latency_ms,
        )

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        timeout_seconds: float | None = None,
        retry_count: int | None = None,
    ) -> str:
        diagnostics = self.generate_with_diagnostics(
            model=model,
            prompt=prompt,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
        )
        if diagnostics.status != "ok":
            raise OllamaClientError(diagnostics.error_message or diagnostics.status)
        return diagnostics.extracted_text

    def health(self) -> dict[str, object]:
        url = f"{self.base_url.rstrip('/')}/api/tags"
        req = request.Request(url=url, method="GET")
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return {
                "ok": True,
                "models_count": len(data.get("models", [])) if isinstance(data, dict) else 0,
            }
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
