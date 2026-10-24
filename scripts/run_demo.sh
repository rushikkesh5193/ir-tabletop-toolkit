#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m irkit examples/sample_plan.json --exercise examples/sample_exercise.json --as-of 2026-10-24 --out-dir examples
python3 -m unittest discover -s tests
