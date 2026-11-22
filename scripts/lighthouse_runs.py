#!/usr/bin/env python3
"""Run Lighthouse (mobile) several times and print the middle score and range per category.

usage: python3 -I lighthouse_runs.py <url> [runs=5] [out_dir=lighthouse]
       python3 -I lighthouse_runs.py --self-test

Scores drift between runs and between days, so the deck shows the middle value
and states the range. Set LIGHTHOUSE to a lighthouse CLI path to skip npx.
"""
import json, os, shutil, statistics, subprocess, sys

CATS = ["performance", "accessibility", "best-practices", "seo"]


def summarize(runs):
    """runs: list of {category: score 0-100}. Returns {category: (middle, low, high)}."""
    return {c: (round(statistics.median(r[c] for r in runs)), min(r[c] for r in runs), max(r[c] for r in runs))
            for c in CATS if all(r.get(c) is not None for r in runs)}


def run_once(url, path):
    lh = os.environ.get("LIGHTHOUSE")
    cmd = (["node", lh] if lh else [shutil.which("npx") or "npx", "-y", "lighthouse"]) + [
        url, "--quiet", "--chrome-flags=--headless=new", "--output=json", f"--output-path={path}",
        "--only-categories=" + ",".join(CATS)]
    subprocess.run(cmd, capture_output=True)
    d = json.load(open(path))
    if d.get("runtimeError"):
        sys.exit(f"Lighthouse could not load {url}: {d['runtimeError'].get('message')}")
    return {k: round(v["score"] * 100) for k, v in d["categories"].items() if v["score"] is not None}


if sys.argv[1:] == ["--self-test"]:
    s = summarize([{c: 60 for c in CATS}, {c: 80 for c in CATS}, {c: 70 for c in CATS}])
    assert s["performance"] == (70, 60, 80), s
    print("ok")
    sys.exit()

url = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
out = sys.argv[3] if len(sys.argv) > 3 else "lighthouse"
os.makedirs(out, exist_ok=True)
runs = []
for i in range(n):
    runs.append(run_once(url, os.path.join(out, f"run-{i + 1}.json")))
    print(f"run {i + 1}: {runs[-1]}", file=sys.stderr)
print(json.dumps({"url": url, "runs": n,
                  "scores": {c: {"middle": m, "low": lo, "high": hi} for c, (m, lo, hi) in summarize(runs).items()}},
                 indent=2))
