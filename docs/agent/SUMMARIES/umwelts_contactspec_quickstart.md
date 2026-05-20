# UMWELT-S ContactSpec / Contact IR Quickstart

## 1) What ContactSpec Is
`ContactSpec` is a symbolic contact declaration layer:
- backend-agnostic;
- declares public channels/refs/surfaces/providers;
- validates those declarations against safety constraints;
- normalizes into `ContactIR`;
- produces a `UMWELT0`-compatible construction plan for downstream runtime use.

Core intent: describe **public contact surfaces**, not world truth.

## 2) What ContactSpec Is Not
`ContactSpec` is not:
- WORLD0 runner;
- adapter execution loop;
- planner;
- action selector;
- AP01 request creator;
- recipe oracle;
- provider behavior implementation;
- raw perception pipeline;
- final human-friendly DSL syntax.

## 3) Pipeline
`ContactSpec`
-> `ContactIR`
-> `UMWELT0` construction plan
-> `UMWELT0` runtime frames
-> `CONTACT-PROJECTION-GATE`
-> `subject_tick`
-> `AP01/effect` later through `WORLD0`

## 4) Channel Kinds
`symbolic_world`
- Allowed: resources/stations/entities/sites/hazards as public symbolic contact.
- Forbidden overclaim: world truth, hidden map, selected action.

`knowledge_affordance`
- Allowed: source-bound hints, manual/tooling/provider claims.
- Forbidden overclaim: provider truth, mature recipe, final value.

`language_contact`
- Allowed: utterance/testimony/speech-act candidates.
- Forbidden overclaim: linguistic claim as fact.

`sensory_candidate`
- Allowed: candidate perceptual events/objects.
- Forbidden overclaim: mature object truth/identity certainty.

`body_internal`
- Allowed: public body pressure/state cues.
- Forbidden overclaim: intrinsic-need rewriting policy.

`social_external_actor`
- Allowed: observed external cues/proposals/warnings.
- Forbidden overclaim: copied skill/policy truth.

`system_status`
- Allowed: public status/degradation/availability indicators.
- Forbidden overclaim: backend oracle diagnosis.

`unknown_public`
- Allowed: bounded, source-bound, uncertainty-marked unknown contact.
- Forbidden overclaim: unbounded unlabeled trust payload.

## 5) Ref Kinds
Typical kinds:
- `resource`
- `station`
- `entity`
- `map_site`
- `inventory`
- `route_segment`
- `hazard`
- `effect`
- `action_surface`
- `knowledge_hint`
- `language_utterance`
- `speech_act_candidate`
- `sensory_candidate`
- `body_pressure`
- `system_status`
- `provider_claim`
- `objective_hint`
- `conflict`
- `residue`
- `uncertainty`
- `lossiness`

Use them as typed **public references**, not hidden backend payload carriers.

## 6) Action Surfaces
Allowed action-surface kinds include:
- `inspect`
- `move_toward`
- `gather`
- `pickup`
- `place`
- `use_station`
- `wait`
- `scan`
- `ask`
- `repair_check`

Forbidden in action surfaces:
- `selected_action`
- policy logic
- route plan
- AP01 request envelope
- imperative command
- factory solution sequence

Action surfaces are basis surfaces, never selected execution.

## 7) Effect Surfaces
Allowed:
- request-correlated effect surfaces;
- passive public events;
- blocked effects;
- residue/conflict/uncertainty traces.

Forbidden:
- fact proof;
- cause proof;
- success truth oracle;
- hidden diagnosis.

## 8) Provider Surfaces
Provider declarations can model surfaces such as:
- JEI/index-like;
- encyclopedia;
- questbook;
- manual/tooltip;
- machine UI/status;
- scanner;
- language contact provider;
- sensory candidate provider.

Current boundary:
- provider declaration only;
- no provider behavior implementation;
- no provider truth authority.

