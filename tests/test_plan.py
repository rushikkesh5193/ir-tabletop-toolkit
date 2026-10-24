import unittest

from irkit.core import check_actions, add_months, norm, pdate
from helpers import plan, checks, AS_OF
from datetime import date


class TestPlanChecks(unittest.TestCase):
    def test_clean_plan_has_no_issues(self):
        self.assertEqual(checks(), set())

    def test_missing_phase(self):
        self.assertIn(("PHASE_MISSING", "Phases"), checks(phases_documented=["preparation"]))

    def test_missing_role_and_unassigned_primary(self):
        roles = [{"role": "Incident Commander", "primary": "A", "deputy": "B", "contact_verified": "2026-08-01"}]
        self.assertIn(("ROLE_MISSING", "Technical Lead"), checks(roles=roles))
        roles[0]["primary"] = ""
        self.assertIn(("ROLE_UNASSIGNED", "Incident Commander"), checks(roles=roles))

    def test_deputy_required(self):
        p = plan()
        p["roles"][0]["deputy"] = ""
        self.assertIn(("NO_DEPUTY", "Incident Commander"), checks(roles=p["roles"]))

    def test_contact_verification_window(self):
        p = plan()
        p["roles"][0]["contact_verified"] = "2026-04-24"      # exactly 6 months before as-of: still fine
        self.assertNotIn(("CONTACT_STALE", "Incident Commander"), checks(roles=p["roles"]))
        p["roles"][0]["contact_verified"] = "2026-04-23"
        self.assertIn(("CONTACT_STALE", "Incident Commander"), checks(roles=p["roles"]))
        p["roles"][0]["contact_verified"] = ""
        self.assertIn(("CONTACT_STALE", "Incident Commander"), checks(roles=p["roles"]))

    def test_severity_and_notifications(self):
        self.assertIn(("NO_SEVERITY_LEVELS", "Severity"), checks(severity_levels=[]))
        self.assertIn(("SEVERITY_INCOMPLETE", "SEV2"), checks(severity_levels=[{"name": "SEV2", "response_minutes": 60}]))
        self.assertIn(("NO_NOTIFICATION_RULES", "Notifications"), checks(notifications=[]))

    def test_playbooks(self):
        self.assertIn(("PLAYBOOK_MISSING", "Playbooks"), checks(playbooks=["ransomware"]))

    def test_test_and_review_windows(self):
        self.assertIn(("PLAN_NOT_TESTED", "Plan"), checks(last_tested="2025-10-23"))
        self.assertNotIn(("PLAN_NOT_TESTED", "Plan"), checks(last_tested="2025-10-24"))
        self.assertIn(("PLAN_NOT_TESTED", "Plan"), checks(last_tested=""))
        self.assertIn(("PLAN_NOT_REVIEWED", "Plan"), checks(last_reviewed="2025-10-23"))

    def test_corrective_action_overdue(self):
        ca = lambda **k: plan(corrective_actions=[dict(id="C", title="t", owner="o", due="2026-10-23", **k)])
        self.assertIn("CORRECTIVE_ACTION_OVERDUE", {c for c, _ in checks(**{"corrective_actions": ca()["corrective_actions"]})})
        self.assertNotIn("CORRECTIVE_ACTION_OVERDUE", {c for c, _ in checks(**{"corrective_actions": ca(closed="2026-10-01")["corrective_actions"]})})
        self.assertNotIn("CORRECTIVE_ACTION_OVERDUE",
                         {c for c, _ in checks(corrective_actions=[dict(id="C", title="t", due="2026-10-24")])})


class TestHelpers(unittest.TestCase):
    def test_norm_ignores_case_and_punctuation(self):
        self.assertEqual(norm("  Isolate the host. "), norm("isolate the HOST"))

    def test_add_months_clamps(self):
        self.assertEqual(add_months(date(2026, 8, 31), 6), date(2027, 2, 28))

    def test_bad_date(self):
        with self.assertRaises(ValueError):
            pdate("24-10-2026")


if __name__ == "__main__":
    unittest.main()
