#!/usr/bin/env python3
# Cyan Eclipse Grantseal — requirement-mapped test suite.
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""Every test names the requirement it verifies (SPEC-GRANTSEAL
section 3) and, where the bench plan restates it, the bench claim
(section 6). Builder tests are not bench evidence; they are the
build's own verification that the bench can later re-run.
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "fixtures"))

import logic  # noqa: E402
import grantseal  # noqa: E402
import server  # noqa: E402
import captures  # noqa: E402

KEYS = grantseal.load_runtime_keys(
    os.path.join(ROOT, "keys", "runtime-keys.json"))

BANNED = ("proves consent", "the user agreed", "prevents scope",
          "blocks scope", "acted maliciously", "prevents scope "
          "abuse", "blocks scope abuse")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "state.json")
        self.store = grantseal.Store(self.path, KEYS)

    def seal(self, **kw):
        return self.store.seal_grant(captures.grant(**kw))

    def seal_and_use(self, exercised=None, **grant_kw):
        out = self.seal(**grant_kw)
        seal_id = out["grant_seal_id"]
        return seal_id, self.store.capture_use(
            captures.use(seal_id, exercised=exercised))


class TestDiffDetection(Base):
    """GNT-REQ-002(ii) / GNT-REQ-010 / GS-B1: exercised scope
    exceeding the sealed grant verdicts OUT-OF-SCOPE-USE naming
    the scopes; within-grant controls verdict WITHIN-GRANT."""

    def test_within_grant_control(self):
        _, out = self.seal_and_use(exercised=["gmail.readonly",
                                              "gmail.send"])
        self.assertEqual(out["verdict"], "WITHIN-GRANT")
        self.assertEqual(out["out_of_scope_scopes"], [])

    def test_out_of_scope_named(self):
        _, out = self.seal_and_use(
            exercised=["gmail.readonly", "calendar.events"])
        self.assertEqual(out["verdict"], "OUT-OF-SCOPE-USE")
        self.assertEqual(out["out_of_scope_scopes"],
                         ["calendar.events"])

    def test_cross_provider_mapping_within(self):
        # Granted under Google identifiers; exercised under
        # Microsoft identifiers for the same canonical scopes.
        seal_id, out = None, None
        out_g = self.seal()
        seal_id = out_g["grant_seal_id"]
        out = self.store.capture_use(captures.use(
            seal_id, exercised=["Mail.Read", "Files.Read"]))
        self.assertEqual(out["verdict"], "WITHIN-GRANT")

    def test_cross_provider_out_of_scope(self):
        out_g = self.seal(granted=["Mail.Read"])
        out = self.store.capture_use(captures.use(
            out_g["grant_seal_id"], exercised=["gmail.send"]))
        self.assertEqual(out["verdict"], "OUT-OF-SCOPE-USE")
        self.assertEqual(out["out_of_scope_scopes"], ["gmail.send"])

    def test_unmapped_scope_unverifiable(self):
        _, out = self.seal_and_use(
            exercised=["gmail.readonly", "acme.teleport"])
        self.assertEqual(out["verdict"], "UNVERIFIABLE")
        self.assertEqual(out["unresolvable_scopes"],
                         ["acme.teleport"])
        self.assertEqual(out["out_of_scope_scopes"], [])


