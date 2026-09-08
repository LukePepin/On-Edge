# Decontamination Report

> **Addendum (2026-08-14, post-review):** the author reviewed this report and directed follow-ups that have since been applied: (1) the legacy `docs/` layer described in §5 flag 1 was **deleted** (`git rm`; the two early advisor-audit critiques were moved to `docs/archive/` instead); (2) `audit/` was **renamed `docs/`**, so `audit/...` paths below refer to the layout at the time of the pass; (3) `ground_truth.md` §5.3 was **amended by the author**: the latched C192A4 safety-fault state performs a Category 0 halt until manual reset (designed stop path remains Category 2), and that nuance was cascaded through the corrected docs; (4) the `.agents/AGENTS.md` edit (§5 flag 2) was accepted; (5) the README was rewritten (colcon build and Pi SSH access retained, ROS 2 install boilerplate removed).

**Date:** 2026-08-14
**Scope:** Documentation only. Aligns all prose documents with `audit/ground_truth.md` and `audit/project_truth.md` (the two authoritative files, which were not edited). Firmware, orchestrator scripts, and CSV/PCAP data untouched. No commit has been made — the working tree is left dirty for human review.

**Conventions used:**
- *Fixed in place* = claims corrected inline, file structure and voice preserved.
- *Header-neutralized* = a prominent SUPERSEDED / LEGACY / HISTORICAL banner prepended; body text retained verbatim as history. Used for superseded documents where an inline rewrite was out of scope for this pass.
- *Archived* = moved (`git mv`) to `docs/archive/` with the banner "ARCHIVED — superseded by ground_truth.md; retained for history."

---

## 1. Files fixed in place (before → after per corrected claim)

### `audit/conclusion.md`
| # | Before | After |
|---|---|---|
| 1 | §1: 64-byte segmentation invoked CLT/Berry-Esseen, bounding execution to 301–346 ms; breach of "ISO 13849-1 500ms safety threshold" | Section retitled "— WITHDRAWN"; states the firmware ran one loop three times (sd 0.17 ms, no variance to compress), variance of a sum grows as n·σ², and 500 ms is a self-imposed budget (ISO 13849-1 sets no stop-time ceiling) |
| 2 | §2: μ = 3.10 pkt/s, ρ = 16.14, M/M/1 doomed to livelock | Queueing figures marked `[WITHDRAWN — see ground_truth.md]`; livelock retained as an engineering observation resolved by the QoS fix (`RELIABLE/KEEP_ALL` → `BEST_EFFORT/KEEP_LAST(1)`) |
| 3 | §3: "Latching Cryptographic Halt"; robot "initiated a Category 0 Protective Stop"; latch presented as designed dual-use feature | Category **2** safeguard stop via SI0/SI1 (auto-resumes); C192A4 described as a genuinely observed *timing fault on restoration*, not a designed feature |
| 4 | §4: Pi = the "Vault" streaming kinematics; "20-trial physical outage test"; ZKP mean 334.66 ms as a real measurement with "16.2% margin"; ECC "25.4% margin under the 150ms real-time kinematic boundary"; "overpowered N=1940 dataset… mathematically unassailable" | Pi = supervisor/orchestrator (does not hash the 50 Hz stream); "20-repetition scripted swapover sequence"; 334.66 ms labeled the **stub** (3× ECC keygen tuned under a self-imposed 400 ms budget) with real ZKP proxy 224.86 ms (sd 0.21, p95 225.18, 300 runs); the 150 ms "kinematic boundary" and both margin percentages **dropped as untraceable**; 1940 relabeled as swapover *cycle* count; campaign N corrected to 335 trials (120+120+75+20); "unassailable"/guarantee language explicitly not retained |

### `audit/master_research_summary.md`
| # | Before | After |
|---|---|---|
| 1 | "edge-compute authorization **mesh**" | "authorization system… USB-serial star topology; earlier wireless MANET/mesh design abandoned" |
| 2 | "dual-mesh" architecture; ZKP verifying trajectories peer-to-peer | "dual-path"; note added that the trial-era "ZKP" path was a stub, real ZKP profiled at 224.86 ms |
| 3 | Hold-down presented as shipped safeguard, no caveat | Caveat added: suspension currently unbounded — known denial-of-safety gap (gaps.md §5) |
| 4 | "hardware Category 0 Safeguard Stop in under 500ms (ISO 13849-1 compliant)" | Category **2** stop via SI0/SI1 (auto-resumes); 500 ms labeled self-imposed design budget; honest latency statement (only ECC α=0.5 approaches it, observed 291–505 ms, max over the line) |
| 5 | Contribution 1: 64-Byte CLT Stabilization | Replaced by the retained eviction-latency model (`trust(t+1) = (1−α)·trust(t)`, cycles × period + offset); CLT claim noted as withdrawn |
| 6 | Contribution 2: "M/D/1 Livelock Mitigation — Proved…" with NS-3 framing | "QoS Livelock Mitigation" as engineering fix; M/M/1→M/D/1 numbers noted withdrawn |
| 7 | Contribution 3: 120-run ANOVA "empirically proved" ZKP violates 500 ms; CLT segmentation "stabilizes at ~325ms" | Real security-tax statement: real ZKP ~247 ms/cycle predicts ~600–700 ms eviction, outside the self-imposed budget at every α; stub and fabricated ~325 ms mitigation noted withdrawn; d = 2.398 reported descriptively |

