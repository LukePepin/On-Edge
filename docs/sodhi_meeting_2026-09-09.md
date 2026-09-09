# Sodhi meeting, Wed 2026-09-09 — agenda and hand-off note

## Hand-off: Draft 1 (Methods + Results)
- Thesis repo `LukePepin/Thesis`, folder `draft 9-9/`, `thesis.pdf` (34 pages). Chapters 3 and 4 complete; 1, 2, 5, 6 structured placeholders.
- Everything in it traces to `On-Edge/ground_truth_v2.md`; the audit that produced it is in `On-Edge/audit/`.
- Ask: comments on scope and framing of chapters 3-4; turnaround by 9/18 so Draft 2 (10/10) can absorb them.

## Purpose of the meeting (Luke, 9/8)
Get Sodhi's general read of the project: does the framing hold, is the contribution the right size for an M.S., what would he push on. Not a line-edit session.

## Decisions already made (state, don't ask)
- The ZKP path is the "ZKP-cost proxy" (two secp256r1 scalar multiplications; no proof verified).
- Sub-500 ms stops are reported as "commanded trajectory not executed"; the arm was stationary at eviction.
- Bench work first (Pi-side proxy profile, failover sweep re-run), then Draft 2 writing.

## Questions for Sodhi (open-ended)
1. Does the one-sentence contribution land: a measured, inverted latency model for an EWMA trust monitor driving a hardware safety input, validated at two cryptographic loop periods?
2. Is the honest scope (cost proxy, Category 2, stationary arm) a problem for the committee, or a strength if presented as an audited pipeline?
3. Which chapter would he want strongest for this committee: the model (ch5), the experiments (ch4), or the safety framing (ch1/ch6)?
4. Anything he wants added to Draft 2 that is not in the chapter map?

## Facts that changed since August (so nothing surprises anyone later)
- Cycle times: 120.4 ms (ECC), 232.1 ms (proxy), measured on one clock. The 247 ms figure is withdrawn.
- V6 (120 ECC trials) and V7 (75 proxy trials) with a working outage factor: stop iff outage >= n(alpha) x T_cycle, 27/27 cells, no partial cells once stop is judged by joint motion.
- The joint logger drops 10-20 % of firmware lines; corrected by using the motion columns. Stated as an instrument limit.
- Category 2 safeguard stop, one pin to SI0+SI1 in parallel. Not Category 0, not STO.
- 500 ms is a self-imposed design budget; ISO 13849-1 sets no stop time.
- Withdrawn and gone from the repo: 334 ms, 22.85 %, CLT window, 368 ms, 99.6 %, Cohen's-d power, "335 physical trials".

## Admin (from the task list)
- Chair confirmation (Rosseau); committee Maier-Speredelozzi, Sun; defense date 12/11.
- Draft 1 scope/turnaround; Draft 2 = unified time-to-safe-state model + hold-down/watchdog analysis (10/10); Draft 3 full (11/11).
- Workshop paper venue; Wednesday absences; Industry 4.0 certificate.
- Nomination for Graduation 10/12-10/14; Request to Schedule Oral Defense ~11/17 (verify vs 11/15).

## Working title (for reaction, not decision)
"Decentralized Edge Authorization for Industrial Robotics in DIL Environments: Verification Cost and Safety-Stop Latency"
