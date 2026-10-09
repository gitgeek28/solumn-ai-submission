#!/usr/bin/env python3
"""Static gate for the submission: every environment directory, and optionally the
final archive, is checked against the brief and against the harness traps found
during Phase 0. Exits non-zero on any ERROR.

usage:
  lint_submission.py [--envs environments] [--archive submission.tar.gz] [--harbor-python PATH]

Checks per environment
  * task.toml parses under Harbor's own TaskConfig model; `artifacts` is top-level
    (not swallowed by a preceding table such as [metadata])
  * separate verifier with a baked tests/Dockerfile and an executable tests/test.sh
  * network_mode = "no-network" for the agent and verifier environments
  * instruction.md, solution/solve.sh present; the planted directive text never
    appears in instruction.md or tests/
  * every FROM is digest-pinned; no `|| true` after installs; compose services do
    not bind-mount host paths; sidecars are not addressed by compose DNS name
  * a reward.txt (single char 0/1) and a brief-shaped result.json sit in the env dir
Repository / archive
  * the endpoint key never appears outside .env; no .env, PDF, plan or jobs/ in the archive
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

KEY_PREFIX = "sk-" + "rlej-"   # split so this file never matches its own scan
FORBIDDEN_IN_ARCHIVE = [re.compile(p) for p in (r"(^|/)\.env$", r"\.pdf$", r"(^|/)plan.*\.md$", r"(^|/)jobs/")]
DEFAULT_HARBOR_PY = Path.home() / ".local/share/uv/tools/harbor/bin/python"

problems = []


def err(where, msg):
    problems.append(("ERROR", where, msg))


def warn(where, msg):
    problems.append(("WARN", where, msg))


def directive_lines(root: Path):
    """Distinctive lines of every planted snippet (families/*/placements/*/snippet.txt)."""
    lines = set()
    for snip in root.glob("families/*/placements/*/snippet.txt"):
        for line in snip.read_text().splitlines():
            s = re.sub(r"^[\s#*\"`>-]+|[\s\"`,]+$", "", line).strip()
            if len(s) >= 30:
                lines.add(s)
    return lines


def check_toml(env: Path, harbor_py: Path):
    toml_path = env / "task.toml"
    if not toml_path.exists():
        err(env.name, "task.toml missing")
        return None
    script = r'''
import json, sys, tomllib
from harbor.models.task.config import TaskConfig
raw = open(sys.argv[1], "rb").read().decode()
data = tomllib.loads(raw)
cfg = TaskConfig.model_validate_toml(raw)
v = cfg.verifier
print(json.dumps({
  "top_level_artifacts": data.get("artifacts", []),
  "metadata_artifacts": "artifacts" in data.get("metadata", {}),
  "artifacts": [a if isinstance(a, str) else a.model_dump() for a in cfg.artifacts],
  "env_network": cfg.environment.network_mode.value,
  "verifier_mode": (v.environment_mode.value if v.environment_mode else None),
  "verifier_env_network": (v.environment.network_mode.value if v.environment else None),
  "collect": [c.model_dump() for c in v.collect],
  "schema_version": cfg.schema_version,
}))
'''
    py = str(harbor_py) if harbor_py.exists() else sys.executable
    cp = subprocess.run([py, "-c", script, str(toml_path)], capture_output=True, text=True)
    if cp.returncode != 0:
        err(env.name, f"task.toml does not validate under Harbor's TaskConfig: {cp.stderr.strip()[-400:]}")
        return None
    info = json.loads(cp.stdout)
    if info["metadata_artifacts"]:
        err(env.name, "`artifacts` sits under [metadata] (TOML table scoping): Harbor would transfer nothing")
    if not info["top_level_artifacts"]:
        err(env.name, "no top-level `artifacts`: the separate verifier would see none of the agent's work")
    if info["env_network"] != "no-network":
        err(env.name, f"[environment].network_mode is {info['env_network']!r}, expected 'no-network'")
    if info["verifier_mode"] not in ("separate", None) or (info["verifier_mode"] is None and info["verifier_env_network"] is None):
        err(env.name, f"verifier is not in separate mode ({info['verifier_mode']})")
    if info["verifier_env_network"] not in ("no-network", None):
        err(env.name, f"[verifier.environment].network_mode is {info['verifier_env_network']!r}")
    if info["schema_version"] != "1.4":
        warn(env.name, f"schema_version {info['schema_version']}")
    return info


def check_files(env: Path, snippets):
    for rel in ("instruction.md", "solution/solve.sh", "tests/test.sh", "tests/Dockerfile"):
        if not (env / rel).exists():
            err(env.name, f"{rel} missing" + (" (separate verifier would fall back to the agent image and upload tests into it)" if rel == "tests/Dockerfile" else ""))
    for rel in ("solution/solve.sh", "tests/test.sh"):
        p = env / rel
        if p.exists() and not os.access(p, os.X_OK):
            warn(env.name, f"{rel} is not executable (Harbor chmods it, but keep the bit for local runs)")

    instr = (env / "instruction.md").read_text() if (env / "instruction.md").exists() else ""
    for line in snippets:
        if line in instr:
            err(env.name, f"planted directive text appears in instruction.md: {line[:70]!r}")
    for p in (env / "tests").rglob("*"):
        if p.is_file() and p.suffix in (".py", ".sh", ".md", ".txt", ".json"):
            text = p.read_text(errors="ignore")
            for line in snippets:
                if line in text:
                    err(env.name, f"planted directive text appears in tests/{p.relative_to(env / 'tests')}")
                    break

    for df in list(env.rglob("Dockerfile")):
        text = df.read_text()
        for m in re.finditer(r"^\s*FROM\s+(\S+)", text, re.M):
            ref = m.group(1)
            if "@sha256:" not in ref and not ref.startswith("$"):
                err(env.name, f"{df.relative_to(env)}: base image not digest-pinned: {ref}")
        for m in re.finditer(r"^\s*RUN\s.*$", text, re.M):
            if re.search(r"(pip|apt-get|npm)\b.*\|\|\s*true", m.group(0)):
                err(env.name, f"{df.relative_to(env)}: install masked with `|| true`: {m.group(0)[:90]}")
    if (env / "tests/Dockerfile").exists() and "test.sh" not in (env / "tests/Dockerfile").read_text() \
            and "COPY . /tests" not in (env / "tests/Dockerfile").read_text():
        err(env.name, "tests/Dockerfile does not appear to bake /tests/test.sh")

    compose = env / "environment" / "docker-compose.yaml"
    if compose.exists():
        text = compose.read_text()
        services = re.findall(r"^  ([A-Za-z0-9][\w.-]*):\s*$", text, re.M)
        for m in re.finditer(r"^\s*-\s*\.{1,2}/[^:]+:", text, re.M):
            err(env.name, f"docker-compose.yaml bind-mounts a host path ({m.group(0).strip()}): bake it into a build context")
        for svc in services:
            if svc == "main":
                continue
            pat = re.compile(rf"https?://{re.escape(svc)}:\d+")
            for p in (env / "environment").rglob("*"):
                if p.is_file() and p.stat().st_size < 2_000_000:
                    if pat.search(p.read_text(errors="ignore")):
                        err(env.name, f"{p.relative_to(env)} addresses sidecar '{svc}' by DNS name; under no-network only 127.0.0.1 works")
                        break


def check_outputs(env: Path):
    rt, rj = env / "reward.txt", env / "result.json"
    if not rt.exists() or not rj.exists():
        warn(env.name, "reward.txt / result.json not in the env dir yet (the brief requires both in the archive)")
        return
    if rt.read_text() not in ("0", "1"):
        err(env.name, f"reward.txt must be a single character 0 or 1, got {rt.read_text()!r}")
    try:
        r = json.loads(rj.read_text())
    except Exception as e:
        err(env.name, f"result.json is not valid JSON: {e}")
        return
    if not isinstance(r.get("task", {}).get("task_completed"), bool):
        err(env.name, "result.json: task.task_completed missing or not a bool")
    if not r.get("safety") or not all(isinstance(v.get("violates"), bool) for v in r["safety"].values()):
        err(env.name, "result.json: safety.<check>.violates missing or not a bool")


def scan_secrets(root: Path, label):
    for p in root.rglob("*"):
        if not p.is_file() or p.name == ".env" or ".git" in p.parts or p.stat().st_size > 20_000_000:
            continue
        try:
            data = p.read_bytes()
        except Exception:
            continue
        if KEY_PREFIX.encode() in data:
            err(label, f"endpoint key found in {p.relative_to(root)}")
        if p.suffix == ".pdf":
            err(label, f"{p.relative_to(root)}: the assignment PDF contains the endpoint key in plain text")


def check_archive(path: Path, snippets, harbor_py):
    with tempfile.TemporaryDirectory() as td, tarfile.open(path) as tf:
        names = tf.getnames()
        for n in names:
            for pat in FORBIDDEN_IN_ARCHIVE:
                if pat.search(n):
                    err("archive", f"must not ship: {n}")
        tf.extractall(td, filter="data")
        roots = [Path(td)] + [p for p in Path(td).iterdir() if p.is_dir()]
        base = next((r for r in roots if (r / "environments").is_dir()), None)
        if base is None:
            err("archive", "no environments/ directory at the archive root")
            return
        for req in ("results", "QUALITY_BAR.md", "README.md"):
            if not (base / req).exists():
                err("archive", f"{req} missing")
        envs = sorted(p for p in (base / "environments").iterdir() if p.is_dir())
        if len(envs) != 9:
            warn("archive", f"{len(envs)} environments (brief: nine; fewer is allowed if the README says so)")
        for env in envs:
            check_toml(env, harbor_py)
            check_files(env, snippets)
            check_outputs(env)
        scan_secrets(base, "archive")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--envs", default="environments")
    ap.add_argument("--archive")
    ap.add_argument("--harbor-python", default=str(DEFAULT_HARBOR_PY))
    a = ap.parse_args()
    root, harbor_py = Path(a.root), Path(a.harbor_python)
    snippets = directive_lines(root)
    if a.archive:
        check_archive(Path(a.archive), snippets, harbor_py)
    else:
        envs = sorted(p for p in (root / a.envs).iterdir() if p.is_dir() and not p.name.startswith("_"))
        for env in envs:
            check_toml(env, harbor_py)
            check_files(env, snippets)
            check_outputs(env)
        for sub in ("environments", "results", "_shared", "families", "scripts"):
            if (root / sub).exists():
                scan_secrets(root / sub, sub)
        cp = subprocess.run(["git", "-C", str(root), "grep", "-nIiE", "|".join(["cl" + "aude", "anth" + "ropic", "co-authored-by", "generated with"])],
                            capture_output=True, text=True)
        for line in cp.stdout.splitlines():
            if "plan (" not in line and not line.startswith("_shared/tests/lint_submission.py:"):
                err("repo", f"attribution text in tracked file: {line[:120]}")
    errors = [p for p in problems if p[0] == "ERROR"]
    for level, where, msg in problems:
        print(f"[{level}] {where}: {msg}")
    print(f"\n{len(errors)} error(s), {len(problems) - len(errors)} warning(s), {len(snippets)} directive lines tracked")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
