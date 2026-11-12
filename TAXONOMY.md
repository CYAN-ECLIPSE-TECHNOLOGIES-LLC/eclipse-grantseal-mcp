# Cyan Eclipse Grantseal — scope-taxonomy grammar (published)

**Taxonomy version:** `grantseal-taxonomy/1`

Grantseal compares the scope set sealed at connect against the
scope set captured in the principal's own agent runtime. The
comparison runs under this published grammar (GNT-REQ-010): the
scope-identifier rules, the cross-provider mapping table, and the
verdict rules over them. Any holder of the sealed captures and
this grammar can recompute the verdict with no service access.

## Scope identifiers

A scope identifier is the string a provider presents for a
permission — an OAuth scope, a platform permission name, or a
full scope URI. Identifiers are matched case-insensitively with
surrounding whitespace ignored. Nothing about a scope beyond its
identifier is ever recorded: no resource contents, no call
payloads, no data the scope was exercised on.

## Comparison rules (in order)

1. **Identity.** A scope identifier is equal to itself: the same
   identifier on the grant side and the use side is the same
   scope. No mapping is needed and none is consulted.
2. **Mapping.** Two different identifiers are the same scope only
   when the mapping table below resolves both to the same
   canonical scope. A scope *renamed* between grant and use is
   resolved by this rule — or not at all.
3. **No silent equation.** An exercised scope that is neither in
   the sealed grant nor resolvable under the mapping table is
   **unresolvable**: the verdict on it is UNVERIFIABLE. It is
   never quietly passed, and it is never named out-of-scope on
   evidence the grammar cannot support (GS-C7).

## Mapping table — taxonomy v1

Canonical scopes are the taxonomy's own identifiers (right
column). Presented identifiers are grouped by the canonical scope
they resolve to.

| Canonical | Presented identifiers that resolve to it |
|---|---|
| `mail.read` | `https://www.googleapis.com/auth/gmail.readonly` · `gmail.readonly` · `Mail.Read` |
| `mail.send` | `https://www.googleapis.com/auth/gmail.send` · `gmail.send` · `Mail.Send` |
| `mail.modify` | `https://www.googleapis.com/auth/gmail.modify` · `gmail.modify` · `Mail.ReadWrite` |
| `files.read` | `https://www.googleapis.com/auth/drive.readonly` · `drive.readonly` · `Files.Read` |
| `files.write` | `https://www.googleapis.com/auth/drive.file` · `drive.file` · `Files.ReadWrite` |
| `calendar.read` | `https://www.googleapis.com/auth/calendar.readonly` · `calendar.readonly` · `Calendars.Read` |
| `calendar.write` | `https://www.googleapis.com/auth/calendar.events` · `calendar.events` · `Calendars.ReadWrite` |
| `contacts.read` | `https://www.googleapis.com/auth/contacts.readonly` · `contacts.readonly` · `Contacts.Read` |
| `store.products.read` | `read_products` |
| `store.products.write` | `write_products` |
| `store.orders.read` | `read_orders` |
| `store.orders.write` | `write_orders` |

A canonical identifier presented directly (for example a grant
recorded as `mail.read`) resolves to itself.

## Verdict rules

- **Use diff** (grant seal + a principal-runtime use capture,
  Class F): every exercised scope inside the sealed grant →
  **WITHIN-GRANT**. An exercised scope known to the taxonomy but
  outside the grant → **OUT-OF-SCOPE-USE**, naming it. An
  unresolvable exercised scope → **UNVERIFIABLE**, naming it.
  Use is diffed against the *original* sealed grant;
  renewal-added scopes are witnessed by the renewal verdict and
  are never silently absorbed into the baseline.
- **Renewal diff** (a renewal grant as presented, against the
  original seal): presented scopes that neither appear in the
  original grant nor resolve into it under the rules above →
  **EXPANDED-AT-RENEWAL**, naming them, whether or not they are
  ever exercised. A renewal that adds nothing records a
  no-change marker.
- **Class G** (grant seal only): the only verdict is
  **GRANT-SEALED**. No use verdict is mintable for a Class G
  record, in this grammar or any tool surface.

## Versioning

Every verdict names its taxonomy version. A taxonomy revision
adds a new version; it never retro-alters a minted verdict, and
recomputation runs under the version the verdict names (GS-C7).
