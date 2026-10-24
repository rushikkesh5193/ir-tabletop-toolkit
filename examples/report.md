# Incident Response Readiness Report: ExampleOrg Pvt Ltd (fictional)

As of **2026-10-24**. Data is synthetic unless you supplied your own.

## Summary

- Issues: 2 critical, 4 high, 8 medium, 0 low
- Exercise "Ransomware on file server" (2026-10-15): expected actions taken **85.7%**, injects handled on time **60.0%**

## Issues needing action

### Plan and programme

| Severity | Ref | Check | Detail | Action |
|---|---|---|---|---|
| high | CA-PREV-1 | CORRECTIVE_ACTION_OVERDUE | Corrective action CA-PREV-1 is overdue. Add out-of-hours on-call rota. Due 2026-09-30 (24 days late), owner IT Manager. | Re-baseline with the owner or escalate. |
| high | Legal / Compliance | ROLE_MISSING | No one is assigned the Legal / Compliance role. Required role is absent from the plan. | Name a primary and a deputy. |
| high | Phases | PHASE_MISSING | 1 response phase(s) not documented. post_incident_review. | Document each phase with owners, steps and exit criteria. |
| high | Plan | PLAN_NOT_TESTED | Plan not tested in the last 12 months. Last tested: 2025-08-20. | Run a tabletop exercise. |
| medium | Communications Lead | CONTACT_STALE | Communications Lead contact details not verified in 6 months. Last verified: 2026-01-15. | Call-test the contact numbers. |
| medium | Playbooks | PLAYBOOK_MISSING | 2 scenario playbooks missing. data_breach, third_party_incident. | Write a short playbook for each. |
| medium | SEV3 | SEVERITY_INCOMPLETE | Severity SEV3 lacks a response time or escalation point.  | Add both. |
| medium | Technical Lead | NO_DEPUTY | Technical Lead has no deputy. If S. Khan is unavailable nobody is named to act. | Name a deputy who has been briefed. |

### Tabletop exercise

| Severity | Ref | Check | Detail | Action |
|---|---|---|---|---|
| critical | Affected customers | NOTIFICATION_MISSED | Affected customers was never notified in the exercise. Deadline is 72 h from awareness. | Add the notification step and owner to the plan. |
| critical | Regulator (CERT-In, example) | NOTIFICATION_LATE | Regulator (CERT-In, example) notified after the deadline. Notified 8.7 h after awareness; deadline 6 h. | Pre-draft the notification and name who sends it. |
| medium | I2 | ACTION_MISSED | Expected action not taken: assess data exposure. Inject I2: Ransom note found; attacker claims data was stolen | Add 'assess data exposure' to the playbook and rehearse it with the Incident Commander. |
| medium | I2 | RESPONSE_LATE | Inject I2 not handled in time. responded after 35 min, target 20. | Review escalation and on-call arrangements. |
| medium | I5 | ACTION_MISSED | Expected action not taken: notify affected customers. Inject I5: Legal asks if reporting obligations are triggered | Add 'notify affected customers' to the playbook and rehearse it with the Legal / Compliance. |
| medium | I5 | RESPONSE_LATE | Inject I5 not handled in time. responded after 370 min, target 20. | Review escalation and on-call arrangements. |

## After-action review

### Timeline and scorecard

| Minute | Inject | Expected actions | Taken | Response time | Target | On time |
|---|---|---|---|---|---|---|
| 0 | I1: SOC reports mass file renaming on the finance file server | 3 | 3 | 9 min | 15 min | yes |
| 20 | I2: Ransom note found; attacker claims data was stolen | 3 | 2 | 35 min | 20 min | NO |
| 45 | I3: Journalist emails asking about an 'outage and breach' | 2 | 2 | 25 min | 30 min | yes |
| 90 | I4: Backups appear intact; restore decision needed | 3 | 3 | 20 min | 30 min | yes |
| 150 | I5: Legal asks if reporting obligations are triggered | 3 | 2 | 370 min | 20 min | NO |

### External notifications

| Party | Deadline (h) | Elapsed (h) | Met |
|---|---|---|---|
| Regulator (CERT-In, example) | 6 | 8.7 | NO |
| Affected customers | 72 | never | NO |

### What went well

- I1: SOC reports mass file renaming on the finance file server
- I3: Journalist emails asking about an 'outage and breach'
- I4: Backups appear intact; restore decision needed

### Corrective actions

| ID | Action | From | Severity | Due |
|---|---|---|---|---|
| CA-01 | Add 'assess data exposure' to the playbook and rehearse it with the Incident Commander. | Expected action not taken: assess data exposure | medium | 2026-11-14 |
| CA-02 | Review escalation and on-call arrangements. | Inject I2 not handled in time | medium | 2026-11-14 |
| CA-03 | Add 'notify affected customers' to the playbook and rehearse it with the Legal / Compliance. | Expected action not taken: notify affected customers | medium | 2026-11-14 |
| CA-04 | Review escalation and on-call arrangements. | Inject I5 not handled in time | medium | 2026-11-14 |
| CA-05 | Pre-draft the notification and name who sends it. | Regulator (CERT-In, example) notified after the deadline | critical | 2026-11-14 |
| CA-06 | Add the notification step and owner to the plan. | Affected customers was never notified in the exercise | critical | 2026-11-14 |