## 9) Forbidden Payloads
Reject payloads/tokens such as:
- `selected_action`
- `preferred_action`
- `if_then_policy`
- `route_plan`
- `goal_selection`
- `solution_sequence`
- `factory_steps`
- `true_recipe`
- `recipe_truth`
- `full_map`
- `worldstate`
- `backend_object_id`
- `hidden_label`
- `eval_label`
- `scenario_label`
- `intrinsic_need`
- `drive_weight`
- `homeostatic_rule`
- `subject_goal`
- `badness_function`

## 10) Compact Examples
### A) Minimal symbolic grid spec (safe)
```python
{
  "spec_id": "grid_min",
  "channel_declarations": [
    {"channel_id": "ch_world", "channel_kind": "symbolic_world", "public": True, "max_refs": 16, "requires_source_refs": True}
  ],
  "public_ref_declarations": [
    {"ref_id": "resource:ore", "ref_kind": "resource", "channel_id": "ch_world", "source_requirements": {"required": True, "source_refs": ["src:grid:public"]}}
  ],
  "action_surface_declarations": [
    {"surface_id": "surface:inspect", "action_kind": "inspect", "channel_id": "ch_world"}
  ],
  "effect_surface_declarations": [
    {"effect_surface_id": "effect:delta", "effect_kind": "position_update", "channel_id": "ch_world", "request_correlated_allowed": True, "passive_event_allowed": False}
  ]
}
```

### B) Symbolic factory contact with provider hint (no recipe truth)
```python
{
  "spec_id": "factory_symbolic",
  "channel_declarations": [
    {"channel_id": "ch_world", "channel_kind": "symbolic_world", "public": True, "max_refs": 32, "requires_source_refs": True},
    {"channel_id": "ch_knowledge", "channel_kind": "knowledge_affordance", "public": True, "max_refs": 12, "requires_source_refs": True}
  ],
  "public_ref_declarations": [
    {"ref_id": "station:smelter", "ref_kind": "station", "channel_id": "ch_world", "source_requirements": {"required": True, "source_refs": ["src:factory:public"]}},
    {"ref_id": "knowledge_hint:slot_filter", "ref_kind": "knowledge_hint", "channel_id": "ch_knowledge", "source_requirements": {"required": True, "source_refs": ["src:factory:public"]}}
  ],
  "provider_declarations": [
    {"provider_id": "provider:manual", "provider_kind": "manual_tooltip", "channel_id": "ch_knowledge", "hint_only": True, "truth_authority": False}
  ]
}
```

### C) Language + sensory candidate spec (testimony/candidate only)
```python
{
  "spec_id": "lang_sensor",
  "channel_declarations": [
    {"channel_id": "ch_lang", "channel_kind": "language_contact", "public": True, "max_refs": 20, "requires_source_refs": True},
    {"channel_id": "ch_sens", "channel_kind": "sensory_candidate", "public": True, "max_refs": 20, "requires_source_refs": True}
  ],
  "public_ref_declarations": [
    {"ref_id": "language_utterance:u1", "ref_kind": "language_utterance", "channel_id": "ch_lang", "source_requirements": {"required": True, "source_refs": ["src:lang:public"]}},
    {"ref_id": "sensory_candidate:v1", "ref_kind": "sensory_candidate", "channel_id": "ch_sens", "source_requirements": {"required": True, "source_refs": ["src:sens:public"]}}
  ]
}
```

## 11) Common Mistakes
- Using ContactSpec as planner/policy container.
- Encoding recipe oracle truth in provider/ref metadata.
- Turning ContactSpec into WorldState schema/pass-through.
- Treating quest text as truth.
- Rewriting intrinsic needs through `body_internal`.
- Using `unknown_public` without source + uncertainty + bounds.
- Letting provider defaults invent missing evidence.

## 12) Claims
Allowed claim:
- MORA can declare and validate symbolic public contact specs into UMWELT0-compatible IR.

Forbidden claims:
- MORA can run a world.
- MORA can play Minecraft.
- MORA can build factories live.
- MORA has final DSL syntax.
- MORA understands provider text as truth.
- MORA has raw perception.
