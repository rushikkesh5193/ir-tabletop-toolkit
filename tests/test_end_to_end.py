import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from irkit.core import load_config, load_json, analyse
from helpers import AS_OF

ROOT = Path(__file__).resolve().parent.parent
PLAN, EX = ROOT / "examples" / "sample_plan.json", ROOT / "examples" / "sample_exercise.json"

EXPECTED = {
    ("plan", "Phases", "PHASE_MISSING"), ("plan", "Legal / Compliance", "ROLE_MISSING"), ("plan", "Technical Lead", "NO_DEPUTY"),
    ("plan", "Communications Lead", "CONTACT_STALE"), ("plan", "SEV3", "SEVERITY_INCOMPLETE"), ("plan", "Playbooks", "PLAYBOOK_MISSING"),
    ("plan", "Plan", "PLAN_NOT_TESTED"), ("actions", "CA-PREV-1", "CORRECTIVE_ACTION_OVERDUE"),
    ("exercise", "I2", "ACTION_MISSED"), ("exercise", "I2", "RESPONSE_LATE"), ("exercise", "I5", "ACTION_MISSED"),
    ("exercise", "I5", "RESPONSE_LATE"), ("exercise", "Regulator (CERT-In, example)", "NOTIFICATION_LATE"),
    ("exercise", "Affected customers", "NOTIFICATION_MISSED"),
}


class TestSample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = analyse(load_json(PLAN, "plan"), load_config(), AS_OF, load_json(EX, "exercise"))

    def test_finds_exactly_the_injected_problems(self):
        got = {(i.area, i.ref, i.check) for i in self.res["issues"]}
        self.assertEqual(got - EXPECTED, set(), "false positives")
        self.assertEqual(EXPECTED - got, set(), "missed")

    def test_metrics(self):
        m = self.res["exercise"]["metrics"]
        self.assertEqual((m["action_coverage_pct"], m["on_time_pct"]), (85.7, 60.0))
        reg = next(n for n in m["notifications"] if n["party"].startswith("Regulator"))
        self.assertEqual((reg["elapsed_hours"], reg["met"]), (8.7, False))

    def test_corrective_actions_generated_from_findings(self):
        cas = self.res["exercise"]["corrective_actions"]
        self.assertEqual(len(cas), 6)      # 2 missed actions, 2 late responses, 2 notification failures
        self.assertEqual({c["due"] for c in cas}, {"2026-11-14"})

    def test_plan_only_run_has_no_exercise(self):
        r = analyse(load_json(PLAN, "plan"), load_config(), AS_OF)
        self.assertIsNone(r["exercise"])
        self.assertEqual({i.area for i in r["issues"]}, {"plan", "actions"})


class TestValidationAndCli(unittest.TestCase):
    def write(self, d, data):
        p = Path(d) / "x.json"
        p.write_text(json.dumps(data))
        return str(p)

    def test_bad_exercise_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for bad in ({"injects": []},
                        {"injects": [{"id": "A", "minute": 0, "text": "t"}, {"id": "A", "minute": 1, "text": "t"}]},
                        {"injects": [{"id": "A", "minute": 0, "text": "t"}], "responses": [{"inject": "Z", "minute": 1}]}):
                with self.assertRaises(ValueError):
                    load_json(self.write(d, bad), "exercise")

    def test_bad_notification_deadline_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                load_json(self.write(d, {"notifications": [{"party": "x", "deadline_hours": 0}]}), "plan")

    def cli(self, *a):
        return subprocess.run([sys.executable, "-m", "irkit", *a], cwd=ROOT, capture_output=True, text=True)

    def test_cli_outputs_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.cli(str(PLAN), "--exercise", str(EX), "--as-of", "2026-10-24", "--out-dir", d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(len(json.loads((Path(d) / "report.json").read_text())["issues"]), len(EXPECTED))
            self.assertIn("After-action review", (Path(d) / "report.md").read_text())
        self.assertEqual(self.cli(str(PLAN), "--as-of", "2026-10-24", "--fail-on", "critical").returncode, 0)   # plan only: no critical
        self.assertEqual(self.cli(str(PLAN), "--exercise", str(EX), "--as-of", "2026-10-24", "--fail-on", "critical").returncode, 1)
        self.assertEqual(self.cli("nope.json").returncode, 2)
        self.assertEqual(self.cli(str(PLAN), "--as-of", "x").returncode, 2)


if __name__ == "__main__":
    unittest.main()
