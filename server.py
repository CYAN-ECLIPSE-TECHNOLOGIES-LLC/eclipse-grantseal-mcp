#!/usr/bin/env python3
# Cyan Eclipse Grantseal MCP server (spec: SPEC-GRANTSEAL section 4.1).
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""MCP over stdio (newline-delimited JSON-RPC 2.0), stdlib only.

Exactly the seven section 4.1 tools. There is no aggregation
tool, no enforcement tool (no blocking, no revocation — spec P3),
and no tool that accepts a token, key, or credential as an input
in any form: every call's arguments pass the credential gate
first, and a credential-shaped input is refused and receipted
(GNT-REQ-013, ADV-2).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grantseal  # noqa: E402
from licence_gate import LicenceGate  # noqa: E402

SERVER_NAME = "eclipse-grantseal"
SERVER_VERSION = grantseal.TOOL_VERSION
_STR = {"type": "string"}
_OBJ = {"type": "object"}
_ARR_STR = {"type": "array", "items": _STR}


def _obj(props, required):
    return {"type": "object", "properties": props,
            "required": required, "additionalProperties": False}


DESCRIPTIONS = {
    "grantseal_seal_grant":
        "Seal the exact scope granted at connect time, as "
        "presented by the principal-side connect flow: granted "
        "scope set, connector identity, agent identity, and the "
        "integration class (F = grant seal + runtime use capture; "
        "G = grant seal only). One metered op per grant seal. "
        + grantseal.CLAIM,
    "grantseal_capture_use":
        "Present an exercised-scope capture from the principal's "
        "own agent runtime (Class F records only) and mint the "
        "diff verdict against the original sealed grant. Captures "
        "from any other provenance are rejected. One metered op "
        "per use-window diff; UNVERIFIABLE captures do not meter.",
    "grantseal_seal_renewal":
        "Seal a renewal or re-connect grant and diff it against "
        "the original seal at presentation: added scopes verdict "
        "EXPANDED-AT-RENEWAL naming them; a renewal that changes "
        "nothing records a no-change marker. Renewals do not "
        "meter.",
    "grantseal_get_verdict":
        "The full verdict record for a grant seal: verdict, use "
        "verdict facet, named out-of-scope and added scopes, "
        "taxonomy version, receipt refs. Class G records return "
        "GRANT-SEALED. Unmetered.",
    "grantseal_check":
        "Counterparty view: the verdict class and the names of "
        "out-of-scope or added scopes only. Unmetered.",
    "grantseal_recompute":
        "Recompute a verdict from the exported captures plus the "
        "taxonomy version, with no service state. Unmetered.",
    "grantseal_export_captures":
        "Export the sealed captures for a grant (grant capture, "
        "latest use capture, renewal records) with the receipt "
        "chain head and taxonomy version, for independent "
        "recomputation. Unmetered.",
}

SCHEMAS = {
    "grantseal_seal_grant": _obj({
        "connector_id": _STR, "agent_id": _STR,
        "granted_scopes": _ARR_STR,
        "integration_class": {"type": "string",
                              "enum": ["F", "G"]},
        "connect_timestamp": _STR},
        ["connector_id", "agent_id", "granted_scopes",
         "integration_class"]),
    "grantseal_capture_use": _obj({
        "grant_seal_id": _STR, "exercised_scopes": _ARR_STR,
        "window_start": _STR, "window_end": _STR,
        "runtime_id": _STR, "source": _STR,
        "runtime_attestation": _STR, "capture_timestamp": _STR},
        ["grant_seal_id", "exercised_scopes", "window_start",
         "window_end", "runtime_id", "source",
         "runtime_attestation"]),
    "grantseal_seal_renewal": _obj({
        "grant_seal_id": _STR, "renewed_scopes": _ARR_STR,
        "renewal_timestamp": _STR},
        ["grant_seal_id", "renewed_scopes"]),
    "grantseal_get_verdict": _obj({"grant_seal_id": _STR},
                                  ["grant_seal_id"]),
    "grantseal_check": _obj({"grant_seal_id": _STR},
                            ["grant_seal_id"]),
    "grantseal_recompute": _obj({
        "grant_capture": _OBJ, "use_capture": _OBJ,
        "taxonomy_version": _STR},
        ["grant_capture", "taxonomy_version"]),
    "grantseal_export_captures": _obj({"grant_seal_id": _STR},
                                      ["grant_seal_id"]),
}

_store = None


def store() -> grantseal.Store:
    global _store
    if _store is None:
        base = os.path.dirname(os.path.abspath(__file__))
        state = os.environ.get(
            "ECLIPSE_GRANTSEAL_STATE",
            os.path.join(base, "data", "grantseal-state.json"))
        os.makedirs(os.path.dirname(state), exist_ok=True)
        keys_path = os.environ.get(
            "ECLIPSE_GRANTSEAL_RUNTIME_KEYS",
            os.path.join(base, "keys", "runtime-keys.json"))
        # ETO-44: licence gate wiring as in Routeseal (configured
        # licence state or GRANTSEAL_LICENCE_REQUIRED=1 enforces;
        # unconfigured = fixture mode, metering journal still on).
        gate = None
        if os.environ.get("GRANTSEAL_LICENCE_STATE") or \
                os.environ.get("GRANTSEAL_LICENCE_REQUIRED") == "1":
            gate = LicenceGate()
            print(f"grantseal licence gate mode: {gate.mode}",
                  file=sys.stderr)
        _store = grantseal.Store(
            state, grantseal.load_runtime_keys(keys_path),
            licence_gate=gate)
    return _store


def call_tool(name: str, args: dict):
    if name not in SCHEMAS:
        return {"error": "NO_SUCH_TOOL"}
    st = store()
    # The credential gate runs before every tool (GNT-REQ-013):
    # no tool accepts a token, key, or credential in any form.
    hit = grantseal.find_credential_key(args)
    if hit is not None:
        return st.refuse_credential(name, hit)
    if name == "grantseal_seal_grant":
        return st.seal_grant(args)
    if name == "grantseal_capture_use":
        return st.capture_use(args)
    if name == "grantseal_seal_renewal":
        return st.seal_renewal(args)
    if name == "grantseal_get_verdict":
        return st.get_verdict(args["grant_seal_id"])
    if name == "grantseal_check":
        return st.check(args["grant_seal_id"])
    if name == "grantseal_recompute":
        return grantseal.recompute(args["grant_capture"],
                                   args.get("use_capture"),
                                   args["taxonomy_version"])
    if name == "grantseal_export_captures":
        return st.export_captures(args["grant_seal_id"])
    return {"error": "NO_SUCH_TOOL"}


def handle(msg: dict):
    method = msg.get("method")
    if method == "initialize":
        return {"protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME,
                               "version": SERVER_VERSION}}
    if method == "tools/list":
        return {"tools": [{"name": n, "description": DESCRIPTIONS[n],
                           "inputSchema": SCHEMAS[n]}
                          for n in SCHEMAS]}
    if method == "tools/call":
        params = msg.get("params", {})
        result = call_tool(params.get("name"),
                           params.get("arguments", {}))
        return {"content": [{"type": "text",
                             "text": json.dumps(result,
                                                sort_keys=True)}],
                "isError": "error" in result}
    if method and method.startswith("notifications/"):
        return None
    return {"error": "NO_SUCH_METHOD"}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        result = handle(msg)
        if result is not None and "id" in msg:
            sys.stdout.write(json.dumps(
                {"jsonrpc": "2.0", "id": msg["id"],
                 "result": result}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