class TestClassDiscipline(Base):
    """GNT-REQ-002 / GNT-REQ-011 / GS-B3: Class G records mint
    GRANT-SEALED only and cannot mint a use verdict under any
    API path; Class F use verdicts require a principal-runtime
    capture."""

    def test_class_g_mints_grant_sealed(self):
        out = self.seal(integration_class="G")
        self.assertEqual(out["verdict"], "GRANT-SEALED")
        view = self.store.get_verdict(out["grant_seal_id"])
        self.assertEqual(view["verdict"], "GRANT-SEALED")
        self.assertIsNone(view["use_verdict"])

    def test_class_g_use_capture_refused_store(self):
        out = self.seal(integration_class="G")
        res = self.store.capture_use(
            captures.use(out["grant_seal_id"]))
        self.assertFalse(res["accepted"])
        self.assertEqual(res["error"], "CLASS_G_NO_USE_CAPTURE")
        self.assertEqual(self.store.uses, {})
        kinds = [e["kind"] for e in self.store.journal]
        self.assertIn("use_capture_refused_class_g", kinds)

    def test_class_g_use_capture_refused_api(self):
        st = server.store()
        out = st.seal_grant(captures.grant(integration_class="G",
                                           agent_id="agent-api-g"))
        res = server.call_tool(
            "grantseal_capture_use",
            captures.use(out["grant_seal_id"]))
        self.assertFalse(res["accepted"])
        self.assertEqual(res["error"], "CLASS_G_NO_USE_CAPTURE")
        view = server.call_tool(
            "grantseal_get_verdict",
            {"grant_seal_id": out["grant_seal_id"]})
        self.assertEqual(view["verdict"], "GRANT-SEALED")

    def test_class_g_recompute_stays_grant_sealed(self):
        out = self.seal(integration_class="G")
        export = self.store.export_captures(out["grant_seal_id"])
        forged_use = {"provenance": "principal-runtime",
                      "exercised_scopes": ["gmail.send"]}
        fresh = grantseal.recompute(export["grant_capture"],
                                    forged_use,
                                    logic.TAXONOMY_VERSION)
        self.assertEqual(fresh["verdict"], "GRANT-SEALED")


class TestCaptureStandard(Base):
    """GNT-REQ-004 / GS-B3 + ADV-1: use evidence arrives only
    from principal-side runtime capture; provider-log provenance
    is rejected and receipted; below-standard captures verdict
    UNVERIFIABLE in 100% of cases."""

    def test_provider_log_rejected(self):
        out = self.seal()
        res = self.store.capture_use(captures.use(
            out["grant_seal_id"], source="provider-log-export"))
        self.assertFalse(res["accepted"])
        self.assertEqual(res["verdict"], "UNVERIFIABLE")
        self.assertEqual(self.store.uses, {})
        kinds = [e["kind"] for e in self.store.journal]
        self.assertIn("use_capture_rejected", kinds)

    def test_relayed_log_rejected(self):
        out = self.seal()
        res = self.store.capture_use(captures.use(
            out["grant_seal_id"], source="runtime-relay"))
        self.assertFalse(res["accepted"])

    def test_forged_attestation_rejected(self):
        out = self.seal()
        cap = captures.use(out["grant_seal_id"])
        cap["runtime_attestation"] = "00" * 32
        res = self.store.capture_use(cap)
        self.assertFalse(res["accepted"])
        self.assertEqual(self.store.uses, {})

    def test_wrong_runtime_key_rejected(self):
        out = self.seal()
        cap = captures.use(out["grant_seal_id"],
                           key="fixture-runtime-key-runtime-beta")
        res = self.store.capture_use(cap)
        self.assertFalse(res["accepted"])

    def test_missing_window_below_standard(self):
        out = self.seal()
        cap = captures.use(out["grant_seal_id"], window=("", ""))
        # attestation covers the empty window; provenance is fine,
        # the bundle is below standard.
        res = self.store.capture_use(cap)
        self.assertTrue(res["accepted"])
        self.assertEqual(res["verdict"], "UNVERIFIABLE")

    def test_inverted_window_below_standard(self):
        out = self.seal()
        cap = captures.use(
            out["grant_seal_id"],
            window=("2026-11-11T13:00:00Z", "2026-11-11T12:00:00Z"))
        res = self.store.capture_use(cap)
        self.assertEqual(res["verdict"], "UNVERIFIABLE")

    def test_empty_exercised_set_within_grant(self):
        _, out = self.seal_and_use(exercised=[])
        self.assertEqual(out["verdict"], "WITHIN-GRANT")


