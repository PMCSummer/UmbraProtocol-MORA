# MORA Claim Constitution

## Purpose
P6 introduces an executable claim-governance layer that authorizes the strongest claim supported by evidence and blocks overclaim inflation.

## Claim Ladder
- L0: documentation/design claim
- L1: implemented surface claim
- L2: unit-tested mechanism claim
- L3: harness-integrated claim
- L4: subject_tick-integrated claim
- L5: embodied action/effect loop claim
- L6: internal candidate production claim
- L7: causal necessity / ablation-supported claim
- L8: baseline-compared claim
- L9: cross-domain / cross-backend claim
- L10: consciousness-adjacent functional evidence claim

## Evidence Requirements
- L0: design/ADR text only.
- L1: importable code + typed contract presence.
- L2: focused tests + invariants + negative controls.
- L3: harness execution + trace + falsifier pass.
- L4: mechanism appears in `subject_tick` result/state/telemetry.
- L5: observation -> subject_tick -> AP01 -> world effect -> next observation.
- L6: internal candidate from typed public basis; no scenario/eval/private/manual basis.
- L7: ablation and necessity evidence.
- L8: baseline comparison artifacts.
- L9: materially different backend evidence.
- L10: functional subjecthood evidence bundle (not consciousness proof).

## Forbidden Claim Patterns
- Closed/mature claim with unresolved blockers or incomplete validation.
- L8/L9/L10 language without baseline/benchmark/ablation/review artifacts.
- Dangerous vocabulary: "consciousness proven", "AGI achieved", "fully autonomous subject".
- AP01 claimed as execution/world mutation authority.
- ACP01 claimed as planner/open-ended strategy authority.

## Allowed Current Claims
- Typed mechanistic substrate claim.
- Subject-owned AP01 publication claim.
- Request != execution discipline.
- Embodied action/effect loop claim in controlled GridWorld.
- ACP01 bounded internal candidate production claim.
- Public/eval split claim.
- Anti-shortcut falsifier discipline claim.
- Bounded proto-subject contour claim.

## Near-Defensible Claims (Need Additional Evidence)
- Load-bearing necessity versus simpler baselines.
- Self/world boundary under perturbation.
- Calibrated uncertainty/residue report.
- Delayed/confounded learning.
- Cross-backend portability.

## Not-Yet-Defensible Claims
- Full autonomy.
- Open-ended planning.
- Strong artificial subjecthood.
- Consciousness proof.
- General AGI.
- Robust real-world intelligence.

## Checker Usage
- `python tools/claim_constitution_checker.py`
- `python tools/claim_constitution_checker.py --json`
- `python tools/claim_constitution_checker.py --include-advisory`
- `python tools/claim_constitution_checker.py --fail-on-overclaim`

## Relationship to Roadmap
Checker reports governance findings; it does not mutate roadmap/phase statuses.

## Relationship to External Reviewer Pack
Checker can require artifact anchors for L8-L10 claims, but it does not build the external reviewer pack itself.
