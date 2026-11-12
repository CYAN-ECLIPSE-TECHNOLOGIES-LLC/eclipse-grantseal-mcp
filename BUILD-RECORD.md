PROPRIETARY — CYAN ECLIPSE TECHNOLOGIES LLC · COMPANY INTELLECTUAL PROPERTY

# (INT — INTERNAL) BUILD RECORD — Cyan Eclipse Grantseal v0.1.0

- Built: 2026-11-11 · Build authority: owner commission 2026-11-11 17:08 PT (Argus trio builds, serial per P-2: Routeseal → Grantseal → Darkseal; Routeseal built + bench-filed first — repo eclipse-routeseal-mcp @ 7b351bc). GNT-REQ-001 is satisfied by that commission; the SPEC itself conferred no build slot.
- Spec of record: SPEC-GRANTSEAL.md (this repo) · Gate: argus-gate-grantseal-20261111.md, PASS-WITH-CONDITIONS, narrowings binding.
- Estate: maintenance home Shard E `/home/witness/app-family/cyan-eclipse-grantseal` · GitHub `CYAN-ECLIPSE-TECHNOLOGIES-LLC/eclipse-grantseal-mcp` (full MIT LICENSE in the first commit).
- Shape: stdlib-only Python MCP server over stdio (`server.py`), pure taxonomy/verdict engine (`logic.py`), store/provenance/receipt/metering layer (`grantseal.py`). Exactly the seven §4.1 tools.

## What was built, per requirement

- GNT-REQ-002 — three-part mechanism held jointly: grant sealing at connect through the principal-side connect flow · exercised-scope capture + diff verdict under the published scope-taxonomy grammar (TAXONOMY.md, `grantseal-taxonomy/1`) · stateless third-party recomputation (`grantseal_recompute`). Class F / Class G discipline enforced in the API: Class G mints GRANT-SEALED only.
- GNT-REQ-003 — no listing, quote, pilot, or checkout artefact exists; metering is event-class counts only (no price row adopted; PC-8 pattern fit is a gate fact, not a build feature).
- GNT-REQ-004 — minimum sealed bundle per class enforced; below-standard use captures verdict UNVERIFIABLE; use evidence arrives only via the principal-runtime channel (source + per-runtime HMAC attestation + binding to the grant seal); provider-log and relay captures rejected + receipted (ADV-1).
- GNT-REQ-005 — store field sets are exactly the §2 sets (asserted in code + tests for grant, use, and renewal records); no tokens, keys, or credentials in any form, including as digests; no resource contents, no call payloads; extra input fields are never retained.
- GNT-REQ-006 — no cross-principal aggregation code path or tool exists (inventory test).
- GNT-REQ-007 — every verdict names its taxonomy version; a taxonomy revision never retro-alters a minted verdict (byte-identical test); renamed scopes resolve by the published mapping rules or verdict UNVERIFIABLE on that scope — never silently equated.
- GNT-REQ-008 — WATCH.md records the GS-C8 trigger class; reviewed at build, no triggering shipment known.
- GNT-REQ-009 — claim line verbatim in README + seal tool description; §2 verdict vocabulary only; banned-term scan in the suite.
- GNT-REQ-010 — taxonomy grammar + cross-provider mappings published (TAXONOMY.md) and carried in code as the versioned registry; unmapped-scope fixtures verdict UNVERIFIABLE in 100% of cases.
- GNT-REQ-011 — Class G is structurally incapable of a use verdict: `grantseal_capture_use` against a Class G record is refused + receipted at the store layer and the API layer, and recomputation over a Class G capture never grades an offered use capture.
- GNT-REQ-012 — every renewal is diffed against the ORIGINAL seal at presentation; added scopes verdict EXPANDED-AT-RENEWAL naming them whether or not exercised; no-change renewals record the marker and never meter; renewal-added scopes are never silently absorbed into the use-diff baseline.
- GNT-REQ-013 — tool inventory == §4.1 exactly; `grantseal_check` reveals the verdict class + scope names only; recompute runs with no service state; every tool's arguments pass the credential gate first — credential-shaped inputs (including digest-shaped keys such as `token_digest`) are refused + receipted (ADV-2).
- GNT-REQ-014 — hash-chained receipt journal, one receipt per grant seal, use capture, renewal record, and rejection/refusal; exports carry the chain head; tamper + truncation detected; a tampered store fails closed at load.
- GNT-REQ-015 — one metered op per grant seal and per use-window diff; renewals (changed or not), UNVERIFIABLE captures, rejections, refusals, recompute, and check never meter; ledger = class + count only.
- GNT-REQ-016 — branding applied at creation (branding/BRANDING.md): composite wordmark, canonical theme tokens, server identity surfaces. **Icon: DRAFT candidate only (branding/icon-candidate.svg), NOT approved, NOT shipped, NOT public — owner approval is the outstanding gate.**

## Verification (builder-side; bench verdict is Verity's)

- Unit suite: **48/48 PASS** on the droplet (python3 -m unittest, tests/test_grantseal.py; each test names its requirement / bench claim).
- MCP smoke over real stdio JSON-RPC: **PASS** (tools list · GRANT-SEALED · WITHIN-GRANT · OUT-OF-SCOPE-USE · provider-log rejection · Class G use capture refused · EXPANDED-AT-RENEWAL · check · export · recompute reproduced · credential input refused). Transcript: evidence/TRANSCRIPT-20261111.txt.

## What this build does NOT do (gate narrowings, honored by construction)

Two-class discipline (Class F mints diffs, Class G is grant-only) · NO credential custody of any kind — including no credential digests/hashes held as custody; credential-shaped inputs are refused, never stored · no provider-log review (party-kept logs are claims, not witnessing) · no verdicts over provider-internal use the principal's runtime cannot see · no enforcement (no blocking, revoking, or scope policing) · no cross-principal aggregation, statistics, or feeds · no listing, directory submission, public launch, or pricing/checkout wiring.

## Open items / gaps

- Icon owner approval outstanding (draft candidate only).
- TM screen for the name (GS-CQ-3) and counsel queue GS-CQ-1/2 remain open; name stays provisional.
- Slate ETO-12 (tkt-b54a8b4a1e97): this seat's Slate API probe was rejected — "authentication failed: no valid directory session; state unchanged" (same standing limitation recorded by sibling lanes; no transition forced, SLT-3 respected). Comment text for ETO-12, ready for the main seat to post verbatim:
  - Progress: "Grantseal build started 2026-11-11 under owner commission 17:08 PT (Argus trio serial order: Routeseal → Grantseal → Darkseal). Building to SPEC-GRANTSEAL GNT-REQ-001…016 on Shard E; GitHub repo eclipse-grantseal-mcp."
  - Completion: "Grantseal v0.1.0 build complete 2026-11-11: suite 48/48 + MCP smoke PASS on droplet; GitHub == droplet; BENCH-REQUEST-DELTA filed (claims C1–C10 ← GS-B1…B5 + ADV-1/2), bench-pending; two-class discipline + no-credential-custody narrowings honored; icon draft candidate only (owner approval outstanding); no listing/launch. Record: BUILD-RECORD.md in repo."
- Loom verifications for req 1793–1808 remain not-run (bench will move them; nothing fabricated here).

© Cyan Eclipse Technologies LLC — Proprietary · Company Intellectual Property
