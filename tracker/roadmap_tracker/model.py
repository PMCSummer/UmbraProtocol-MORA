from __future__ import annotations

import json
import re
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from docx import Document
except Exception:
    Document = None


SCHEMA_VERSION = 5
DEFAULT_STATUS = "later"
DEFAULT_STATUS_SOURCE = "user"
DEFAULT_TRACK = "build"
DEFAULT_LINE = "misc"
DEFAULT_VALIDATION_STATE = "planned"
DEFAULT_CLAIM_ROLE = "core_foundation_or_support"
DEFAULT_PRIORITY_BUCKET = "historical_foundation"
DEFAULT_CLAIM_STATE = "unknown"
DEFAULT_MATURITY = "L1_theoretical_only"
DEFAULT_NODE_TYPE = "phase"
DEFAULT_GRAPH_LAYER = "causal"
DEFAULT_EVIDENCE_STATUS = "planned"
DEFAULT_EVIDENCE_ROLE = "validation"

STATUS_LABELS = {
    "closed": "SEALED",
    "current": "ACTIVE",
    "next": "QUEUED",
    "later": "LATENT",
    "proposed": "PROPOSED",
}
TRACK_LABELS = {
    "build": "Assembly",
    "frontier": "Frontier",
    "refinement": "Refinement",
}
VALIDATION_LABELS = {
    "implemented_baseline": "Baseline sealed",
    "implemented_needs_calibration": "Calibration required",
    "implemented_but_not_claim_validated": "Implemented / claim unverified",
    "not_started_claim_gate": "Claim gate pending",
    "planned": "Planned",
}
CLAIM_ROLE_LABELS = {
    "core_foundation_or_support": "Foundation / support",
    "critical_honesty_gate": "Honesty gate",
    "world_grounding_gate": "Grounding gate",
    "validation_gate": "Validation gate",
    "supporting_agency_gate": "Agency support gate",
    "optional_enrichment": "Optional enrichment",
    "post_claim_extension": "Post-claim extension",
}
PRIORITY_LABELS = {
    "historical_foundation": "Archive foundation",
    "phase_1_honesty_and_protection": "Protocol I / honesty",
    "phase_2_long_run_validation_backbone": "Protocol II / validation backbone",
    "phase_3_world_grounding": "Protocol III / world grounding",
    "phase_4_strong_claim_audit": "Protocol IV / claim audit",
    "phase_5_optional_enrichment": "Protocol V / optional enrichment",
    "phase_6_post_claim_extension": "Protocol VI / post-claim extension",
    "governance": "Governance",
}
CLAIM_STATE_LABELS = {
    "unknown": "Unknown",
    "hypothesis": "Hypothesis",
    "mechanistically_specified": "Mechanistic spec",
    "implemented": "Implemented",
    "telemetry_supported": "Telemetry supported",
    "contested": "Contested",
    "falsified": "Falsified",
    "deprecated": "Deprecated",
}
MATURITY_LABELS = {
    "L1_theoretical_only": "L1 / theoretical",
    "L2_mechanistic_spec": "L2 / mechanism spec",
    "L3_toy_prototype": "L3 / toy prototype",
    "L4_integrated_prototype": "L4 / integrated prototype",
    "L5_telemetry_validated": "L5 / telemetry validated",
    "L6_adversarially_tested": "L6 / adversarially tested",
    "L7_stable_in_contour": "L7 / contour stable",
    "L8_externally_benchmarked": "L8 / externally benchmarked",
}
NODE_TYPE_LABELS = {
    "phase": "Phase module",
    "mechanism": "Mechanism",
    "evidence": "Evidence",
    "validation_protocol": "Validation surface",
    "failure_mode": "Failure mode",
    "constraint": "Constraint",
    "capability": "Capability",
    "biological_process": "Biological analogue",
    "governance": "Governance",
}
GRAPH_LAYER_LABELS = {
    "causal": "Causal lattice",
    "workflow": "Workflow chain",
    "provenance": "Evidence provenance",
    "validation": "Validation grid",
}
EDGE_RELATION_DEFAULT = "requires"
EDGE_RELATION_LABELS = {
    "requires": "requires",
    "modulates": "modulates",
    "gates": "gates",
    "invalidates": "invalidates",
    "arbitrates": "arbitrates",
    "observes_only": "observes_only",
    "requests_revalidation": "requests_revalidation",
    "feedback_learns": "feedback_learns",
    "body_world_couples": "body_world_couples",
    "overrides_survival": "overrides_survival",
    # Legacy relations are kept for backward-compatible load/edit paths.
    "causes": "causes",
    "enables": "enables",
    "tests": "tests",
    "contradicts": "contradicts",
    "grounds": "grounds",
    "generated_by": "generated_by",
    "implemented_by": "implemented_by",
    "measured_by": "measured_by",
    "supports": "supports",
    "challenged_by": "challenged_by",
    "refines": "refines",
    "abstracts_to": "abstracts_to",
    "belongs_to_scope": "belongs_to_scope",
    "blocks_claim": "blocks_claim",
    "forbids_shortcut": "forbids_shortcut",
}
EDGE_RELATION_LEGACY_ALIASES = {
    "blocks_claim": "invalidates",
}
EDGE_RELATION_STYLE_HINTS = {
    "requires": "solid_neutral",
    "modulates": "dotted_neutral",
    "gates": "dashed_attention",
    "invalidates": "solid_critical",
    "arbitrates": "solid_guidance",
    "observes_only": "dotted_low_authority",
    "requests_revalidation": "dashed_recheck",
    "feedback_learns": "solid_feedback",
    "body_world_couples": "solid_coupling",
    "overrides_survival": "solid_override",
}
DISCIPLINE_OPTIONS = [
    "psycholinguistics",
    "formal_semantics",
    "pragmatics",
    "systems_neuroscience",
    "computational_cognitive_science",
    "software_architecture",
    "ml_engineering",
    "validation_research",
]
EVIDENCE_STATUS_LABELS = {
    "planned": "PLANNED",
    "in_progress": "IN PROGRESS",
    "filled": "FILLED",
    "reviewed": "REVIEWED",
    "deprecated": "DEPRECATED",
}
EVIDENCE_ROLE_LABELS = {
    "principle": "Principle",
    "implementation": "Implementation",
    "validation": "Validation",
    "counterevidence": "Counterevidence",
    "failure_case": "Failure case",
}
EVIDENCE_STRENGTH_OPTIONS = ("weak", "moderate", "strong")
EVIDENCE_RELATION_OPTIONS = [
    "supports",
    "challenges",
    "constrains",
    "validates_test_surface",
    "blocks_claim",
]
EVIDENCE_SUPPORT_RELATIONS = {"supports", "constrains", "validates_test_surface"}
EVIDENCE_CHALLENGE_RELATIONS = {"challenges", "blocks_claim"}
EVIDENCE_MECHANISTIC_FIELDS = [
    ("source_type", "Source type", "single"),
    ("system_or_context", "System / context", "multi"),
    ("core_mechanism", "Core mechanism", "multi"),
    ("observed_effect", "Observed effect", "multi"),
    ("phase_relevance", "Phase relevance", "multi"),
    ("supports_claim", "Supports claim", "multi"),
    ("challenge_to_claim", "Challenge / counterclaim", "multi"),
    ("boundary_conditions", "Boundary conditions", "list"),
    ("failure_signal", "Failure signals", "list"),
    ("measurement_or_test", "Measurement / test", "multi"),
    ("notes", "Mechanistic notes", "multi"),
]
EVIDENCE_MECHANISTIC_FIELD_KINDS = {key: kind for key, _label, kind in EVIDENCE_MECHANISTIC_FIELDS}
LEGACY_MECHANISTIC_ALIASES = {
    "what_was_tested": "measurement_or_test",
    "what_mechanism_it_bears_on": "core_mechanism",
    "what_result_would_count_as_support": "supports_claim",
    "what_result_would_count_as_failure": "failure_signal",
}
EVIDENCE_ROLE_REQUIRED_MECHANISTIC_FIELDS = {
    "principle": ["core_mechanism", "phase_relevance"],
    "implementation": ["system_or_context", "core_mechanism", "phase_relevance"],
    "validation": ["measurement_or_test", "observed_effect", "core_mechanism", "phase_relevance"],
    "counterevidence": ["challenge_to_claim", "phase_relevance"],
    "failure_case": ["system_or_context", "failure_signal", "phase_relevance"],
}

PHASE_RE = re.compile(r"^([A-Z]\d(?:\.\d+)?[A-Z]?)\.\s+(.+)$")
AFTER_CODE_RE = re.compile(r"(?i)\bпосле\s+([A-Z]\d(?:\.\d+)?[A-Z]?)")


