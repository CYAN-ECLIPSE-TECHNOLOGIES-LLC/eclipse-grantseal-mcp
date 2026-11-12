#!/usr/bin/env python3
# Cyan Eclipse Grantseal — MCP smoke transcript.
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""Drives the real server over stdio JSON-RPC: tools/list, a
Class F grant seal, a within-grant use diff, an out-of-scope use
diff, a provider-log rejection, a Class G grant seal with a
refused use capture, a renewal expansion, check, export, an
offline recompute, and a credential-shaped input refusal.
Exits non-zero on any mismatch."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "fixtures"))
import captures  # noqa: E402


def rpc(proc, mid, method, params=None):
    msg = {"jsonrpc": "2.0", "id": mid, "method": method}
    if params is not None:
        msg["params"] = params
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()
    return json.loads(proc.stdout.readline())


def call(proc, mid, name, args):
    out = rpc(proc, mid, "tools/call",
              {"name": name, "arguments": args})
    return json.loads(out["result"]["content"][0]["text"])


def main():
    tmp = tempfile.mkdtemp()
    env = dict(os.environ,
               ECLIPSE_GRANTSEAL_STATE=os.path.join(tmp, "s.json"))
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "server.py")],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        text=True, env=env)
    try:
        init = rpc(proc, 1, "initialize")
        assert init["result"]["serverInfo"]["name"] == \
            "eclipse-grantseal", init
        tools = rpc(proc, 2, "tools/list")
        names = [t["name"] for t in tools["result"]["tools"]]
        assert names == ["grantseal_seal_grant",
                         "grantseal_capture_use",
                         "grantseal_seal_renewal",
                         "grantseal_get_verdict",
                         "grantseal_check",
                         "grantseal_recompute",
                         "grantseal_export_captures"], names
        g = call(proc, 3, "grantseal_seal_grant", captures.grant())
        assert g["verdict"] == "GRANT-SEALED", g
        seal_id = g["grant_seal_id"]
        ok = call(proc, 4, "grantseal_capture_use",
                  captures.use(seal_id))
        assert ok["verdict"] == "WITHIN-GRANT", ok
        out = call(proc, 5, "grantseal_capture_use",
                   captures.use(seal_id,
                                exercised=["gmail.readonly",
                                           "calendar.events"],
                                capture_timestamp=
                                "2026-11-11T13:05:01Z"))
        assert out["verdict"] == "OUT-OF-SCOPE-USE", out
        assert out["out_of_scope_scopes"] == ["calendar.events"], out
        rej = call(proc, 6, "grantseal_capture_use",
                   captures.use(seal_id,
                                source="provider-log-export",
                                capture_timestamp=
                                "2026-11-11T13:10:01Z"))
        assert rej["accepted"] is False and \
            rej["verdict"] == "UNVERIFIABLE", rej
        gg = call(proc, 7, "grantseal_seal_grant",
                  captures.grant(integration_class="G",
                                 agent_id="agent-smoke-g"))
        assert gg["verdict"] == "GRANT-SEALED", gg
        refused = call(proc, 8, "grantseal_capture_use",
                       captures.use(gg["grant_seal_id"]))
        assert refused["accepted"] is False and \
            refused["error"] == "CLASS_G_NO_USE_CAPTURE", refused
        rnw = call(proc, 9, "grantseal_seal_renewal",
                   captures.renewal(
                       seal_id,
                       renewed=captures.GRANTED
                       + ["calendar.readonly"]))
        assert rnw["verdict"] == "EXPANDED-AT-RENEWAL", rnw
        assert rnw["added_scopes"] == ["calendar.readonly"], rnw
        view = call(proc, 10, "grantseal_check",
                    {"grant_seal_id": seal_id})
        assert view == {"verdict": "OUT-OF-SCOPE-USE",
                        "out_of_scope_scopes": ["calendar.events"],
                        "added_scopes": ["calendar.readonly"]}, view
        export = call(proc, 11, "grantseal_export_captures",
                      {"grant_seal_id": seal_id})
        assert export["chain_head"], export
        fresh = call(proc, 12, "grantseal_recompute",
                     {"grant_capture": export["grant_capture"],
                      "use_capture": export["use_capture"],
                      "taxonomy_version":
                          export["taxonomy_version"]})
        assert fresh["verdict"] == "OUT-OF-SCOPE-USE", fresh
        cred = call(proc, 13, "grantseal_seal_grant",
                    {**captures.grant(agent_id="agent-smoke-c"),
                     "access_token": "ya29.fixture"})
        assert cred["accepted"] is False and \
            cred["error"] == "CREDENTIAL_INPUT_REFUSED", cred
        print("SMOKE PASS: 7 tools · GRANT-SEALED · WITHIN-GRANT · "
              "OUT-OF-SCOPE-USE · provider-log rejected · Class G "
              "use capture refused · EXPANDED-AT-RENEWAL · check · "
              "export · recompute reproduced · credential input "
              "refused")
        return 0
    finally:
        proc.stdin.close()
        proc.wait(timeout=10)


if __name__ == "__main__":
    sys.exit(main())
