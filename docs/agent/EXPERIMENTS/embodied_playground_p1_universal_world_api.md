# Embodied Playground P1 / EPG-01

## Purpose
EPG-01 defines a backend-neutral embodied world API surface for experiments.  
It introduces typed contracts for body, inventory, visible objects, action-space, AP01 request envelopes, and external world effect feedback.

## What This Slice Proves
- A subject-visible `ObservationFrame` can be represented without hidden/eval truth.
- `ActionSpaceFrame` is explicitly separated from permission/selection/execution.
- `PublishedActionEnvelope` preserves AP01 boundary (`request != execution`).
- `PublishedActionEnvelope` constrains AP01 request refs (`ap01_request:`/`ap01:req:` prefixes, no scenario/eval/hidden markers).
- `ActionEffectFrame` is a separate world-feedback artifact correlated to a request/envelope.
- `PublicWorldSnapshot` and `EvalOnlyWorldTruth` are explicitly separated.
- A backend protocol can be defined without action-selection authority.

## What This Slice Does Not Prove
- No GridWorld implementation.
- No subject_tick loop integration.
- No world simulation semantics.
- No planner/action selection logic.
- No automation/recipe/station behavior execution.
- No Minecraft adapter.
- No GUI.

## Core Contracts
- `BodyState`, `InventoryState`, `WorldObjectObservation`
- `AvailableInteractionSurface`, `ActionSpaceFrame`
- `ObservationFrame`
- `PublishedActionEnvelope` (AP01-bound publication artifact)
  - includes constrained `AP01RequestRef` boundary wrapper
- `ActionEffectFrame` (external feedback artifact)
- `PublicWorldSnapshot`, `EvalOnlyWorldTruth`
- `WorldBackend` protocol

## Boundary Discipline
- Hidden/eval truth must not enter subject-visible payloads.
- Available interaction surfaces are not permission.
- AP01 envelope is not execution/success/completion.
- Effect records must carry request correlation or be marked passive/ambiguous.

## Validation and Falsifiers
Validation helpers enforce:
- subject-visible exclusion of hidden/eval payloads
- action-space non-permission boundary
- AP01 envelope boundary
- request/effect correlation

Falsifiers cover:
- hidden truth leakage
- eval label leakage
- action-space as permission
- action without AP01 envelope
- request as execution
- request as success/completion
- effect without correlation
- inventory/body delta without effect
- hidden recipe visibility
- backend action selection leakage
- minecraft-specific field leakage
- grid lock-in
- AP01 boundary missing
- scenario-id action selection leakage

## Demo
`tools/embodied_playground_api_demo.py` demonstrates:
- observation/action-space/envelope/effect separation
- boundary claims (`request!=execution/success/completion`)
- no world-competence overclaim
