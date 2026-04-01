# ADR-F01: Causal Substrate

## Status
Accepted for phase `F01` as foundation-only implementation.

## Decision
Use one canonical mutation gateway:

`execute_transition(request, state) -> TransitionResult`

This is the only public route for meaningful runtime-state mutation.

## Why This Is Not A God-Object
- The public write seam is singular, but internals are split into pure stages.
- Stage pipeline: validate request/state, resolve kind, authority gate, pure apply, delta, provenance, invariant checks, honest failure emission, result build.
- State writes are constrained by an explicit field-level authority matrix.
- All mutations are represented as typed output (`TransitionResult`) and append-only traces.

## Enforced Causal Discipline
- Typed state, typed request/result, typed event/provenance/failure/delta.
- Eventless state changes are rejected by invariant checks.
- Missing provenance is impossible in returned successful/rejected results.
- Invalid transition contracts produce explicit rejection + failure marker (no silent fallback).
- Runtime state is immutable-shaped (`frozen` dataclasses + tuple traces), so direct field mutation bypass is blocked.

## Deferred By Design (Not F01)
- Semantic interpretation (F02)
- Allostatic regulation (R01)
- Self-regulation loops (R02)
- Intent, planning, dialogue policy, realization logic
- Global singleton runtime, plugin framework, hidden side effects

## Telemetry Added In F01
- `trace.events` append-only `EventRecord`
- `trace.transitions` append-only `ProvenanceRecord`
- `runtime.revision` monotonic counter
- `runtime.last_transition_id` and `runtime.last_event_id`
- `failures.current` explicit `FailureMarker`
