from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request


class OllamaClientError(RuntimeError):
    pass


@dataclass(slots=True)
class OllamaClient:
    base_url: str
    timeout_seconds: float
    retry_count: int = 1

    def _post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        url = f"{self.base_url.rstrip('/')}{path}"
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        req = request.Request(
            url=url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        last_error: Exception | None = None
        for _ in range(max(1, self.retry_count + 1)):
            try:
                with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    data = resp.read().decode("utf-8")
                parsed = json.loads(data)
                if not isinstance(parsed, dict):
                    raise OllamaClientError("ollama response is not JSON object")
                return parsed
            except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
        raise OllamaClientError(f"ollama request failed: {last_error}")

    def generate(self, *, model: str, prompt: str) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            # Keep each review call isolated; no carry-over chat session state.
            "keep_alive": 0,
        }
        response = self._post_json("/api/generate", payload)
        text = response.get("response")
        if not isinstance(text, str):
            raise OllamaClientError("ollama /api/generate returned non-string response")
        return text

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

