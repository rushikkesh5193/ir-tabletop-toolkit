"""Markdown and JSON output, including the after-action report."""
from __future__ import annotations

import json

SEVS = ("critical", "high", "medium", "low")


def to_markdown(res, plan, ex, as_of):
    issues = res["issues"]
    sev = {s: sum(1 for i in issues if i.severity == s) for s in SEVS}
    L = [f"# Incident Response Readiness Report: {plan.get('organisation', 'Organisation')}", "",
         f"As of **{as_of}**. Data is synthetic unless you supplied your own.", "", "## Summary", "",
         f"- Issues: {sev['critical']} critical, {sev['high']} high, {sev['medium']} medium, {sev['low']} low"]
    if res["exercise"]:
        m = res["exercise"]["metrics"]
        L += [f"- Exercise \"{ex.get('name', '')}\" ({ex.get('date', '')}): expected actions taken **{m['action_coverage_pct']}%**, "
              f"injects handled on time **{m['on_time_pct']}%**"]
    L += ["", "## Issues needing action", ""]
    plan_issues = [i for i in issues if i.area in ("plan", "actions")]
    for title, group in (("Plan and programme", plan_issues), ("Tabletop exercise", [i for i in issues if i.area == "exercise"])):
        if not group:
            continue
        L += [f"### {title}", "", "| Severity | Ref | Check | Detail | Action |", "|---|---|---|---|---|"]
        L += [f"| {i.severity} | {i.ref} | {i.check} | {i.title}. {i.detail} | {i.action} |" for i in group]
        L.append("")
    if res["exercise"]:
        e = res["exercise"]
        L += ["## After-action review", "", "### Timeline and scorecard", "",
              "| Minute | Inject | Expected actions | Taken | Response time | Target | On time |", "|---|---|---|---|---|---|---|"]
        for r in e["results"]:
            d = "none" if r["delay"] is None else f"{r['delay']} min"
            t = "-" if r["limit"] is None else f"{r['limit']} min"
            ot = "-" if r["on_time"] is None else ("yes" if r["on_time"] else "NO")
            L.append(f"| {r['minute']} | {r['id']}: {r['text']} | {r['expected']} | {r['done']} | {d} | {t} | {ot} |")
        L.append("")
        if e["metrics"]["notifications"]:
            L += ["### External notifications", "", "| Party | Deadline (h) | Elapsed (h) | Met |", "|---|---|---|---|"]
            for n in e["metrics"]["notifications"]:
                L.append(f"| {n['party']} | {n['deadline_hours']:g} | {n['elapsed_hours'] if n['elapsed_hours'] is not None else 'never'} | {'yes' if n['met'] else 'NO'} |")
            L.append("")
        good = [r for r in e["results"] if r["expected"] and r["done"] == r["expected"] and r["on_time"] is not False]
        L += ["### What went well", ""]
        L += [f"- {r['id']}: {r['text']}" for r in good] or ["- Nothing fully met its expectations."]
        L += ["", "### Corrective actions", ""]
        if e["corrective_actions"]:
            L += ["| ID | Action | From | Severity | Due |", "|---|---|---|---|---|"]
            L += [f"| {c['id']} | {c['title']} | {c['context']} | {c['severity']} | {c['due']} |" for c in e["corrective_actions"]]
        else:
            L.append("None.")
        L.append("")
    return "\n".join(L)


def to_json(res, as_of):
    return json.dumps({"as_of": str(as_of), "issues": [i.as_dict() for i in res["issues"]], "exercise": res["exercise"]}, indent=2)
