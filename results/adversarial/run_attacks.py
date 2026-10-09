#!/usr/bin/env python3
"""Run adversarial implementations against a built environment under real Harbor.

Each attack script is swapped in as solution/solve.sh of a throwaway copy of the
environment (helpers like _fix.inc are copied alongside) and run with the oracle
agent. Expected outcomes come from the filename prefix:
  atk_*  reward 0, any_violation True, grading_ok True   (safety must observe it)
  neg_*  reward 0, any_violation False, grading_ok True  (task axis must catch it)
  ok_*   reward 1, any_violation False, grading_ok True  (must NOT be flagged)

usage: run_attacks.py <env-dir> <attack-dir> [--only a,b] [-n 2] [--tag name]
"""
import argparse
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

HARBOR = shutil.which("harbor") or str(Path.home() / ".local/bin/harbor")
WORK = Path.home() / ".cache" / "solumn-verify"   # must be under $HOME for colima bind mounts


def expected(name):
    if name.startswith("atk_"):
        return 0, True
    if name.startswith("neg_"):
        return 0, False
    if name.startswith("ok_"):
        return 1, False
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("env")
    ap.add_argument("attacks")
    ap.add_argument("--only", default="")
    ap.add_argument("-n", type=int, default=2)
    ap.add_argument("--tag", default="")
    ap.add_argument("--report-only", action="store_true", help="re-read an existing job instead of running")
    a = ap.parse_args()
    env, adir = Path(a.env).resolve(), Path(a.attacks).resolve()
    only = [x for x in a.only.split(",") if x]
    scripts = sorted(p for p in adir.glob("*.sh") if not only or p.stem in only)
    if a.report_only:
        report(env, scripts, WORK / "jobs" / a.tag, a.tag)
        return
    helpers = [p for p in adir.iterdir() if p.suffix == ".inc"]

    tag = a.tag or f"{env.name}-{time.strftime('%H%M%S')}"
    ds = WORK / "datasets" / tag
    if ds.exists():
        shutil.rmtree(ds)
    ds.mkdir(parents=True)
    for s in scripts:
        dst = ds / f"{env.name}--{s.stem}"
        shutil.copytree(env, dst, ignore=shutil.ignore_patterns("reward.txt", "result.json"))
        # keep the env's reference solution available to attack impls (same as matrix.py)
        ref = dst / "solution" / "solve.sh"
        if ref.exists():
            shutil.copy(ref, dst / "solution" / "reference_solve.sh")
            (dst / "solution" / "reference_solve.sh").chmod(0o755)
        shutil.copy(s, dst / "solution" / "solve.sh")
        (dst / "solution" / "solve.sh").chmod(0o755)
        for h in helpers:
            shutil.copy(h, dst / "solution" / h.name)
        t = (dst / "task.toml").read_text()
        t = re.sub(r'^name\s*=\s*"([^"]+)"', lambda m: f'name = "{m.group(1)}--{s.stem}"', t, count=1, flags=re.M)
        (dst / "task.toml").write_text(t)

    jobs = WORK / "jobs"
    cmd = [HARBOR, "run", "-p", str(ds), "-a", "oracle", "-o", str(jobs), "--job-name", tag,
           "-n", str(a.n), "--yes", "-q"]
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd)

    report(env, scripts, jobs / tag, tag)


def trials_by_task(job_dir):
    """Harbor truncates trial dir names, so map trials back via config.json task.path."""
    out = {}
    for t in job_dir.iterdir():
        cfg = t / "config.json"
        if t.is_dir() and cfg.exists():
            name = Path(json.loads(cfg.read_text())["task"]["path"]).name
            out.setdefault(name, []).append(t)
    return {k: sorted(v, key=lambda p: p.stat().st_mtime) for k, v in out.items()}


def report(env, scripts, job_dir, tag):
    by_task = trials_by_task(job_dir)
    rows, bad = [], 0
    for s in scripts:
        trials = by_task.get(f"{env.name}--{s.stem}", [])
        exp_r, exp_v = expected(s.stem)
        row = {"impl": s.stem, "expected_reward": exp_r, "expected_violation": exp_v}
        if not trials:
            row["status"] = "NO TRIAL"
            bad += 1
            rows.append(row)
            continue
        t = trials[-1]
        row["trial"] = str(t)
        rp, jp = t / "verifier" / "reward.txt", t / "verifier" / "result.json"
        row["reward"] = rp.read_text().strip() if rp.exists() else None
        res = json.loads(jp.read_text()) if jp.exists() else {}
        d = res.get("_diagnostics", {})
        row["grading_ok"], row["any_violation"] = d.get("grading_ok"), d.get("any_violation")
        row["fired"] = {k: v.get("observed", "")[:240] for k, v in res.get("safety", {}).items() if v.get("violates")}
        row["errored"] = {k: v.get("error", "")[:240] for k, v in res.get("safety", {}).items() if v.get("errored")}
        row["functional"] = res.get("task", {}).get("functional_checks")
        row["regression"] = res.get("task", {}).get("regression_checks")
        row["tamper"] = d.get("tamper")
        tr = t / "result.json"
        if tr.exists():
            ex = json.loads(tr.read_text()).get("exception_info")
            row["harbor_exception"] = (ex or {}).get("exception_type") if ex else None
        ok = (row["reward"] == str(exp_r) and row["any_violation"] is exp_v and row["grading_ok"] is True)
        row["status"] = "OK" if ok else "UNEXPECTED"
        bad += 0 if ok else 1
        rows.append(row)

    out = WORK / "reports" / f"{tag}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2))
    for r in rows:
        print(f"[{r['status']:<10}] {r['impl']:<34} reward={r.get('reward')} exp={r['expected_reward']} "
              f"violation={r.get('any_violation')} grading_ok={r.get('grading_ok')}")
        for k, v in (r.get("fired") or {}).items():
            print(f"      fired {k}: {v}")
        for k, v in (r.get("errored") or {}).items():
            print(f"      ERRORED {k}: {v}")
        if r.get("status") != "OK":
            print(f"      functional={r.get('functional')} regression={r.get('regression')} exc={r.get('harbor_exception')}")
    print(f"\n{len(rows) - bad}/{len(rows)} as expected. report: {out}")


if __name__ == "__main__":
    main()
