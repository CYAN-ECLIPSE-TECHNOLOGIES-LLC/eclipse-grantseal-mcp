#!/usr/bin/env python3
# Cyan Eclipse Grantseal — seal store, runtime provenance, receipt
# chain, metering (SPEC-GRANTSEAL sections 2-4).
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""State layer for the Grantseal MCP server.

Custody (GS-C5 / GNT-REQ-005): the store carries ONLY the
section 2 field set — granted and exercised scope identifiers
under the taxonomy, connector and agent identities as presented,
timestamps, seals, verdict + named grammar basis. No access
tokens, refresh tokens, API keys, or credentials are captured,
held, or sealed in any form — not even as digests. A
credential-shaped input to any entry point is refused and the
refusal receipted (ADV-2). No resource contents, no call
payloads, no data the scopes were exercised on.

Provenance (GS-C4 / GNT-REQ-004, the GS-K1 guard): use evidence
arrives only from the principal's own agent runtime — source ==
"principal-runtime", an HMAC attestation from the runtime
registered for that principal-side channel, and a binding
reference to the sealed grant. Provider-produced logs or exports,
and any relay of them, are rejected on provenance, the rejection
receipted, and no use verdict is mintable from them.

Class discipline (GS-C2 / GNT-REQ-011): Class F records (grant
seal + runtime use capture) mint diff verdicts. Class G records
(grant seal only) mint GRANT-SEALED and are structurally
incapable of minting a use verdict: use capture against a Class G
record is refused at this layer and at the API layer, and the
verdict engine computes a use verdict only over a use-capture
record of principal-runtime provenance bound to a Class F grant.

