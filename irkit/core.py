"""Incident response plan readiness checks, tabletop exercise scoring and after-action output.

The tool checks that the plan is complete and current, and scores how an
exercise went against the expectations written into the scenario. It cannot
judge whether the decisions were good, only whether the expected actions
happened, on time, in the record the facilitator kept.
"""
from __future__ import annotations

import calendar
import json
import re
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path

SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@dataclass
class Issue:
    area: str          # plan | exercise | actions
    check: str
    severity: str
    ref: str
    title: str
    detail: str
    action: str

    def as_dict(self):
        return asdict(self)


def load_config(path=None):
    return json.loads(Path(path or Path(__file__).with_name("config.json")).read_text(encoding="utf-8"))


def pdate(v, what="date"):
    if v in (None, ""):
        return None
    try:
        return date.fromisoformat(str(v))
    except ValueError as exc:
        raise ValueError(f"bad {what} {v!r}: expected YYYY-MM-DD") from exc


def add_months(d, n):
    i = d.month - 1 + n
    y, m = d.year + i // 12, i % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def norm(s):
    """Normalise an action string so 'Isolate the host.' matches 'isolate the host'."""
    return re.sub(r"[^a-z0-9 ]", "", str(s).lower()).strip()


def load_json(path, kind):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if kind == "plan":
        for k in ("last_reviewed", "last_tested", "contacts_verified"):
            pdate(data.get(k), k)
        for ca in data.get("corrective_actions", []):
            pdate(ca.get("due"), f"due for {ca.get('id')}")
        for n in data.get("notifications", []):
            if float(n["deadline_hours"]) <= 0:
                raise ValueError(f"notification {n['party']}: deadline_hours must be positive")
    else:
        ids = [i["id"] for i in data.get("injects", [])]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate inject ids")
        if not data.get("injects"):
            raise ValueError("exercise has no injects")
        for r in data.get("responses", []):
            if r["inject"] not in ids:
                raise ValueError(f"response refers to unknown inject {r['inject']!r}")
        pdate(data.get("date"), "exercise date")
    return data


def _ids(xs, cfg):
    n = cfg["max_ids_listed"]
    return ", ".join(xs[:n]) + (f" and {len(xs) - n} more" if len(xs) > n else "")


# ---------------------------------------------------------------- plan

def check_plan(plan, cfg, as_of):
    out = []
    I = lambda *a: out.append(Issue("plan", *a))
    missing = [p for p in cfg["required_phases"] if p not in plan.get("phases_documented", [])]
    if missing:
        I("PHASE_MISSING", "high", "Phases", f"{len(missing)} response phase(s) not documented", ", ".join(missing) + ".",
          "Document each phase with owners, steps and exit criteria.")
    have = {r["role"]: r for r in plan.get("roles", [])}
    for role in cfg["required_roles"]:
        if role not in have:
            I("ROLE_MISSING", "high", role, f"No one is assigned the {role} role", "Required role is absent from the plan.",
              "Name a primary and a deputy.")
    for name, r in have.items():
        if not r.get("primary"):
            I("ROLE_UNASSIGNED", "high", name, f"{name} has no named primary", "", "Name a primary.")
        elif not r.get("deputy"):
            I("NO_DEPUTY", "medium", name, f"{name} has no deputy", f"If {r['primary']} is unavailable nobody is named to act.",
              "Name a deputy who has been briefed.")
        v = pdate(r.get("contact_verified"))
        if v is None or as_of > add_months(v, cfg["contact_verified_max_months"]):
            I("CONTACT_STALE", "medium", name, f"{name} contact details not verified in {cfg['contact_verified_max_months']} months",
              f"Last verified: {v or 'never'}.", "Call-test the contact numbers.")
    if not plan.get("severity_levels"):
        I("NO_SEVERITY_LEVELS", "high", "Severity", "No incident severity levels defined", "", "Define levels with response times and escalation.")
    else:
        for s in plan["severity_levels"]:
            if not s.get("escalate_to") or not s.get("response_minutes"):
                I("SEVERITY_INCOMPLETE", "medium", s.get("name", "?"), f"Severity {s.get('name')} lacks a response time or escalation point", "",
                  "Add both.")
    if not plan.get("notifications"):
        I("NO_NOTIFICATION_RULES", "high", "Notifications", "No external notification obligations recorded", "",
          "List who must be told (regulators, customers, partners) and by when.")
    miss_pb = [p for p in cfg["required_playbooks"] if p not in plan.get("playbooks", [])]
    if miss_pb:
        I("PLAYBOOK_MISSING", "medium", "Playbooks", f"{len(miss_pb)} scenario playbooks missing", ", ".join(miss_pb) + ".",
          "Write a short playbook for each.")
    for key, months, check, what, sev in (("last_reviewed", cfg["plan_review_max_months"], "PLAN_NOT_REVIEWED", "reviewed", "medium"),
                                          ("last_tested", cfg["plan_test_max_months"], "PLAN_NOT_TESTED", "tested", "high")):
        d = pdate(plan.get(key))
        if d is None or as_of > add_months(d, months):
            I(check, sev, "Plan", f"Plan not {what} in the last {months} months", f"Last {what}: {d or 'never'}.",
              "Run a tabletop exercise." if what == "tested" else "Review and re-approve the plan.")
    return out


