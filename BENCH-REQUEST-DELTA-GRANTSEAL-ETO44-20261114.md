PROPRIETARY — CYAN ECLIPSE TECHNOLOGIES LLC · COMPANY INTELLECTUAL PROPERTY

# (INT — INTERNAL) BENCH REQUEST DELTA — Cyan Eclipse Grantseal, ETO-44 licence-checked metering

- Filed: 2026-11-14 · Seat: ETO-44 metering lane (Leg 3) · Slate: ETO-44 tkt-b24d8dbdffd3 (Grantseal parent ETO-12 tkt-b54a8b4a1e97)
- Subject: Grantseal per-op licence-checked metering ($0.25/op, PC-8), repo CYAN-ECLIPSE-TECHNOLOGIES-LLC/eclipse-grantseal-mcp, maintenance home Shard E /home/witness/app-family/cyan-eclipse-grantseal
- Commits: cf7ec63 (metering leg) · 01ac56f (legacy-baseline fix) · aaba885 (proof re-run tolerance), all pushed to main
- Scope: fixture/test only. No real customer licences, no Stripe, no real charges. Nothing is claimed production, live-for-customers, or certified. Builder evidence below is NOT a verdict.
- HARD FENCE HELD: Darkseal was not touched in any way.

## What changed

- licence_gate.py (new): ACT/Folio L-3 pattern gate vs the deployed License Server (Shard E 127.0.0.1:8799, tenant cet fixture scope). Activation-once with install_id binding, check-in per priced op, LICENSE_VALID/LICENSE_GRACE only; check-in presents activation token + artefact hash only.
- metering_journal.py (new): ACT/SCA-pattern append-only hash-chained JSONL. One record per priced op that meters under the pre-existing classes (grant_seal per grant seal; use_diff per use-window diff with verdict WITHIN-GRANT/OUT-OF-SCOPE-USE), payload {product, op, subject, unit_price_minor 25, currency USD, fixture true, licence_state}.
- grantseal.py: Store takes optional licence_gate; seal_grant and capture_use check the gate (credential gate still runs first, preserving ADV-2 receipted refusals) before any record/receipt/metering; existing metering counts now also append metering-journal records at the exact pre-existing increment points. seal_renewal is never metered and is not licence-gated (pre-existing spec behaviour). Metering journal is a separate file: it never feeds record seals or verdicts; the F-1 seal-verification cure is untouched.
- Load behaviour: metering journal chain verified at load, fails closed on tamper. Pre-ETO-44 counts become a persisted metering_baseline at load: reconciled == (journal counts + baseline == store counts); a journal recording ops the store never counted fails closed. (This fix was driven by a real reload failure of the repo's own legacy data state during this leg; suites were then run twice consecutively green.)
- server.py: wires a gate whenever GRANTSEAL_LICENCE_STATE is configured or GRANTSEAL_LICENCE_REQUIRED=1. GAP, stated plainly: an MCP process started with neither env set runs in unconfigured fixture mode (gate absent; metering journal still written) — the ACT core pattern. The bench is asked to judge whether that wiring satisfies ETO-44 or whether default-enforced is required.
- tests/test_licence_metering.py (new, 8 tests): fake-transport gate — valid grant+diff meter + reconcile · no licence refused + unmetered · revoked refused at check-in with reads served · renewal unmetered + ungated · UNVERIFIABLE use = no record · metering-journal tamper fails closed · legacy baseline · reload reconciles. No existing test was modified.
- fixtures/licence_proof.py (new): live proof driver vs the deployed server (see evidence).

## Builder evidence (not a verdict)

- Suite: 64/64 unittest OK on Shard E, run twice consecutively (56 pre-existing + 8 new); smoke.py PASS.
- Live fixture proof (evidence/grantseal-licence-evidence.json in the ETO-44 leg folder; driver in repo fixtures/): all 6 assertions true — grant without licence refused LICENSE_NOT_CONFIGURED · grant seal + use diff with valid fixture licence accepted (GRANT-SEALED + WITHIN-GRANT) · reconcile ops_counted 2 == journal_records 2 (grant_seal 1 + use_diff 1; metering journal seqs 1–2, chain head in evidence) · after revoke, next priced op (use capture) refused LICENSE_REVOKED · refused ops unmetered · read after revoke served.
- License Server journal (tenant cet): first proof run counts 144 → 148 (register/tier/mandate/issue) → 150 (revoke); filed evidence is the clean re-run, counts 154 → 156 → 158, fixture licence 8cf252ef-d38c-4a69-a00e-d1fd067fa241 (revoked in the proof). First-run licence 13b5086c-180b-41ef-b22d-b2872438d8ae also revoked in its proof.

## Claims for independent verification

- M1: a priced op with no licence state is refused, creates no record/receipt, and writes no metering record.
- M2: priced ops with a valid fixture licence succeed; metering counts == metering journal records per op class (grant_seal, use_diff), chain verifying.
- M3: after licence revocation, the next priced op is refused LICENSE_REVOKED at check-in; reads remain served.
- M4: pre-existing metering classes unchanged (renewals, UNVERIFIABLE captures, rejections, credential refusals, recompute, check never meter) and the F-1 cure still refuses tampered records at load and in recompute; the credential gate still precedes the licence gate.
- M5: a tampered metering journal fails closed at load; legacy pre-journal counts reconcile via the persisted baseline and cannot hide journal-recorded ops.
- M6: the gate presents only activation token + artefact hash at check-in (no usage/content data), per the Folio L-3 pattern.

© Cyan Eclipse Technologies LLC — Proprietary · Company Intellectual Property