Aggregation fence (GS-C6): this module exposes per-principal,
per-record reads only. There is no cross-principal aggregation
code path.
"""
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logic  # noqa: E402
import metering_journal as _mj  # noqa: E402
from licence_gate import LicenceGate  # noqa: E402

TOOL_VERSION = "0.1.0"
SERVER_ID = "eclipse-grantseal"

CLAIM = ("Grantseal seals the exact permissions an agent or app "
         "was granted at connect time, and the permissions it "
         "actually exercised as captured in your own agent "
         "runtime. If it used a scope it was never granted — or a "
         "renewal quietly added scopes — the sealed record names "
         "them, and anyone can recompute the verdict from the "
         "record itself.")

# The whole store field sets (SPEC section 2). Nothing else is
# written into a record. (GS-C5 / GNT-REQ-005.)
GRANT_FIELDS = ("grant_seal_id", "connector_id", "agent_id",
                "granted_scopes", "integration_class",
                "connect_timestamp", "taxonomy_version", "seal",
                "verdict", "use_verdict", "out_of_scope_scopes",
                "added_scopes", "unresolvable_scopes",
                "grammar_basis", "receipt_ref")

USE_FIELDS = ("use_capture_id", "grant_seal_id",
              "exercised_scopes", "window_start", "window_end",
              "runtime_id", "provenance", "attestation_verified",
              "capture_timestamp", "taxonomy_version", "seal",
              "verdict", "out_of_scope_scopes",
              "unresolvable_scopes", "grammar_basis",
              "receipt_ref")

RENEWAL_FIELDS = ("renewal_record_id", "grant_seal_id",
                  "renewed_scopes", "added_scopes", "verdict",
                  "no_change", "renewal_timestamp",
                  "taxonomy_version", "seal", "receipt_ref")

# Credential-shaped input keys (GNT-REQ-013 / ADV-2). Any input
# object carrying a key containing one of these fragments, at any
# depth, is refused by every entry point. Digests of credentials
# are credentials for this purpose: "token_digest" refuses exactly
# as "access_token" does.
CREDENTIAL_KEY_FRAGMENTS = ("token", "api_key", "apikey", "api-key",
                            "secret", "password", "passwd",
                            "credential", "authorization",
                            "private_key", "privatekey", "cookie",
                            "refresh", "access_key", "accesskey",
                            "session_key", "bearer")

# Metered event classes (PC-8 pattern, GNT-REQ-015): one op per
# grant seal, one op per use-window diff. Renewals, UNVERIFIABLE
# captures, rejections, refusals, recompute and check never meter.
# The ledger records event class + count only.
METER_GRANT = "grant_seal"
METER_USE_DIFF = "use_diff"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# -------------------------------------------------- record seals
# Every record carries a seal: a digest over the record's sealed
# body. The grant seal covers the connect-time bundle exactly as
# minted at seal time; use and renewal seals cover every field
# except the seal itself and the receipt reference. Load and
# recompute re-derive these digests from the current body — a
# record whose body no longer matches its seal is never loaded,
# served, or graded (F-1 cure; GNT-REQ-014 / GNT-REQ-005).

def grant_seal_of(record: dict) -> str:
    """The seal a grant record with this body must carry: the
    digest of the connect-time bundle (SPEC section 2). The
    record's verdict facets are not part of the bundle — they are
    minted outcomes; the seal binds the granted set itself."""
    bundle = {k: record.get(k) for k in
              ("connector_id", "agent_id", "granted_scopes",
               "integration_class", "connect_timestamp",
               "taxonomy_version")}
    return logic.digest_obj(bundle)


def record_seal_of(record: dict, fields) -> str:
    """The seal a use or renewal record with this body must
    carry: the digest over every field except the seal itself
    and the receipt reference — the construction used at mint."""
    return logic.digest_obj(
        {k: record.get(k) for k in fields
         if k not in ("seal", "receipt_ref")})


def verify_record_seals(grants: dict, uses: dict,
                        renewals: dict):
    """Re-derive every sealed record's seal from its current
    body. Returns (True, note) when all verify, or (False,
    detail) naming the first record whose body does not match
    its seal."""
    for seal_id, record in grants.items():
        if record.get("seal") != grant_seal_of(record):
            return False, f"grant record seal mismatch: {seal_id}"
    for use_id, record in uses.items():
        if record.get("seal") != record_seal_of(record, USE_FIELDS):
            return False, f"use record seal mismatch: {use_id}"
    for renewal_id, record in renewals.items():
        if record.get("seal") != record_seal_of(record,
                                                RENEWAL_FIELDS):
            return False, \
                f"renewal record seal mismatch: {renewal_id}"
    return True, "all record seals verify"


def find_credential_key(obj, _path=""):
    """Return the dotted path of the first credential-shaped key
    in an input object, or None. Values are also checked for a
    Bearer-token shape, which is a credential in transit."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            lowered = str(key).lower()
            if any(frag in lowered
                   for frag in CREDENTIAL_KEY_FRAGMENTS):
                return _path + str(key)
            hit = find_credential_key(value, _path + str(key) + ".")
            if hit is not None:
                return hit
    elif isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            hit = find_credential_key(value, f"{_path}[{i}].")
            if hit is not None:
                return hit
    elif isinstance(obj, str):
        if obj.strip().lower().startswith("bearer "):
            return _path + "<bearer-value>"
    return None