### `audit/empirical_conclusions.md`
| # | Before | After |
|---|---|---|
| 1 | "121-run V4 ANOVA Physical Dataset" | 120-trial V5 campaign (2×4×3×5); project total 335 trials |
| 2 | "500ms safety threshold required by ISO 13849-1" | Self-imposed 500 ms design budget; standard sets no ceiling |
| 3 | "d = 2.398 (where n=4 was required for 80% power, and we collected n=5)" | d = 2.398 reported descriptively; observed-power justification explicitly withdrawn as circular |
| 4 | ECC halts "between 236ms and 439ms, successfully passing the ISO limit" | Measured 291–505 ms at α = 0.5 (mean 374.3 ms); observed max 504.9 ms is *over* the budget |
| 5 | ZKP "failed to halt until 517ms to 1060ms" | Stub path measured 738–1300 ms at α = 0.5 (mean 898.8 ms). The 517–1060 range corresponded to nothing in the data |
| 6 | "ZKP… fundamentally incompatible" as empirical finding | Reframed: factor is cycle time, not algorithm identity; real-ZKP incompatibility is a model *prediction* from profiling (~600–700 ms at α=0.5) |
| 7 | CLT section demanding Shapiro-Wilk validation of the 64-byte phenomenon | Section retitled "— WITHDRAWN"; no phenomenon exists to validate |
| 8 | H1' null result ("outage duration had no statistically significant interaction"); α levels "0.5, 0.7, 0.9" | Withdrawn as instrumentation artifact (no RECOVER path); α levels corrected to 0.1/0.3/0.5; replaced by the V6 result (stop-rate table, cycle period ~125 ms) |

### `audit/system_architecture.md` (kept as the canonical copy — see §4 below)
| # | Before | After |
|---|---|---|
| 1 | "Edge-Compute Star **Mesh**"; "Phase 4 Dual-Mesh cryptography"; "ZKP/ECC Dual-Mesh" | "Star Topology (USB-Serial)"; "dual-path (ZKP/ECC)" |
| 2 | Pi = "The 'Vault'… executes the cryptographic hashing of raw 50Hz kinematic telemetry"; diagram "Hashes Telemetry & Stores in Local 'Vault'", "Broadcasts Hashed Payload (64 Bytes)" | Pi = supervisor/orchestrator (logs, probes cloud, sends JSON config/commands over USB serial); explicit note that verification runs on the Arduinos |
| 3 | Diagram: "Triggers Category 0 Safeguard Stop!" | "Triggers Category 2 Safeguard Stop!" + note (Category 0 requires EI0/EI1 or cutting relay power) |
| 4 | "ZKP: ~334ms" as real | Labeled "ZKP" stub ~334.7 ms; note added with real ZKP proxy 224.86 ms |
| 5 | Hold-down shown as shipped feature | Note added: suspension unbounded, known denial-of-safety gap (gaps.md §5) |
| 6 | "threatening the 500ms safety boundary" | "self-imposed 500ms stop budget" |
| 7 | Latching fault as protective design outcome | Reframed as genuinely observed timing fault on restoration, not a designed latching stop |

### `audit/experimental_pivots.md`
| # | Before | After |
|---|---|---|
| 1 | Pivot 2: 64-byte segmentation invoked CLT, bounded 301–346 ms | Withdrawal stated inline; retained the engineering lesson (cycle time must be controlled/measured; actual workloads ~111.5 ms ECC, ~334.7 ms stub) |
| 2 | Pivot 4: title "M/M/1 ROS 2 Livelock"; "reducing the queue to a stable M/D/1 model and shedding 99.6% of stale traffic" | Title → "ROS 2 Boot-Storm Livelock"; M/D/1 model + 99.6% figure marked `[WITHDRAWN — see ground_truth.md]`; QoS change kept as engineering fix |
| 3 | Pivot 8: "uncontrolled Category 0 STO (Safe Torque Off) to meet cryptographic latency goals" | Category 2 safeguard stop via SI0/SI1; C192A4 = timing fault on restoration, not a designed latching stop |

