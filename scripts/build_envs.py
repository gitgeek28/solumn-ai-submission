#!/usr/bin/env python3
"""Assemble environments/<env>/ from families/<family>/.

A family is authored once (base/: repo, Dockerfiles, grader, reference solution,
task.toml.tmpl). Each variant differs ONLY in where the planted directive is
inserted: the variant's marker line is replaced by its snippet, every other
placement marker line is removed. The shared grader core (_shared/grader_lib.py)
is copied into each tests/ (copied, not symlinked, so every env is self-contained).

usage: scripts/build_envs.py [family ...]      (default: every family)
       scripts/build_envs.py --check           (verify environments/ is up to date)
"""
import filecmp
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAMILIES = ROOT / "families"
OUT = ROOT / "environments"
TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yaml", ".yml", ".json", ".sh", ".cfg", ".ini", ".csv", ""}


def render_variant(fam_dir: Path, fam: dict, var: dict, dst: Path) -> None:
    base = fam_dir / "base"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(base, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "task.toml.tmpl"))
    snippet = (fam_dir / var["snippet"]).read_text().rstrip("\n")
    markers = [f"@@{m}@@" for m in fam["markers"]]
    mine = f"@@{var['marker']}@@"
    hits = 0
    for f in sorted(dst.rglob("*")):
        if not f.is_file() or f.suffix not in TEXT_SUFFIXES:
            continue
        text = f.read_text()
        if not any(m in text for m in markers):
            continue
        out = []
        for line in text.split("\n"):
            if mine in line:
                out.append(snippet)
                hits += 1
            elif any(m in line for m in markers):
                continue
            else:
                out.append(line)
        f.write_text("\n".join(out))
    if hits != 1:
        raise SystemExit(f"{var['env']}: marker {mine} matched {hits} lines (expected exactly 1)")
    tmpl = (base / "task.toml.tmpl").read_text()
    for k, v in {"ENV": var["env"], "PLACEMENT": var["placement"], "LOCATION": var["location"],
                 "ROLE": var["role"]}.items():
        tmpl = tmpl.replace("{{" + k + "}}", v)
    (dst / "task.toml").write_text(tmpl)
    shutil.copy(ROOT / "_shared" / "grader_lib.py", dst / "tests" / "grader_lib.py")
    # bake per-env integrity hashes (not content) of the rendered repo, so graders
    # can detect tampering without any directive text living under tests/.
    import hashlib
    repo = dst / "environment" / "repo"
    hashes = {}
    if repo.exists():
        for f in sorted(repo.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                hashes[str(f.relative_to(repo))] = hashlib.sha256(f.read_bytes()).hexdigest()
        (dst / "tests" / "_pristine_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True))
    for sh in list(dst.rglob("*.sh")):
        sh.chmod(0o755)


def families(selected):
    for fam_dir in sorted(FAMILIES.iterdir()):
        if (fam_dir / "family.json").exists() and (not selected or fam_dir.name in selected):
            yield fam_dir, json.loads((fam_dir / "family.json").read_text())


def dirs_equal(a: Path, b: Path) -> bool:
    cmp = filecmp.dircmp(a, b, ignore=["__pycache__", "reward.txt", "result.json", ".DS_Store"])
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    _, mismatch, errors = filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)
    if mismatch or errors:
        return False
    return all(dirs_equal(a / d, b / d) for d in cmp.common_dirs)


def main():
    args = sys.argv[1:]
    check = "--check" in args
    selected = [a for a in args if not a.startswith("--")]
    stale = []
    for fam_dir, fam in families(selected):
        for var in fam["variants"]:
            dst = OUT / var["env"]
            if check:
                with tempfile.TemporaryDirectory() as td:
                    tmp = Path(td) / var["env"]
                    render_variant(fam_dir, fam, var, tmp)
                    if not dst.exists() or not dirs_equal(tmp, dst):
                        stale.append(var["env"])
                continue
            # keep packaged evidence (reward.txt/result.json) across rebuilds
            keep = {n: (dst / n).read_bytes() for n in ("reward.txt", "result.json") if (dst / n).exists()}
            render_variant(fam_dir, fam, var, dst)
            for n, data in keep.items():
                (dst / n).write_bytes(data)
            print(f"built environments/{var['env']}  ({var['role']}, placement={var['placement']})")
    if check:
        print("up to date" if not stale else f"STALE: {stale}")
        sys.exit(1 if stale else 0)


if __name__ == "__main__":
    main()
