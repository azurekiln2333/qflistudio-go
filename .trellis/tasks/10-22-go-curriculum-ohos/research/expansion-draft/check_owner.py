"""Snapshot and verify an author's exact draft ID range, with isolated catalogs."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
TOOL = ROOT / "tool/go_curriculum"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--first", type=int, required=True)
parser.add_argument("--last", type=int, required=True)
parser.add_argument("--tag", required=True)
parser.add_argument("--backend", choices=("native", "official", "inventory"), required=True)
parser.add_argument("--timeout", type=float, default=15)
args = parser.parse_args()
if not 121 <= args.first <= args.last <= 280 or not re.fullmatch(r"[a-zA-Z0-9_-]+", args.tag):
    parser.error("expected draft IDs 121..280 and a simple evidence tag")
snapshot = HERE / "checks" / args.tag
topics = snapshot / "topics"
topics.mkdir(parents=True, exist_ok=True)
expected = {f"T{number:03d}.json" for number in range(args.first, args.last+1)}
if {path.name for path in topics.glob("T*.json")} - expected:
    parser.error("evidence tag already contains a different topic range; choose a fresh tag")
for name in sorted(expected):
    shutil.copyfile(HERE / "topics" / name, topics / name)
env = dict(os.environ, GOMEMLIMIT="512MiB", GOGC="20")


def run(*command):
    subprocess.run([sys.executable, *map(str, command)], cwd=ROOT, env=env, check=True)


run(TOOL / "assemble.py", "--topics-dir", topics, "--samples-dir", HERE / "samples",
    "--out", snapshot / "content", "--app-out", snapshot / "catalogs")
run(TOOL / "dedup.py", "--topics-dir", topics)
run(TOOL / "audit_native.py", "--backend", args.backend, "--topics", topics,
    "--samples", HERE / "samples", "--tutorials", snapshot / "catalogs/tutorials.json",
    "--examples", snapshot / "catalogs/examples.json", "--manifest-out", snapshot / "manifest.json",
    "--out", snapshot / f"{args.backend}.json", "--timeout", args.timeout)