def check_actions(plan, as_of):
    out = []
    for ca in plan.get("corrective_actions", []):
        due = pdate(ca.get("due"))
        if not ca.get("closed") and due and due < as_of:
            out.append(Issue("actions", "CORRECTIVE_ACTION_OVERDUE", "high", ca["id"], f"Corrective action {ca['id']} is overdue",
                             f"{ca['title']}. Due {due} ({(as_of - due).days} days late), owner {ca.get('owner') or 'unassigned'}.",
                             "Re-baseline with the owner or escalate."))
    return out


# ---------------------------------------------------------------- exercise

def score_exercise(plan, ex, cfg):
    """Return per-inject results, overall metrics and issues."""
    resp = {}
    for r in ex.get("responses", []):
        resp.setdefault(r["inject"], []).append(r)
    awareness = next((i["minute"] for i in ex["injects"] if i.get("aware")), ex["injects"][0]["minute"])
    deadlines = {n["party"]: float(n["deadline_hours"]) for n in plan.get("notifications", [])}
    results, issues = [], []
    for inj in ex["injects"]:
        rs = resp.get(inj["id"], [])
        done = {norm(a) for r in rs for a in r.get("actions", [])}
        expected = inj.get("expected", [])
        hit = [a for a in expected if norm(a) in done]
        miss = [a for a in expected if norm(a) not in done]
        first = min((r["minute"] for r in rs), default=None)
        delay = None if first is None else first - inj["minute"]
        limit = inj.get("respond_within")
        late = limit is not None and (delay is None or delay > limit)
        results.append({"id": inj["id"], "minute": inj["minute"], "text": inj["text"], "owner_role": inj.get("owner_role", ""),
                        "expected": len(expected), "done": len(hit), "missed": miss, "delay": delay, "limit": limit,
                        "on_time": (not late) if limit is not None else None})
        for a in miss:
            issues.append(Issue("exercise", "ACTION_MISSED", "high" if inj.get("critical") else "medium", inj["id"],
                                f"Expected action not taken: {a}", f"Inject {inj['id']}: {inj['text']}",
                                f"Add '{a}' to the playbook and rehearse it" + (f" with the {inj['owner_role']}." if inj.get("owner_role") else ".")))
        if late:
            when = "no response recorded" if delay is None else f"responded after {delay} min, target {limit}"
            issues.append(Issue("exercise", "RESPONSE_LATE", "high" if inj.get("critical") else "medium", inj["id"],
                                f"Inject {inj['id']} not handled in time", f"{when}.", "Review escalation and on-call arrangements."))
    notified = {}
    for r in ex.get("responses", []):
        for p in r.get("notified", []):
            notified[p] = min(notified.get(p, 10 ** 9), r["minute"])
    notes = []
    for party, hours in deadlines.items():
        if party in notified:
            elapsed = (notified[party] - awareness) / 60
            ok = elapsed <= hours
            notes.append({"party": party, "deadline_hours": hours, "elapsed_hours": round(elapsed, 1), "met": ok})
            if not ok:
                issues.append(Issue("exercise", "NOTIFICATION_LATE", "critical", party, f"{party} notified after the deadline",
                                    f"Notified {elapsed:.1f} h after awareness; deadline {hours:g} h.",
                                    "Pre-draft the notification and name who sends it."))
        elif ex.get("expects_notification", []) and party in ex["expects_notification"]:
            notes.append({"party": party, "deadline_hours": hours, "elapsed_hours": None, "met": False})
            issues.append(Issue("exercise", "NOTIFICATION_MISSED", "critical", party, f"{party} was never notified in the exercise",
                                f"Deadline is {hours:g} h from awareness.", "Add the notification step and owner to the plan."))
    exp = sum(r["expected"] for r in results)
    got = sum(r["done"] for r in results)
    timed = [r for r in results if r["on_time"] is not None]
    metrics = {"action_coverage_pct": round(100 * got / exp, 1) if exp else None,
               "on_time_pct": round(100 * sum(r["on_time"] for r in timed) / len(timed), 1) if timed else None,
               "injects": len(results), "notifications": notes}
    if metrics["action_coverage_pct"] is not None and metrics["action_coverage_pct"] < cfg["min_action_coverage_pct"]:
        issues.append(Issue("exercise", "LOW_ACTION_COVERAGE", "high", "Exercise",
                            f"Only {metrics['action_coverage_pct']}% of expected actions were taken",
                            f"Target is {cfg['min_action_coverage_pct']}%.", "Prioritise the corrective actions below."))
    return results, metrics, issues


def corrective_actions(issues, ex, cfg):
    """Turn exercise findings into trackable corrective actions with owners and dates."""
    base = pdate(ex.get("date")) or date.today()
    due = base + timedelta(days=cfg["corrective_action_days"])
    out = []
    for n, i in enumerate((i for i in issues if i.area == "exercise" and i.check != "LOW_ACTION_COVERAGE"), 1):
        out.append({"id": f"CA-{n:02d}", "from": i.check, "title": i.action, "context": i.title, "due": str(due),
                    "severity": i.severity})
    return out


def analyse(plan, cfg, as_of, ex=None):
    issues = check_plan(plan, cfg, as_of) + check_actions(plan, as_of)
    res = {"plan_issues": None, "exercise": None}
    if ex is not None:
        results, metrics, ex_issues = score_exercise(plan, ex, cfg)
        issues += ex_issues
        res["exercise"] = {"results": results, "metrics": metrics, "corrective_actions": corrective_actions(ex_issues, ex, cfg)}
    issues.sort(key=lambda i: (SEV_ORDER[i.severity], i.area, i.ref, i.check))
    res["issues"] = issues
    return res
