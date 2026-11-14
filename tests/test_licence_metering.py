#!/usr/bin/env python3
# Cyan Eclipse Grantseal - ETO-44 licence metering tests.
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""ETO-44: per-op licence-checked metering. Fake transport with the
ActivationClient shape; the live deployed-server proof is
fixtures/licence_proof.py (evidence, not a unit test). Priced ops:
grant seal + use-window diff ($0.25/op, PC-8). Renewals never meter
and are never licence-gated (existing spec behaviour preserved)."""
import base64
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "fixtures"))

import grantseal  # noqa: E402
import captures  # noqa: E402
from licence_gate import LicenceGate  # noqa: E402
import metering_journal  # noqa: E402

KEYS = grantseal.load_runtime_keys(
    os.path.join(ROOT, "keys", "runtime-keys.json"))


class FakeClient:
    def __init__(self, checkin_state="LICENSE_VALID"):
        self.checkin_state = checkin_state

    def activate(self, artefact, install_id, label=""):
        return {"state": "LICENSE_VALID", "activation_token": "tok-1",
                "license_id": "lic-fixture-1"}

    def checkin(self, token, artefact_hash):
        return {"state": self.checkin_state}


def make_gate(tmp, client):
    artefact = base64.urlsafe_b64encode(
        json.dumps({"license_id": "lic-fixture-1"}).encode()
    ).decode().rstrip("=") + ".sig"
    path = os.path.join(tmp, "licence-state.json")
    with open(path, "w") as f:
        json.dump({"artefact": artefact, "install_id": "inst-1",
                   "install_label": "grantseal-test"}, f)
    return LicenceGate(state_path=path, client=client)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "state.json")


class TestLicenceMetering(Base):
    def test_valid_licence_grant_and_diff_meter(self):
        gate = make_gate(self.tmp, FakeClient())
        st = grantseal.Store(self.path, KEYS, licence_gate=gate)
        out = st.seal_grant(captures.grant())
        self.assertTrue(out["accepted"])
        res = st.capture_use(captures.use(out["grant_seal_id"]))
        self.assertTrue(res["accepted"])
        self.assertEqual(st.metering,
                         {"grant_seal": 1, "use_diff": 1})
        rec = st.metering_reconcile()
        self.assertTrue(rec["reconciled"], rec)
        self.assertEqual(rec["ops_counted"], 2)
        self.assertEqual(rec["journal_records"], 2)
        j = metering_journal.MeteringJournal(
            self.path + ".metering.jsonl")
        self.assertTrue(all(
            r["payload"]["unit_price_minor"] == 25
            for r in j.read_all()))

    def test_no_licence_grant_refused_and_unmetered(self):
        gate = LicenceGate(state_path=os.path.join(
            self.tmp, "absent.json"), client=FakeClient())
        st = grantseal.Store(self.path, KEYS, licence_gate=gate)
        out = st.seal_grant(captures.grant())
        self.assertFalse(out["accepted"])
        self.assertEqual(out["error"], "LICENSE_NOT_CONFIGURED")
        self.assertEqual(st.metering, {})
        self.assertEqual(st.grants, {})

    def test_revoked_licence_refused_at_checkin(self):
        client = FakeClient()
        gate = make_gate(self.tmp, client)
        st = grantseal.Store(self.path, KEYS, licence_gate=gate)
        out = st.seal_grant(captures.grant())
        self.assertTrue(out["accepted"])
        client.checkin_state = "LICENSE_REVOKED"
        res = st.capture_use(captures.use(out["grant_seal_id"]))
        self.assertFalse(res["accepted"])
        self.assertEqual(res["error"], "LICENSE_REVOKED")
        self.assertEqual(st.metering, {"grant_seal": 1})
        # reads still available after revoke
        self.assertEqual(
            st.get_verdict(out["grant_seal_id"])["verdict"],
            "GRANT-SEALED")

    def test_renewal_unmetered_and_ungated(self):
        client = FakeClient()
        gate = make_gate(self.tmp, client)
        st = grantseal.Store(self.path, KEYS, licence_gate=gate)
        out = st.seal_grant(captures.grant())
        client.checkin_state = "LICENSE_REVOKED"
        ren = st.seal_renewal({
            "grant_seal_id": out["grant_seal_id"],
            "renewed_scopes": captures.grant()["granted_scopes"]})
        self.assertTrue(ren["accepted"])
        self.assertEqual(st.metering, {"grant_seal": 1})
        self.assertEqual(st.metering_reconcile()["journal_records"], 1)

    def test_unverifiable_use_writes_no_record(self):
        gate = make_gate(self.tmp, FakeClient())
        st = grantseal.Store(self.path, KEYS, licence_gate=gate)
        out = st.seal_grant(captures.grant())
        res = st.capture_use(captures.use(
            out["grant_seal_id"], source="provider-log"))
        self.assertFalse(res["accepted"])
        self.assertEqual(st.metering, {"grant_seal": 1})

    def test_metering_journal_tamper_fails_closed_at_load(self):
        gate = make_gate(self.tmp, FakeClient())
        st = grantseal.Store(self.path, KEYS, licence_gate=gate)
        st.seal_grant(captures.grant())
        jpath = self.path + ".metering.jsonl"
        with open(jpath) as f:
            rec = json.loads(f.readline())
        rec["payload"]["unit_price_minor"] = 1
        with open(jpath, "w") as f:
            f.write(json.dumps(rec) + "\n")
        with self.assertRaises(ValueError):
            grantseal.Store(self.path, KEYS, licence_gate=gate)

    def test_reload_reconciles(self):
        gate = make_gate(self.tmp, FakeClient())
        st = grantseal.Store(self.path, KEYS, licence_gate=gate)
        st.seal_grant(captures.grant())
        st2 = grantseal.Store(self.path, KEYS, licence_gate=gate)
        self.assertTrue(st2.metering_reconcile()["reconciled"])


if __name__ == "__main__":
    unittest.main()
