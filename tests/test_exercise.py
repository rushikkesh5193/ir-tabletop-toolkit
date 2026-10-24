import unittest

from irkit.core import score_exercise, corrective_actions
from helpers import CFG, plan, exercise, inject


def run(injects, responses=(), **kw):
    return score_exercise(plan(), exercise(injects, responses, **kw), CFG)


def names(issues):
    return {(i.check, i.ref) for i in issues}


class TestExerciseScoring(unittest.TestCase):
    def test_full_marks(self):
        res, m, issues = run([inject()], [{"inject": "I1", "minute": 5, "actions": ["Do A."]}])
        self.assertEqual((m["action_coverage_pct"], m["on_time_pct"]), (100.0, 100.0))
        self.assertEqual(issues, [])

    def test_missed_action_reported_and_critical_inject_is_high(self):
        _, _, i = run([inject(expected=["do a", "do b"], critical=True)], [{"inject": "I1", "minute": 5, "actions": ["do a"]}])
        hit = [x for x in i if x.check == "ACTION_MISSED"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0].severity, "high")
        self.assertIn("do b", hit[0].title)

    def test_non_critical_miss_is_medium(self):
        _, _, i = run([inject()], [{"inject": "I1", "minute": 5, "actions": []}])
        self.assertEqual({x.severity for x in i if x.check == "ACTION_MISSED"}, {"medium"})

    def test_response_time_boundary(self):
        ok = [{"inject": "I1", "minute": 10, "actions": ["do a"]}]
        late = [{"inject": "I1", "minute": 11, "actions": ["do a"]}]
        self.assertNotIn(("RESPONSE_LATE", "I1"), names(run([inject()], ok)[2]))
        self.assertIn(("RESPONSE_LATE", "I1"), names(run([inject()], late)[2]))

    def test_no_response_is_late_and_missed(self):
        n = names(run([inject()])[2])
        self.assertIn(("RESPONSE_LATE", "I1"), n)
        self.assertIn(("ACTION_MISSED", "I1"), n)

    def test_delay_measured_from_inject_not_from_start(self):
        _, _, i = run([inject(minute=100)], [{"inject": "I1", "minute": 105, "actions": ["do a"]}])
        self.assertEqual(i, [])

    def test_uses_earliest_response_for_timeliness(self):
        rs = [{"inject": "I1", "minute": 30, "actions": ["do a"]}, {"inject": "I1", "minute": 5, "actions": []}]
        self.assertNotIn(("RESPONSE_LATE", "I1"), names(run([inject()], rs)[2]))

    def test_actions_from_several_responses_are_combined(self):
        rs = [{"inject": "I1", "minute": 2, "actions": ["do a"]}, {"inject": "I1", "minute": 4, "actions": ["do b"]}]
        _, m, i = run([inject(expected=["do a", "do b"])], rs)
        self.assertEqual(m["action_coverage_pct"], 100.0)

    def test_inject_without_target_has_no_timeliness(self):
        _, m, _ = run([inject(respond_within=None)], [{"inject": "I1", "minute": 500, "actions": ["do a"]}])
        self.assertIsNone(m["on_time_pct"])

    def test_low_coverage_flag(self):
        inj = [inject(id=f"I{k}", expected=["a"]) for k in range(5)]
        rs = [{"inject": f"I{k}", "minute": 1, "actions": ["a"]} for k in range(3)]          # 60%
        self.assertIn(("LOW_ACTION_COVERAGE", "Exercise"), names(run(inj, rs)[2]))
        rs = [{"inject": f"I{k}", "minute": 1, "actions": ["a"]} for k in range(4)]          # 80% = target, ok
        self.assertNotIn(("LOW_ACTION_COVERAGE", "Exercise"), names(run(inj, rs)[2]))


class TestNotifications(unittest.TestCase):
    def inj(self):
        return [inject(id="I1", minute=60, aware=True, respond_within=None, expected=[]), inject(id="I2", minute=120, respond_within=None, expected=[])]

    def test_deadline_measured_from_awareness(self):
        # aware at minute 60, deadline 6h = minute 420. 420 is on time, 421 is late.
        ok = run(self.inj(), [{"inject": "I2", "minute": 420, "actions": [], "notified": ["Regulator"]}])
        late = run(self.inj(), [{"inject": "I2", "minute": 421, "actions": [], "notified": ["Regulator"]}])
        self.assertTrue(ok[1]["notifications"][0]["met"])
        self.assertIn(("NOTIFICATION_LATE", "Regulator"), names(late[2]))
        self.assertEqual({i.severity for i in late[2] if i.check == "NOTIFICATION_LATE"}, {"critical"})

    def test_expected_but_never_notified(self):
        i = run(self.inj(), [], expects_notification=["Regulator"])[2]
        self.assertIn(("NOTIFICATION_MISSED", "Regulator"), names(i))

    def test_not_expected_not_flagged(self):
        self.assertNotIn("NOTIFICATION_MISSED", {c for c, _ in names(run(self.inj(), [])[2])})


class TestCorrectiveActions(unittest.TestCase):
    def test_actions_dated_from_exercise(self):
        _, _, issues = run([inject()], [])
        cas = corrective_actions(issues, exercise([inject()]), CFG)
        self.assertTrue(cas)
        self.assertEqual({c["due"] for c in cas}, {"2026-11-14"})       # 2026-10-15 + 30 days
        self.assertEqual([c["id"] for c in cas], [f"CA-{n:02d}" for n in range(1, len(cas) + 1)])


if __name__ == "__main__":
    unittest.main()
