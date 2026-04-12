from __future__ import annotations

import importlib.util
import random
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from reviewer.models import GeneratedCase
from substrate.runtime_tap_trace import (
    deactivate_tick_trace,
    derive_tick_id,
    finish_tick_trace,
    start_tick_trace,
)
from substrate.runtime_topology import RuntimeDispatchRequest, RuntimeRouteClass, dispatch_runtime_tick
from substrate.runtime_topology.models import (
    RuntimeEpistemicCaseInput,
    RuntimeRegulationSharedDomainInput,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput


def _load_battery_module():
    try:
        import tools.edgy_behavioral_case_battery as module  # type: ignore

        return module
    except ModuleNotFoundError:
        root = Path(__file__).resolve().parents[2]
        module_path = root / "tools" / "edgy_behavioral_case_battery.py"
        spec = importlib.util.spec_from_file_location("_edgy_battery_module", module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("unable to load edgy_behavioral_case_battery module")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)  # type: ignore[arg-type]
        return module


def _clamp(value: float, *, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


class SeededCaseGenerator:
    def __init__(self) -> None:
        module = _load_battery_module()
        self._case_battery = tuple(module.CASE_BATTERY)

    def available_themes(self) -> set[str]:
        return {str(case.scenario_family) for case in self._case_battery}

    def _pick_template(self, *, seed: int, theme: str | None) -> Any:
        rng = random.Random(seed)
        templates = [
            case
            for case in self._case_battery
            if theme is None or str(case.scenario_family) == theme
        ]
        if not templates:
            raise ValueError(f"no templates available for theme={theme!r}")
        return templates[rng.randrange(len(templates))]

    def _materialize_template(self, template: Any, *, seed: int) -> Any:
        rng = random.Random(seed)
        energy = _clamp(float(template.energy) + rng.uniform(-10.0, 10.0))
        cognitive = _clamp(float(template.cognitive) + rng.uniform(-10.0, 10.0))
        safety = _clamp(float(template.safety) + rng.uniform(-10.0, 10.0))
        unresolved_preference = bool(template.unresolved_preference)
        if rng.random() >= 0.7:
            unresolved_preference = not unresolved_preference
        return replace(
            template,
            energy=round(energy, 4),
            cognitive=round(cognitive, 4),
            safety=round(safety, 4),
            unresolved_preference=unresolved_preference,
        )

    def generate_case(
        self,
        *,
        seed: int,
        theme: str | None,
        traces_output_dir: str | Path,
    ) -> GeneratedCase:
        template = self._pick_template(seed=seed, theme=theme)
        materialized = self._materialize_template(template, seed=seed)
        case_id = f"{materialized.case_id}-seed-{seed}"
        tick_id = derive_tick_id(case_id, prior_tick_index=None)
        traces_dir = Path(traces_output_dir).expanduser().resolve()
        traces_dir.mkdir(parents=True, exist_ok=True)
        token = start_tick_trace(tick_id=tick_id, output_root=traces_dir)
        try:
            dispatch_runtime_tick(
                RuntimeDispatchRequest(
                    tick_input=SubjectTickInput(
                        case_id=case_id,
                        energy=float(materialized.energy),
                        cognitive=float(materialized.cognitive),
                        safety=float(materialized.safety),
                        unresolved_preference=bool(materialized.unresolved_preference),
                    ),
                    context=SubjectTickContext(**dict(materialized.context_overrides)),
                    epistemic_case_input=(
                        RuntimeEpistemicCaseInput(**dict(materialized.epistemic_overrides))
                        if materialized.epistemic_overrides
                        else None
                    ),
                    regulation_shared_domain_input=(
                        RuntimeRegulationSharedDomainInput(**dict(materialized.regulation_overrides))
                        if materialized.regulation_overrides
                        else None
                    ),
                    route_class=RuntimeRouteClass(str(materialized.route_class)),
                )
            )
        finally:
            deactivate_tick_trace(token)
        trace_meta = finish_tick_trace(tick_id=tick_id)

        return GeneratedCase(
            case_id=case_id,
            seed=seed,
            theme=str(materialized.scenario_family),
            scenario_family=str(materialized.scenario_family),
            scenario_intent=str(materialized.scenario_intent),
            paired_with=(
                None if materialized.paired_with is None else str(materialized.paired_with)
            ),
            key_tension_axis=tuple(str(item) for item in materialized.key_tension_axis),
            what_to_inspect_in_trace=tuple(
                str(item) for item in materialized.what_to_inspect_in_trace
            ),
            why_this_case_exists=str(materialized.why_this_case_exists),
            trace_path=str(trace_meta["trace_path"]),
            generation_params={
                "seed": seed,
                "template_case_id": str(materialized.case_id),
                "theme_requested": theme,
                "energy": float(materialized.energy),
                "cognitive": float(materialized.cognitive),
                "safety": float(materialized.safety),
                "unresolved_preference": bool(materialized.unresolved_preference),
                "route_class": str(materialized.route_class),
            },
        )