class TestCustody(Base):
    """GNT-REQ-005 / GS-B4: the store contains only the section 2
    field set — no credentials, payloads, or resource contents in
    any form."""

    def test_record_field_sets_exact(self):
        seal_id, _ = self.seal_and_use()
        grant = self.store.grants[seal_id]
        self.assertEqual(set(grant.keys()),
                         set(grantseal.GRANT_FIELDS))
        use = next(iter(self.store.uses.values()))
        self.assertEqual(set(use.keys()), set(grantseal.USE_FIELDS))
        self.store.seal_renewal(captures.renewal(seal_id))
        renewal = next(iter(self.store.renewals.values()))
        self.assertEqual(set(renewal.keys()),
                         set(grantseal.RENEWAL_FIELDS))

    def test_state_file_has_no_credential_material(self):
        seal_id, _ = self.seal_and_use()
        self.store.seal_renewal(captures.renewal(seal_id))
        with open(self.path, encoding="utf-8") as fh:
            text = fh.read().lower()
        for fragment in ("access_token", "refresh_token",
                         "api_key", "bearer ", "password"):
            self.assertNotIn(fragment, text)

    def test_extra_grant_fields_not_retained(self):
        cap = captures.grant()
        cap["resource_contents"] = "should never be retained"
        cap["call_payload"] = {"body": " likewise"}
        out = self.store.seal_grant(cap)
        record = self.store.grants[out["grant_seal_id"]]
        self.assertEqual(set(record.keys()),
                         set(grantseal.GRANT_FIELDS))
        with open(self.path, encoding="utf-8") as fh:
            self.assertNotIn("should never be retained", fh.read())


class TestCredentialRefusal(Base):
    """GNT-REQ-013 / ADV-2 (GS-K2): no tool accepts a token, key,
    or credential in any form — including as a digest; a class
    observable only by holding its tokens is refused, and zero
    custody records are created."""

    def test_seal_grant_with_access_token_refused(self):
        cap = captures.grant()
        cap["access_token"] = "ya29.fixture"
        out = self.store.seal_grant(cap)
        self.assertFalse(out["accepted"])
        self.assertEqual(out["error"], "CREDENTIAL_INPUT_REFUSED")
        self.assertEqual(self.store.grants, {})

    def test_digest_only_token_refused(self):
        cap = captures.grant()
        cap["token_digest"] = "ab" * 32
        out = self.store.seal_grant(cap)
        self.assertFalse(out["accepted"])
        self.assertEqual(out["error"], "CREDENTIAL_INPUT_REFUSED")
        self.assertEqual(self.store.grants, {})

    def test_capture_use_with_api_key_refused(self):
        out = self.seal()
        cap = captures.use(out["grant_seal_id"])
        cap["api_key"] = "fixture-key"
        res = self.store.capture_use(cap)
        self.assertFalse(res["accepted"])
        self.assertEqual(res["error"], "CREDENTIAL_INPUT_REFUSED")
        self.assertEqual(self.store.uses, {})

    def test_every_tool_refuses_via_api(self):
        st = server.store()
        out = st.seal_grant(captures.grant(agent_id="agent-api-c"))
        seal_id = out["grant_seal_id"]
        for name, args in (
                ("grantseal_get_verdict",
                 {"grant_seal_id": seal_id,
                  "authorization": "Bearer fixture"}),
                ("grantseal_check",
                 {"grant_seal_id": seal_id,
                  "session_cookie": "fixture"}),
                ("grantseal_recompute",
                 {"grant_capture": {"integration_class": "G"},
                  "taxonomy_version": logic.TAXONOMY_VERSION,
                  "refresh_token": "fixture"}),
                ("grantseal_export_captures",
                 {"grant_seal_id": seal_id,
                  "client_secret": "fixture"})):
            res = server.call_tool(name, args)
            self.assertEqual(res.get("error"),
                             "CREDENTIAL_INPUT_REFUSED", name)

    def test_refusal_is_receipted(self):
        cap = captures.grant()
        cap["access_token"] = "ya29.fixture"
        self.store.seal_grant(cap)
        kinds = [e["kind"] for e in self.store.journal]
        self.assertIn("credential_input_refused", kinds)


