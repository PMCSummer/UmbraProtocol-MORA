Seam contracts live in docs/seams/*.seam.md

For any phase implementation, validation, or refactor:
- identify the current phase seam file first
- treat it as a binding operational contract
- obey OPEN SEAMS TO LEAVE and FORBIDDEN OVERREACH
- use SEAM OBLIGATIONS, LOAD-BEARING SEAM TELEMETRY, REQUIRED SEAM TESTS, and SEAM FALSIFIERS during implementation and validation
- do not ignore direct upstream/downstream constraints from the seam file

Collaboration defaults for this workspace owner:
- Respect explicit mode per request (`BUILD`, `AUDIT`, `HARDENING`); do not silently switch modes.
- Keep scope narrow; no phase creep. If a requested fix crosses phase authority, stop at boundary and report explicit bound.
- Prove causal/load-bearing impact; green tests alone are not sufficient acceptance.
- Preserve first-class uncertainty (`unknown`, `provisional`, `mixed`, `unresolved`, `degraded`) and never launder fallback as normal path.
- Prefer falsifier-oriented validation: include negative controls, ablation where relevant, and downstream-obedience checks.
- Keep typed gate discipline and F01-only persistence seam intact unless explicitly requested otherwise.
- Avoid broad refactors for hardening/remediation tasks; apply minimal, high-impact changes.
- In final reports, separate: `mechanistic/load-bearing`, `bounded/non-claim`, `falsifiers closed`, `falsifiers partial/open`, and exact test commands/results.

Operational tools:
- Preferred ripgrep binary: `C:\Users\Thanatos\Desktop\UmbraProtocol_MORA\tools\ripgrep\rg.exe`

Roadmap operational memory (current architectural intent):
- `T04` is the only new standalone phase from this decision: `Attention schema / focus ownership model`.
- `R04.1`, `RT01.1`, `S01.1`, `W05.1`, `W06.1`, `T03.1`, `C06.1`, `O01.1`, `P04.1` are embedded augmentation blocks over existing phases, not new top-level lines.
- Do not create standalone phases for autopoiesis / predictive coding / ToM / GWT without a new explicit human decision.
- Keep IIT untouched in this decision family.
