from __future__ import annotations

from dataclasses import asdict

from .models import ContactSpecValidationResult


def umwelts_contact_spec_snapshot(result: ContactSpecValidationResult) -> dict[str, object]:
    payload: dict[str, object] = {
        "spec_id": result.spec_id,
        "status": result.status.value,
        "blocked_reasons": result.blocked_reasons,
        "warnings": result.warnings,
        "counters": asdict(result.counters),
        "authority_flags": asdict(result.authority_flags),
        "has_normalized_ir": result.normalized_ir is not None,
        "has_umwelt0_plan": result.umwelt0_construction_plan is not None,
        "action_request_emitted": result.action_request_emitted,
        "world_action_emitted": result.world_action_emitted,
        "fact_claimed": result.fact_claimed,
        "cause_confirmed": result.cause_confirmed,
        "value_assigned": result.value_assigned,
        "mature_recipe_claimed": result.mature_recipe_claimed,
        "mature_skill_claimed": result.mature_skill_claimed,
        "automation_claimed": result.automation_claimed,
    }
    if result.normalized_ir is not None:
        payload["ir"] = {
            "ir_id": result.normalized_ir.ir_id,
            "channel_count": len(result.normalized_ir.normalized_channels),
            "ref_count": len(result.normalized_ir.normalized_refs),
            "action_surface_count": len(result.normalized_ir.normalized_action_surfaces),
            "effect_surface_count": len(result.normalized_ir.normalized_effect_surfaces),
            "provider_count": len(result.normalized_ir.normalized_providers),
            "blocked_items": result.normalized_ir.blocked_items,
            "conformance_status": result.normalized_ir.conformance_status.value,
        }
    if result.umwelt0_construction_plan is not None:
        payload["umwelt0_plan"] = {
            "plan_id": result.umwelt0_construction_plan.plan_id,
            "public_observation_refs": len(result.umwelt0_construction_plan.public_observation_refs),
            "public_effect_refs": len(result.umwelt0_construction_plan.public_effect_refs),
            "passive_event_refs": len(result.umwelt0_construction_plan.passive_event_refs),
            "action_surface_refs": len(result.umwelt0_construction_plan.action_surface_refs),
            "effect_surface_refs": len(result.umwelt0_construction_plan.effect_surface_refs),
            "blocked_reasons": result.umwelt0_construction_plan.blocked_reasons,
        }
    return payload

