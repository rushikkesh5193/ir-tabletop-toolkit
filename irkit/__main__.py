"""CLI: python3 -m irkit plan.json [--exercise ex.json] [--as-of YYYY-MM-DD] [--out-dir DIR] [--fail-on SEV]"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .core import analyse, load_config, load_json, pdate, SEV_ORDER
from .report import to_markdown, to_json


def main(argv=None):
    ap = argparse.ArgumentParser(prog="irkit", description="Incident response plan readiness and tabletop exercise scoring")
    ap.add_argument("plan")
    ap.add_argument("--exercise")
    ap.add_argument("--as-of")
    ap.add_argument("--config")
    ap.add_argument("--out-dir")
    ap.add_argument("--fail-on", choices=list(SEV_ORDER))
    a = ap.parse_args(argv)
    for p in (a.plan, a.exercise):
        if p and not Path(p).is_file():
            print(f"error: {p} not found", file=sys.stderr)
            return 2
    try:
        as_of = pdate(a.as_of, "--as-of") if a.as_of else date.today()
        cfg, plan = load_config(a.config), load_json(a.plan, "plan")
        ex = load_json(a.exercise, "exercise") if a.exercise else None
        res = analyse(plan, cfg, as_of, ex)
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    md = to_markdown(res, plan, ex, as_of)
    if a.out_dir:
        out = Path(a.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "report.md").write_text(md, encoding="utf-8")
        (out / "report.json").write_text(to_json(res, as_of), encoding="utf-8")
        print(f"{len(res['issues'])} issues -> {out}/report.md, report.json")
    else:
        print(md)
    return 1 if a.fail_on and any(SEV_ORDER[i.severity] <= SEV_ORDER[a.fail_on] for i in res["issues"]) else 0


if __name__ == "__main__":
    sys.exit(main())