class TestRenewal(Base):
    """GNT-REQ-012 / GS-B5: renewals are diffed against the
    original seal at presentation; added scopes verdict
    EXPANDED-AT-RENEWAL naming them; no-change renewals record
    the marker and do not meter."""

    def test_renewal_expansion_named(self):
        out = self.seal()
        res = self.store.seal_renewal(captures.renewal(
            out["grant_seal_id"],
            renewed=captures.GRANTED + ["calendar.readonly"]))
        self.assertEqual(res["verdict"], "EXPANDED-AT-RENEWAL")
        self.assertEqual(res["added_scopes"], ["calendar.readonly"])
        view = self.store.get_verdict(out["grant_seal_id"])
        self.assertEqual(view["verdict"], "EXPANDED-AT-RENEWAL")
        self.assertEqual(view["added_scopes"], ["calendar.readonly"])

    def test_no_change_renewal_marker(self):
        out = self.seal()
        res = self.store.seal_renewal(
            captures.renewal(out["grant_seal_id"]))
        self.assertTrue(res["no_change"])
        self.assertEqual(res["verdict"], "WITHIN-GRANT")
        view = self.store.get_verdict(out["grant_seal_id"])
        self.assertEqual(view["verdict"], "GRANT-SEALED")

    def test_renamed_scope_is_not_an_expansion(self):
        out = self.seal()
        res = self.store.seal_renewal(captures.renewal(
            out["grant_seal_id"],
            renewed=["Mail.Read", "gmail.send", "Files.Read"]))
        self.assertTrue(res["no_change"])
        self.assertEqual(res["added_scopes"], [])

    def test_renewal_diffs_against_original_seal(self):
        out = self.seal()
        seal_id = out["grant_seal_id"]
        self.store.seal_renewal(captures.renewal(
            seal_id, renewed=captures.GRANTED + ["calendar.read"],
            renewal_timestamp="2026-11-11T14:00:00Z"))
        # A second renewal presenting the same added scope is
        # still diffed against the ORIGINAL seal and names it.
        res = self.store.seal_renewal(captures.renewal(
            seal_id, renewed=captures.GRANTED + ["calendar.read"],
            renewal_timestamp="2026-11-11T15:00:00Z"))
        self.assertEqual(res["verdict"], "EXPANDED-AT-RENEWAL")
        self.assertEqual(res["added_scopes"], ["calendar.read"])

    def test_original_grant_not_rewritten_by_renewal(self):
        out = self.seal()
        seal_id = out["grant_seal_id"]
        before = list(self.store.grants[seal_id]["granted_scopes"])
        self.store.seal_renewal(captures.renewal(
            seal_id, renewed=captures.GRANTED + ["calendar.read"]))
        self.assertEqual(
            self.store.grants[seal_id]["granted_scopes"], before)


class TestVersioning(Base):
    """GNT-REQ-007 / GNT-REQ-010 / GS-B5: verdicts name their
    taxonomy version; a revision never retro-alters a minted
    verdict."""

    def test_taxonomy_version_named(self):
        seal_id, out = self.seal_and_use()
        self.assertEqual(out["taxonomy_version"],
                         logic.TAXONOMY_VERSION)
        view = self.store.get_verdict(seal_id)
        self.assertEqual(view["taxonomy_version"],
                         "grantseal-taxonomy/1")

    def test_revision_does_not_rewrite(self):
        seal_id, _ = self.seal_and_use(exercised=["gmail.send"])
        snapshot = json.dumps(self.store.grants[seal_id],
                              sort_keys=True)
        logic.TAXONOMIES["grantseal-taxonomy/2"] = {
            **logic._MAPPINGS_V1, "gmail.send": "mail.read"}
        try:
            fresh = grantseal.recompute(
                self.store.export_captures(seal_id)
                ["grant_capture"],
                self.store.export_captures(seal_id)["use_capture"],
                "grantseal-taxonomy/1")
            self.assertEqual(fresh["verdict"], "WITHIN-GRANT")
        finally:
            del logic.TAXONOMIES["grantseal-taxonomy/2"]
        self.assertEqual(
            json.dumps(self.store.grants[seal_id], sort_keys=True),
            snapshot)

    def test_unknown_taxonomy_version_unverifiable(self):
        out = self.seal()
        export = self.store.export_captures(out["grant_seal_id"])
        fresh = grantseal.recompute(export["grant_capture"],
                                    export["use_capture"],
                                    "grantseal-taxonomy/99")
        self.assertEqual(fresh["verdict"], "UNVERIFIABLE")


