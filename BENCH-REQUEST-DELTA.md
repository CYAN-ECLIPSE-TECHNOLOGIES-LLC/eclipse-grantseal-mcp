PROPRIETARY — CYAN ECLIPSE TECHNOLOGIES LLC · COMPANY INTELLECTUAL PROPERTY

# (INT — INTERNAL) BENCH REQUEST — Cyan Eclipse Grantseal v0.1.0 (build delta)

- Filed: 2026-11-11 · Seat: builder lane (Grantseal build 2 of the Argus trio)
- Subject: Cyan Eclipse Grantseal v0.1.0 — repo `CYAN-ECLIPSE-TECHNOLOGIES-LLC/eclipse-grantseal-mcp`, maintenance home Shard E `/home/witness/app-family/cyan-eclipse-grantseal`
- Spec of record: SPEC-GRANTSEAL.md (GNT-REQ-001…016; Loom project 33, req ids 1793–1808, CANDIDATE, verdicts not-run)
- Gate: argus-gate-grantseal-20261111.md — PASS-WITH-CONDITIONS (GS-C1…GS-C9)
- Builder evidence (NOT a verdict): unit suite 48/48 on the droplet + MCP smoke PASS; transcript `evidence/TRANSCRIPT-20261111.txt`

## Claims for independent verification (spec §6, restated)

- **C1 / GS-B1 (GNT-REQ-002(ii), GNT-REQ-010):** fixtures where exercised scope exceeds the sealed grant verdict OUT-OF-SCOPE-USE naming the exercised scopes; within-grant controls verdict WITHIN-GRANT — 100% of fixtures, including cross-provider fixtures judged under the published mapping table in TAXONOMY.md.
- **C2 / GS-B2 (GNT-REQ-002(iii), GNT-REQ-013):** a verifier holding only the two sealed captures (Class F) or the grant capture (Class G) + the published taxonomy grammar reproduces the verdict with no service access.
- **C3 / GS-B3 (GNT-REQ-002, GNT-REQ-011, GNT-REQ-004):** Class G records provably cannot mint use verdicts under any API path (store-level and MCP-level attempts both refused + receipted); below-standard captures verdict UNVERIFIABLE in 100% of cases; a use capture offered against a Class G grant at recomputation is not graded.
- **C4 / GS-B4 (GNT-REQ-005):** the store, inspected directly, contains only the §2 field set — no tokens, keys, credentials (in any form, digests included), payloads, or resource contents; surplus input fields are never retained.
- **C5 / GS-B5, first half (GNT-REQ-012):** renewal fixtures adding scopes verdict EXPANDED-AT-RENEWAL naming them; renamed-scope renewals resolve under the mapping rules and are not expansions; every renewal is diffed against the original seal (a second renewal re-presents an already-added scope and still names it); no-change renewals record the marker with no metering event.
- **C6 / GS-B5, second half (GNT-REQ-007):** verdicts name their taxonomy version; a taxonomy revision (a v2 mapping registered after minting) leaves minted verdicts byte-identical and v1-pinned recomputation unchanged.
- **C7 / ADV-1 (GNT-REQ-004, GS-K1 guard):** a use capture whose provenance is a connector-exported audit log (party-kept, connector-graded), or a relay of one, or an unattested/forged capture, is rejected on provenance, the rejection receipted, and no use verdict is mintable in that configuration across all API paths — the record caps at GRANT-SEALED or UNVERIFIABLE.
- **C8 / ADV-2 (GNT-REQ-013, GNT-REQ-005, GS-K2):** credential-shaped inputs — an access token, an API key, and a digest-only token field (`token_digest`) — are refused by every tool, the refusals receipted, and zero custody records are created; a connector class observable only by holding its tokens is refused as out of scope.
- **C9 (GNT-REQ-014):** the receipt journal verifies end-to-end; a tampered record and a truncated export (chain-head mismatch) are both detected; a tampered store fails closed at load.
- **C10 (GNT-REQ-015, GNT-REQ-013, GNT-REQ-009):** metering charges exactly one op per grant seal and per use-window diff; renewals (changed or not), UNVERIFIABLE captures, rejections, refusals, recompute, and check never meter; the ledger records event class + count only. The MCP tool inventory equals SPEC §4.1 exactly; `grantseal_check` reveals verdict class + scope names only; no §5 banned term appears on any output surface.

## Icon election note — 2026-11-12

The product icon (`branding/icon.svg`, promoted from the v2 candidate) was **elected by the owner 2026-11-12** on the human-verified renders, class MARGINAL (48 px legible · 32 px marginal). The **formal Icongate check is still owed** when the Icongate tool lands — no gate verdict is claimed here.

## Fences the bench is asked to hold the build to

Principal-side witnessing only — no provider-log verdicts, no claims over provider-internal use, no credential custody in any form (digests included), no enforcement surface, no cross-principal aggregation. Claims stay **bench-pending** until Verity's verdict lands; builder tests are not evidence.

© Cyan Eclipse Technologies LLC — Proprietary · Company Intellectual Property
