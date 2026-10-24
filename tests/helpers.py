from datetime import date

from irkit.core import load_config, analyse, score_exercise, check_plan

AS_OF = date(2026, 10, 24)
CFG = load_config()
ROLES = ["Incident Commander", "Technical Lead", "Communications Lead", "Legal / Compliance"]


def plan(**kw):
    """A clean plan that triggers no plan checks; override per test."""
    d = {"organisation": "T", "last_reviewed": "2026-06-01", "last_tested": "2026-06-01",
         "phases_documented": list(CFG["required_phases"]),
         "roles": [{"role": r, "primary": "P", "deputy": "D", "contact_verified": "2026-08-01"} for r in ROLES],
         "severity_levels": [{"name": "SEV1", "response_minutes": 15, "escalate_to": "CISO"}],
         "notifications": [{"party": "Regulator", "deadline_hours": 6}],
         "playbooks": list(CFG["required_playbooks"]), "corrective_actions": []}
    d.update(kw)
    return d


def exercise(injects, responses=(), **kw):
    d = {"name": "x", "date": "2026-10-15", "injects": injects, "responses": list(responses)}
    d.update(kw)
    return d


def checks(**kw):
    return {(i.check, i.ref) for i in analyse(plan(**kw), CFG, AS_OF)["issues"]}


def inject(**kw):
    d = {"id": "I1", "minute": 0, "text": "t", "expected": ["do a"], "respond_within": 10}
    d.update(kw)
    return d
