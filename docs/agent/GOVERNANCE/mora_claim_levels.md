# MORA Claim Levels

| Level | Name | Required Evidence | Allowed Language | Forbidden Language | Example Claim | Required Falsifiers |
|---|---|---|---|---|---|---|
| L0 | Documentation/Design | ADR/design doc | "designed", "proposed" | "implemented", "proven" | "Design for AP01 seam exists" | Scope overreach guard |
| L1 | Implemented Surface | Importable code, typed contracts | "surface exists" | "runtime verified" | "PublishedActionEnvelope model exists" | Interface mismatch falsifier |
| L2 | Unit-Tested Mechanism | Unit tests, invariants, negatives | "mechanism tested" | "integrated contour" | "AP01 boundary invariant tested" | Boundary bypass falsifier |
| L3 | Harness-Integrated | Harness runs, trace, falsifiers | "harness integrated" | "autonomous" | "Bridge harness executes bounded loop" | Harness shortcut falsifier |
| L4 | SubjectTick-Integrated | Appears in SubjectTickResult/state/telemetry | "subject_tick integrated" | "world-executing authority" | "ACP01 counters in subject_tick" | SubjectTick bypass falsifier |
| L5 | Embodied Action/Effect Loop | observe->tick->AP01->effect->next observe | "embodied bounded loop" | "general intelligence" | "GridWorld loop with AP01 gating" | Request-as-success falsifier |
| L6 | Internal Candidate Production | Typed public basis + AP01 handoff | "bounded internal candidate" | "planner", "open-ended strategy" | "ACP01 emits AP01-ready candidate set" | Scenario/eval/private basis falsifiers |
| L7 | Causal Necessity/Ablation | Ablation + degraded behavior evidence | "load-bearing necessity" | "robust autonomy" | "Removing seam degrades bounded behavior" | Ablation counterfactual falsifier |
| L8 | Baseline-Compared | Matched-budget baseline artifacts | "better than baseline in scope" | "externally benchmarked" without artifacts | "Beats scripted baseline under matched info" | Baseline leakage falsifier |
| L9 | Cross-Backend | Same contour on distinct backends | "cross-backend bounded portability" | "general AGI" | "Contour survives backend switch" | Backend lock-in falsifier |
| L10 | Consciousness-Adjacent Functional Evidence | Boundary, uncertainty, continuity, perturbation, review bundle | "consciousness-adjacent indicators" | "consciousness proven" | "Functional subjecthood indicators observed" | Consciousness overclaim falsifier |