def humanize_token(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "—"
    return value.replace("_", " ")


def display_from_map(value: str, mapping: Dict[str, str]) -> str:
    return mapping.get(value, humanize_token(value))


def reverse_lookup(mapping: Dict[str, str], label: str, fallback: str) -> str:
    reverse = {v: k for k, v in mapping.items()}
    return reverse.get(label, fallback)


def normalize_code(code: str | None) -> str:
    return (code or "").strip().upper()


def parse_phase_node_code(node_id: str | None) -> str:
    token = str(node_id or "").strip()
    if token.startswith("phase::"):
        return normalize_code(token.split("::", 1)[1])
    return ""


def normalize_edge_relation(value: str | None) -> str:
    token = str(value or "").strip()
    if not token:
        return EDGE_RELATION_DEFAULT
    canonical = EDGE_RELATION_LEGACY_ALIASES.get(token, token)
    if canonical in EDGE_RELATION_LABELS:
        return canonical
    return EDGE_RELATION_DEFAULT


def listify(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value).strip()
    return [text] if text else []


def textblock_to_list(text: str) -> List[str]:
    lines: List[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        lines.append(line)
    return lines


def list_to_textblock(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items if str(item).strip())


def normalize_choice(value: str, allowed: Iterable[str], default: str) -> str:
    token = str(value or "").strip()
    return token if token in set(allowed) else default


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    output: List[str] = []
    for item in items:
        token = str(item).strip()
        if not token:
            continue
        if token in seen:
            continue
        seen.add(token)
        output.append(token)
    return output


def dedupe_text_blocks(text: str) -> str:
    blocks: List[str] = []
    current: List[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.rstrip()
        if line.strip():
            current.append(line)
            continue
        if current:
            blocks.append("\n".join(current).strip())
            current = []
    if current:
        blocks.append("\n".join(current).strip())

    seen: set[str] = set()
    output: List[str] = []
    for block in blocks:
        normalized = re.sub(r"\s+", " ", block).strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(block)
    return "\n\n".join(output)


def relation_is_supporting(relation: str) -> bool:
    return (relation or "supports").strip() in EVIDENCE_SUPPORT_RELATIONS


def relation_is_challenging(relation: str) -> bool:
    return (relation or "supports").strip() in EVIDENCE_CHALLENGE_RELATIONS


def normalize_phase_refs(phase_refs: Iterable[Dict[str, Any]]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for ref in phase_refs or []:
        if not isinstance(ref, dict):
            continue
        code = normalize_code(ref.get("code", ""))
        title = str(ref.get("title", "")).strip()
        relation = str(ref.get("relation", "supports")).strip() or "supports"
        if not code:
            continue
        marker = (code, relation)
        if marker in seen:
            continue
        seen.add(marker)
        normalized.append({"code": code, "title": title, "relation": relation})
    return normalized


def _normalize_mechanistic_value(value: Any, kind: str) -> Any:
    if kind == "list":
        if isinstance(value, list):
            return dedupe_preserve_order(str(item).strip() for item in value)
        return textblock_to_list(str(value or ""))
    return str(value or "").strip()


def normalize_mechanistic_payload(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    raw = dict(payload or {})
    normalized: Dict[str, Any] = {}
    field_names = {key for key, _label, _kind in EVIDENCE_MECHANISTIC_FIELDS}

    for key, _label, kind in EVIDENCE_MECHANISTIC_FIELDS:
        value = raw.get(key)
        if value in (None, "", []):
            for legacy_key, canonical_key in LEGACY_MECHANISTIC_ALIASES.items():
                if canonical_key == key and raw.get(legacy_key) not in (None, "", []):
                    value = raw.get(legacy_key)
                    break
        normalized_value = _normalize_mechanistic_value(value, kind)
        if normalized_value:
            normalized[key] = normalized_value

    for key, value in raw.items():
        if key in field_names or key in LEGACY_MECHANISTIC_ALIASES:
            continue
        if isinstance(value, list):
            extras = dedupe_preserve_order(str(item).strip() for item in value)
            if extras:
                normalized[key] = extras
        elif isinstance(value, dict):
            if value:
                normalized[key] = value
        else:
            token = str(value or "").strip()
            if token:
                normalized[key] = token
    return normalized


def extract_extra_mechanistic_payload(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    normalized = normalize_mechanistic_payload(payload)
    field_names = {key for key, _label, _kind in EVIDENCE_MECHANISTIC_FIELDS}
    return {key: value for key, value in normalized.items() if key not in field_names}


def mechanistic_payload_to_text_map(payload: Dict[str, Any] | None) -> Dict[str, str]:
    normalized = normalize_mechanistic_payload(payload)
    text_map: Dict[str, str] = {}
    for key, _label, kind in EVIDENCE_MECHANISTIC_FIELDS:
        value = normalized.get(key, [] if kind == "list" else "")
        if kind == "list":
            text_map[key] = list_to_textblock(value if isinstance(value, list) else textblock_to_list(str(value)))
        else:
            text_map[key] = str(value or "")
    return text_map


def build_mechanistic_payload_from_text_map(text_map: Dict[str, str], extra_payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for key, _label, kind in EVIDENCE_MECHANISTIC_FIELDS:
        raw = str((text_map or {}).get(key, "") or "")
        value = _normalize_mechanistic_value(raw, kind)
        if value:
            payload[key] = value
    for key, value in dict(extra_payload or {}).items():
        if key in {field for field, _label, _kind in EVIDENCE_MECHANISTIC_FIELDS}:
            continue
        if key in LEGACY_MECHANISTIC_ALIASES:
            continue
        payload[key] = value
    return normalize_mechanistic_payload(payload)


def export_mechanistic_payload(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    normalized = normalize_mechanistic_payload(payload)
    exported = dict(normalized)
    for legacy_key, canonical_key in LEGACY_MECHANISTIC_ALIASES.items():
        value = normalized.get(canonical_key)
        if not value:
            continue
        if isinstance(value, list):
            exported[legacy_key] = list_to_textblock(value)
        else:
            exported[legacy_key] = value
    return exported


def evidence_missing_fields(entry: "EvidenceEntry") -> List[str]:
    missing: List[str] = []
    if not entry.title.strip():
        missing.append("title")
    if not entry.summary.strip():
        missing.append("summary")
    if not entry.provenance.strip():
        missing.append("provenance")
    if not (entry.url.strip() or entry.citation.strip() or normalize_mechanistic_payload(entry.mechanistic_payload).get("source_type")):
        missing.append("citation_or_url_or_source_type")
    attached_phase_nodes = [value for value in entry.supports + entry.challenges if value.startswith("phase::")]
    if not entry.phase_refs and not attached_phase_nodes:
        missing.append("phase_attachment")

    mech = normalize_mechanistic_payload(entry.mechanistic_payload)
    for field in EVIDENCE_ROLE_REQUIRED_MECHANISTIC_FIELDS.get(entry.evidence_role, []):
        value = mech.get(field)
        if not value:
            missing.append(f"mechanistic_payload.{field}")
    return missing


def deep_merge_dict(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for key in set(base) | set(patch):
        base_value = base.get(key)
        patch_value = patch.get(key)
        if isinstance(base_value, dict) and isinstance(patch_value, dict):
            merged[key] = deep_merge_dict(base_value, patch_value)
        elif key in patch:
            merged[key] = patch_value
        else:
            merged[key] = base_value
    return merged


def infer_line_from_code(code: str) -> str:
    code = normalize_code(code)
    if not code:
        return DEFAULT_LINE
    mapping = {
        "F": "foundation",
        "I": "identity_and_infrastructure",
        "C": "continuity",
        "S": "self_and_non_self",
        "T": "thought_and_semantic_runtime",
        "O": "social_ecology_and_other_models",
        "G": "semantic_grounding_and_verbal_causality",
        "V": "communicative_intent_and_verbalization",
        "A": "external_action_and_tool_agency",
        "E": "endogenous_attractors_and_autonomous_drive",
        "R": "refinement",
        "L": "regulation_refinement",
        "N": "narrative_refinement",
        "P": "projects_and_long_horizon_causality",
        "W": "world_grounding_and_priors",
        "M": "benchmark_and_measurement",
        "K": "authority_audit",
        "GOV": "governance",
    }
    if code.startswith("GOV"):
        return "governance"
    return mapping.get(code[0], DEFAULT_LINE)


@dataclass
class AlternativeModel:
    title: str = ""
    summary: str = ""
    why_not_adopted: str = ""

    @classmethod
    def from_dict(cls, item: Dict[str, Any]) -> "AlternativeModel":
        return cls(
            title=str(item.get("title", "")).strip(),
            summary=str(item.get("summary", "")).strip(),
            why_not_adopted=str(item.get("why_not_adopted", "")).strip(),
        )


@dataclass
class KnowledgeCard:
    functional_role: str = ""
    why_exists: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    authority: str = ""
    forbidden_shortcuts: List[str] = field(default_factory=list)
    uncertainty_policy: str = ""
    observables: List[str] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    falsifiers: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    biological_analogy: str = ""
    biological_support: str = ""
    evidence_strength: str = ""
    provenance_note: str = ""
    disciplines: List[str] = field(default_factory=list)
    alternative_models: List[AlternativeModel] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)

    def searchable_blob(self) -> str:
        parts: List[str] = [
            self.functional_role,
            self.why_exists,
            self.authority,
            self.uncertainty_policy,
            self.biological_analogy,
            self.biological_support,
            self.evidence_strength,
            self.provenance_note,
            " ".join(self.inputs),
            " ".join(self.outputs),
            " ".join(self.forbidden_shortcuts),
            " ".join(self.observables),
            " ".join(self.failure_modes),
            " ".join(self.falsifiers),
            " ".join(self.tests),
            " ".join(self.disciplines),
            " ".join(self.evidence_ids),
            " ".join(a.title + " " + a.summary + " " + a.why_not_adopted for a in self.alternative_models),
        ]
        return " ".join(p for p in parts if p).lower()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "functional_role": self.functional_role,
            "why_exists": self.why_exists,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "authority": self.authority,
            "forbidden_shortcuts": self.forbidden_shortcuts,
            "uncertainty_policy": self.uncertainty_policy,
            "observables": self.observables,
            "failure_modes": self.failure_modes,
            "falsifiers": self.falsifiers,
            "tests": self.tests,
            "biological_analogy": self.biological_analogy,
            "biological_support": self.biological_support,
            "evidence_strength": self.evidence_strength,
            "provenance_note": self.provenance_note,
            "disciplines": self.disciplines,
            "alternative_models": [asdict(item) for item in self.alternative_models],
            "evidence_ids": self.evidence_ids,
        }

    @classmethod
    def from_dict(cls, item: Dict[str, Any] | None) -> "KnowledgeCard":
        item = item or {}
        return cls(
            functional_role=str(item.get("functional_role", "")).strip(),
            why_exists=str(item.get("why_exists", "")).strip(),
            inputs=listify(item.get("inputs", [])),
            outputs=listify(item.get("outputs", [])),
            authority=str(item.get("authority", "")).strip(),
            forbidden_shortcuts=listify(item.get("forbidden_shortcuts", [])),
            uncertainty_policy=str(item.get("uncertainty_policy", "")).strip(),
            observables=listify(item.get("observables", [])),
            failure_modes=listify(item.get("failure_modes", [])),
            falsifiers=listify(item.get("falsifiers", [])),
            tests=listify(item.get("tests", [])),
            biological_analogy=str(item.get("biological_analogy", "")).strip(),
            biological_support=str(item.get("biological_support", "")).strip(),
            evidence_strength=str(item.get("evidence_strength", "")).strip(),
            provenance_note=str(item.get("provenance_note", "")).strip(),
            disciplines=listify(item.get("disciplines", [])),
            alternative_models=[AlternativeModel.from_dict(x) for x in item.get("alternative_models", []) or []],
            evidence_ids=listify(item.get("evidence_ids", [])),
        )


@dataclass
class Phase:
    code: str
    title: str
    track: str = DEFAULT_TRACK
    line: str = DEFAULT_LINE
    after: Optional[str] = None
    status: str = DEFAULT_STATUS
    status_source: str = DEFAULT_STATUS_SOURCE
    spec: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    implemented_after: Optional[str] = None
    conceptually_after: List[str] = field(default_factory=list)
    claim_blocked_by: List[str] = field(default_factory=list)
    validation_state: str = DEFAULT_VALIDATION_STATE
    claim_role: str = DEFAULT_CLAIM_ROLE
    priority_bucket: str = DEFAULT_PRIORITY_BUCKET
    risk_tags: List[str] = field(default_factory=list)
    claim_state: str = DEFAULT_CLAIM_STATE
    maturity: str = DEFAULT_MATURITY
    knowledge_card: KnowledgeCard = field(default_factory=KnowledgeCard)
    related_node_ids: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.code = normalize_code(self.code)
        self.title = self.title.strip()
        self.track = (self.track or DEFAULT_TRACK).strip() or DEFAULT_TRACK
        self.line = (self.line or infer_line_from_code(self.code)).strip() or DEFAULT_LINE
        self.after = normalize_code(self.after) or None
        self.implemented_after = normalize_code(self.implemented_after) or None
        self.conceptually_after = [normalize_code(item) for item in self.conceptually_after if normalize_code(item)]
        self.claim_blocked_by = [normalize_code(item) for item in self.claim_blocked_by if normalize_code(item)]
        self.risk_tags = [str(item).strip() for item in self.risk_tags if str(item).strip()]
        self.related_node_ids = [str(item).strip() for item in self.related_node_ids if str(item).strip()]
        self.notes = self.notes.strip()

    @property
    def display_track(self) -> str:
        return display_from_map(self.track, TRACK_LABELS)

    @property
    def display_status(self) -> str:
        return display_from_map(self.status, STATUS_LABELS)

    @property
    def display_validation_state(self) -> str:
        return display_from_map(self.validation_state, VALIDATION_LABELS)

    @property
    def display_claim_role(self) -> str:
        return display_from_map(self.claim_role, CLAIM_ROLE_LABELS)

    @property
    def display_priority_bucket(self) -> str:
        return display_from_map(self.priority_bucket, PRIORITY_LABELS)

    @property
    def display_claim_state(self) -> str:
        return display_from_map(self.claim_state, CLAIM_STATE_LABELS)

    @property
    def display_maturity(self) -> str:
        return display_from_map(self.maturity, MATURITY_LABELS)

    @property
    def protocol_label(self) -> str:
        return f"{self.code} // {self.title}"

    def protocol_vector(self) -> List[str]:
        return [
            f"TRACK    {self.display_track}",
            f"LINE     {humanize_token(self.line)}",
            f"STATE    {self.display_status}",
            f"VERIFY   {self.display_validation_state}",
            f"CLAIM    {self.display_claim_state}",
            f"ROLE     {self.display_claim_role}",
            f"LEVEL    {self.display_maturity}",
        ]

    def dependency_codes(self) -> List[str]:
        deps: List[str] = []
        for source in [self.after, self.implemented_after, *self.conceptually_after]:
            code = normalize_code(source)
            if code and code != normalize_code(self.code) and code not in deps:
                deps.append(code)
        return deps

    def rendered_description(self) -> str:
        lines: List[str] = []
        if self.after:
            lines.append(f"Operational dependency: {self.after}")
        if self.implemented_after and self.implemented_after != self.after:
            lines.append(f"Historical implementation: {self.implemented_after}")
        if self.conceptually_after:
            lines.append(f"Conceptual chain: {', '.join(self.conceptually_after)}")
        if self.claim_blocked_by:
            lines.append(f"Claim blockers: {', '.join(self.claim_blocked_by)}")
        if lines:
            lines.append("")

        objective = (self.spec or {}).get("objective", "")
        includes = listify((self.spec or {}).get("includes", []))
        rationale = (self.spec or {}).get("rationale", "")
        excludes = listify((self.spec or {}).get("excludes", []))

        if objective:
            lines.append("Directive:")
            lines.append(str(objective).strip())
            lines.append("")
        if includes:
            lines.append("Included surfaces:")
            for item in includes:
                lines.append(f"- {item}")
            lines.append("")
        if rationale:
            lines.append("Rationale:")
            lines.append(str(rationale).strip())
            lines.append("")
        if excludes:
            lines.append("Excluded surfaces:")
            for item in excludes:
                lines.append(f"- {item}")
            lines.append("")
        if self.risk_tags:
            lines.append("Risk markers:")
            for tag in self.risk_tags:
                lines.append(f"- {tag}")
            lines.append("")
        if self.knowledge_card.functional_role:
            lines.append("Functional role:")
            lines.append(self.knowledge_card.functional_role)
            lines.append("")
        if self.knowledge_card.forbidden_shortcuts:
            lines.append("Forbidden shortcuts:")
            for item in self.knowledge_card.forbidden_shortcuts:
                lines.append(f"- {item}")
            lines.append("")

        rendered = "\n".join(lines).strip()
        return rendered or "(Directive not recorded)"

    def searchable_blob(self) -> str:
        parts = [
            self.code,
            self.title,
            self.track,
            self.line,
            self.status,
            self.validation_state,
            self.claim_role,
            self.priority_bucket,
            self.claim_state,
            self.maturity,
            self.rendered_description(),
            self.notes,
            " ".join(self.claim_blocked_by),
            " ".join(self.risk_tags),
            " ".join(self.related_node_ids),
            self.knowledge_card.searchable_blob(),
        ]
        return " ".join(p for p in parts if p).lower()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "track": self.track,
            "line": self.line,
            "after": self.after,
            "status": self.status,
            "status_source": self.status_source,
            "spec": self.spec,
            "notes": self.notes,
            "implemented_after": self.implemented_after,
            "conceptually_after": self.conceptually_after,
            "claim_blocked_by": self.claim_blocked_by,
            "validation_state": self.validation_state,
            "claim_role": self.claim_role,
            "priority_bucket": self.priority_bucket,
            "risk_tags": self.risk_tags,
            "claim_state": self.claim_state,
            "maturity": self.maturity,
            "knowledge_card": self.knowledge_card.to_dict(),
            "related_node_ids": self.related_node_ids,
        }

    def to_todo_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "track": self.track,
            "line": self.line,
            "after": self.after,
            "status": self.status,
            "status_source": self.status_source,
            "spec": {
                "objective": "TODO: Какой точный механизм или state-transition реализует эта фаза? Что должно стать истинным после её работы?",
                "includes": [
                    "TODO: Какие компоненты обязательны для этой фазы?",
                    "TODO: Какие подпроцессы должны существовать явно, а не подразумеваться?",
                ],
                "rationale": "TODO: Какую архитектурную дыру закрывает эта фаза? Что ломается или становится нечестным без неё?",
                "excludes": [
                    "TODO: Что НЕ входит в ответственность этой фазы?",
                    "TODO: Какие соседние функции эта фаза не должна молча подменять?",
                ],
            },
            "notes": "TODO: Свободные заметки, caveats, blast radius, открытые вопросы, implementation warnings.",
            "implemented_after": self.implemented_after,
            "conceptually_after": list(self.conceptually_after),
            "claim_blocked_by": list(self.claim_blocked_by),
            "validation_state": self.validation_state,
            "claim_role": self.claim_role,
            "priority_bucket": self.priority_bucket,
            "risk_tags": [
                "TODO: Самый вероятный shortcut / подмена механизма",
                "TODO: Самый вероятный calibration / regression / drift risk",
                "TODO: Самый опасный каскадный эффект на соседние фазы",
            ],
            "claim_state": self.claim_state,
            "maturity": self.maturity,
            "knowledge_card": {
                "functional_role": "TODO: Какую незаменимую каузальную роль играет эта фаза?",
                "why_exists": "TODO: Какую дыру в архитектуре она закрывает и почему это отдельный слой?",
                "inputs": ["TODO: Какие точные входы, контракты и предпосылки у фазы?"],
                "outputs": ["TODO: Какие точные выходы и обязательные поля она должна выдавать?"],
                "authority": "TODO: Что эта фаза имеет право утверждать, а что ей утверждать запрещено?",
                "forbidden_shortcuts": [
                    "TODO: Какие shortcut-реализации здесь особенно опасны?",
                    "TODO: Какие эвристики допустимы только как fallback, но не как ядро?",
                ],
                "uncertainty_policy": "TODO: Что делает слой при непонимании, неоднозначности или недостатке сигнала?",
                "observables": ["TODO: Какие наблюдаемые признаки подтверждают, что слой реально работает?"],
                "failure_modes": [
                    "TODO: Какой типовой режим поломки у этой фазы?",
                    "TODO: Какой опасный failure mode выглядит как успех?",
                ],
                "falsifiers": ["TODO: Что опровергнет корректность этого слоя?"],
                "tests": [
                    "TODO: Какой механизм-ориентированный тест обязан проходить?",
                    "TODO: Какой adversarial / ablation / perturbation test нужен?",
                ],
                "biological_analogy": "TODO: На какой биологический/когнитивный процесс это функционально похоже?",
                "biological_support": "TODO: Насколько сильна биологическая/когнитивная поддержка этой идеи?",
                "evidence_strength": "TODO: Насколько сильна доказательная база и почему?",
                "provenance_note": "TODO: Откуда вообще взят этот дизайн слоя?",
                "disciplines": ["TODO: Какая дисциплина реально даёт механизм / ограничения / язык описания?"],
                "alternative_models": [
                    {
                        "title": "TODO: Название альтернативной модели",
                        "summary": "TODO: В чём состоит альтернатива?",
                        "why_not_adopted": "TODO: Почему альтернатива не выбрана?",
                    }
                ],
                "evidence_ids": ["TODO: Какие evidence entries реально поддерживают или оспаривают фазу?"],
            },
            "related_node_ids": list(self.related_node_ids),
        }

    @classmethod
    def from_dict(cls, item: Dict[str, Any]) -> "Phase":
        legacy_knowledge = {}
        if not item.get("knowledge_card"):
            legacy_knowledge = {"functional_role": str((item.get("spec") or {}).get("objective", "")).strip()}
        return cls(
            code=str(item.get("code", "")).strip(),
            title=str(item.get("title", "")).strip(),
            track=str(item.get("track", DEFAULT_TRACK)).strip() or DEFAULT_TRACK,
            line=str(item.get("line", infer_line_from_code(str(item.get("code", ""))))).strip() or DEFAULT_LINE,
            after=(str(item.get("after")).strip() if item.get("after") is not None else None),
            status=str(item.get("status", DEFAULT_STATUS)).strip() or DEFAULT_STATUS,
            status_source=str(item.get("status_source", DEFAULT_STATUS_SOURCE)).strip() or DEFAULT_STATUS_SOURCE,
            spec=item.get("spec", {}) or {},
            notes=str(item.get("notes", "")).strip(),
            implemented_after=(str(item.get("implemented_after")).strip() if item.get("implemented_after") is not None else None),
            conceptually_after=listify(item.get("conceptually_after", [])),
            claim_blocked_by=listify(item.get("claim_blocked_by", [])),
            validation_state=str(item.get("validation_state", DEFAULT_VALIDATION_STATE)).strip() or DEFAULT_VALIDATION_STATE,
            claim_role=str(item.get("claim_role", DEFAULT_CLAIM_ROLE)).strip() or DEFAULT_CLAIM_ROLE,
            priority_bucket=str(item.get("priority_bucket", DEFAULT_PRIORITY_BUCKET)).strip() or DEFAULT_PRIORITY_BUCKET,
            risk_tags=listify(item.get("risk_tags", [])),
            claim_state=str(item.get("claim_state", DEFAULT_CLAIM_STATE)).strip() or DEFAULT_CLAIM_STATE,
            maturity=str(item.get("maturity", DEFAULT_MATURITY)).strip() or DEFAULT_MATURITY,
            knowledge_card=KnowledgeCard.from_dict(item.get("knowledge_card") or legacy_knowledge),
            related_node_ids=listify(item.get("related_node_ids", [])),
        )

    @classmethod
    def from_legacy(cls, raw: Dict[str, Any]) -> "Phase":
        code = str(raw.get("code", "")).strip()
        title = str(raw.get("title", "")).strip()
        section = str(raw.get("section", "Other")).strip()
        description = str(raw.get("description", "")).strip()
        suggested_status = str(raw.get("suggested_status", DEFAULT_STATUS)).strip() or DEFAULT_STATUS
        user_status = raw.get("user_status")
        notes = str(raw.get("notes", "")).strip()

        section_to_track = {"Build": "build", "Refinement": "refinement", "Other": "frontier"}
        track = section_to_track.get(section, DEFAULT_TRACK)
        status = str(user_status or suggested_status or DEFAULT_STATUS).strip()
        if status == "refine":
            status = DEFAULT_STATUS
            if track != "refinement":
                track = "refinement"

        after_match = AFTER_CODE_RE.search(description)
        after = after_match.group(1).strip().upper() if after_match else None
        spec = {"objective": description, "includes": [], "rationale": "", "excludes": []}
        return cls(
            code=code,
            title=title,
            track=track,
            line=infer_line_from_code(code),
            after=after,
            status=status if status in STATUS_LABELS else DEFAULT_STATUS,
            status_source="derived",
            spec=spec,
            notes=notes,
            implemented_after=after,
            validation_state="implemented_baseline" if status == "closed" else "planned",
            claim_role="core_foundation_or_support",
            priority_bucket="historical_foundation" if status == "closed" else "phase_2_long_run_validation_backbone",
            knowledge_card=KnowledgeCard(functional_role=description),
        )


def phase_objective_text(phase: "Phase") -> str:
    return str((phase.spec or {}).get("objective", "")).strip()


@dataclass
class GovernanceGate:
    code: str
    title: str
    status: str = DEFAULT_STATUS
    objective: str = ""
    rationale: str = ""
    notes: str = ""
    claim_state: str = DEFAULT_CLAIM_STATE
    maturity: str = DEFAULT_MATURITY

    def __post_init__(self) -> None:
        self.code = normalize_code(self.code)
        self.title = self.title.strip()
        self.notes = self.notes.strip()

    @property
    def display_status(self) -> str:
        return display_from_map(self.status, STATUS_LABELS)

    @property
    def protocol_label(self) -> str:
        return f"{self.code} // {self.title}"

    def searchable_blob(self) -> str:
        return " ".join([
            self.code, self.title, self.status, self.objective, self.rationale, self.notes, self.claim_state, self.maturity
        ]).lower()

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "code": self.code,
            "title": self.title,
            "status": self.status,
            "objective": self.objective,
            "rationale": self.rationale,
            "claim_state": self.claim_state,
            "maturity": self.maturity,
        }
        if self.notes:
            data["notes"] = self.notes
        return data

    @classmethod
    def from_dict(cls, item: Dict[str, Any]) -> "GovernanceGate":
        return cls(
            code=str(item.get("code", "")).strip(),
            title=str(item.get("title", "")).strip(),
            status=str(item.get("status", DEFAULT_STATUS)).strip() or DEFAULT_STATUS,
            objective=str(item.get("objective", "")).strip(),
            rationale=str(item.get("rationale", "")).strip(),
            notes=str(item.get("notes", "")).strip(),
            claim_state=str(item.get("claim_state", DEFAULT_CLAIM_STATE)).strip() or DEFAULT_CLAIM_STATE,
            maturity=str(item.get("maturity", DEFAULT_MATURITY)).strip() or DEFAULT_MATURITY,
        )


@dataclass
class ClaimLevel:
    level: str
    name: str
    allowed_claim: str
    requires: List[str] = field(default_factory=list)
    forbidden_shortcuts: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, item: Dict[str, Any]) -> "ClaimLevel":
        return cls(
            level=str(item.get("level", "")).strip(),
            name=str(item.get("name", "")).strip(),
            allowed_claim=str(item.get("allowed_claim", "")).strip(),
            requires=listify(item.get("requires", [])),
            forbidden_shortcuts=listify(item.get("forbidden_shortcuts", [])),
        )


@dataclass
class EvidenceEntry:
    evidence_id: str
    title: str
    kind: str = "paper"
    status: str = DEFAULT_EVIDENCE_STATUS
    evidence_role: str = DEFAULT_EVIDENCE_ROLE
    phase_refs: List[Dict[str, str]] = field(default_factory=list)
    claim_refs: List[str] = field(default_factory=list)
    gate_refs: List[str] = field(default_factory=list)
    citation: str = ""
    url: str = ""
    summary: str = ""
    mechanistic_payload: Dict[str, Any] = field(default_factory=dict)
    supports: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    provenance: str = ""
    updated_at: str = ""
    evidence_strength: str = "weak"
    ready_for_use: bool = False

    def __post_init__(self) -> None:
        self.evidence_id = self.evidence_id.strip()
        self.title = self.title.strip()
        self.kind = self.kind.strip() or "paper"
        self.status = normalize_choice(self.status, EVIDENCE_STATUS_LABELS.keys(), DEFAULT_EVIDENCE_STATUS)
        self.evidence_role = normalize_choice(self.evidence_role, EVIDENCE_ROLE_LABELS.keys(), DEFAULT_EVIDENCE_ROLE)
        self.evidence_strength = normalize_choice(self.evidence_strength, EVIDENCE_STRENGTH_OPTIONS, "weak")
        self.citation = self.citation.strip()
        self.url = self.url.strip()
        self.summary = self.summary.strip()
        self.phase_refs = normalize_phase_refs(self.phase_refs)
        self.claim_refs = dedupe_preserve_order(self.claim_refs)
        self.gate_refs = dedupe_preserve_order(self.gate_refs)
        self.supports = dedupe_preserve_order(self.supports)
        self.challenges = dedupe_preserve_order(self.challenges)
        self.limitations = dedupe_preserve_order(self.limitations)
        self.open_questions = dedupe_preserve_order(self.open_questions)
        self.provenance = self.provenance.strip()
        self.updated_at = self.updated_at.strip()
        self.mechanistic_payload = normalize_mechanistic_payload(self.mechanistic_payload)
        self.ready_for_use = bool(self.ready_for_use)

    @property
    def protocol_label(self) -> str:
        return f"{self.evidence_id} // {self.title}"

    @property
    def readiness_missing_fields(self) -> List[str]:
        return evidence_missing_fields(self)

    @property
    def effective_ready_for_use(self) -> bool:
        return self.ready_for_use and not self.readiness_missing_fields

    @property
    def readiness_label(self) -> str:
        return "READY" if self.effective_ready_for_use else "HOLD"

    def searchable_blob(self) -> str:
        mech_blob: List[str] = []
        for value in normalize_mechanistic_payload(self.mechanistic_payload).values():
            if isinstance(value, list):
                mech_blob.extend(value)
            elif isinstance(value, dict):
                mech_blob.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
            else:
                mech_blob.append(str(value))
        return " ".join([
            self.evidence_id,
            self.title,
            self.kind,
            self.status,
            self.evidence_role,
            self.citation,
            self.url,
            self.summary,
            self.provenance,
            self.updated_at,
            self.evidence_strength,
            " ".join(self.supports),
            " ".join(self.challenges),
            " ".join(self.claim_refs),
            " ".join(self.gate_refs),
            " ".join(self.limitations),
            " ".join(self.open_questions),
            " ".join(f"{r.get('code','')} {r.get('title','')} {r.get('relation','')}" for r in self.phase_refs),
            " ".join(mech_blob),
        ]).lower()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "title": self.title,
            "kind": self.kind,
            "status": self.status,
            "evidence_role": self.evidence_role,
            "phase_refs": self.phase_refs,
            "claim_refs": self.claim_refs,
            "gate_refs": self.gate_refs,
            "citation": self.citation,
            "url": self.url,
            "summary": self.summary,
            "mechanistic_payload": export_mechanistic_payload(self.mechanistic_payload),
            "supports": self.supports,
            "challenges": self.challenges,
            "limitations": self.limitations,
            "open_questions": self.open_questions,
            "provenance": self.provenance,
            "updated_at": self.updated_at,
            "evidence_strength": self.evidence_strength,
            "ready_for_use": self.ready_for_use,
        }

    @classmethod
    def from_dict(cls, item: Dict[str, Any]) -> "EvidenceEntry":
        phase_refs = item.get("phase_refs", []) or []
        if not phase_refs:
            for support in listify(item.get("supports", [])):
                if support.startswith("phase::"):
                    phase_refs.append({"code": support.split("::", 1)[1].upper(), "title": "", "relation": "supports"})
            for challenge in listify(item.get("challenges", [])):
                if challenge.startswith("phase::"):
                    phase_refs.append({"code": challenge.split("::", 1)[1].upper(), "title": "", "relation": "challenges"})
        return cls(
            evidence_id=str(item.get("evidence_id", "")).strip(),
            title=str(item.get("title", "")).strip(),
            kind=str(item.get("kind", "paper")).strip() or "paper",
            status=str(item.get("status", DEFAULT_EVIDENCE_STATUS)).strip() or DEFAULT_EVIDENCE_STATUS,
            evidence_role=str(item.get("evidence_role", DEFAULT_EVIDENCE_ROLE)).strip() or DEFAULT_EVIDENCE_ROLE,
            phase_refs=phase_refs,
            claim_refs=listify(item.get("claim_refs", [])),
            gate_refs=listify(item.get("gate_refs", [])),
            citation=str(item.get("citation", "")).strip(),
            url=str(item.get("url", "")).strip(),
            summary=str(item.get("summary", "")).strip(),
            mechanistic_payload=dict(item.get("mechanistic_payload", {}) or {}),
            supports=listify(item.get("supports", [])),
            challenges=listify(item.get("challenges", [])),
            limitations=listify(item.get("limitations", [])),
            open_questions=listify(item.get("open_questions", [])),
            provenance=str(item.get("provenance", "")).strip(),
            updated_at=str(item.get("updated_at", "")).strip(),
            evidence_strength=str(item.get("evidence_strength", "weak")).strip() or "weak",
            ready_for_use=bool(item.get("ready_for_use", False)),
        )

    def to_export_dict(self, model: "RoadmapModel") -> Dict[str, Any]:
        payload = self.to_dict()
        if self.phase_refs:
            payload["phase_refs"] = [
                {
                    "code": ref.get("code", ""),
                    "title": (model.get_phase(ref.get("code", "")).title if model.get_phase(ref.get("code", "")) else ref.get("title", "")),
                    "relation": ref.get("relation", "supports"),
                }
                for ref in self.phase_refs
            ]
        payload["readiness_missing_fields"] = self.readiness_missing_fields
        payload["effective_ready_for_use"] = self.effective_ready_for_use
        return payload

    def attached_summary(self) -> str:
        if self.phase_refs:
            chunks = []
            for ref in self.phase_refs[:3]:
                code = ref.get("code", "")
                title = ref.get("title", "")
                relation = ref.get("relation", "supports")
                if title:
                    chunks.append(f"{code} — {title} ({relation})")
                else:
                    chunks.append(f"{code} ({relation})")
            return ", ".join(chunks) + ("" if len(self.phase_refs) <= 3 else " …")
        refs = [x for x in self.supports + self.challenges if x.startswith("phase::")]
        return ", ".join(refs[:3]) + ("" if len(refs) <= 3 else " …") if refs else "—"


@dataclass
class GraphNode:
    node_id: str
    label: str
    node_type: str = DEFAULT_NODE_TYPE
    layer_hint: str = DEFAULT_GRAPH_LAYER
    summary: str = ""
    phase_code: Optional[str] = None
    claim_state: str = DEFAULT_CLAIM_STATE
    maturity: str = DEFAULT_MATURITY
    x: float = 0.0
    y: float = 0.0
    width: float = 280.0
    height: float = 108.0
    knowledge_card: KnowledgeCard = field(default_factory=KnowledgeCard)
    notes: str = ""

    def __post_init__(self) -> None:
        self.node_id = self.node_id.strip()
        self.label = self.label.strip()
        self.summary = self.summary.strip()
        self.phase_code = normalize_code(self.phase_code) or None
        self.notes = self.notes.strip()

    @property
    def protocol_label(self) -> str:
        return f"{self.node_id} // {self.label}"

    def display_node_type(self) -> str:
        return display_from_map(self.node_type, NODE_TYPE_LABELS)

    def display_layer_hint(self) -> str:
        return display_from_map(self.layer_hint, GRAPH_LAYER_LABELS)

    def searchable_blob(self) -> str:
        return " ".join([
            self.node_id, self.label, self.node_type, self.layer_hint, self.summary,
            self.phase_code or "", self.claim_state, self.maturity, self.notes,
            self.knowledge_card.searchable_blob(),
        ]).lower()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type,
            "layer_hint": self.layer_hint,
            "summary": self.summary,
            "phase_code": self.phase_code,
            "claim_state": self.claim_state,
            "maturity": self.maturity,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "knowledge_card": self.knowledge_card.to_dict(),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, item: Dict[str, Any]) -> "GraphNode":
        return cls(
            node_id=str(item.get("node_id", "")).strip(),
            label=str(item.get("label", "")).strip(),
            node_type=str(item.get("node_type", DEFAULT_NODE_TYPE)).strip() or DEFAULT_NODE_TYPE,
            layer_hint=str(item.get("layer_hint", DEFAULT_GRAPH_LAYER)).strip() or DEFAULT_GRAPH_LAYER,
            summary=str(item.get("summary", "")).strip(),
            phase_code=(str(item.get("phase_code")).strip() if item.get("phase_code") is not None else None),
            claim_state=str(item.get("claim_state", DEFAULT_CLAIM_STATE)).strip() or DEFAULT_CLAIM_STATE,
            maturity=str(item.get("maturity", DEFAULT_MATURITY)).strip() or DEFAULT_MATURITY,
            x=float(item.get("x", 0.0) or 0.0),
            y=float(item.get("y", 0.0) or 0.0),
            width=float(item.get("width", 280.0) or 280.0),
            height=float(item.get("height", 108.0) or 108.0),
            knowledge_card=KnowledgeCard.from_dict(item.get("knowledge_card")),
            notes=str(item.get("notes", "")).strip(),
        )


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str = EDGE_RELATION_DEFAULT
    layer: str = DEFAULT_GRAPH_LAYER
    note: str = ""

    def __post_init__(self) -> None:
        self.source = str(self.source or "").strip()
        self.target = str(self.target or "").strip()
        self.relation = normalize_edge_relation(self.relation)
        self.layer = str(self.layer or DEFAULT_GRAPH_LAYER).strip() or DEFAULT_GRAPH_LAYER
        self.note = str(self.note or "").strip()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["relation"] = normalize_edge_relation(data.get("relation"))
        return data

    @classmethod
    def from_dict(cls, item: Dict[str, Any]) -> "GraphEdge":
        return cls(
            source=str(item.get("source", "")).strip(),
            target=str(item.get("target", "")).strip(),
            relation=normalize_edge_relation(item.get("relation", EDGE_RELATION_DEFAULT)),
            layer=str(item.get("layer", DEFAULT_GRAPH_LAYER)).strip() or DEFAULT_GRAPH_LAYER,
            note=str(item.get("note", "")).strip(),
        )


class RoadmapModel:
    def __init__(self) -> None:
        self.schema_version = SCHEMA_VERSION
        self.meta: Dict[str, Any] = {}
        self.status_vocab: Dict[str, str] = {}
        self.validation_state_vocab: Dict[str, str] = {}
        self.claim_role_vocab: Dict[str, str] = {}
        self.claim_state_vocab: Dict[str, str] = {}
        self.maturity_vocab: Dict[str, str] = {}
        self.edge_relation_vocab: Dict[str, str] = {}
        self.strategic_answers: Dict[str, Any] = {}
        self.non_negotiables: List[str] = []
        self.falsification_conditions: List[str] = []
        self.claim_ladder: List[ClaimLevel] = []
        self.governance_gates: List[GovernanceGate] = []
        self.critical_path_groups: List[Dict[str, Any]] = []
        self.phases: List[Phase] = []
        self.evidence_entries: List[EvidenceEntry] = []
        self.graph_nodes: List[GraphNode] = []
        self.graph_edges: List[GraphEdge] = []
        self.raw_meta_source: Dict[str, Any] = {}

    @classmethod
    def from_json(cls, raw: Dict[str, Any]) -> "RoadmapModel":
        model = cls()
        schema_version = int(raw.get("schema_version", 1)) if str(raw.get("schema_version", 1)).isdigit() else SCHEMA_VERSION
        model.schema_version = max(schema_version, SCHEMA_VERSION)
        model.meta = raw.get("meta", {}) or {}
        model.status_vocab = raw.get("status_vocab", {}) or {}
        model.validation_state_vocab = raw.get("validation_state_vocab", {}) or {}
        model.claim_role_vocab = raw.get("claim_role_vocab", {}) or {}
        model.claim_state_vocab = raw.get("claim_state_vocab", {}) or {}
        model.maturity_vocab = raw.get("maturity_vocab", {}) or {}
        model.edge_relation_vocab = raw.get("edge_relation_vocab", {}) or {}
        model.strategic_answers = raw.get("strategic_answers", {}) or {}
        model.non_negotiables = listify(raw.get("non_negotiables", []))
        model.falsification_conditions = listify(raw.get("falsification_conditions", []))
        model.claim_ladder = [ClaimLevel.from_dict(x) for x in raw.get("claim_ladder", []) or []]
        model.governance_gates = [GovernanceGate.from_dict(x) for x in raw.get("governance_gates", []) or []]
        model.critical_path_groups = raw.get("critical_path_groups", []) or []
        phases_raw = raw.get("phases", []) or []
        if schema_version >= 2 and phases_raw and "track" in phases_raw[0]:
            model.phases = [Phase.from_dict(item) for item in phases_raw]
        else:
            model.meta = {**model.meta, "migrated_from_legacy": True}
            model.phases = [Phase.from_legacy(item) for item in phases_raw]
        model.evidence_entries = [EvidenceEntry.from_dict(x) for x in raw.get("evidence_entries", []) or []]
        graph_raw = raw.get("graph", {}) or {}
        model.graph_nodes = [GraphNode.from_dict(x) for x in graph_raw.get("nodes", []) or []]
        model.graph_edges = [GraphEdge.from_dict(x) for x in graph_raw.get("edges", []) or []]
        model.ensure_graph_consistency()
        model.conservative_relation_migration()
        model._sync_evidence_phase_links()
        return model

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "meta": self.meta,
            "status_vocab": self.status_vocab or {"closed": "historically implemented and accepted as a build artifact", "current": "current highest-priority build or governance focus", "next": "next immediate focus after current", "later": "planned later or intentionally deferred", "proposed": "newly proposed, not yet accepted"},
            "validation_state_vocab": self.validation_state_vocab or {key: value for key, value in VALIDATION_LABELS.items()},
            "claim_role_vocab": self.claim_role_vocab or {key: value for key, value in CLAIM_ROLE_LABELS.items()},
            "claim_state_vocab": self.claim_state_vocab or {key: value for key, value in CLAIM_STATE_LABELS.items()},
            "maturity_vocab": self.maturity_vocab or {key: value for key, value in MATURITY_LABELS.items()},
            "edge_relation_vocab": self.edge_relation_vocab or {key: value for key, value in EDGE_RELATION_LABELS.items()},
            "strategic_answers": self.strategic_answers,
            "non_negotiables": self.non_negotiables,
            "falsification_conditions": self.falsification_conditions,
            "claim_ladder": [{"level": item.level, "name": item.name, "allowed_claim": item.allowed_claim, "requires": item.requires, "forbidden_shortcuts": item.forbidden_shortcuts} for item in self.claim_ladder],
            "governance_gates": [gate.to_dict() for gate in self.governance_gates],
            "critical_path_groups": self.critical_path_groups,
            "phases": [phase.to_dict() for phase in self.phases],
            "evidence_entries": [entry.to_dict() for entry in self.evidence_entries],
            "graph": {"nodes": [node.to_dict() for node in self.graph_nodes], "edges": [edge.to_dict() for edge in self.graph_edges]},
        }

    def to_json_text(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def save(self, path: Path) -> None:
        path.write_text(self.to_json_text(), encoding="utf-8")

    def status_counts(self) -> Dict[str, int]:
        counts = {key: 0 for key in STATUS_LABELS}
        for phase in self.phases:
            counts[phase.status] = counts.get(phase.status, 0) + 1
        for gate in self.governance_gates:
            counts[gate.status] = counts.get(gate.status, 0) + 1
        return counts

    def archive_metrics(self) -> Dict[str, int]:
        return {
            "phases": len(self.phases),
            "gates": len(self.governance_gates),
            "evidence": len(self.evidence_entries),
            "ready_evidence": sum(1 for entry in self.evidence_entries if entry.ready_for_use),
            "nodes": len(self.graph_nodes),
            "edges": len(self.graph_edges),
        }

    def item_status(self, code: str) -> Optional[str]:
        code = normalize_code(code)
        for phase in self.phases:
            if normalize_code(phase.code) == code:
                return phase.status
        for gate in self.governance_gates:
            if normalize_code(gate.code) == code:
                return gate.status
        return None

    def item_title(self, code: str) -> str:
        code = normalize_code(code)
        for phase in self.phases:
            if normalize_code(phase.code) == code:
                return phase.title
        for gate in self.governance_gates:
            if normalize_code(gate.code) == code:
                return gate.title
        return code

    def get_phase(self, code: str) -> Optional[Phase]:
        target = normalize_code(code)
        for phase in self.phases:
            if normalize_code(phase.code) == target:
                return phase
        return None

    def get_phase_index(self, code: str) -> Optional[int]:
        target = normalize_code(code)
        for idx, phase in enumerate(self.phases):
            if normalize_code(phase.code) == target:
                return idx
        return None

    def phase_to_json_text(self, code: str) -> str:
        phase = self.get_phase(code)
        if not phase:
            raise KeyError(f"Фаза не найдена: {code}")
        return json.dumps(phase.to_dict(), ensure_ascii=False, indent=2)

    def phase_to_todo_text(self, code: str) -> str:
        phase = self.get_phase(code)
        if not phase:
            raise KeyError(f"Фаза не найдена: {code}")
        return json.dumps(phase.to_todo_dict(), ensure_ascii=False, indent=2)

    def replace_phase_from_dict(self, code: str, payload: Dict[str, Any]) -> Phase:
        idx = self.get_phase_index(code)
        if idx is None:
            raise KeyError(f"Фаза не найдена: {code}")
        current_phase = self.phases[idx]
        merged_payload = deep_merge_dict(current_phase.to_dict(), payload or {})
        merged_payload["code"] = current_phase.code
        if not str(merged_payload.get("title", "")).strip():
            merged_payload["title"] = current_phase.title
        updated_phase = Phase.from_dict(merged_payload)
        self.phases[idx] = updated_phase
        self.rebuild_phase_bindings()
        self._sync_evidence_phase_links()
        return updated_phase

    def rebuild_phase_bindings(self) -> None:
        valid_phase_node_ids = {f"phase::{normalize_code(phase.code)}" for phase in self.phases}
        self.graph_nodes = [node for node in self.graph_nodes if not (node.node_id.startswith("phase::") and node.node_id not in valid_phase_node_ids)]
        self.graph_edges = [
            edge for edge in self.graph_edges
            if not (
                edge.source.startswith("phase::") and edge.target.startswith("phase::") and
                (
                    (edge.relation == EDGE_RELATION_DEFAULT and edge.layer == "workflow")
                    or (edge.relation == "invalidates" and edge.layer == "validation")
                )
            )
        ]
        existing_nodes = {node.node_id: node for node in self.graph_nodes}
        x_spacing = 320.0
        y_spacing = 180.0
        phase_depths = self._phase_depth_map()
        row_counts: Dict[int, int] = {}
        for phase in self.phases:
            phase_node_id = f"phase::{normalize_code(phase.code)}"
            node = existing_nodes.get(phase_node_id)
            if node is None:
                depth = phase_depths.get(normalize_code(phase.code), 0)
                row = row_counts.get(depth, 0)
                row_counts[depth] = row + 1
                node = GraphNode(
                    node_id=phase_node_id,
                    label=f"{phase.code}. {phase.title}",
                    node_type="phase",
                    layer_hint="causal",
                    summary=(phase.spec or {}).get("objective", ""),
                    phase_code=phase.code,
                    claim_state=phase.claim_state,
                    maturity=phase.maturity,
                    x=80.0 + depth * x_spacing,
                    y=80.0 + row * y_spacing,
                    width=280.0,
                    height=108.0,
                    knowledge_card=KnowledgeCard.from_dict(phase.knowledge_card.to_dict()),
                    notes=phase.notes,
                )
                self.graph_nodes.append(node)
                existing_nodes[phase_node_id] = node
            else:
                node.label = f"{phase.code}. {phase.title}"
                node.node_type = "phase"
                node.layer_hint = "causal"
                node.summary = (phase.spec or {}).get("objective", "")
                node.phase_code = phase.code
                node.claim_state = phase.claim_state
                node.maturity = phase.maturity
                node.knowledge_card = KnowledgeCard.from_dict(phase.knowledge_card.to_dict())
                node.notes = phase.notes
            if phase_node_id not in phase.related_node_ids:
                phase.related_node_ids.append(phase_node_id)
        existing_workflow_pairs = {
            (edge.source, edge.target)
            for edge in self.graph_edges
            if edge.layer == "workflow"
        }
        existing_validation_pairs = {
            (edge.source, edge.target)
            for edge in self.graph_edges
            if edge.layer == "validation"
        }
        for phase in self.phases:
            target = f"phase::{normalize_code(phase.code)}"
            for dep in phase.dependency_codes():
                source = f"phase::{dep}"
                edge_pair = (source, target)
                if source != target and edge_pair not in existing_workflow_pairs and self.get_node(source):
                    self.graph_edges.append(
                        GraphEdge(
                            source=source,
                            target=target,
                            relation=EDGE_RELATION_DEFAULT,
                            layer="workflow",
                        )
                    )
                    existing_workflow_pairs.add(edge_pair)
            for blocker in phase.claim_blocked_by:
                source = f"phase::{normalize_code(blocker)}"
                edge_pair = (source, target)
                if source != target and edge_pair not in existing_validation_pairs and self.get_node(source):
                    self.graph_edges.append(
                        GraphEdge(
                            source=source,
                            target=target,
                            relation="invalidates",
                            layer="validation",
                        )
                    )
                    existing_validation_pairs.add(edge_pair)

    def conservative_relation_migration(self) -> int:
        migrated = 0
        for edge in self.graph_edges:
            original = edge.relation
            if edge.relation == "blocks_claim":
                edge.relation = "invalidates"
            elif edge.relation == EDGE_RELATION_DEFAULT:
                inferred = self._infer_relation_from_phase_pair(edge.source, edge.target)
                if inferred is not None:
                    edge.relation = inferred
            else:
                edge.relation = normalize_edge_relation(edge.relation)
            if edge.relation != original:
                migrated += 1
        return migrated

    def _infer_relation_from_phase_pair(self, source_node_id: str, target_node_id: str) -> Optional[str]:
        source_code = parse_phase_node_code(source_node_id)
        target_code = parse_phase_node_code(target_node_id)
        if not source_code or not target_code:
            return None

        if source_code == "C04" and target_code in {
            "C05", "A01", "A03", "N01", "O02", "S01", "S02", "S03", "S04", "S05"
        }:
            return "arbitrates"
        if source_code == "C05" and target_code in {
            "A01", "A02", "A03", "D01", "M01", "M02", "M03", "N01", "N02", "N03",
            "O02", "S01", "S02", "S03", "S04", "S05", "T01", "T02", "T03"
        }:
            return "requests_revalidation"
        if source_code == "R04" and target_code in {"C04", "S01", "S02", "S03", "S04", "S05"}:
            return "overrides_survival"
        if source_code == "R04" and target_code in {"C01", "C02", "C03", "C05"}:
            return "modulates"
        if source_code == "C02" and target_code in {"C03", "C04", "C05"}:
            return "gates"
        if source_code == "D01" and target_code in {"M01", "M02", "M03"}:
            return "observes_only"
        if source_code == "S05" and target_code in {"D01", "M01", "M02", "M03"}:
            return "feedback_learns"
        if source_code in {"S04", "S05"} and target_code == "O01":
            return "body_world_couples"
        return None

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        for node in self.graph_nodes:
            if node.node_id == node_id:
                return node
        return None

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceEntry]:
        for entry in self.evidence_entries:
            if entry.evidence_id == evidence_id:
                return entry
        return None

    def get_evidence_index(self, evidence_id: str) -> Optional[int]:
        for idx, entry in enumerate(self.evidence_entries):
            if entry.evidence_id == evidence_id:
                return idx
        return None

    def replace_evidence_from_dict(self, evidence_id: str, payload: Dict[str, Any]) -> EvidenceEntry:
        idx = self.get_evidence_index(evidence_id)
        if idx is None:
            raise KeyError(f"Evidence не найден: {evidence_id}")

        current = self.evidence_entries[idx]
        merged_payload = deep_merge_dict(current.to_dict(), payload or {})
        new_id = str(merged_payload.get("evidence_id", current.evidence_id)).strip() or current.evidence_id
        existing_ids = {entry.evidence_id for i, entry in enumerate(self.evidence_entries) if i != idx}
        if new_id in existing_ids:
            raise ValueError(f"Evidence ID уже существует: {new_id}")
        merged_payload["evidence_id"] = new_id

        updated = EvidenceEntry.from_dict(merged_payload)
        old_id = current.evidence_id
        self.evidence_entries[idx] = updated

        if old_id != updated.evidence_id:
            for phase in self.phases:
                phase.knowledge_card.evidence_ids = [updated.evidence_id if eid == old_id else eid for eid in phase.knowledge_card.evidence_ids]
            for node in self.graph_nodes:
                node.knowledge_card.evidence_ids = [updated.evidence_id if eid == old_id else eid for eid in node.knowledge_card.evidence_ids]

        self._sync_evidence_phase_links()
        return updated

    def attached_phase_for_evidence(self, entry: EvidenceEntry) -> Optional[Phase]:
        for ref in entry.phase_refs:
            phase = self.get_phase(ref.get("code", ""))
            if phase:
                return phase
        for value in entry.supports + entry.challenges:
            if value.startswith("phase::"):
                phase = self.get_phase(value.split("::", 1)[1])
                if phase:
                    return phase
        return None

    def attached_phase_context_text(self, entry: EvidenceEntry) -> str:
        phase = self.attached_phase_for_evidence(entry)
        if not phase:
            return ""

        sections: List[str] = [phase.protocol_label]
        rendered = dedupe_text_blocks(phase.rendered_description() or "—")
        if rendered:
            sections.append(f"Directive:\n{rendered}")
        if phase.notes:
            sections.append(f"Field notes:\n{phase.notes.strip()}")
        if phase.knowledge_card.functional_role:
            sections.append(f"Functional role:\n{phase.knowledge_card.functional_role}")
        if phase.knowledge_card.observables:
            sections.append("Observables:\n" + "\n".join(f"- {item}" for item in dedupe_preserve_order(phase.knowledge_card.observables)))
        if phase.knowledge_card.failure_modes:
            sections.append("Failure modes:\n" + "\n".join(f"- {item}" for item in dedupe_preserve_order(phase.knowledge_card.failure_modes)))
        if phase.knowledge_card.forbidden_shortcuts:
            sections.append("Forbidden shortcuts:\n" + "\n".join(f"- {item}" for item in dedupe_preserve_order(phase.knowledge_card.forbidden_shortcuts)))
        return dedupe_text_blocks("\n\n".join(section for section in sections if section.strip())).strip()

    def _phase_graph_snapshot(self, phase: Phase) -> Dict[str, Any]:
        phase_code = normalize_code(phase.code)
        phase_node_id = f"phase::{phase_code}"
        incoming: List[Dict[str, Any]] = []
        outgoing: List[Dict[str, Any]] = []
        phase_neighbors: List[str] = []
        adjacent_nodes: List[Dict[str, Any]] = []

        for edge in self.graph_edges:
            if edge.source != phase_node_id and edge.target != phase_node_id:
                continue
            other_id = edge.target if edge.source == phase_node_id else edge.source
            direction = "outgoing" if edge.source == phase_node_id else "incoming"
            other_node = self.get_node(other_id)
            other_phase_code = normalize_code(other_node.phase_code) if other_node and other_node.phase_code else ""
            if not other_phase_code and other_id.startswith("phase::"):
                other_phase_code = normalize_code(other_id.split("::", 1)[1])

            record = {
                "direction": direction,
                "relation": edge.relation,
                "relation_label": display_from_map(edge.relation, EDGE_RELATION_LABELS),
                "layer": edge.layer,
                "layer_label": display_from_map(edge.layer, GRAPH_LAYER_LABELS),
                "note": edge.note,
                "other_node_id": other_id,
                "other_phase_code": other_phase_code or None,
            }
            if other_node is not None:
                record.update({
                    "other_node_label": other_node.label,
                    "other_node_type": other_node.node_type,
                    "other_node_type_label": display_from_map(other_node.node_type, NODE_TYPE_LABELS),
                    "other_node_summary": other_node.summary,
                })
            elif other_phase_code:
                other_phase = self.get_phase(other_phase_code)
                if other_phase is not None:
                    record.update({
                        "other_node_label": other_phase.title,
                        "other_node_type": "phase",
                        "other_node_type_label": display_from_map("phase", NODE_TYPE_LABELS),
                        "other_node_summary": (other_phase.spec or {}).get("objective", ""),
                    })

            if direction == "incoming":
                incoming.append(record)
            else:
                outgoing.append(record)

            if other_phase_code and other_phase_code != phase_code:
                if other_phase_code not in phase_neighbors:
                    phase_neighbors.append(other_phase_code)
            else:
                adjacent_nodes.append(record)

        related_nodes: List[Dict[str, Any]] = []
        seen_related: set[str] = set()
        for node_id in phase.related_node_ids:
            if node_id == phase_node_id or node_id in seen_related:
                continue
            node = self.get_node(node_id)
            if not node:
                continue
            seen_related.add(node_id)
            related_nodes.append({
                "node_id": node.node_id,
                "label": node.label,
                "node_type": node.node_type,
                "node_type_label": display_from_map(node.node_type, NODE_TYPE_LABELS),
                "layer": node.layer_hint,
                "layer_label": display_from_map(node.layer_hint, GRAPH_LAYER_LABELS),
                "summary": node.summary,
            })

        return {
            "incoming": incoming,
            "outgoing": outgoing,
            "phase_neighbors": phase_neighbors,
            "adjacent_nodes": adjacent_nodes,
            "related_nodes": related_nodes,
        }

    def _phase_neighbor_codes(self, phase: Phase, graph_snapshot: Optional[Dict[str, Any]] = None) -> List[str]:
        phase_code = normalize_code(phase.code)
        snapshot = graph_snapshot or self._phase_graph_snapshot(phase)
        neighbors: List[str] = []

        for code in phase.dependency_codes():
            if code != phase_code and code not in neighbors:
                neighbors.append(code)
        for code in phase.claim_blocked_by:
            if code != phase_code and code not in neighbors:
                neighbors.append(code)
        for code in snapshot.get("phase_neighbors", []):
            if code != phase_code and code not in neighbors:
                neighbors.append(code)

        for other in self.phases:
            other_code = normalize_code(other.code)
            if other_code == phase_code:
                continue
            if phase_code in other.dependency_codes() and other_code not in neighbors:
                neighbors.append(other_code)
            if phase_code in [normalize_code(item) for item in other.claim_blocked_by] and other_code not in neighbors:
                neighbors.append(other_code)

        return neighbors

    def _phase_relation_tags(self, phase: Phase, neighbor_code: str, graph_snapshot: Optional[Dict[str, Any]] = None) -> List[str]:
        phase_code = normalize_code(phase.code)
        neighbor_code = normalize_code(neighbor_code)
        tags: List[str] = []
        snapshot = graph_snapshot or self._phase_graph_snapshot(phase)

        if normalize_code(phase.after) == neighbor_code:
            tags.append("operational_dependency")
        if normalize_code(phase.implemented_after) == neighbor_code:
            tags.append("historical_dependency")
        if neighbor_code in [normalize_code(item) for item in phase.conceptually_after]:
            tags.append("conceptual_dependency")
        if neighbor_code in [normalize_code(item) for item in phase.claim_blocked_by]:
            tags.append("claim_blocker")

        neighbor = self.get_phase(neighbor_code)
        if neighbor is not None:
            if phase_code in neighbor.dependency_codes():
                tags.append("downstream_dependent")
            if phase_code in [normalize_code(item) for item in neighbor.claim_blocked_by]:
                tags.append("blocks_downstream_claim")

        for record in snapshot.get("incoming", []) + snapshot.get("outgoing", []):
            if normalize_code(record.get("other_phase_code") or "") != neighbor_code:
                continue
            direction = record.get("direction", "")
            relation = str(record.get("relation", "")).strip()
            layer = str(record.get("layer", "")).strip()
            marker = f"graph_{direction}:{layer}:{relation}"
            if marker not in tags:
                tags.append(marker)
        return tags

    def _evidence_entries_for_phase(self, phase_code: str) -> List[EvidenceEntry]:
        phase = self.get_phase(phase_code)
        if not phase:
            return []
        target = normalize_code(phase.code)
        target_node = f"phase::{target}"
        matches: List[EvidenceEntry] = []
        for entry in self.evidence_entries:
            attached_codes = {normalize_code(ref.get("code", "")) for ref in entry.phase_refs}
            if target in attached_codes or target_node in entry.supports or target_node in entry.challenges or entry.evidence_id in phase.knowledge_card.evidence_ids:
                matches.append(entry)
        return matches

    def _build_evidence_distillate(self, entry: EvidenceEntry, phase_code: str) -> Dict[str, Any]:
        target = normalize_code(phase_code)
        relation = "supports"
        for ref in entry.phase_refs:
            if normalize_code(ref.get("code", "")) == target:
                relation = str(ref.get("relation", "supports")).strip() or "supports"
                break
        mech = normalize_mechanistic_payload(entry.mechanistic_payload)
        core_mechanism = str(mech.get("core_mechanism", "")).strip()
        supports_claim = str(mech.get("supports_claim", "")).strip()
        challenge_to_claim = str(mech.get("challenge_to_claim", "")).strip()
        phase_relevance = str(mech.get("phase_relevance", "")).strip()
        measurement_or_test = str(mech.get("measurement_or_test", "")).strip()

        obligations: List[str] = []
        if core_mechanism:
            obligations.append(core_mechanism)
        if measurement_or_test:
            obligations.append(f"Validate with: {measurement_or_test}")
        if supports_claim and not challenge_to_claim:
            obligations.append(f"Use only for this claim surface: {supports_claim}")
        if challenge_to_claim:
            obligations.append(f"Treat as challenge pressure: {challenge_to_claim}")

        limitations = dedupe_preserve_order(entry.limitations)
        return {
            "evidence_id": entry.evidence_id,
            "title": entry.title,
            "kind": entry.kind,
            "status": entry.status,
            "status_label": display_from_map(entry.status, EVIDENCE_STATUS_LABELS),
            "evidence_role": entry.evidence_role,
            "evidence_role_label": display_from_map(entry.evidence_role, EVIDENCE_ROLE_LABELS),
            "relation": relation,
            "relation_kind": "challenge" if relation_is_challenging(relation) else "support",
            "citation": entry.citation,
            "url": entry.url,
            "summary": entry.summary,
            "evidence_strength": entry.evidence_strength,
            "declared_ready_for_use": entry.ready_for_use,
            "effective_ready_for_use": entry.effective_ready_for_use,
            "readiness_missing_fields": entry.readiness_missing_fields,
            "mechanism_supported": core_mechanism,
            "phase_relevance": phase_relevance,
            "local_design_obligation": " ".join(part for part in obligations if part).strip(),
            "what_it_does_not_prove": limitations,
            "test_implication": measurement_or_test,
            "open_questions": dedupe_preserve_order(entry.open_questions),
        }

    def build_phase_execution_packet(self, phase_code: str) -> Dict[str, Any]:
        phase = self.get_phase(phase_code)
        if not phase:
            raise KeyError(f"Фаза не найдена: {phase_code}")

        phase_code_norm = normalize_code(phase.code)
        snapshot = self._phase_graph_snapshot(phase)
        neighbor_codes = self._phase_neighbor_codes(phase, snapshot)
        neighbors: List[Dict[str, Any]] = []
        for code in neighbor_codes:
            neighbor = self.get_phase(code)
            if not neighbor:
                continue
            relation_tags = self._phase_relation_tags(phase, code, snapshot)
            shared_risk_surface = dedupe_preserve_order(list(phase.risk_tags) + list(neighbor.risk_tags))[:8]
            neighbors.append({
                "code": neighbor.code,
                "title": neighbor.title,
                "track": neighbor.track,
                "line": neighbor.line,
                "relation_tags": relation_tags,
                "functional_role": neighbor.knowledge_card.functional_role,
                "authority_summary": neighbor.knowledge_card.authority,
                "inputs": neighbor.knowledge_card.inputs,
                "outputs": neighbor.knowledge_card.outputs,
                "excluded_surfaces": listify((neighbor.spec or {}).get("excludes", [])),
                "shared_risk_surface": shared_risk_surface,
                "claim_state": neighbor.claim_state,
                "maturity": neighbor.maturity,
            })

        evidence_entries = self._evidence_entries_for_phase(phase.code)
        evidence_distillates = [self._build_evidence_distillate(entry, phase.code) for entry in evidence_entries]
        supporting_evidence = [item for item in evidence_distillates if item["relation_kind"] == "support"]
        effective_ready_support = [item for item in supporting_evidence if item["effective_ready_for_use"]]

        objective = str((phase.spec or {}).get("objective", "")).strip()
        includes = listify((phase.spec or {}).get("includes", []))
        excludes = listify((phase.spec or {}).get("excludes", []))
        rationale = str((phase.spec or {}).get("rationale", "")).strip()

        phase_data_gaps: List[str] = []
        if not objective:
            phase_data_gaps.append("phase.spec.objective_missing")
        if not includes:
            phase_data_gaps.append("phase.spec.includes_missing")
        if not excludes:
            phase_data_gaps.append("phase.spec.excludes_missing")
        if not phase.knowledge_card.inputs:
            phase_data_gaps.append("knowledge_card.inputs_missing")
        if not phase.knowledge_card.outputs:
            phase_data_gaps.append("knowledge_card.outputs_missing")
        if not phase.knowledge_card.authority.strip():
            phase_data_gaps.append("knowledge_card.authority_missing")
        if not phase.knowledge_card.observables:
            phase_data_gaps.append("knowledge_card.observables_missing")
        if not phase.knowledge_card.failure_modes:
            phase_data_gaps.append("knowledge_card.failure_modes_missing")
        if not phase.knowledge_card.falsifiers:
            phase_data_gaps.append("knowledge_card.falsifiers_missing")
        if not phase.knowledge_card.tests:
            phase_data_gaps.append("knowledge_card.tests_missing")
        if not phase.knowledge_card.forbidden_shortcuts:
            phase_data_gaps.append("knowledge_card.forbidden_shortcuts_missing")
        if not neighbors and phase.track != "build":
            phase_data_gaps.append("critical_neighbor_seams_missing")

        evidence_gaps: List[str] = []
        if not evidence_distillates:
            evidence_gaps.append("no_evidence_attached")
        if evidence_distillates and not supporting_evidence:
            evidence_gaps.append("no_supporting_evidence_attached")
        if supporting_evidence and not effective_ready_support:
            evidence_gaps.append("no_effective_ready_supporting_evidence")

        tracker_schema_gaps = [
            "repo_file_anchors_not_encoded_in_tracker_data",
            "field_level_authority_matrix_not_encoded_in_tracker_data",
            "typed_transition_route_not_encoded_in_tracker_data",
            "allowed_change_budget_not_encoded_in_tracker_data",
        ]

        packet = {
            "packet_version": "phase_execution_packet_v1",
            "phase": {
                "code": phase.code,
                "title": phase.title,
                "track": phase.track,
                "line": phase.line,
                "status": phase.status,
                "validation_state": phase.validation_state,
                "claim_role": phase.claim_role,
                "claim_state": phase.claim_state,
                "maturity": phase.maturity,
                "priority_bucket": phase.priority_bucket,
            },
            "assembly_status": {
                "ready_for_design_reasoning": not phase_data_gaps,
                "ready_for_repo_codegen": not phase_data_gaps and not tracker_schema_gaps,
                "phase_data_gaps": phase_data_gaps,
                "evidence_gaps": evidence_gaps,
                "tracker_schema_gaps": tracker_schema_gaps,
            },
            "phase_core": {
                "objective": objective,
                "rationale": rationale,
                "includes": includes,
                "excludes": excludes,
                "notes": phase.notes,
                "functional_role": phase.knowledge_card.functional_role,
                "why_exists": phase.knowledge_card.why_exists,
                "risk_tags": dedupe_preserve_order(phase.risk_tags),
            },
            "contour_placement": {
                "operational_dependency": phase.after,
                "historical_dependency": phase.implemented_after,
                "conceptual_dependencies": list(phase.conceptually_after),
                "claim_blocked_by": list(phase.claim_blocked_by),
                "downstream_dependents": [other.code for other in self.phases if phase_code_norm in other.dependency_codes()],
                "blocks_downstream_claims_for": [other.code for other in self.phases if phase_code_norm in [normalize_code(item) for item in other.claim_blocked_by]],
                "graph_incoming": snapshot["incoming"],
                "graph_outgoing": snapshot["outgoing"],
                "related_nodes": snapshot["related_nodes"],
                "adjacent_non_phase_nodes": snapshot["adjacent_nodes"],
            },
            "neighbor_seams": neighbors,
            "transition_contract": {
                "phase_inputs": list(phase.knowledge_card.inputs),
                "phase_outputs": list(phase.knowledge_card.outputs),
                "authority": phase.knowledge_card.authority,
                "uncertainty_policy": phase.knowledge_card.uncertainty_policy,
                "required_observables": list(phase.knowledge_card.observables),
                "required_failure_modes": list(phase.knowledge_card.failure_modes),
                "must_hold_after_phase": list(phase.knowledge_card.observables),
                "must_fail_honestly_when": list(phase.knowledge_card.failure_modes),
                "must_not_claim": excludes,
            },
            "authority_pack": {
                "phase_authority": phase.knowledge_card.authority,
                "forbidden_shortcuts": list(phase.knowledge_card.forbidden_shortcuts),
                "must_not_infer": excludes,
                "claim_boundaries": {
                    "allowed_claim_state": phase.claim_state,
                    "claim_role": phase.claim_role,
                    "blocked_by": list(phase.claim_blocked_by),
                },
            },
            "evidence_distillates": evidence_distillates,
            "validation_pack": {
                "validation_state": phase.validation_state,
                "claim_state": phase.claim_state,
                "maturity": phase.maturity,
                "tests": list(phase.knowledge_card.tests),
                "falsifiers": list(phase.knowledge_card.falsifiers),
                "observables": list(phase.knowledge_card.observables),
                "supporting_evidence_count": len(supporting_evidence),
                "effective_ready_supporting_evidence_count": len(effective_ready_support),
            },
            "repo_integration_pack": {
                "available_from_tracker": [],
                "missing_from_tracker_schema": tracker_schema_gaps,
            },
            "missing_context_blockers": {
                "phase_data_gaps": phase_data_gaps,
                "evidence_gaps": evidence_gaps,
                "tracker_schema_gaps": tracker_schema_gaps,
            },
        }
        return packet

    def phase_execution_packet_text(self, phase_code: str) -> str:
        return json.dumps(self.build_phase_execution_packet(phase_code), ensure_ascii=False, indent=2)

    def phase_execution_packet_summary_text(self, phase_code: str) -> str:
        packet = self.build_phase_execution_packet(phase_code)
        status = packet.get("assembly_status", {})
        phase = packet.get("phase", {})
        lines = [f"{phase.get('code', '')} // {phase.get('title', '')}", ""]
        lines.append(f"Design reasoning ready: {'YES' if status.get('ready_for_design_reasoning') else 'NO'}")
        lines.append(f"Repo codegen ready: {'YES' if status.get('ready_for_repo_codegen') else 'NO'}")
        lines.append("")
        for label, items in [
            ("Phase data gaps", status.get("phase_data_gaps", [])),
            ("Evidence gaps", status.get("evidence_gaps", [])),
            ("Tracker schema gaps", status.get("tracker_schema_gaps", [])),
        ]:
            lines.append(f"{label}:")
            if items:
                lines.extend(f"- {item}" for item in items)
            else:
                lines.append("- none")
            lines.append("")

        neighbors = packet.get("neighbor_seams", [])
        lines.append(f"Critical neighbors: {len(neighbors)}")
        for item in neighbors[:8]:
            tags = ", ".join(item.get("relation_tags", [])) or "—"
            lines.append(f"- {item.get('code', '')}: {tags}")
        lines.append("")

        evidence_items = packet.get("evidence_distillates", [])
        lines.append(f"Evidence records: {len(evidence_items)}")
        for item in evidence_items[:8]:
            lines.append(
                f"- {item.get('evidence_id', '')}: relation={item.get('relation', '')}, strength={item.get('evidence_strength', '')}, effective_ready={'yes' if item.get('effective_ready_for_use') else 'no'}"
            )
        return "\n".join(lines).strip()

    def ensure_graph_consistency(self) -> None:
        self.rebuild_phase_bindings()

    def _phase_depth_map(self) -> Dict[str, int]:
        depth: Dict[str, int] = {}
        visiting: set[str] = set()
        phase_index = {normalize_code(phase.code): phase for phase in self.phases}
        def compute(code: str) -> int:
            if code in depth:
                return depth[code]
            if code in visiting:
                return 0
            visiting.add(code)
            phase = phase_index.get(code)
            if not phase:
                visiting.discard(code)
                return 0
            max_parent = 0
            for dep in phase.dependency_codes():
                if dep in phase_index:
                    max_parent = max(max_parent, compute(dep) + 1)
            visiting.discard(code)
            depth[code] = max_parent
            return max_parent
        for code in phase_index:
            compute(code)
        return depth

    def graph_nodes_for_layer(self, layer: str) -> List[GraphNode]:
        layer = layer.strip()
        if layer == "all":
            return list(self.graph_nodes)
        relevant = {edge.source for edge in self.graph_edges if edge.layer == layer}
        relevant.update(edge.target for edge in self.graph_edges if edge.layer == layer)
        for node in self.graph_nodes:
            if node.layer_hint == layer or node.node_type == "phase":
                relevant.add(node.node_id)
        return [node for node in self.graph_nodes if node.node_id in relevant]

    def graph_edges_for_layer(self, layer: str) -> List[GraphEdge]:
        if layer == "all":
            return list(self.graph_edges)
        return [edge for edge in self.graph_edges if edge.layer == layer]


    def apply_graph_layout(
        self,
        layer: str = "all",
        *,
        x_spacing: float = 380.0,
        y_spacing: float = 170.0,
        start_x: float = 120.0,
        start_y: float = 100.0,
    ) -> None:
        nodes = self.graph_nodes_for_layer(layer)
        if not nodes:
            return

        node_ids = {node.node_id for node in nodes}
        edges = [edge for edge in self.graph_edges_for_layer(layer) if edge.source in node_ids and edge.target in node_ids and edge.source != edge.target]
        layers = self._graph_layout_layers(nodes, edges)

        for depth, layer_nodes in enumerate(layers):
            for row, node_id in enumerate(layer_nodes):
                node = self.get_node(node_id)
                if not node:
                    continue
                node.x = start_x + depth * x_spacing
                node.y = start_y + row * y_spacing

    def _graph_layout_layers(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> List[List[str]]:
        if not nodes:
            return []

        node_lookup = {node.node_id: node for node in nodes}
        node_ids = [node.node_id for node in nodes]
        children: Dict[str, List[str]] = defaultdict(list)
        parents: Dict[str, List[str]] = defaultdict(list)
        indegree: Dict[str, int] = {node_id: 0 for node_id in node_ids}

        for edge in edges:
            if edge.source not in node_lookup or edge.target not in node_lookup:
                continue
            children[edge.source].append(edge.target)
            parents[edge.target].append(edge.source)
            indegree[edge.target] += 1

        ready = [node_id for node_id, degree in indegree.items() if degree == 0]
        ready.sort(key=lambda node_id: (node_lookup[node_id].x, node_lookup[node_id].y, node_lookup[node_id].label.lower()))

        queue: deque[str] = deque(ready)
        order: List[str] = []
        indegree_work = dict(indegree)
        while queue:
            node_id = queue.popleft()
            order.append(node_id)
            new_ready: List[str] = []
            for child in children.get(node_id, []):
                indegree_work[child] -= 1
                if indegree_work[child] == 0:
                    new_ready.append(child)
            new_ready.sort(key=lambda item: (node_lookup[item].x, node_lookup[item].y, node_lookup[item].label.lower()))
            for item in new_ready:
                queue.append(item)

        seen = set(order)
        if len(order) != len(node_ids):
            remaining = [node_id for node_id in node_ids if node_id not in seen]
            remaining.sort(key=lambda node_id: (node_lookup[node_id].x, node_lookup[node_id].y, node_lookup[node_id].label.lower()))
            order.extend(remaining)

        depth: Dict[str, int] = {node_id: 0 for node_id in order}
        for node_id in order:
            for child in children.get(node_id, []):
                depth[child] = max(depth.get(child, 0), depth[node_id] + 1)

        if not depth:
            return [node_ids]

        max_depth = max(depth.values())
        layers: List[List[str]] = [[] for _ in range(max_depth + 1)]
        for node_id in order:
            layers[depth.get(node_id, 0)].append(node_id)

        for _ in range(6):
            for layer_index in range(1, len(layers)):
                previous_positions = {node_id: idx for idx, node_id in enumerate(layers[layer_index - 1])}
                baseline = {node_id: idx for idx, node_id in enumerate(layers[layer_index])}

                def sort_key(node_id: str) -> tuple[float, int, str]:
                    refs = [previous_positions[parent] for parent in parents.get(node_id, []) if parent in previous_positions]
                    if refs:
                        return (sum(refs) / len(refs), baseline[node_id], node_lookup[node_id].label.lower())
                    return (1_000_000.0, baseline[node_id], node_lookup[node_id].label.lower())

                layers[layer_index].sort(key=sort_key)

            for layer_index in range(len(layers) - 2, -1, -1):
                next_positions = {node_id: idx for idx, node_id in enumerate(layers[layer_index + 1])}
                baseline = {node_id: idx for idx, node_id in enumerate(layers[layer_index])}

                def sort_key(node_id: str) -> tuple[float, int, str]:
                    refs = [next_positions[child] for child in children.get(node_id, []) if child in next_positions]
                    if refs:
                        return (sum(refs) / len(refs), baseline[node_id], node_lookup[node_id].label.lower())
                    return (1_000_000.0, baseline[node_id], node_lookup[node_id].label.lower())

                layers[layer_index].sort(key=sort_key)

        return [layer for layer in layers if layer]

    def _sync_evidence_phase_links(self) -> None:
        by_id = {entry.evidence_id: entry for entry in self.evidence_entries}
        phase_by_code = {normalize_code(phase.code): phase for phase in self.phases}

        for entry in self.evidence_entries:
            entry.phase_refs = normalize_phase_refs(entry.phase_refs)
            entry.supports = dedupe_preserve_order(entry.supports)
            entry.challenges = dedupe_preserve_order(entry.challenges)

        for phase in self.phases:
            phase_code = normalize_code(phase.code)
            phase_node = f"phase::{phase_code}"
            cleaned_ids: List[str] = []
            for evidence_id in phase.knowledge_card.evidence_ids:
                if evidence_id in by_id and evidence_id not in cleaned_ids:
                    cleaned_ids.append(evidence_id)
            phase.knowledge_card.evidence_ids = cleaned_ids

            for evidence_id in phase.knowledge_card.evidence_ids:
                entry = by_id.get(evidence_id)
                if not entry:
                    continue
                if phase_code not in {normalize_code(ref.get("code", "")) for ref in entry.phase_refs}:
                    entry.phase_refs.append({"code": phase.code, "title": phase.title, "relation": "supports"})
                if phase_node not in entry.supports and phase_node not in entry.challenges:
                    entry.supports.append(phase_node)

        for entry in self.evidence_entries:
            entry.phase_refs = normalize_phase_refs(entry.phase_refs)
            attached_codes = {normalize_code(ref.get("code", "")) for ref in entry.phase_refs}
            for ref in entry.phase_refs:
                code = normalize_code(ref.get("code", ""))
                phase = phase_by_code.get(code)
                if phase and not ref.get("title"):
                    ref["title"] = phase.title
                phase_node = f"phase::{code}"
                if relation_is_challenging(ref.get("relation", "supports")):
                    if phase_node not in entry.challenges:
                        entry.challenges.append(phase_node)
                    entry.supports = [item for item in entry.supports if item != phase_node]
                else:
                    if phase_node not in entry.supports:
                        entry.supports.append(phase_node)
                    entry.challenges = [item for item in entry.challenges if item != phase_node]

            entry.supports = dedupe_preserve_order(entry.supports)
            entry.challenges = dedupe_preserve_order(entry.challenges)

            for code in attached_codes:
                phase = phase_by_code.get(code)
                if not phase:
                    continue
                if entry.evidence_id not in phase.knowledge_card.evidence_ids:
                    phase.knowledge_card.evidence_ids.append(entry.evidence_id)

    def create_blank_evidence(self, phase: Optional[Phase] = None) -> EvidenceEntry:
        base = f"evidence::new::{len(self.evidence_entries) + 1}"
        candidate = base
        counter = 2
        existing = {entry.evidence_id for entry in self.evidence_entries}
        while candidate in existing:
            candidate = f"{base}_{counter}"
            counter += 1
        title = f"Evidence for {phase.code}" if phase else "New evidence"
        entry = EvidenceEntry(
            evidence_id=candidate,
            title=title,
            kind="design_note",
            status=DEFAULT_EVIDENCE_STATUS,
            evidence_role=DEFAULT_EVIDENCE_ROLE,
            mechanistic_payload=normalize_mechanistic_payload({
                "source_type": "",
                "system_or_context": "",
                "core_mechanism": "",
                "observed_effect": "",
                "phase_relevance": "",
                "supports_claim": "",
                "challenge_to_claim": "",
                "boundary_conditions": [],
                "failure_signal": [],
                "measurement_or_test": "",
                "notes": "",
            }),
        )
        if phase:
            entry.phase_refs.append({"code": phase.code, "title": phase.title, "relation": "supports"})
            phase_node = f"phase::{normalize_code(phase.code)}"
            entry.supports.append(phase_node)
        return entry

    def export_phase_evidence_json(self, phase_code: str) -> List[Dict[str, Any]]:
        phase = self.get_phase(phase_code)
        if not phase:
            return []
        target = normalize_code(phase.code)
        target_node = f"phase::{target}"
        collected: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for entry in self.evidence_entries:
            attached_codes = {normalize_code(ref.get("code", "")) for ref in entry.phase_refs}
            if target in attached_codes or target_node in entry.supports or target_node in entry.challenges or entry.evidence_id in phase.knowledge_card.evidence_ids:
                if entry.evidence_id not in seen:
                    seen.add(entry.evidence_id)
                    collected.append(entry.to_export_dict(self))
        return collected

    def export_phase_evidence_pack(self, phase_code: str) -> List[Dict[str, Any]]:
        phase = self.get_phase(phase_code)
        if not phase:
            return []
        output: List[Dict[str, Any]] = []
        for item in self.export_phase_evidence_json(phase_code):
            entry = EvidenceEntry.from_dict(item)
            relation = "supports"
            phase_refs = item.get("phase_refs", []) or []
            if phase_refs:
                relation = phase_refs[0].get("relation", "supports")
            output.append({
                "phase": {"code": phase.code, "title": phase.title},
                "phase_context": self.attached_phase_context_text(entry),
                "evidence_id": item.get("evidence_id", ""),
                "title": item.get("title", ""),
                "kind": item.get("kind", ""),
                "status": item.get("status", ""),
                "role": item.get("evidence_role", ""),
                "relation": relation,
                "citation": item.get("citation", ""),
                "url": item.get("url", ""),
                "summary": item.get("summary", ""),
                "evidence_strength": item.get("evidence_strength", "weak"),
                "ready_for_use": item.get("ready_for_use", False),
                "effective_ready_for_use": entry.effective_ready_for_use,
                "mechanistic_payload": item.get("mechanistic_payload", {}) or {},
                "limitations": item.get("limitations", []),
                "open_questions": item.get("open_questions", []),
                "supports": item.get("supports", []),
                "challenges": item.get("challenges", []),
                "missing": entry.readiness_missing_fields,
            })
        return output


class LegacyRoadmapParser:
    def parse_docx(self, path: Path) -> List[Phase]:
        if Document is None:
            raise RuntimeError("python-docx не установлен. Установи: pip install python-docx")
        doc = Document(path)
        paragraphs = [p.text.strip() for p in doc.paragraphs]
        return self._parse_lines([p for p in paragraphs if p])

    def _parse_lines(self, lines: List[str]) -> List[Phase]:
        phases: List[Phase] = []
        current_phase: Optional[Phase] = None
        current_track = "frontier"
        buffer: List[str] = []

        def flush_current() -> None:
            nonlocal current_phase, buffer
            if current_phase is None:
                buffer = []
                return
            description = "\n".join(line for line in buffer if line.strip()).strip()
            after_match = AFTER_CODE_RE.search(description)
            current_phase.after = after_match.group(1).strip().upper() if after_match else None
            current_phase.implemented_after = current_phase.after
            current_phase.spec = {"objective": description, "includes": [], "rationale": "", "excludes": []}
            current_phase.knowledge_card = KnowledgeCard(functional_role=description)
            if current_phase.status == "closed":
                current_phase.validation_state = "implemented_baseline"
                current_phase.priority_bucket = "historical_foundation"
                current_phase.claim_state = "implemented"
            phases.append(current_phase)
            current_phase = None
            buffer = []

        for line in lines:
            if line.startswith("I. Build Track"):
                current_track = "build"
                continue
            if line.startswith("II. Refinement Track"):
                current_track = "refinement"
                continue
            if line.startswith("III. "):
                current_track = "frontier"
                continue
            match = PHASE_RE.match(line)
            if match:
                flush_current()
                code, title = match.groups()
                current_phase = Phase(
                    code=code,
                    title=title,
                    track=current_track,
                    line=infer_line_from_code(code),
                    status=DEFAULT_STATUS,
                    status_source="derived",
                    spec={},
                    validation_state="planned",
                    claim_role="core_foundation_or_support",
                    priority_bucket="phase_2_long_run_validation_backbone",
                )
                continue
            if current_phase is not None:
                buffer.append(line)
                upper_line = line.upper()
                if "[ТЕКУЩАЯ]" in upper_line:
                    current_phase.status = "current"
                elif "[СЛЕДУЮЩИЙ ШАГ]" in upper_line:
                    current_phase.status = "next"
                elif "[ЗАКРЫТО]" in upper_line:
                    current_phase.status = "closed"
                elif "[ПРЕДЛОЖЕНА]" in upper_line:
                    current_phase.status = "proposed"
                elif "[ДАЛЬШЕ ПО ОЧЕРЕДИ]" in upper_line:
                    current_phase.status = "later"
                elif "[НУЖЕН РЕФАЙН]" in upper_line or "[REFINEMENT]" in upper_line:
                    current_phase.track = "refinement"
        flush_current()
        return phases