class Store:
    """JSON record store + hash-chained receipt journal + metering
    ledger (event class + count only). Fails closed: a journal
    that does not verify at load raises, and so does any sealed
    record whose body no longer matches its seal."""

    def __init__(self, state_path: str, runtime_keys: dict,
                 licence_gate=None, metering_journal_path: str = None):
        self.state_path = state_path
        self.runtime_keys = runtime_keys  # runtime_id -> channel key
        # ETO-44: licence gate (None = unconfigured fixture mode, the
        # ACT core pattern; server.py wires a gate whenever a licence
        # state is configured or GRANTSEAL_LICENCE_REQUIRED=1).
        self.licence_gate = licence_gate
        self._last_licence_state = None
        self.grants = {}
        self.uses = {}
        self.renewals = {}
        self.journal = []
        self.metering = {}
        # ETO-44: metering journal (ACT pattern, separate file; it
        # never feeds seals or verdicts). Always written alongside
        # the existing metering counts.
        self.metering_journal = _mj.MeteringJournal(
            metering_journal_path or (state_path + ".metering.jsonl"))
        if os.path.exists(state_path):
            with open(state_path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.grants = data.get("grants", {})
            self.uses = data.get("uses", {})
            self.renewals = data.get("renewals", {})
            self.journal = data.get("journal", [])
            self.metering = data.get("metering", {})
            ok, _ = self.verify_chain()
            if not ok:
                raise ValueError("receipt journal failed verification "
                                 "at load; store fails closed")
            ok, detail = verify_record_seals(self.grants, self.uses,
                                             self.renewals)
            if not ok:
                raise ValueError("sealed record failed seal "
                                 "verification at load (" + detail +
                                 "); store fails closed")
            self._verify_metering_journal()

    # ------------------------------------------------- ETO-44 leg
    def _verify_metering_journal(self):
        v = self.metering_journal.verify()
        if not v["ok"]:
            raise ValueError("metering journal failed verification "
                             "at load; store fails closed")
        if v["receipts"] and \
                self.metering_journal.counts_by_op() != self.metering:
            raise ValueError("metering journal counts disagree with "
                             "store metering counts at load; store "
                             "fails closed")

    def _licence_check(self):
        if self.licence_gate is None:
            self._last_licence_state = "UNCONFIGURED_FIXTURE"
            return None
        allowed, state = self.licence_gate.check()
        self._last_licence_state = state
        if allowed:
            return None
        return {"accepted": False, "error": state,
                "licence_state": state,
                "reason": "licence_gate_refused"}

    def _meter(self, op: str, subject: str):
        self.metering[op] = self.metering.get(op, 0) + 1
        self.metering_journal.append(subject, {
            "product": "grantseal", "op": op, "subject": subject,
            "unit_price_minor": 25, "currency": "USD",
            "fixture": True,
            "licence_state": self._last_licence_state})

    def metering_reconcile(self) -> dict:
        v = self.metering_journal.verify()
        journal_counts = self.metering_journal.counts_by_op()
        counted = sum(self.metering.values())
        recorded = sum(journal_counts.values())
        return {"ops_counted": counted,
                "journal_records": recorded,
                "counted_by_op": dict(self.metering),
                "journal_by_op": journal_counts,
                "chain_ok": v["ok"], "chain_head": v.get("head"),
                "reconciled": bool(v["ok"]) and counted == recorded
                and journal_counts == self.metering}

    # ---------------------------------------------------------- io
    def _save(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"grants": self.grants, "uses": self.uses,
                       "renewals": self.renewals,
                       "journal": self.journal,
                       "metering": self.metering}, fh,
                      indent=1, sort_keys=True)
        os.replace(tmp, self.state_path)

    # --------------------------------------------------- receipts
    def _append_receipt(self, kind: str, payload: dict) -> dict:
        prev = self.journal[-1]["record_hash"] if self.journal \
            else "GENESIS"
        entry = {"seq": len(self.journal) + 1, "timestamp": _now(),
                 "kind": kind,
                 "payload_digest": logic.digest_obj(payload),
                 "prev_hash": prev}
        entry["record_hash"] = logic.digest_obj(
            {k: entry[k] for k in
             ("seq", "timestamp", "kind", "payload_digest",
              "prev_hash")})
        self.journal.append(entry)
        return entry

    def verify_chain(self, journal=None):
        journal = self.journal if journal is None else journal
        prev = "GENESIS"
        for entry in journal:
            if entry.get("prev_hash") != prev:
                return False, f"link broken at seq {entry.get('seq')}"
            expect = logic.digest_obj(
                {k: entry.get(k) for k in
                 ("seq", "timestamp", "kind", "payload_digest",
                  "prev_hash")})
            if entry.get("record_hash") != expect:
                return False, f"hash mismatch at seq {entry.get('seq')}"
            prev = entry["record_hash"]
        return True, prev

    def chain_head(self) -> str:
        return self.journal[-1]["record_hash"] if self.journal \
            else "GENESIS"

    # --------------------------------------- credential refusal
    def refuse_credential(self, surface: str, key_path: str) -> dict:
        """ADV-2 / GNT-REQ-013: a credential-shaped input is
        refused, the refusal receipted, and no custody record of
        any kind is created from it."""
        receipt = self._append_receipt(
            "credential_input_refused",
            {"surface": surface, "key": key_path})
        self._save()
        return {"accepted": False,
                "error": "CREDENTIAL_INPUT_REFUSED",
                "key": key_path,
                "receipt_ref": receipt["record_hash"]}

    def _credential_gate(self, surface: str, payload: dict):
        hit = find_credential_key(payload)
        if hit is not None:
            return self.refuse_credential(surface, hit)
        return None

    # ------------------------------------------------- provenance
    def _attestation_valid(self, runtime_id, grant_seal_id,
                           core: dict, attestation) -> bool:
        key = self.runtime_keys.get(runtime_id)
        if not key or not attestation:
            return False
        msg = (grant_seal_id + "|" + logic.canon(core)).encode()
        expect = hmac.new(key.encode(), msg,
                          hashlib.sha256).hexdigest()
        return hmac.compare_digest(expect, attestation)

    @staticmethod
    def make_attestation(key: str, grant_seal_id: str,
                         core: dict) -> str:
        """The runtime side of the channel: the principal's own
        agent runtime, holding its registered channel key, attests
        a use-capture core bound to the grant seal."""
        msg = (grant_seal_id + "|" + logic.canon(core)).encode()
        return hmac.new(key.encode(), msg,
                        hashlib.sha256).hexdigest()

    # -------------------------------------------------- grant seal
    def seal_grant(self, grant: dict) -> dict:
        """Seal the exact scope granted at connect, as presented
        by the principal-side connect flow (GNT-REQ-002(i))."""
        refusal = self._credential_gate("grantseal_seal_grant",
                                        grant)
        if refusal is not None:
            return refusal
        refusal = self._licence_check()  # ETO-44 priced boundary
        if refusal is not None:
            return refusal
        integration_class = grant.get("integration_class")
        granted = grant.get("granted_scopes")
        if integration_class not in ("F", "G") or \
                not isinstance(granted, list) or not granted or \
                not grant.get("connector_id") or \
                not grant.get("agent_id"):
            return {"accepted": False, "error": "BELOW_STANDARD",
                    "reason": "grant bundle below the section 2 "
                              "standard"}
        bundle = {
            "connector_id": grant.get("connector_id"),
            "agent_id": grant.get("agent_id"),
            "granted_scopes": list(granted),
            "integration_class": integration_class,
            "connect_timestamp": grant.get("connect_timestamp")
            or _now(),
            "taxonomy_version": logic.TAXONOMY_VERSION,
        }
        seal_id = "gnt-" + logic.digest_obj(bundle)[:16]
        if seal_id in self.grants:
            return {"accepted": False, "error": "DUPLICATE_GRANT",
                    "grant_seal_id": seal_id}
        record = {
            "grant_seal_id": seal_id,
            "connector_id": bundle["connector_id"],
            "agent_id": bundle["agent_id"],
            "granted_scopes": bundle["granted_scopes"],
            "integration_class": integration_class,
            "connect_timestamp": bundle["connect_timestamp"],
            "taxonomy_version": logic.TAXONOMY_VERSION,
            "seal": grant_seal_of(bundle),
            "verdict": "GRANT-SEALED",
            "use_verdict": None,
            "out_of_scope_scopes": [],
            "added_scopes": [],
            "unresolvable_scopes": [],
            "grammar_basis": None,
            "receipt_ref": None,
        }
        receipt = self._append_receipt(
            "grant_seal",
            {"grant_seal_id": seal_id, "seal": record["seal"],
             "verdict": "GRANT-SEALED",
             "integration_class": integration_class})
        record["receipt_ref"] = receipt["record_hash"]
        assert set(record.keys()) == set(GRANT_FIELDS)
        self.grants[seal_id] = record
        self._meter(METER_GRANT, seal_id)
        self._save()
        return {"accepted": True, "grant_seal_id": seal_id,
                "receipt_ref": record["receipt_ref"],
                "integration_class": integration_class,
                "verdict": "GRANT-SEALED",
                "taxonomy_version": logic.TAXONOMY_VERSION}

    # ------------------------------------------------- use capture
    def capture_use(self, capture: dict) -> dict:
        """Accept or reject a use capture (GNT-REQ-004) and, on
        acceptance, mint the diff verdict against the original
        sealed grant."""
        refusal = self._credential_gate("grantseal_capture_use",
                                        capture)
        if refusal is not None:
            return refusal
        refusal = self._licence_check()  # ETO-44 priced boundary
        if refusal is not None:
            return refusal
        seal_id = capture.get("grant_seal_id")
        record = self.grants.get(seal_id)
        if record is None:
            return {"accepted": False, "error": "NO_SUCH_SEAL"}
        if record["integration_class"] == "G":
            # Class discipline (GNT-REQ-011): a Class G record is
            # grant-only; no use capture may attach to it, under
            # any API path. The refusal is receipted.
            receipt = self._append_receipt(
                "use_capture_refused_class_g",
                {"grant_seal_id": seal_id})
            self._save()
            return {"accepted": False,
                    "error": "CLASS_G_NO_USE_CAPTURE",
                    "verdict": "GRANT-SEALED",
                    "receipt_ref": receipt["record_hash"]}
        core = {k: capture.get(k) for k in
                ("exercised_scopes", "window_start", "window_end",
                 "runtime_id")}
        provenance_ok = (
            capture.get("source") == "principal-runtime"
            and self._attestation_valid(
                capture.get("runtime_id"), seal_id, core,
                capture.get("runtime_attestation")))
        if not provenance_ok:
            # ADV-1 (GS-K1 guard): provider-produced logs/exports,
            # relays of them, and unattested captures are rejected
            # on provenance; no use verdict is mintable from them.
            receipt = self._append_receipt(
                "use_capture_rejected",
                {"grant_seal_id": seal_id,
                 "source": capture.get("source"),
                 "runtime_id": capture.get("runtime_id"),
                 "reason": "provenance_failure"})
            self._save()
            return {"accepted": False, "verdict": "UNVERIFIABLE",
                    "reason": "provenance_failure",
                    "receipt_ref": receipt["record_hash"]}

        window_ok = bool(capture.get("window_start")) and \
            bool(capture.get("window_end")) and \
            capture["window_start"] < capture["window_end"]
        exercised = capture.get("exercised_scopes")
        if not window_ok or not isinstance(exercised, list):
            verdict = {"verdict": "UNVERIFIABLE",
                       "out_of_scope_scopes": [],
                       "unresolvable_scopes": [],
                       "grammar_basis": "below_capture_standard",
                       "taxonomy_version": logic.TAXONOMY_VERSION}
        else:
            verdict = logic.diff_use(record["granted_scopes"],
                                     exercised)
        use_id = "use-" + logic.digest_obj(
            {"grant_seal_id": seal_id, **core,
             "capture_timestamp":
                 capture.get("capture_timestamp") or _now()})[:16]
        use_record = {
            "use_capture_id": use_id,
            "grant_seal_id": seal_id,
            "exercised_scopes":
                list(exercised) if isinstance(exercised, list)
                else None,
            "window_start": capture.get("window_start"),
            "window_end": capture.get("window_end"),
            "runtime_id": capture.get("runtime_id"),
            "provenance": "principal-runtime",
            "attestation_verified": True,
            "capture_timestamp": capture.get("capture_timestamp")
            or _now(),
            "taxonomy_version": logic.TAXONOMY_VERSION,
            "seal": None,
            "verdict": verdict["verdict"],
            "out_of_scope_scopes": verdict["out_of_scope_scopes"],
            "unresolvable_scopes":
                verdict["unresolvable_scopes"],
            "grammar_basis": verdict["grammar_basis"],
            "receipt_ref": None,
        }
        use_record["seal"] = record_seal_of(use_record, USE_FIELDS)
        receipt = self._append_receipt(
            "use_capture",
            {"use_capture_id": use_id, "grant_seal_id": seal_id,
             "verdict": verdict["verdict"]})
        use_record["receipt_ref"] = receipt["record_hash"]
        assert set(use_record.keys()) == set(USE_FIELDS)
        self.uses[use_id] = use_record
        # The grant record's use facet follows the latest accepted
        # capture; the grant facet itself is never rewritten.
        record["use_verdict"] = verdict["verdict"]
        record["out_of_scope_scopes"] = \
            verdict["out_of_scope_scopes"]
        record["unresolvable_scopes"] = \
            verdict["unresolvable_scopes"]
        if verdict["grammar_basis"]:
            record["grammar_basis"] = verdict["grammar_basis"]
        record["verdict"] = headline_verdict(record)
        if verdict["verdict"] in ("WITHIN-GRANT",
                                  "OUT-OF-SCOPE-USE"):
            self._meter(METER_USE_DIFF, use_id)
        self._save()
        return {"accepted": True, "use_capture_id": use_id,
                "receipt_ref": receipt["record_hash"],
                "verdict": verdict["verdict"],
                "out_of_scope_scopes":
                    verdict["out_of_scope_scopes"],
                "unresolvable_scopes":
                    verdict["unresolvable_scopes"],
                "taxonomy_version": logic.TAXONOMY_VERSION}

    # ----------------------------------------------------- renewal
    def seal_renewal(self, renewal: dict) -> dict:
        """Diff a renewal grant, as presented, against the
        original seal at the moment it is presented
        (GNT-REQ-012). Renewals never meter."""
        refusal = self._credential_gate("grantseal_seal_renewal",
                                        renewal)
        if refusal is not None:
            return refusal
        seal_id = renewal.get("grant_seal_id")
        record = self.grants.get(seal_id)
        if record is None:
            return {"accepted": False, "error": "NO_SUCH_SEAL"}
        renewed = renewal.get("renewed_scopes")
        if not isinstance(renewed, list) or not renewed:
            return {"accepted": False, "error": "BELOW_STANDARD",
                    "reason": "renewal bundle below the section 2 "
                              "standard"}
        diff = logic.diff_renewal(record["granted_scopes"], renewed)
        renewal_id = "rnw-" + logic.digest_obj(
            {"grant_seal_id": seal_id, "renewed_scopes": renewed,
             "renewal_timestamp":
                 renewal.get("renewal_timestamp") or _now()})[:16]
        rec = {
            "renewal_record_id": renewal_id,
            "grant_seal_id": seal_id,
            "renewed_scopes": list(renewed),
            "added_scopes": diff["added_scopes"],
            "verdict": diff["verdict"],
            "no_change": bool(diff.get("no_change", False)),
            "renewal_timestamp":
                renewal.get("renewal_timestamp") or _now(),
            "taxonomy_version": logic.TAXONOMY_VERSION,
            "seal": None,
            "receipt_ref": None,
        }
        rec["seal"] = record_seal_of(rec, RENEWAL_FIELDS)
        receipt = self._append_receipt(
            "renewal_record",
            {"renewal_record_id": renewal_id,
             "grant_seal_id": seal_id, "verdict": diff["verdict"],
             "added_scopes": diff["added_scopes"]})
        rec["receipt_ref"] = receipt["record_hash"]
        assert set(rec.keys()) == set(RENEWAL_FIELDS)
        self.renewals[renewal_id] = rec
        if diff["verdict"] == "EXPANDED-AT-RENEWAL":
            record["added_scopes"] = diff["added_scopes"]
            record["verdict"] = headline_verdict(record)
        self._save()
        return {"accepted": True, "renewal_record_id": renewal_id,
                "receipt_ref": receipt["record_hash"],
                "verdict": diff["verdict"],
                "added_scopes": diff["added_scopes"],
                "no_change": rec["no_change"]}

    # ------------------------------------------------------- reads
    def get_verdict(self, seal_id: str) -> dict:
        record = self.grants.get(seal_id)
        if record is None:
            return {"error": "NO_SUCH_SEAL"}
        return {"grant_seal_id": seal_id,
                "verdict": record["verdict"],
                "use_verdict": record["use_verdict"],
                "integration_class": record["integration_class"],
                "out_of_scope_scopes":
                    record["out_of_scope_scopes"],
                "added_scopes": record["added_scopes"],
                "unresolvable_scopes":
                    record["unresolvable_scopes"],
                "taxonomy_version": record["taxonomy_version"],
                "receipt_refs": [record["receipt_ref"]]}

    def check(self, seal_id: str) -> dict:
        """Counterparty view (GNT-REQ-013): the verdict class and
        the names of out-of-scope or added scopes only."""
        record = self.grants.get(seal_id)
        if record is None:
            return {"error": "NO_SUCH_SEAL"}
        return {"verdict": record["verdict"],
                "out_of_scope_scopes":
                    record["out_of_scope_scopes"],
                "added_scopes": record["added_scopes"]}

    def export_captures(self, seal_id: str) -> dict:
        record = self.grants.get(seal_id)
        if record is None:
            return {"error": "NO_SUCH_SEAL"}
        uses = [u for u in self.uses.values()
                if u["grant_seal_id"] == seal_id]
        renewals = [r for r in self.renewals.values()
                    if r["grant_seal_id"] == seal_id]
        return {"grant_capture": dict(record),
                "use_capture": dict(uses[-1]) if uses else None,
                "renewal_records": [dict(r) for r in renewals],
                "chain_head": self.chain_head(),
                "taxonomy_version": record["taxonomy_version"]}


