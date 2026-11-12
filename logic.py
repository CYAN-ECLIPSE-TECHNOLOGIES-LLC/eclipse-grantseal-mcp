#!/usr/bin/env python3
# Cyan Eclipse Grantseal — scope-taxonomy grammar + verdict engine
# (SPEC-GRANTSEAL sections 2, 3; gate GS-C4/C7).
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""Pure verdict logic. Holds no state and reads no store: given a
sealed grant's scope set and an exercised scope set captured on the
principal's side, it mints exactly one verdict from the fixed
grammar:

  WITHIN-GRANT · OUT-OF-SCOPE-USE · EXPANDED-AT-RENEWAL ·
  GRANT-SEALED · UNVERIFIABLE

Scope comparison runs under the published scope-taxonomy grammar
(TAXONOMY.md, `grantseal-taxonomy/1`):

  - identity rule: a scope identifier is equal to itself — the same
    identifier on both sides is the same scope, no mapping needed;
  - mapping rule: two different identifiers are the same scope
    only when the published mapping table resolves both to the
    same canonical scope;
  - no silent equation: an exercised scope that is neither in the
    grant nor resolvable under the mapping table is UNRESOLVABLE —
    the verdict on it is UNVERIFIABLE, never a quiet pass and never
    an out-of-scope naming the evidence cannot support (GS-C7,
    GNT-REQ-010).

Use is diffed against the ORIGINAL sealed grant. Renewal-added
scopes are witnessed by the renewal verdict; they are never
silently absorbed into the baseline (GNT-REQ-012).

