# Historical exposure-analysis artifacts

Published September 28, 2026 to preserve previously local work for the repository handoff. The existing artifacts and their generating script were not changed or rerun during publication.

- `exposure_gantt.pdf` and `exposure_gantt_slide.png` are historical figure outputs.
- [Source script](../../scripts/build_exposure_figure.py).
- [Saved summary](../../data/exposure_summary.csv).

These are not validated V8 results or approved evidence for the current thesis. A read-only inspection found issues that must be resolved before reuse:

- The script uses the inaccurate label "Real ZKP" for the two-multiplication workload.
- It retains older cycle-time assumptions and a modeled `2P` detection bound.
- It combines separate bench detection and campaign threshold-observation measurements into a quantity labeled as a measured total. This is not a directly observed end-to-end interval for the same trial.
- Its V5 duplicate-selection rule is chosen by matching an earlier summary. Inclusion rules need independent justification, not selection to reproduce a desired result.
- Arithmetic additivity does not independently validate the timing model or physical stopping time.

Consult the [current evidence corrections](../../audit/writing_evidence_status_2026-09-16.md) before using these files. Preserve their history; do not adopt them as dashboard acceptance targets or overwrite them with new experiment records.