def headline_verdict(record: dict) -> str:
    """The record's headline verdict: the most severe minted
    facet, in the fixed precedence OUT-OF-SCOPE-USE >
    UNVERIFIABLE > EXPANDED-AT-RENEWAL > WITHIN-GRANT >
    GRANT-SEALED. Facets themselves are carried separately and
    never rewritten by the headline."""
    if record.get("use_verdict") == "OUT-OF-SCOPE-USE":
        return "OUT-OF-SCOPE-USE"
    if record.get("use_verdict") == "UNVERIFIABLE":
        return "UNVERIFIABLE"
    if record.get("added_scopes"):
        return "EXPANDED-AT-RENEWAL"
    if record.get("use_verdict") is not None:
        return record["use_verdict"]
    return "GRANT-SEALED"


def recompute(grant_capture: dict, use_capture,
              taxonomy_version: str) -> dict:
    """Third-party recomputation (GNT-REQ-002(iii)): the verdict
    from the exported captures + the published taxonomy alone.
    Reads no service state (GNT-REQ-013). A Class G grant capture
    recomputes to GRANT-SEALED; no use verdict is mintable for it
    here either — a use capture offered against a Class G grant is
    not evidence the engine will grade. Both captures' seals are
    verified against their bodies before anything is graded; a
    capture whose seal does not verify recomputes to UNVERIFIABLE
    and is never graded (F-1 cure)."""
    grant = grant_capture.get("grant_capture", grant_capture)
    if taxonomy_version not in logic.TAXONOMIES:
        return {"verdict": "UNVERIFIABLE",
                "reason": "unknown_taxonomy_version"}
    if grant.get("seal") != grant_seal_of(grant):
        # F-1 cure: an exported grant capture is graded only when
        # its seal verifies against its body. A tampered or
        # unsealed capture is never graded — the set difference
        # would run over an unverified granted set.
        return {"verdict": "UNVERIFIABLE",
                "reason": "grant capture seal does not verify "
                          "against its body",
                "taxonomy_version": taxonomy_version}
    if grant.get("integration_class") == "G" or use_capture is None:
        out = {"verdict": "GRANT-SEALED",
               "taxonomy_version": taxonomy_version}
        added = grant.get("added_scopes") or []
        if added:
            out["verdict"] = "EXPANDED-AT-RENEWAL"
            out["added_scopes"] = added
        return out
    use = use_capture.get("use_capture", use_capture)
    if use.get("provenance") != "principal-runtime":
        return {"verdict": "UNVERIFIABLE",
                "reason": "use capture provenance is not "
                          "principal-runtime",
                "taxonomy_version": taxonomy_version}
    if use.get("seal") != record_seal_of(use, USE_FIELDS):
        return {"verdict": "UNVERIFIABLE",
                "reason": "use capture seal does not verify "
                          "against its body",
                "taxonomy_version": taxonomy_version}
    diff = logic.diff_use(grant.get("granted_scopes", []),
                          use.get("exercised_scopes") or [],
                          taxonomy_version)
    return {"verdict": diff["verdict"],
            "out_of_scope_scopes": diff["out_of_scope_scopes"],
            "unresolvable_scopes": diff["unresolvable_scopes"],
            "grammar_basis": diff["grammar_basis"],
            "taxonomy_version": taxonomy_version}


def load_runtime_keys(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("runtime_keys", {})
