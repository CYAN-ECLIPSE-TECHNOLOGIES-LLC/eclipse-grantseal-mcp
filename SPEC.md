PROPRIETARY — CYAN ECLIPSE TECHNOLOGIES LLC · COMPANY INTELLECTUAL PROPERTY

# (IP — PROPRIETARY IP) SPEC — Cyan Eclipse Grantseal v0.1 (DRAFT — spec only)

- Gate: argus-gate-grantseal-20261111.md — PASS-WITH-CONDITIONS (GS-C1…GS-C9 · kill criteria GS-K1…GS-K4 · counsel queue GS-CQ-1…GS-CQ-3). Every gate condition is carried into §3 as a numbered requirement, verbatim in force; the gate's FAIL shapes are carried into §5 as spec-level prohibitions. Where the suggestion text (Argus daily batch 2026-11-11, entry 9) conflicts with the gate, the GATE wins and the conflict is noted (§1, §9).
- Commissioned: owner tap 2026-11-11 16:57 PT ("Commission specs for all three, gate conditions as spec requirements").
- Status: SPEC ONLY. No build, no listing, no external contact is authorized by this document. Build slot: P-2 — builds serialize behind the current flagship, on the owner's build word (GNT-REQ-001).
- Requirements: GNT-REQ-001…016, filed as Loom CANDIDATEs (Loom project "Cyan Eclipse Grantseal") with verifications at filing, verdicts not-run, NOT baselined — ratification is the owner's act.
- Name: "Cyan Eclipse Grantseal" is a PROVISIONAL working name, internal until the TM screen rides the counsel package (GS-CQ-3); composite form mandatory on every surface.

## (IP — PROPRIETARY IP) 1. Purpose and product definition

