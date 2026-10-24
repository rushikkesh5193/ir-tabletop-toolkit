# ir-tabletop-toolkit

A small Python tool for **incident response (IR) readiness**: it checks whether an IR plan is complete and current, scores a **tabletop exercise** against what the scenario expected, and produces an **after-action report** with dated corrective actions.

Python standard library only (tested on 3.13).

> **Data note.** `examples/sample_plan.json` and `examples/sample_exercise.json` are **synthetic**, for a fictional company. They contain 14 problems injected on purpose so the tests can check the tool finds exactly those. The notification deadlines in the sample (a 6-hour regulator report, 72 hours for customers) are **examples**: confirm the current legal requirements that apply to your organisation.

## Why

Auditors and regulators ask two questions about incident response: *do you have a plan*, and *have you tested it*. A plan that is out of date, has no deputies or has never been exercised fails the second question. This tool turns both into measurable checks and makes the follow-up (corrective actions) trackable.

## Usage

```bash
python3 -m irkit examples/sample_plan.json --as-of 2026-10-24                                         # plan checks only
python3 -m irkit examples/sample_plan.json --exercise examples/sample_exercise.json --out-dir out      # plan + exercise + after-action review
python3 -m irkit examples/sample_plan.json --exercise examples/sample_exercise.json --fail-on critical # exit 1 for CI / cron
python3 -m unittest discover -s tests                                                                  # 33 tests
bash scripts/run_demo.sh
```

## What it checks

**The plan**

| Check | Raised when |
|---|---|
| `PHASE_MISSING` | A response phase is not documented (preparation, detection, containment, eradication, recovery, post-incident review) |
| `ROLE_MISSING` / `ROLE_UNASSIGNED` / `NO_DEPUTY` | A required role is absent, has no named primary, or has no deputy |
| `CONTACT_STALE` | Contact details not verified in 6 months |
| `NO_SEVERITY_LEVELS` / `SEVERITY_INCOMPLETE` | No severity scale, or a level lacks a response time or escalation point |
| `NO_NOTIFICATION_RULES` | No external notification obligations recorded |
| `PLAYBOOK_MISSING` | A required scenario playbook is missing (ransomware, phishing/account compromise, data breach, third-party incident) |
| `PLAN_NOT_REVIEWED` / `PLAN_NOT_TESTED` | Not reviewed or not tested within 12 months |
| `CORRECTIVE_ACTION_OVERDUE` | An open corrective action is past its due date |

**The exercise.** The facilitator writes timed *injects* with the actions expected, and records the responses. The tool measures:

- **Action coverage**: share of expected actions that were taken (`ACTION_MISSED`, `LOW_ACTION_COVERAGE`).
- **Timeliness**: first response against each inject's target, measured from the inject (`RESPONSE_LATE`).
- **Notification deadlines**: time from the moment of awareness to each external notification, against the plan's deadlines (`NOTIFICATION_LATE`, `NOTIFICATION_MISSED`).

Each exercise failure becomes a corrective action with an ID and a due date 30 days after the exercise.

Thresholds live in `irkit/config.json`. They are my defaults, so change them to match your own policy.

## Input format

See the two files in `examples/`. Inputs are validated (duplicate inject IDs, responses to unknown injects, non-positive deadlines and malformed dates are rejected with exit code 2). Action matching ignores case and punctuation, but otherwise needs the same wording as the scenario's expected actions.

## Tests

33 tests cover each plan check on both sides of its boundary, scoring (including awareness-based clocks, earliest response, combining several responses), notification deadlines, corrective-action generation, validation and an end-to-end run that must find **exactly** the injected problems. I also broke the code five ways (flipped boundaries, a clock started from the exercise start instead of awareness, using the latest response instead of the earliest, a longer test window) and confirmed the tests fail each time.

## Limitations

- **It scores the record, not the decisions.** It can show that an expected action did not happen, not whether what the team did instead was reasonable.
- **Exact-wording matching** of actions means the facilitator has to record responses consistently.
- **Not legal advice.** Notification deadlines and who must be notified depend on your regulators and contracts.
- **No UI or persistence.** JSON in, reports out.

## Layout

```
irkit/       core.py  report.py  config.json  __main__.py
tests/       33 tests
examples/    sample_plan.json  sample_exercise.json  report.md  report.json
scripts/     run_demo.sh
```
