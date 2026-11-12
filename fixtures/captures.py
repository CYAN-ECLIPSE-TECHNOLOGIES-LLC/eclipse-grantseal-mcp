#!/usr/bin/env python3
# Cyan Eclipse Grantseal — fixture capture builder.
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""Builds grant, use, and renewal presentations the way the
principal-side connect flow and the principal's own agent runtime
present them: scope sets + identities, and for use captures the
runtime's HMAC attestation over (grant_seal_id | canonical core).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
import grantseal  # noqa: E402

KEY = "fixture-runtime-key-runtime-alpha"

GRANTED = ["gmail.readonly", "gmail.send", "drive.readonly"]
WINDOW = ("2026-11-11T12:00:00Z", "2026-11-11T13:00:00Z")


def grant(integration_class="F", granted=None,
          connector_id="gmail-connector", agent_id="agent-alpha",
          **overrides):
    cap = {
        "connector_id": connector_id,
        "agent_id": agent_id,
        "granted_scopes": GRANTED if granted is None else granted,
        "integration_class": integration_class,
        "connect_timestamp": "2026-11-11T11:59:00Z",
    }
    cap.update(overrides)
    return cap


def use(grant_seal_id, exercised=None, source="principal-runtime",
        runtime_id="runtime-alpha", key=KEY, window=WINDOW,
        **overrides):
    cap = {
        "grant_seal_id": grant_seal_id,
        "exercised_scopes": ["gmail.readonly"]
        if exercised is None else exercised,
        "window_start": window[0],
        "window_end": window[1],
        "runtime_id": runtime_id,
        "source": source,
        "capture_timestamp": "2026-11-11T13:00:01Z",
    }
    cap.update(overrides)
    core = {k: cap.get(k) for k in
            ("exercised_scopes", "window_start", "window_end",
             "runtime_id")}
    cap["runtime_attestation"] = grantseal.Store.make_attestation(
        key, grant_seal_id, core)
    return cap


def renewal(grant_seal_id, renewed=None, **overrides):
    cap = {
        "grant_seal_id": grant_seal_id,
        "renewed_scopes": GRANTED if renewed is None else renewed,
        "renewal_timestamp": "2026-11-11T14:00:00Z",
    }
    cap.update(overrides)
    return cap