Verdicts name facts only — scope identifiers and the grammar basis
that resolved or failed to resolve them. No string in this module
speaks to any person's agreement, any party's intent, or any
provider-internal behaviour (gate GS-C9 / spec P5).
"""
import hashlib
import json

TAXONOMY_VERSION = "grantseal-taxonomy/1"

VERDICTS = ("WITHIN-GRANT", "OUT-OF-SCOPE-USE",
            "EXPANDED-AT-RENEWAL", "GRANT-SEALED", "UNVERIFIABLE")

# The published cross-provider scope mapping table for taxonomy v1
# (TAXONOMY.md carries the same table; the two are kept in step).
# Keys are scope identifiers as presented by a provider (matched
# case-insensitively, surrounding whitespace ignored); values are
# the taxonomy's canonical scope identifiers.
_MAPPINGS_V1 = {
    # mail
    "https://www.googleapis.com/auth/gmail.readonly": "mail.read",
    "gmail.readonly": "mail.read",
    "mail.read": "mail.read",
    "https://www.googleapis.com/auth/gmail.send": "mail.send",
    "gmail.send": "mail.send",
    "mail.send": "mail.send",
    "https://www.googleapis.com/auth/gmail.modify": "mail.modify",
    "gmail.modify": "mail.modify",
    "mail.readwrite": "mail.modify",
    # files
    "https://www.googleapis.com/auth/drive.readonly": "files.read",
    "drive.readonly": "files.read",
    "files.read": "files.read",
    "https://www.googleapis.com/auth/drive.file": "files.write",
    "drive.file": "files.write",
    "files.readwrite": "files.write",
    # calendar
    "https://www.googleapis.com/auth/calendar.readonly":
        "calendar.read",
    "calendar.readonly": "calendar.read",
    "calendars.read": "calendar.read",
    "https://www.googleapis.com/auth/calendar.events":
        "calendar.write",
    "calendar.events": "calendar.write",
    "calendars.readwrite": "calendar.write",
    # contacts
    "https://www.googleapis.com/auth/contacts.readonly":
        "contacts.read",
    "contacts.readonly": "contacts.read",
    "contacts.read": "contacts.read",
    # store
    "read_products": "store.products.read",
    "write_products": "store.products.write",
    "read_orders": "store.orders.read",
    "write_orders": "store.orders.write",
}

# Taxonomy registry: version -> mapping table. A revision adds a
# new version; minted verdicts keep the version they name and are
# never recomputed under a later one (GS-C7).
TAXONOMIES = {TAXONOMY_VERSION: _MAPPINGS_V1}


class LogicError(Exception):
    pass


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def digest_obj(obj) -> str:
    return sha(canon(obj))


def _norm(scope_id) -> str:
    return str(scope_id).strip().lower()


def canonical(scope_id, taxonomy_version: str = TAXONOMY_VERSION):
    """The canonical scope a presented identifier resolves to
    under the named taxonomy version, or None when the taxonomy
    carries no mapping for it."""
    table = TAXONOMIES.get(taxonomy_version)
    if table is None:
        return None
    return table.get(_norm(scope_id))


def _resolve_into(scope_id, granted_norm, granted_canonicals,
                  taxonomy_version):
    """Resolve one presented scope against a granted set.
    Returns (status, basis): status is "identity" (same identifier
    in the grant), "mapping" (resolves to a granted canonical), or
    "outside" (known to the taxonomy, not in the grant), or
    "unresolvable" (unknown to the taxonomy, not in the grant)."""
    if _norm(scope_id) in granted_norm:
        return "identity", "identity"
    can = canonical(scope_id, taxonomy_version)
    if can is not None and can in granted_canonicals:
        return "mapping", "mapping:" + can
    if can is not None:
        return "outside", "mapping:" + can
    return "unresolvable", "unmapped:" + str(scope_id)


def _grant_index(granted_scopes, taxonomy_version):
    granted_norm = {_norm(s) for s in granted_scopes}
    canonicals = set()
    for s in granted_scopes:
        can = canonical(s, taxonomy_version)
        if can is not None:
            canonicals.add(can)
        # A granted identifier that IS a canonical form counts too.
        canonicals.add(_norm(s))
    return granted_norm, canonicals


def diff_use(granted_scopes, exercised_scopes,
             taxonomy_version: str = TAXONOMY_VERSION) -> dict:
    """Diff an exercised scope set against the original sealed
    grant (GNT-REQ-002(ii)). Returns the verdict fields:
    verdict · out_of_scope_scopes · unresolvable_scopes ·
    grammar_basis · taxonomy_version."""
    base = {"taxonomy_version": taxonomy_version,
            "out_of_scope_scopes": [], "unresolvable_scopes": [],
            "grammar_basis": None}
    if taxonomy_version not in TAXONOMIES:
        return {**base, "verdict": "UNVERIFIABLE",
                "grammar_basis": "unknown_taxonomy_version"}
    granted_norm, canonicals = _grant_index(granted_scopes,
                                            taxonomy_version)
    bases = []
    for scope in exercised_scopes:
        status, basis = _resolve_into(scope, granted_norm,
                                      canonicals, taxonomy_version)
        if status in ("identity", "mapping"):
            bases.append(basis)
        elif status == "outside":
            base["out_of_scope_scopes"].append(scope)
        else:
            base["unresolvable_scopes"].append(scope)
    if base["unresolvable_scopes"]:
        return {**base, "verdict": "UNVERIFIABLE",
                "grammar_basis": "unmapped_scope"}
    if base["out_of_scope_scopes"]:
        return {**base, "verdict": "OUT-OF-SCOPE-USE",
                "grammar_basis": "set_difference"}
    base["grammar_basis"] = "mapping" if any(
        b.startswith("mapping:") for b in bases) else "identity"
    return {**base, "verdict": "WITHIN-GRANT"}


def diff_renewal(granted_scopes, renewed_scopes,
                 taxonomy_version: str = TAXONOMY_VERSION) -> dict:
    """Diff a renewal grant set, as presented, against the
    ORIGINAL seal (GNT-REQ-012). A presented scope is added when
    it neither appears in the original grant nor resolves into it
    under the mapping rules — a scope renamed between the original
    grant and the renewal is resolved by the mapping, never
    reported as an expansion it is not."""
    base = {"taxonomy_version": taxonomy_version,
            "added_scopes": []}
    if taxonomy_version not in TAXONOMIES:
        return {**base, "verdict": "UNVERIFIABLE",
                "grammar_basis": "unknown_taxonomy_version"}
    granted_norm, canonicals = _grant_index(granted_scopes,
                                            taxonomy_version)
    for scope in renewed_scopes:
        status, _ = _resolve_into(scope, granted_norm, canonicals,
                                  taxonomy_version)
        if status in ("outside", "unresolvable"):
            base["added_scopes"].append(scope)
    if base["added_scopes"]:
        return {**base, "verdict": "EXPANDED-AT-RENEWAL",
                "grammar_basis": "set_difference"}
    return {**base, "verdict": "WITHIN-GRANT", "no_change": True,
            "grammar_basis": "no_change_marker"}
