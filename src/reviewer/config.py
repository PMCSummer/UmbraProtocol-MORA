from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(slots=True)
class TierConfig:
    enabled: bool
    model: str
    max_parallel_workers: int


@dataclass(slots=True)
class EscalationPolicy:
    tier1_escalate_confidence_max: float = 0.7
    tier2_second_opinion_confidence_max: float = 0.55
    second_opinion_on_high_priority: bool = True


@dataclass(slots=True)
class RetentionPolicy:
    keep_non_suspicious_trace: bool = False
    max_non_suspicious_traces: int = 25


@dataclass(slots=True)
class GenerationPolicy:
    base_seed: int = 1000
    themes: tuple[str, ...] = (
        "world_absence_poverty",
        "epistemic_fragility",
        "regulation_mode_validity_pressure",
        "ownership_self_prediction_instability",
        "memory_narrative_temptation",
    )
    max_cases_per_cycle: int = 8


@dataclass(slots=True)
class ReviewerPipelineConfig:
    ollama_base_url: str = "http://127.0.0.1:11434"
    request_timeout_seconds: float = 60.0
    retry_count: int = 1
    prompt_dir: str = "tools/reviewer_prompts"
    artifacts_root: str = "artifacts/reviewer"
    tiers: dict[str, TierConfig] = field(default_factory=dict)
    escalation: EscalationPolicy = field(default_factory=EscalationPolicy)
    retention: RetentionPolicy = field(default_factory=RetentionPolicy)
    generation: GenerationPolicy = field(default_factory=GenerationPolicy)

    @staticmethod
    def default() -> "ReviewerPipelineConfig":
        return ReviewerPipelineConfig(
            tiers={
                "tier1": TierConfig(
                    enabled=True,
                    model="gemma3:4b",
                    max_parallel_workers=2,
                ),
                "tier2": TierConfig(
                    enabled=True,
                    model="qwen3.5:9b",
                    max_parallel_workers=1,
                ),
                "tier3": TierConfig(
                    enabled=True,
                    model="llama3.1:8b",
                    max_parallel_workers=1,
                ),
            }
        )

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return payload

    def save(self, path: str | Path) -> Path:
        dst = Path(path).expanduser().resolve()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(
            json.dumps(self.to_json_dict(), ensure_ascii=True, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return dst

    @staticmethod
    def load(path: str | Path) -> "ReviewerPipelineConfig":
        src = Path(path).expanduser().resolve()
        raw = json.loads(src.read_text(encoding="utf-8"))
        tiers = {
            name: TierConfig(**values)
            for name, values in dict(raw.get("tiers", {})).items()
        }
        return ReviewerPipelineConfig(
            ollama_base_url=str(raw.get("ollama_base_url", "http://127.0.0.1:11434")),
            request_timeout_seconds=float(raw.get("request_timeout_seconds", 60.0)),
            retry_count=int(raw.get("retry_count", 1)),
            prompt_dir=str(raw.get("prompt_dir", "tools/reviewer_prompts")),
            artifacts_root=str(raw.get("artifacts_root", "artifacts/reviewer")),
            tiers=tiers if tiers else ReviewerPipelineConfig.default().tiers,
            escalation=EscalationPolicy(**dict(raw.get("escalation", {}))),
            retention=RetentionPolicy(**dict(raw.get("retention", {}))),
            generation=GenerationPolicy(**dict(raw.get("generation", {}))),
        )