class TestRecompute(Base):
    """GNT-REQ-002(iii) / GNT-REQ-013 / GS-B2: an independent
    verifier reproduces the verdict from the exported captures +
    the taxonomy alone, with no service state."""

    def test_recompute_out_of_scope_matches(self):
        seal_id, _ = self.seal_and_use(
            exercised=["gmail.readonly", "calendar.events"])
        export = self.store.export_captures(seal_id)
        fresh = grantseal.recompute(export["grant_capture"],
                                    export["use_capture"],
                                    logic.TAXONOMY_VERSION)
        self.assertEqual(fresh["verdict"], "OUT-OF-SCOPE-USE")
        self.assertEqual(fresh["out_of_scope_scopes"],
                         ["calendar.events"])

    def test_recompute_within_grant_matches(self):
        seal_id, _ = self.seal_and_use()
        export = self.store.export_captures(seal_id)
        fresh = grantseal.recompute(export["grant_capture"],
                                    export["use_capture"],
                                    logic.TAXONOMY_VERSION)
        self.assertEqual(fresh["verdict"], "WITHIN-GRANT")

    def test_recompute_class_g_grant_only(self):
        out = self.seal(integration_class="G")
        export = self.store.export_captures(out["grant_seal_id"])
        fresh = grantseal.recompute(export["grant_capture"], None,
                                    logic.TAXONOMY_VERSION)
        self.assertEqual(fresh["verdict"], "GRANT-SEALED")

    def test_recompute_rejects_log_provenance(self):
        seal_id, _ = self.seal_and_use()
        export = self.store.export_captures(seal_id)
        forged = dict(export["use_capture"])
        forged["provenance"] = "provider-log"
        fresh = grantseal.recompute(export["grant_capture"],
                                    forged,
                                    logic.TAXONOMY_VERSION)
        self.assertEqual(fresh["verdict"], "UNVERIFIABLE")


class TestReceiptChain(Base):
    """GNT-REQ-014: one receipt per grant seal, use capture,
    renewal record, and verdict; the chain verifies end-to-end;
    tampering and truncation are detected."""

    def _populate(self):
        seal_id, _ = self.seal_and_use()
        self.store.seal_renewal(captures.renewal(seal_id))
        return seal_id

    def test_chain_verifies(self):
        self._populate()
        ok, head = self.store.verify_chain()
        self.assertTrue(ok)
        self.assertEqual(head, self.store.chain_head())
        kinds = [e["kind"] for e in self.store.journal]
        self.assertEqual(kinds, ["grant_seal", "use_capture",
                                 "renewal_record"])

    def test_tamper_detected(self):
        self._populate()
        journal = json.loads(json.dumps(self.store.journal))
        journal[0]["payload_digest"] = "00" * 32
        ok, _ = self.store.verify_chain(journal)
        self.assertFalse(ok)

    def test_truncated_export_detected(self):
        seal_id = self._populate()
        export = self.store.export_captures(seal_id)
        truncated = self.store.journal[:-1]
        ok, head = self.store.verify_chain(truncated)
        self.assertTrue(ok)  # a prefix verifies as a chain…
        self.assertNotEqual(head, export["chain_head"])  # …but its
        # head no longer matches the export's chain head.

    def test_store_fails_closed_on_tampered_journal(self):
        self._populate()
        with open(self.path, encoding="utf-8") as fh:
            data = json.load(fh)
        data["journal"][0]["payload_digest"] = "ff" * 32
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        with self.assertRaises(ValueError):
            grantseal.Store(self.path, KEYS)


