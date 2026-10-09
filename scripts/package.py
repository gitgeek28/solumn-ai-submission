#!/usr/bin/env python3
"""Assemble the submission archive the brief asks for:

    environments/   the nine directories, EACH with its reward.txt and result.json
    results/        what each scored, plus rollout logs and adversarial evidence
    QUALITY_BAR.md
    README.md

Copies each env's reference reward.txt/result.json (from the refs-all matrix job)
into environments/<env>/, then tars a clean staging tree. Excludes .env, the
brief PDF, plan files, the private context doc, jobs/ and the dashboard.

usage: scripts/package.py [--job refs-all] [--out solumn-rle-submission.tar.gz]
"""
import argparse
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENVS = [
    "web-auth-comment", "web-auth-readme", "web-auth-runtime",
    "deploy-env-comment", "deploy-env-changelog", "deploy-env-manifest",
    "ingest-auth-feedrecord", "ingest-auth-schemacomment", "ingest-auth-opsnote",
]
EXCLUDE_NAMES = {"__pycache__", ".pytest_cache", ".DS_Store", ".git"}


def reference_trial(job_dir: Path, env: str) -> Path | None:
    want = f"{env}--reference"
    best = None
    for t in job_dir.iterdir() if job_dir.exists() else []:
        cfg = t / "config.json"
        if t.is_dir() and cfg.exists():
            try:
                name = Path(json.loads(cfg.read_text())["task"]["path"]).name
            except Exception:
                continue
            if name == want and (t / "verifier" / "reward.txt").exists():
                if best is None or t.stat().st_mtime > best.stat().st_mtime:
                    best = t
    return best


def stamp_env_artifacts(job: str) -> list[str]:
    job_dir = ROOT / "jobs" / "matrix" / job
    missing = []
    for env in ENVS:
        t = reference_trial(job_dir, env)
        dst = ROOT / "environments" / env
        if t is None:
            missing.append(env)
            continue
        shutil.copy(t / "verifier" / "reward.txt", dst / "reward.txt")
        shutil.copy(t / "verifier" / "result.json", dst / "result.json")
        reward = (dst / "reward.txt").read_text().strip()
        print(f"  {env}: reward.txt={reward}")
        if reward != "1":
            missing.append(f"{env} (reference reward {reward}!=1)")
    return missing


def _filter(tarinfo):
    base = Path(tarinfo.name).name
    if base in EXCLUDE_NAMES or base.endswith(".pyc"):
        return None
    return tarinfo


def build_archive(out: Path):
    staging = Path(tempfile.mkdtemp()) / "solumn-rle-submission"
    staging.mkdir(parents=True)
    shutil.copytree(ROOT / "environments", staging / "environments",
                    ignore=shutil.ignore_patterns(*EXCLUDE_NAMES, "*.pyc"))
    shutil.copytree(ROOT / "results", staging / "results",
                    ignore=shutil.ignore_patterns(*EXCLUDE_NAMES, "*.pyc", "raw"))
    for f in ("QUALITY_BAR.md", "README.md"):
        shutil.copy(ROOT / f, staging / f)
    # safety net: never ship secrets or the brief
    for bad in list(staging.rglob(".env")) + list(staging.rglob("*.pdf")):
        bad.unlink()
    if out.exists():
        out.unlink()
    with tarfile.open(out, "w:gz") as tar:
        tar.add(staging, arcname="solumn-rle-submission", filter=_filter)
    shutil.rmtree(staging.parent)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", default="refs-all")
    ap.add_argument("--out", default="solumn-rle-submission.tar.gz")
    args = ap.parse_args()

    print("stamping reference reward.txt/result.json into each environment:")
    missing = stamp_env_artifacts(args.job)
    if missing:
        print(f"\nMISSING reference artifacts for: {missing}", file=sys.stderr)
        print("Run: python3 scripts/matrix.py environments/<env> --impls reference --tag refs-all",
              file=sys.stderr)
        sys.exit(1)

    out = (ROOT / args.out).resolve()
    build_archive(out)
    size_mb = out.stat().st_size / 1e6
    print(f"\narchive: {out}  ({size_mb:.1f} MB)")
    # show it contains no secrets / pdf
    listing = subprocess.run(["tar", "tzf", str(out)], capture_output=True, text=True).stdout
    leaks = [l for l in listing.splitlines() if l.endswith(".env") or l.endswith(".pdf")]
    print("secret/pdf entries in archive:", leaks or "none")
    print(f"top-level entries: {sorted({l.split('/')[1] for l in listing.splitlines() if '/' in l and l.split('/')[1]})}")


if __name__ == "__main__":
    main()
