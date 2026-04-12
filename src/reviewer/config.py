from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(slots=True)
class TierConfig:
    enabled: bool
    model: str
    max_parallel_workers: int
    request_timeout_seconds: float | None = None
    retry_count: int | None = None
    num_ctx: int = 8192
    num_predict: int = 384
    temperature: float = 0.0
    max_trace_payload_chars: int | None = None
    trace_compaction_policy: str = "none"  # none | tail | head_tail


@dataclass(slots=True)
class EscalationPolicy:
    tier1_escalate_confidence_max: float = 0.7
    tier2_second_opinion_confidence_max: float = 0.55
    second_opinion_on_high_priority: bool = True


@dataclass(slots=True)
class RetentionPolicy:
    keep_non_suspicious_trace: bool = False
    max_non_suspicious_traces: int = 25
    keep_full_for_ordinary: bool | None = None
    ordinary_full_bundle_sample_rate: float = 0.0
    diagnostics_retention_max_files: int | None = None


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
class SchedulerPolicy:
    mode: str = "balanced_round_robin"  # balanced_round_robin | weighted
    family_weights: dict[str, float] = field(default_factory=dict)
    family_quotas: dict[str, int] = field(default_factory=dict)
    family_min_share: dict[str, float] = field(default_factory=dict)
    family_max_share: dict[str, float] = field(default_factory=dict)
    max_same_family_streak: int = 3
    shuffle_window: int = 0


@dataclass(slots=True)
class GuardrailPolicy:
    max_case_count: int = 1600
    max_duration_seconds: int = 12 * 60 * 60
    max_consecutive_infra_failures: int = 20
    rolling_window_size: int = 50
    max_rolling_infra_failure_rate: float = 0.25
    max_rolling_behavioral_flag_rate: float = 0.75
    rolling_behavioral_rate_action: str = "warn"  # warn | pause | stop
    max_repeated_same_family_streak: int = 5
    max_ordinary_storage_mb: int | None = None
    heartbeat_interval_seconds: int = 10
    checkpoint_interval_cases: int = 10
    warn_signal_code_dominance: float = 0.75
    warn_gap_code_dominance: float = 0.8
    warn_family_imbalance_share: float = 0.55
    warn_insufficient_evidence_rate: float = 0.2


@dataclass(slots=True)
class WarmupPolicy:
    enabled: bool = True
    case_count: int = 8
    max_infra_failures: int = 1
    max_parse_failures: int = 0


@dataclass(slots=True)
class NightRunPolicy:
    enabled: bool = False
    run_mode: str = "long"  # batch | long
    scheduler: SchedulerPolicy = field(default_factory=SchedulerPolicy)
    guardrails: GuardrailPolicy = field(default_factory=GuardrailPolicy)
    warmup: WarmupPolicy = field(default_factory=WarmupPolicy)
    batch_case_count: int = 100
    run_id_prefix: str = "tier1-night-run"
    checkpoint_resume: bool = True


@dataclass(slots=True)
class ReviewerPipelineConfig:
    ollama_base_url: str = "http://127.0.0.1:11434"
    request_timeout_seconds: float = 60.0
    retry_count: int = 1
    prompt_dir: str = "tools/reviewer_prompts"
    artifacts_root: str = "artifacts/reviewer"
    diagnostic_mode: bool = False
    tiers: dict[str, TierConfig] = field(default_factory=dict)
    escalation: EscalationPolicy = field(default_factory=EscalationPolicy)
    retention: RetentionPolicy = field(default_factory=RetentionPolicy)
    generation: GenerationPolicy = field(default_factory=GenerationPolicy)
    night_run: NightRunPolicy = field(default_factory=NightRunPolicy)

    @staticmethod
    def default() -> "ReviewerPipelineConfig":
        return ReviewerPipelineConfig(
            tiers={
                "tier1": TierConfig(
                    enabled=True,
                    model="gemma3:4b",
                    max_parallel_workers=1,
                    request_timeout_seconds=60.0,
                    retry_count=1,
                    num_ctx=8192,
                    num_predict=512,
                    temperature=0.0,
                ),
                "tier2": TierConfig(
                    enabled=False,
                    model="qwen3.5:9b",
                    max_parallel_workers=1,
                    request_timeout_seconds=120.0,
                    retry_count=2,
                    num_ctx=8192,
                    num_predict=512,
                    temperature=0.0,
                ),
                "tier3": TierConfig(
                    enabled=False,
                    model="llama3.1:8b",
                    max_parallel_workers=1,
                    request_timeout_seconds=90.0,
                    retry_count=1,
                    num_ctx=8192,
                    num_predict=512,
                    temperature=0.0,
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
            diagnostic_mode=bool(raw.get("diagnostic_mode", False)),
            tiers=tiers if tiers else ReviewerPipelineConfig.default().tiers,
            escalation=EscalationPolicy(**dict(raw.get("escalation", {}))),
            retention=RetentionPolicy(**dict(raw.get("retention", {}))),
            generation=GenerationPolicy(**dict(raw.get("generation", {}))),
            night_run=NightRunPolicy(
                **{
                    **dict(raw.get("night_run", {})),
                    "scheduler": SchedulerPolicy(
                        **dict(dict(raw.get("night_run", {})).get("scheduler", {}))
                    ),
                    "guardrails": GuardrailPolicy(
                        **dict(dict(raw.get("night_run", {})).get("guardrails", {}))
                    ),
                    "warmup": WarmupPolicy(
                        **dict(dict(raw.get("night_run", {})).get("warmup", {}))
                    ),
                }
            ),
        )