class TestMetering(Base):
    """GNT-REQ-015 / GNT-REQ-003 / spec 4.3: one charge per grant
    seal and per use-window diff; renewals, UNVERIFIABLE
    captures, rejections, recompute, and check never meter; the
    ledger records event class + count only."""

    def test_metering_by_class(self):
        self.seal()                                        # +1 grant
        self.seal(integration_class="G",
                  agent_id="agent-g")                      # +1 grant
        seal_id, _ = None, None
        out = self.seal(agent_id="agent-f2")
        seal_id = out["grant_seal_id"]                     # +1 grant
        self.store.capture_use(captures.use(seal_id))      # +1 diff
        self.store.capture_use(captures.use(
            seal_id, exercised=["acme.teleport"],
            capture_timestamp="2026-11-11T13:30:01Z"))     # UNVERIF.
        self.store.capture_use(captures.use(
            seal_id, source="provider-log-export"))        # rejected
        self.store.seal_renewal(captures.renewal(
            seal_id, renewed=captures.GRANTED
            + ["calendar.read"]))                          # no meter
        self.assertEqual(self.store.metering,
                         {"grant_seal": 3, "use_diff": 1})

    def test_ledger_records_class_and_count_only(self):
        self.seal()
        self.assertEqual(set(self.store.metering.keys()),
                         {"grant_seal"})
        self.assertIsInstance(self.store.metering["grant_seal"],
                              int)


class TestMcpSurface(Base):
    """GNT-REQ-013 / GNT-REQ-009: the MCP surface is exactly
    section 4.1; grantseal_check reveals the verdict class and
    scope names only; no tool accepts a credential; outputs carry
    only the section 2 verdict vocabulary."""

    def test_tool_inventory_exact(self):
        names = set(server.SCHEMAS.keys())
        self.assertEqual(names, {
            "grantseal_seal_grant", "grantseal_capture_use",
            "grantseal_seal_renewal", "grantseal_get_verdict",
            "grantseal_check", "grantseal_recompute",
            "grantseal_export_captures"})

    def test_no_such_tool_for_enforcement_or_aggregation(self):
        for name in ("grantseal_revoke_scope", "grantseal_block",
                     "grantseal_connector_stats",
                     "grantseal_list_all"):
            self.assertEqual(server.call_tool(name, {}),
                             {"error": "NO_SUCH_TOOL"})

    def test_check_reveals_names_only(self):
        st = server.store()
        out = st.seal_grant(captures.grant(agent_id="agent-api-f"))
        seal_id = out["grant_seal_id"]
        st.capture_use(captures.use(
            seal_id, exercised=["gmail.readonly",
                                "calendar.events"]))
        view = server.call_tool("grantseal_check",
                                {"grant_seal_id": seal_id})
        self.assertEqual(set(view.keys()),
                         {"verdict", "out_of_scope_scopes",
                          "added_scopes"})
        self.assertEqual(view["verdict"], "OUT-OF-SCOPE-USE")
        self.assertEqual(view["out_of_scope_scopes"],
                         ["calendar.events"])

    def test_no_schema_property_is_credential_shaped(self):
        blob = json.dumps(server.SCHEMAS).lower()
        for fragment in grantseal.CREDENTIAL_KEY_FRAGMENTS:
            self.assertNotIn(fragment, blob)

    def test_banned_terms_absent_from_surfaces(self):
        blob = json.dumps(server.DESCRIPTIONS) + grantseal.CLAIM
        for term in BANNED:
            self.assertNotIn(term, blob.lower())


class TestAggregationFence(Base):
    """GNT-REQ-006: no cross-principal aggregation code path or
    surface exists in the build."""

    def test_no_aggregation_surface(self):
        names = [n for n in dir(grantseal.Store)
                 if not n.startswith("_")]
        names += list(server.SCHEMAS.keys())
        for token in ("aggregat", "stats", "dossier", "feed",
                      "insight"):
            self.assertFalse(any(token in n for n in names),
                             f"aggregation surface present: {token}")


