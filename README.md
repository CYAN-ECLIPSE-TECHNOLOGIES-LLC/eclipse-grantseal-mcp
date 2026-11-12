# Cyan Eclipse Grantseal

**Powered by Cyan Eclipse Technologies** — https://cetech.ai

Grantseal seals the exact permissions an agent or app was
granted at connect time, and the permissions it actually
exercised as captured in your own agent runtime. If it used a
scope it was never granted — or a renewal quietly added scopes —
the sealed record names them, and anyone can recompute the
verdict from the record itself.

Cyan Eclipse Grantseal is a Model Context Protocol (MCP) server.
It witnesses scope grants from the principal's side of the seam:
the buyer instruments their own connect flow and their own agent
runtime — no connector cooperation is required. At connect, the
connect flow presents the grant as accepted: the granted scope
set, the connector identity, the agent identity. Grantseal seals
that bundle and stamps the record with its integration class.

Two classes, kept honest by construction:

- **Class F (full)** — grant seal + exercised-scope capture from
  the principal's own agent runtime. Mints diff verdicts:
  **WITHIN-GRANT**, or **OUT-OF-SCOPE-USE** naming the exercised
  scopes outside the sealed grant.
- **Class G (grant only)** — grant seal alone, where no runtime
  capture exists for that connector class. Mints **GRANT-SEALED**
  and provably cannot mint a use verdict.

Renewals are witnessed at the moment they are presented: a
renewal grant is diffed against the original seal, and added
scopes verdict **EXPANDED-AT-RENEWAL** naming them, whether or
not they are ever exercised. A capture that cannot be resolved
under the published scope-taxonomy grammar (`TAXONOMY.md`)
verdicts **UNVERIFIABLE** — a state of the evidence, never a
party's fault. Use evidence arrives only from the principal-side
runtime capture; records computed from a provider's own logs are
not witnessing, and captures of that provenance are rejected.

Grantseal is a witness, not an enforcement point: it never
blocks a call, revokes a token, or polices a scope. Its records
may inform a decision the principal takes elsewhere.

## Tools

| Tool | What it does |
|---|---|
| `grantseal_seal_grant` | Seal the scope granted at connect, as presented by the principal-side connect flow. Metered: one op per grant seal (PC-8 pattern). |
| `grantseal_capture_use` | Present an exercised-scope capture from the principal's own agent runtime (Class F only) and mint the diff verdict. Metered: one op per use-window diff; UNVERIFIABLE captures do not meter. |
| `grantseal_seal_renewal` | Seal a renewal grant and diff it against the original seal at presentation. Unmetered. |
| `grantseal_get_verdict` | The full verdict record: verdict, use-verdict facet, named out-of-scope and added scopes, taxonomy version, receipt refs. Unmetered. |
| `grantseal_check` | Counterparty view: verdict class and the names of out-of-scope or added scopes only. Unmetered. |
| `grantseal_recompute` | Recompute a verdict from exported captures + the taxonomy version, with no service state. Unmetered. |
| `grantseal_export_captures` | Export the sealed captures with the receipt-chain head for independent recomputation. Unmetered. |

No tool accepts a token, key, or credential as an input in any
form; a credential-shaped input is refused and the refusal is
receipted.

## Custody

The store carries only the sealed scope field set: granted and
exercised scope identifiers under the taxonomy, connector and
agent identities as presented, timestamps, seals, and the
verdict with its named grammar basis. No access tokens, refresh
tokens, API keys, or credentials are captured, held, or sealed
in any form — not even as digests. No resource contents, no call
payloads, no data the scopes were exercised on. Records serve
the principal whose side sealed them; there is no
cross-principal aggregation surface. Every grant seal, use
capture, renewal record, and verdict appends one record to a
hash-chained receipt journal, verified at load; a store that
fails verification fails closed.

## Status

v0.1.0 · built · **bench-pending** (independent bench requested;
builder tests are not a bench verdict) · name "Cyan Eclipse
Grantseal" is provisional pending trademark screen · not listed,
not offered for sale — review-first standing posture.

## Run

```sh
python3 server.py   # MCP over stdio
```

Environment: `ECLIPSE_GRANTSEAL_STATE` (record store path),
`ECLIPSE_GRANTSEAL_RUNTIME_KEYS` (principal-side runtime channel
keys, JSON — principal-held in production; the keys in `keys/`
are test fixtures only).

## License

MIT — see `LICENSE`.