- **Buyer:** desks and platform operators connecting agents and tools to accounts, stores, and data on behalf of principals — every connection they broker starts with a scope grant, and the mandate chain's missing half is proof of what a connector was *given* and what it *took*.
- **Job:** seal the exact scope granted at connect time from the principal-side connect flow, with a witness that is not the connector; capture the scope actually exercised in the principal's own agent runtime; and mint a diff verdict, so scope creep is a sealed set-difference held by the principal — never a log review the connector grades itself.
- **Vantage — the gate's narrowing binds (GS-C4):** the grant half is witnessed at the principal-side connect flow (the grant as presented and accepted, sealed at connect); the use half is witnessed only where the principal's own agent runtime captures exercised scope. A provider's internal use of a granted scope, invisible to the agent runtime, is outside the vantage and no surface may claim it. **Conflict noted:** the suggestion's unqualified "the permissions it actually exercised" reads wider than this; the gate narrowed it, the gate wins.
- **Integration classes (two honest products):** **Class F (full)** — grant seal + principal-side runtime use capture: mints diff verdicts. **Class G (grant only)** — grant seal alone, where no runtime capture is available for that connector class: mints GRANT-SEALED and **provably cannot** mint a use verdict. Any surface that lets a Class G record imply use coverage is a prohibited shape (§5 P1).
- **Renewal is a first-class event:** a renewal or re-connect grant is diffed against the original seal at the moment it is presented; added scopes verdict EXPANDED-AT-RENEWAL naming them, whether or not they are ever exercised.
- **Adoption shape:** the buyer instruments their own connect flow and agent runtime — one buyer's decision, no connector cooperation required.
- **Sibling separation:** distinct from Ratchet (tightening session permissions *mid-session* — Grantseal holds the connect-time grant against everything exercised under it, including at renewal) and from Consent (a *person's* consent record — Grantseal witnesses a technical scope grant against technical use and takes no position on what any person agreed to).

## (IP — PROPRIETARY IP) 2. Sealed-record data model

- **Scope-taxonomy grammar:** scope identifiers are expressed under a published scope-taxonomy grammar with cross-provider scope mappings. The grammar is published with the product (GNT-REQ-010). A scope renamed between grant and use is handled by the grammar's mapping rules or verdicts UNVERIFIABLE on that scope — never silently equated (GS-C7).
- **Grant seal record:** granted scope set as presented at connect (scope identifiers under the taxonomy) · connector identity as presented · agent identity as presented · integration class (F | G) · connect timestamp · seal. Sealed at connect through the principal-side connect-flow hook.
- **Use capture record (Class F only):** exercised scope set as captured in the principal's own agent runtime over a stated use window · window bounds · runtime attestation and a binding reference to the grant seal. Use evidence arrives only from this capture — never from provider logs (GNT-REQ-004).
- **Renewal record:** the renewal grant set as presented, diffed against the original seal at presentation; the diff (added scopes, or an explicit no-change marker) is sealed with the renewal timestamp.
- **Store field set — the whole store (GS-C5):** granted scope identifiers under the taxonomy · exercised scope identifiers as captured · connector and agent identities as presented · timestamps · seals · verdict + named grammar basis. **No access tokens, refresh tokens, API keys, or credentials in any form — not even as digests. No resource contents, no call payloads, no data the scopes were exercised on. No cross-principal aggregation.**
- **Verdict classes — fixed, exhaustive:** WITHIN-GRANT (every exercised scope was inside the sealed grant) · OUT-OF-SCOPE-USE (names the exercised scopes outside the grant) · EXPANDED-AT-RENEWAL (names the scopes a renewal grant added against the original seal) · GRANT-SEALED (Class G — grant sealed; no use verdict is mintable for this record) · UNVERIFIABLE (capture below the GS-C4 standard; a state of the evidence, never a connector's fault).
- **Taxonomy versioning:** verdicts name their scope-taxonomy grammar version; a taxonomy revision never retro-alters a minted verdict.

## (IP — PROPRIETARY IP) 3. Requirements

- **GNT-REQ-001 (P-2 sequence — GS-C1):** this spec confers no build slot. Any build of Grantseal serializes behind the current flagship and starts only on the owner's build word.
  *Verification:* inspection — the spec, gate, and Slate records state no build authorization; PASS iff no build artefact claims authority from this spec.
- **GNT-REQ-002 (three-part mechanism + two-class discipline — GS-C2):** the product shall hold jointly (i) grant sealing at connect, (ii) exercised-scope capture with a diff verdict under the published scope-taxonomy grammar, (iii) third-party recomputability — and the Class F / Class G discipline shall be enforced in the API: Class G records shall mint GRANT-SEALED only and shall be incapable of minting a use verdict. Dropping (ii), (iii), or the class discipline re-gates the product.
  *Verification:* test — Class F fixtures mint diff verdicts; Class G fixtures mint GRANT-SEALED and no use verdict under any API path (bench claim GS-B3).
- **GNT-REQ-003 (K6 / review-first + pricing boundary — GS-C3):** no listing, quote, or external pilot shall occur until the Assert written answers are filed and read and the listing passes owner review. Metering boundaries bind: the charge events are the grant seal and each use-window diff; re-verification and counterparty recomputation of an existing verdict are unmetered; GRANT-SEALED renewals that change nothing and UNVERIFIABLE captures do not meter.
  *Verification:* inspection — listing/quote artefacts (none may exist pre-clearance) + metering configuration against §4.3.
- **GNT-REQ-004 (capture standard + vantage — GS-C4):** the minimum sealed bundle per connector class is the §2 grant bundle plus, for Class F, the §2 use-capture bundle; below it, UNVERIFIABLE is the only mintable verdict. Use evidence shall come only from principal-side runtime capture — never from provider logs or provider-exported records. Every surface shall claim grant-vs-use *as captured on the principal's side* only.
  *Verification:* test — below-standard fixtures verdict UNVERIFIABLE in 100% of cases; log-derived capture fixtures are rejected on provenance (bench claims GS-B3; bench ADV-1).
- **GNT-REQ-005 (custody — no credentials, ever — GS-C5):** the store shall contain only the §2 field set. No access tokens, refresh tokens, API keys, or credentials shall be captured, held, or sealed in any form — including as digests presented as observation shortcuts. No resource contents, no call payloads, no cross-principal aggregation. A connector class observable only by holding its tokens is out of scope, not an excuse (GS-K2).
  *Verification:* inspection — direct store inspection (bench claim GS-B4): PASS iff the store contains only the §2 field set and no credential-shaped material in any form.
- **GNT-REQ-006 (aggregation fence — GS-C6):** no connector-aggregate statistics, feeds, or insights surface shall be produced from Grantseal records without the Friction counsel posture applying in full (re-gate). Per-principal records for the principal are the only aggregation.
  *Verification:* inspection — product surface and data-model review finds no cross-principal aggregate artefact or code path.
- **GNT-REQ-007 (taxonomy versioning — GS-C7):** every verdict shall name its scope-taxonomy grammar version; a taxonomy revision shall never retro-alter a minted verdict; a scope renamed between grant and use shall be resolved by the grammar's published mapping rules or verdict UNVERIFIABLE on that scope — never silently equated.
  *Verification:* test — verdicts carry the taxonomy version; revision leaves minted verdicts byte-identical; renamed-scope fixtures follow the mapping rule or verdict UNVERIFIABLE on that scope (bench claim GS-B5, second half).
- **GNT-REQ-008 (incumbent + absorption watch — GS-C8):** if a standard, non-party-verifiable grant-and-use receipt ships natively across major OAuth/agent platforms, the product shall be re-gated before any further build or launch step. Provider-kept audit exports do not trigger this.
  *Verification:* inspection — a watch record naming the trigger class exists and is reviewed at each gate event.
- **GNT-REQ-009 (claim line + verdict grammar + bench — GS-C9):** the honest claim line binds every surface: *"Grantseal seals the exact permissions an agent or app was granted at connect time, and the permissions it actually exercised as captured in your own agent runtime. If it used a scope it was never granted — or a renewal quietly added scopes — the sealed record names them, and anyone can recompute the verdict from the record itself."* The verdict grammar is the §2 fixed set. An independent Verity bench (§6) shall pass before any external pilot; builder tests are not evidence. The name remains provisional + internal until the TM screen; composite form mandatory.
  *Verification:* inspection — every product surface carries only the claim line and the §2 vocabulary; no §5 banned term appears.
- **GNT-REQ-010 (scope-taxonomy grammar + mappings publication):** the scope-taxonomy grammar and its cross-provider scope mappings shall be published with the product, and every verdict shall state its taxonomy version. A scope with no published mapping shall never be silently equated across grant and use.
  *Verification:* test — cross-provider fixtures verdict per the published mappings; unmapped-scope fixtures verdict UNVERIFIABLE on that scope, in 100% of cases.
- **GNT-REQ-011 (class discipline, structural):** Class G records shall be structurally incapable of minting WITHIN-GRANT / OUT-OF-SCOPE-USE / EXPANDED-AT-RENEWAL-from-use: the verdict engine shall require a use-capture reference of Class F provenance (GNT-REQ-004) before any use verdict is computed, enforced at the API layer including adversarial calls.
  *Verification:* test — bench claim GS-B3: adversarial attempts to mint use verdicts from Class G records fail in 100% of attempts.
- **GNT-REQ-012 (renewal witnessing):** every renewal or re-connect grant shall be diffed against the original seal at the moment it is presented; added scopes shall verdict EXPANDED-AT-RENEWAL naming them whether or not they are ever exercised; a renewal that changes nothing shall record a no-change marker and shall not meter.
  *Verification:* test — renewal fixtures adding scopes verdict EXPANDED-AT-RENEWAL naming them; no-change renewals record the marker with no metering event (bench claim GS-B5, first half).
- **GNT-REQ-013 (MCP interface conformance):** the MCP surface shall be exactly the tools of §4.1. `grantseal_check` shall reveal the verdict class and the *names* of out-of-scope or added scopes only; `grantseal_recompute` shall accept the two sealed captures (Class F) or the grant capture (Class G) + taxonomy version and return the recomputed verdict with no service state. All outputs shall carry only the §2 verdict vocabulary and no §5 banned term. No tool shall accept a token, key, or credential as an input in any form.
  *Verification:* test — tool inventory equals §4.1 exactly; recompute runs offline against exported captures; credential-shaped inputs are refused by every tool; output scan finds no banned term.
- **GNT-REQ-014 (receipt-chain integration):** every grant seal, use capture, renewal record, and verdict shall append exactly one record to the product's hash-chained receipt journal (sequence · timestamp · record kind · payload digest · previous-hash link · record hash), and the chain shall verify end-to-end. Exports shall carry the chain head.
  *Verification:* test — chain verification passes on a populated journal; tampered-record and truncated-export fixtures are both detected.
- **GNT-REQ-015 (pricing hooks — PC-8):** metering shall implement the PC-8 Episodic-ops (Keyhold) pattern exactly as gate-confirmed: one op = one grant seal, or one use-window diff against a seal ($0.25 pattern per op); re-verification and recomputation are unmetered; no-change renewals and UNVERIFIABLE captures do not meter. Priced-row adoption is a separate owner act at listing time; this spec adopts no price row.
  *Verification:* test — metering fixtures per event class produce exactly the §4.3 charges and no others.
- **GNT-REQ-016 (branding baseline):** the product shall ship with Cyan Eclipse branding applied completely at creation, as baseline scope: icon · name/wordmark · theme tokens (eclipse-brand-system) · splash/launch surfaces · about/identity surfaces, in the Apple-look × Cyan Eclipse theme and plain, obvious labelling. The icon is subject to individual owner approval before it ships; that approval is the owner's gate at build time and is not discharged by this spec.
  *Verification:* inspection — at build, the brand checklist (icon · wordmark · theme tokens · splash/launch · about/identity) is checked against the brand application standard, with the icon-approval record present.

## (IP — PROPRIETARY IP) 4. Interfaces

### 4.1 MCP tool surface (server: `eclipse-grantseal`)

| Tool | Inputs | Outputs |
|---|---|---|
| `grantseal_seal_grant` | connector_id · agent_id · granted_scopes[] · integration_class (F \| G) | grant_seal_id · receipt_ref · class |
| `grantseal_capture_use` | grant_seal_id · exercised_scopes[] · window_bounds · runtime_attestation | use_capture_id · receipt_ref — Class F only; provider-log provenance rejected (GNT-REQ-004) |
| `grantseal_seal_renewal` | grant_seal_id · renewed_scopes[] | renewal_record_id · verdict (EXPANDED-AT-RENEWAL naming added scopes, or no-change marker) · receipt_ref |
| `grantseal_get_verdict` | grant_seal_id | verdict · out_of_scope_scopes[] (names only) · added_scopes[] (names only) · taxonomy_version · receipt_refs — Class G returns GRANT-SEALED |
| `grantseal_check` | grant_seal_id | verdict · scope names only — counterparty view |
| `grantseal_recompute` | grant_capture · use_capture (Class F) · taxonomy_version | verdict — unmetered; runs with no service state |
| `grantseal_export_captures` | grant_seal_id | captures (scope sets + seals) · chain_head · taxonomy_version |

### 4.2 Receipt chain

Append-only, hash-chained receipt journal in the firm's seal/journal pattern: one receipt per grant seal, use capture, renewal record, and verdict (GNT-REQ-014). Exports carry the chain head. Recomputation (GNT-REQ-002) is defined over the exported captures + the published taxonomy grammar and requires no service access. Grantseal compounds the firm's mandate chain: the mandate says what an agent *may* do; the grant seal records what a connector was *given*; the use capture records what it *took*.

### 4.3 Pricing hooks (PC-8 Episodic ops / Keyhold — pattern fit gate-confirmed; no price row adopted)

Metering events: **one grant seal** and **each use-window diff** against a seal, one charge per op. Non-events (never metered): re-verification · `grantseal_recompute` · `grantseal_check` · no-change renewals (GNT-REQ-012) · UNVERIFIABLE captures. The metering ledger records event class + count only.

## (IP — PROPRIETARY IP) 5. Prohibitions (gate FAIL shapes — spec-level)

- **P1.** No use verdict (WITHIN-GRANT / OUT-OF-SCOPE-USE) from a Class G record, and no surface presenting a Class G record as use coverage (gate §1; GNT-REQ-002/011).
- **P2.** No verdict computed from provider-side logs, provider exports, or any record the connector grades itself (gate §0 FAIL (a); GNT-REQ-004).
- **P3.** No enforcement shape: no blocking calls, revoking tokens, or policing scopes. Grantseal's records may *inform* an enforcement decision by the principal or their IAM; the product itself never takes one (gate §0 FAIL (b)).
- **P4.** No credential or token custody in any form — capture, holding, or sealing of access tokens, refresh tokens, API keys, or credentials, including as digests (gate §0 FAIL (c); GS-K2). A design requiring any of these is killed on sight.
- **P5.** Banned on every surface (GS-C9): "proves consent / the user agreed" · "prevents / blocks scope abuse" · "the connector acted maliciously" · any claim about a connector's behaviour in aggregate · any claim over provider-internal use the agent runtime cannot see.

## (IP — PROPRIETARY IP) 6. Bench plan (future Verity bench — claim-by-claim; builder tests are not evidence)

Starting set = the gate's bench-claim drafts (GS-B1…GS-B5), finalized by Verity, restated as acceptance criteria:

- **GS-B1 — Out-of-scope detection:** fixtures where exercised scope exceeds the sealed grant verdict OUT-OF-SCOPE-USE naming the exercised scopes; within-grant controls verdict WITHIN-GRANT — 100% of fixtures.
- **GS-B2 — Independent recomputation:** a verifier holding only the two sealed captures + the taxonomy grammar reproduces the verdict with no service access.
- **GS-B3 — Class + capture discipline:** Class G records provably cannot mint use verdicts (API-level negative test); below-standard captures verdict UNVERIFIABLE in 100% of cases.
- **GS-B4 — Custody negative test:** the store, inspected directly, contains only the §2 field set — no tokens, keys, credentials, payloads, or resource contents in any form.
- **GS-B5 — Renewal + versioning:** renewal fixtures adding scopes verdict EXPANDED-AT-RENEWAL naming them; no-change renewals verdict WITHIN-GRANT without metering events; verdicts name their taxonomy version and a revision never retro-alters a minted verdict.
- **ADV-1 (adversarial — GS-K1, log-review collapse):** the runtime capture channel is replaced by a connector-exported audit log (party-kept, connector-graded) offered as a "use capture." PASS iff the product rejects it on provenance, receipts the rejection, and no use verdict is mintable in this configuration across all API paths — the record caps at GRANT-SEALED or UNVERIFIABLE.
- **ADV-2 (adversarial — GS-K2, credential-custody bait):** a connector-class fixture whose only observation route requires presenting or holding its access token — including a "digest-only token" submission path. PASS iff the class is refused as out of scope, no tool accepts the credential-shaped input, and zero custody records are created.

## (IP — PROPRIETARY IP) 7. Non-goals (v0.1)

No enforcement (no blocking, revocation, or scope policing) · no consent records (a person's consent is Consent's object) · no provider-log review · no credential or token custody in any form · no cross-principal aggregation · no claims over provider-internal use · no mid-session permission tightening (that is Ratchet's object).

## (IP — PROPRIETARY IP) 8. Branding baseline (standing default — also GNT-REQ-016)

Icon · name/wordmark · theme tokens · splash/launch · about/identity surfaces, applied completely at creation in the Apple-look × Cyan Eclipse theme. The icon-program gate is preserved: the owner approves the Grantseal icon individually before it ships.

## (IP — PROPRIETARY IP) 9. Open items — carried, not resolved

- **TM screen** for "Cyan Eclipse Grantseal" (GS-CQ-3 — counsel; name provisional until cleared).
- **Evidentiary weight** of a sealed OUT-OF-SCOPE-USE or EXPANDED-AT-RENEWAL record in a connector dispute or post-incident review (GS-CQ-1 — counsel).
- **Capture posture** for recording exercised scope inside the principal's own agent runtime — monitoring/consent posture and connector ToS posture across v1 classes (GS-CQ-2 — counsel).
- **Priced-row adoption** at listing (owner act; §4.3 is pattern fit only).
- **K6 / Assert posture** (GNT-REQ-003): no listing, quote, or external pilot until the Assert written answers are filed and read and the listing passes owner review.
- **V1 connector classes** (spec scope call at build time, driven by principal-side capture feasibility — the GS-K1/K2 evidence questions) and **Class G-first sequencing** (a build-time call inside GNT-REQ-002's discipline) — both deliberately left open by the gate (§11).
- **Conflict carried:** the suggestion's pitch ("proves any use outside the granted scope or any silent scope expansion at renewal") is retained only in the narrowed sense of §1 — use *as captured in the principal's own runtime*, and renewal expansion witnessed *at the grant* (gate wins; §5 P2/P5 enforce).

© Cyan Eclipse Technologies LLC — Proprietary · Company Intellectual Property