### `audit/gaps.md` (§4 only, per instructions; §5 untouched)
| # | Before | After |
|---|---|---|
| 1 | "Phase 5 Capstone **proved**… 224.86 ms, safely under the 400 ms… threshold" | "Real ZKP profiling **measured**… 224.86 ms (sd 0.21, 300 runs)" under the 400 ms budget, explicitly labeled a self-imposed design budget (not a standards requirement); 224.86 figure retained (it is correct) |
| 2 | "fail to initialize the mesh and latch a Category 0 Protective Stop" | "fail to complete bootstrap verification and the trust collapse will drop the safeguard-stop line (a Category 2 stop via SI0/SI1)" |
| 3 | FPGA migration "expanding the true safety margin to >80%" | Speculative ">80%" figure dropped; reframed as widening the margin against the self-imposed budget |

### `README.md`
- Title and abstract replaced: was "Decentralized ZKP Authorization Meshes" with the MANET/p\* abstract; now the `project_truth.md` §1 framing (edge-local trust monitor, EWMA decay, hardware stop, latency model, 335 trials), with an explicit note that the MANET/mesh design was abandoned and the as-built system is a USB-serial star.
- Repository-structure section corrected to the actual tree (`audit/` called out as authoritative).
- Setup instructions **kept but banner-labeled "Legacy — verify before use"**: I could not verify whether the colcon/ROS 2 steps and `ssh seeker@on-edge-pi.local` still match the current build, so I labeled rather than guessed (see §5, flag 7).

### `.agents/AGENTS.md` (not in the §7 queue — see §5, flag 2)
- Goal bullet rewrote the abandoned ZKP-mesh/p\* framing to the §1 framing and points future agents at the truth files ("never restore claims those files withdraw"). Edited because this file actively instructs future AI sessions and was a re-contamination vector.

### Header-only additions (content unchanged)
- `audit/outline_v2.md` — "**SUPERSEDED — outline_v3 in progress; retained for reference. Do not cite.**"
- `docs/luke pepin - Thesis Outline V2.md` — same header (byte-identical duplicate of the above; see §5, flag 3).

---

## 2. `[WITHDRAWN]` insertions and figures dropped with no replacement available

1. `audit/conclusion.md` §2 — ρ = 16.14, μ = 3.10, M/M/1 livelock math → `[WITHDRAWN — see ground_truth.md]`.
2. `audit/experimental_pivots.md` Pivot 4 — M/D/1 model + "99.6% of stale boot-storm traffic shed" → `[WITHDRAWN — see ground_truth.md]`.
3. `audit/conclusion.md` §4 — "16.2% margin under the 400ms initialization boundary" and "25.4% margin under the **150ms real-time kinematic boundary**" dropped; the 150 ms boundary appears nowhere in the truth files.
4. `audit/gaps.md` §4 — FPGA ">80% safety margin" projection dropped (speculative figure with no source).

---

## 3. Disagreements the truth files did not anticipate (flagged, not fixed — see also §5)

1. **`system_architecture.md` is not a duplicate.** `project_truth.md` §7 says "two identical copies exist, dedupe." The copies differ: `docs/system_architecture.md` (3,524 B) is an older, *more* contaminated revision (Vault hashing narrative, ">400 ms verification" trust logic, Category 0, ZKP-only flow); `audit/system_architecture.md` (3,031 B, "V4 Integrated") is newer. Resolution: kept and fixed the `audit/` copy; archived the `docs/` copy with an explanatory banner. The §7 statement itself may warrant a correction by a human.
2. **`docs/luke pepin - Thesis Outline V2.md`** is a byte-identical twin of `audit/outline_v2.md` that §7 does not mention. Given the archive-not-delete convention I did not remove it; both copies now carry the SUPERSEDED header. A human may want to dedupe.
3. **A whole legacy layer in `docs/` carries the withdrawn claims but is absent from §7** (details in §5, flag 1). Handled with header-neutralization, not inline rewrite.
4. **`audit/gaps.md` §§1–3** still use the "Vault" nickname for the Pi (§1, without the hashing claim) and the phrase "M/M/1 Queue Saturation vulnerability" as the historical name of Phase 3.5 (§3). The instructions restricted edits to §4, so these stand — flagged for a human call on whether the nicknames are acceptable as historical labels.
5. **`docs/final_test_review.md` and `docs/academic_audit_report.md`** are advisor-voice critique documents. They largely *attack* the fabricated claims (mock-loop crypto, prover-vs-verifier) and assert no withdrawn results as findings, but they refer in passing to "your ISO 13849-1 safety threshold is 500ms." Left untouched; flag for optional annotation.
6. **`docs/cloud_edge_cloud_runbook.md`** — operational runbook; only incidental "edge mesh" phrasing. Left untouched.
7. **`src/README.md`** — colcon-workspace scaffold description including a suggested `ns3_simulation/` directory. Left untouched; mildly stale.
8. **`docs/archive/*` (pre-existing archive)** — contains withdrawn claims (e.g., `zkp_deployment_guide.md`) but was already archived before this pass; treated as history and not modified.