class TestRecordSealTamperRefusal(Base):
    """F-1 cure / QA-PATTERNS P6 / GNT-REQ-014 + GNT-REQ-005:
    every sealed record's seal is re-verified at load and in
    recompute. A tampered record body is refused loudly at load
    — never silently loaded — and no diff or grant computation
    consumes an unverified record."""

    def _tamper_state(self, mutate):
        with open(self.path, encoding="utf-8") as fh:
            data = json.load(fh)
        mutate(data)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def _populate(self):
        seal_id, _ = self.seal_and_use()
        self.store.seal_renewal(captures.renewal(seal_id))
        return seal_id

    def test_untouched_store_reloads_and_serves(self):
        seal_id = self._populate()
        fresh = grantseal.Store(self.path, KEYS)
        view = fresh.get_verdict(seal_id)
        self.assertEqual(view["verdict"], "WITHIN-GRANT")
        ok, _ = grantseal.verify_record_seals(
            fresh.grants, fresh.uses, fresh.renewals)
        self.assertTrue(ok)

    def test_tampered_grant_scopes_refused_at_load(self):
        # The verdict's own probe: widen granted_scopes in the
        # state file, journal intact. Pre-cure this loaded
        # silently and graded the widened scope within-grant.
        seal_id = self._populate()

        def widen(data):
            data["grants"][seal_id]["granted_scopes"] = [
                "gmail.readonly", "gmail.send", "drive.readonly",
                "https://www.googleapis.com/auth/calendar.events"]
        self._tamper_state(widen)
        with self.assertRaises(ValueError):
            grantseal.Store(self.path, KEYS)

    def test_tampered_grant_seal_value_refused_at_load(self):
        seal_id = self._populate()

        def forge(data):
            data["grants"][seal_id]["seal"] = "00" * 32
        self._tamper_state(forge)
        with self.assertRaises(ValueError):
            grantseal.Store(self.path, KEYS)

    def test_tampered_use_record_refused_at_load(self):
        self._populate()

        def shrink(data):
            use = next(iter(data["uses"].values()))
            use["exercised_scopes"] = ["gmail.send"]
        self._tamper_state(shrink)
        with self.assertRaises(ValueError):
            grantseal.Store(self.path, KEYS)

    def test_tampered_renewal_record_refused_at_load(self):
        self._populate()

        def grow(data):
            rec = next(iter(data["renewals"].values()))
            rec["renewed_scopes"] = rec["renewed_scopes"] + \
                ["calendar.events"]
        self._tamper_state(grow)
        with self.assertRaises(ValueError):
            grantseal.Store(self.path, KEYS)

    def test_recompute_refuses_tampered_grant_capture(self):
        seal_id, _ = self.seal_and_use(
            exercised=["gmail.readonly", "calendar.events"])
        export = self.store.export_captures(seal_id)
        tampered = json.loads(json.dumps(export["grant_capture"]))
        tampered["granted_scopes"] = tampered["granted_scopes"] \
            + ["https://www.googleapis.com/auth/calendar.events"]
        fresh = grantseal.recompute(tampered, export["use_capture"],
                                    logic.TAXONOMY_VERSION)
        self.assertEqual(fresh["verdict"], "UNVERIFIABLE")
        self.assertIn("seal", fresh["reason"])

    def test_recompute_refuses_tampered_use_capture(self):
        seal_id, _ = self.seal_and_use(
            exercised=["gmail.readonly", "calendar.events"])
        export = self.store.export_captures(seal_id)
        tampered = json.loads(json.dumps(export["use_capture"]))
        tampered["exercised_scopes"] = ["gmail.readonly"]
        fresh = grantseal.recompute(export["grant_capture"],
                                    tampered,
                                    logic.TAXONOMY_VERSION)
        self.assertEqual(fresh["verdict"], "UNVERIFIABLE")
        self.assertIn("seal", fresh["reason"])

    def test_recompute_untouched_export_still_grades(self):
        seal_id, _ = self.seal_and_use(
            exercised=["gmail.readonly", "calendar.events"])
        export = self.store.export_captures(seal_id)
        fresh = grantseal.recompute(export["grant_capture"],
                                    export["use_capture"],
                                    logic.TAXONOMY_VERSION)
        self.assertEqual(fresh["verdict"], "OUT-OF-SCOPE-USE")
        self.assertEqual(fresh["out_of_scope_scopes"],
                         ["calendar.events"])


if __name__ == "__main__":
    unittest.main()
