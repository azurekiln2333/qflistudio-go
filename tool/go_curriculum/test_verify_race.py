#!/usr/bin/env python3
"""Regression tests for verify.py's --race gate (must be fail-closed).

Bug being locked down: `main --race` used to only *annotate* each record with a
`race` field; a `RACE-FAIL`, a missing result, or a race-gate error still
produced `N passed, 0 failed` and exit 0. A verification tool that reports a
failed race check as green is worse than useless.

These tests drive the real `main()` with:
  * an injected fake `verify_topic_fn` (so no Go compile is needed), and
  * an injected fake `race_gate` (so no WSL/real `-race` is needed),
writing evidence into a temporary directory. They assert that only an exact
`RACE-OK` for every selected topic yields exit 0.

Usage:
    python tool/go_curriculum/test_verify_race.py
    python -m unittest tool/go_curriculum/test_verify_race.py
Exit 0 only if every assertion holds.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent


def _load_verify():
    spec = importlib.util.spec_from_file_location(
        "go_curriculum_verify", TOOL_DIR / "verify.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verify = _load_verify()


def _fake_verify_topic(topic, go):
    """A always-passing stand-in for the real compile/run verifier."""
    return {
        "id": topic["id"],
        "runtime": topic["runtime"],
        "importKind": topic["importKind"],
        "verification": topic["verification"]["kind"],
        "result": "fake",
        "exampleVariant": "same-as-tutorial",
    }


def _run(tmp: Path, race_gate, *, only="T001"):
    """Run main with fake verification + a temp evidence dir; return (rc, out)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = verify.main(
            ["--only", only, "--race"],
            race_gate=race_gate,
            verify_topic_fn=_fake_verify_topic,
            evidence_dir=tmp,
        )
    return rc, buf.getvalue()


class RaceGateTests(unittest.TestCase):
    def _evidence(self, tmp: Path):
        return json.loads((tmp / "verify-results.json").read_text(encoding="utf-8"))

    def test_race_ok_passes(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            rc, out = _run(tmp, lambda ids: {"T001": "RACE-OK"})
            self.assertEqual(rc, 0, out)
            self.assertIn("1 passed, 0 failed", out)
            self.assertEqual(self._evidence(tmp)[0]["race"], "RACE-OK")

    def test_race_fail_fails(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            rc, out = _run(tmp, lambda ids: {"T001": "RACE-FAIL"})
            self.assertNotEqual(rc, 0, out)
            self.assertIn("0 passed, 1 failed", out)
            self.assertIn("race=RACE-FAIL", out)
            # evidence is still recorded (auditable), but marked as failed.
            self.assertEqual(self._evidence(tmp)[0]["race"], "RACE-FAIL")

    def test_missing_race_result_fails(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            rc, out = _run(tmp, lambda ids: {})
            self.assertNotEqual(rc, 0, out)
            self.assertIn("0 passed, 1 failed", out)
            self.assertIn("RACE-MISSING", out)
            self.assertEqual(self._evidence(tmp)[0]["race"], "RACE-MISSING")

    def test_race_gate_error_fails(self):
        def boom(ids):
            raise verify.VerificationError("race gate exited 1: wsl missing")

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            rc, out = _run(tmp, boom)
            self.assertNotEqual(rc, 0, out)
            self.assertIn("0 passed, 1 failed", out)
            self.assertIn("race=RACE-MISSING", out)
            rec = self._evidence(tmp)[0]
            self.assertEqual(rec["race"], "RACE-MISSING")
            self.assertIn("race gate exited 1", rec["raceError"])

    def test_race_flag_absent_is_unaffected(self):
        # Without --race, ordinary verification still passes and no race field
        # is invented.
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = verify.main(
                    ["--only", "T001"],
                    race_gate=lambda ids: self.fail("gate must not run without --race"),
                    verify_topic_fn=_fake_verify_topic,
                    evidence_dir=tmp,
                )
            self.assertEqual(rc, 0, buf.getvalue())
            self.assertIn("1 passed, 0 failed", buf.getvalue())
            self.assertNotIn("race", self._evidence(tmp)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