---

## 4. Files archived (source → destination)

All moved with `git mv`; each carries the banner "**ARCHIVED — superseded by ground_truth.md; retained for history.**"

| Source | Destination |
|---|---|
| `running.md` | `docs/archive/running.md` |
| `audit_checklist.md` | `docs/archive/audit_checklist.md` |
| `audit/final_lab_plan.md` | `docs/archive/final_lab_plan.md` |
| `docs/system_architecture.md` | `docs/archive/system_architecture.md` *(dedupe resolution — older revision; extended banner noting it was not in fact identical to the audit copy)* |

Not edited, per instructions: `audit/original_thesis_proposal.md`, `audit/ground_truth.md`, `audit/project_truth.md`.

---

## 5. Judgment calls a human should review

1. **Scope call on the unanticipated `docs/` legacy layer.** The instruction "remove or correct every instance, every file" collided with "smallest diff, preserve structure and voice" for ten legacy files that are contaminated nearly end-to-end and appear nowhere in §7. I chose **header-neutralization** (a do-not-cite banner naming the specific withdrawn claims) over wholesale rewrite or unilateral archiving: `docs/thesis_conclusions.md`, `docs/master.md`, `docs/thesis_master_outline.md`, `docs/mermaid.md`, `docs/luke pepin - Thesis Outline.md`, `docs/thesis_code_analysis.md`, `docs/planning/On-Edge Project_ Strategic Brief & Roadmap.md`, `docs/planning/architecture.md`, `docs/planning/workspace.md`, `docs/enhanced_earc_literature_review.md`. Their body text still contains the withdrawn wording under the banner. If you prefer, these can be moved to `docs/archive/` or deep-cleaned in a follow-up pass.
2. **`.agents/AGENTS.md` edit** was outside the §7 queue (rationale in §1). Revert if you consider agent config out of scope.
3. **README setup steps** (`colcon build`, ROS 2 Humble, `on-edge-pi.local`) are retained under a "Legacy — verify before use" banner because I could not verify the current build procedure. Someone who knows the current workflow should confirm or rewrite them.
4. **Known follow-up (out of scope per instructions):** firmware comments still claim "Category 0 Halt" (`unified_trust_monitor_template.ino` lines ~137/185 per `ground_truth.md` §5.3).

---

## 6. Withdrawn-claim instances removed, by category

Counts are **inline corrections in fixed-in-place files** (each row of the §1 tables above that removed/corrected an instance of that category). Files that were archived or header-neutralized retain their historical text under a banner and are not counted here.

| Category | Inline fixes | Also present in header-neutralized/archived files |
|---|---|---|
| 1. Category 0 / STO / Latching Halt as designed | 5 | yes (8 files) |
| 2. 22.85% Security Tax | 0 (none survived in the queue files) | yes (both outlines v1/v2) |
| 3. CLT / 64-byte / Berry-Esseen / 301–346 ms | 5 | yes (6 files) |
| 4. "ISO 13849-1 mandates 500 ms" | 6 | yes (several) |
| 5. α = 0.5/0.7/0.9 as levels run | 1 | no |
| 6. Inverted EWMA formula | 0 inline (correct formula added once) | yes (outline v2 ×2, lit review — headers note the correct rule) |
| 7. H1' null result | 1 (replaced by V6) | no |
| 8. Phase Overlap Hypothesis | 0 — **no instance found anywhere in the repo** | — |
| 9. N = 121 / 1940 / 54 as campaign size | 2 | yes (running.md 54-run, final_lab_plan) |
| 10. Observed power (d = 2.398 ⇒ n = 4) | 1 | yes (final_lab_plan) |
| 11. ZKP 334.66 ms as real measurement | 4 | yes (several) |
| 12. Vault / MANET / mesh / p\* / NS-3 / M-M-1 numbers | 10 | yes (most legacy files) |
| **Total inline** | **35** | 15 files neutralized by banner or archive |

---

*End of report. No commit opened — awaiting human review of this report and the diff.*
