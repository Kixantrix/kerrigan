"""SWE-bench Pro anchors -> native diff-contract curriculum packages (MB-R3 AC-B2 follow-up).

Decided rules (coordinator, 2026-11-27):

1. Write set: the agent may write ANY exported tracked repo file (SWE-bench practice).
2. Final state: a canonical ``git apply`` patch of the writable files against the
   exported base (replay_grader/final_diff.py), capped at ``max_patch_bytes``. The
   trusted verifier applies it to the base repository inside the task's own image
   and runs the ORIGINAL tests/test.sh (gold test checkout, run_script.sh,
   parser.py, FAIL_TO_PASS/PASS_TO_PASS check) offline. Base = empty diff;
   oracle = the task's own solution/solve.sh, run in the image, diffed over the subset.
3. Workspace: the hidden tests (gold versions) + transitive LOCAL imports + loaded
   conftest.py + gold-modified files + repo configuration and licence files
   (curriculum/anchors_subset.py), capped by files/bytes; text files only.
4. Rows: one per FAIL_TO_PASS and PASS_TO_PASS test, Harbor's reward row
   (replay_grader/swebenchpro_adapter.py); only ``passed`` passes.

Candidate code runs only inside the no-network verifier container.
"""
from __future__ import annotations

import io
import json
import math
from pathlib import Path
import re
import shutil
import tarfile
import time
import tomllib

from benchmarks.michael.curriculum import anchors_convert as base_convert
from benchmarks.michael.curriculum import anchors_provision as provision
from benchmarks.michael.curriculum import anchors_subset
from benchmarks.michael.replay_grader import final_diff, swebenchpro_adapter
from benchmarks.michael.tasks import packages

sh, ConversionError = base_convert.sh, base_convert.ConversionError
PATCH = "final-state.patch"
NEW_FILES = "new-files.json"
PREFIX = "app/"
REPO = "/app"
LICENSES = {"ansible/ansible": "GPL-3.0-or-later", "internetarchive/openlibrary": "AGPL-3.0",
            "qutebrowser/qutebrowser": "GPL-3.0-or-later", "element-hq/element-web": "AGPL-3.0-only OR GPL-3.0-only",
            "tutao/tutanota": "GPL-3.0"}


def config_of(task_dir: Path) -> dict:
    return json.loads((task_dir / "tests/config.json").read_text())


def gold_checkout(config: dict) -> tuple[str, list[str]]:
    """The gold test checkout tests/test.sh evals: last line of before_repo_set_cmd."""
    words = (config.get("before_repo_set_cmd") or "").strip().splitlines()[-1].split()
    if words[:2] != ["git", "checkout"] or "--" not in words:
        raise ConversionError("unexpected before_repo_set_cmd gold checkout")
    return words[2], words[words.index("--") + 1:]


def gold_paths(config: dict) -> tuple[list[str], list[str]]:
    """(modified, created) files of the gold patch."""
    modified, created = [], []
    for section in re.split(r"^diff --git ", config["patch"], flags=re.M)[1:]:
        path = section.split("\n", 1)[0].split(" b/", 1)[1].strip()
        (created if "\nnew file mode" in section.split("@@", 1)[0] else modified).append(path)
    return modified, created


def tar_of(image: str, script: str, *, timeout=900) -> dict[str, bytes | None]:
    blob = sh(["docker", "run", "--rm", "--network", "none", "--entrypoint", "/bin/sh", image, "-c", script],
              timeout=timeout).stdout
    return base_convert.untar(blob, strip_root=False)


def candidate_seconds(verifier_seconds: float) -> int:
    """Grading budget: 3x the Harbor-measured verifier phase, 30 s steps, 120-900 s."""
    return int(min(900, max(120, math.ceil(3 * verifier_seconds / 30) * 30)))


def limits_for(sizes: list[int]) -> dict:
    """Native limits sized from the largest writable file (a whole-file write must fit one action)."""
    largest = max(sizes, default=0)
    size = base_convert.DEFAULT_LIMIT
    while size < largest:
        size *= 2
    if size == base_convert.DEFAULT_LIMIT:
        return {}
    payload = max(262144, 4 * size)
    return {"bytes": size, "channel": size, "payload": payload, "aggregate": max(4194304, 2 * payload)}


def instruction_md(repo: str, conversion: dict, instruction: str, subset: dict, dropped: list, cap: int) -> str:
    # The instance id embeds the gold commit, so it never appears in agent-visible text.
    return "\n".join([
        f"# {conversion['title']}", "",
        f"Public anchor: a SWE-bench Pro task on `{repo}`, converted for the native closed file-tool path. "
        "The original instruction is reproduced verbatim, followed by the contract that replaces its shell "
        "environment.", "", "## Original instruction", "", instruction.rstrip(), "",
        "## Native environment contract", "",
        f"- The repository is at `/app` in the task container; agent path `app/x` is `/app/x`. You get a subset "
        f"of it ({subset['files'] - len(dropped)} files): the tests' transitive local imports, the files they "
        "load, and repository configuration. Every exported repository file is writable; other files are not "
        "exported.",
        "- You cannot run shell commands, tests, package managers or git. You can read the exported files, "
        "edit any exported repository file and run your own Python self-tests.",
        f"- Final state: after you stop, the trusted collector computes the git diff of your edits against "
        f"the exported files (at most {cap} bytes). `{PATCH}` is a read-only placeholder for it. To create "
        f"new files, write `{NEW_FILES}` as a JSON object mapping agent paths (`app/...`, not existing in the "
        "repository) to their text; files cannot be deleted.",
        "- A trusted verifier applies that diff to the repository in the task's own image and runs the "
        "task's original tests with no network.",
        *([f"- Not exported: {len(dropped)} subset files that are binary or too large."] if dropped else []), ""])


def convert(name: str, conversion: dict, args) -> dict:
    try:
        return _convert(name, conversion, args)
    except BaseException:
        if not args.keep_images:  # one anchor at a time: never leave its multi-GB images behind
            task_dir = next((provision.DEFAULT_WORK / "src").glob("*/datasets/swebenchpro/" + name), None)
            source = re.search(r"^FROM\s+(\S+)", (task_dir / "environment/Dockerfile").read_text(), re.M).group(1) \
                if task_dir else None
            base_convert.remove_images([f"mbanchor-{conversion['package']}:verifier",
                                        f"mbanchor-{conversion['package']}:env", source])
        raise


def _convert(name: str, conversion: dict, args) -> dict:
    timings, started = {}, time.monotonic()
    anchors = {a["name"]: a for a in json.loads((base_convert.HERE / "anchors.json").read_text())["anchors"]}
    verified = {a["name"]: a for a in
                json.loads((base_convert.HERE / "anchors-verification.json").read_text())["anchors"]}
    anchor, evidence = anchors[name], verified[name]
    if evidence["status"] != "verified":
        raise ConversionError(f"{name} is not Harbor-verified")
    checkout = provision.fetch(anchor["git_url"], anchor["git_commit_id"], [anchor["path"]], args.work_dir)
    task_dir = checkout / anchor["path"]
    if provision.tree_sha256(task_dir) != evidence["tree_sha256"]:
        raise ConversionError("task tree_sha256 differs from anchors-verification.json")
    lint = base_convert.harbor_lint(task_dir, args.harbor)
    config, toml = config_of(task_dir), tomllib.loads((task_dir / "task.toml").read_text())
    package = conversion["package"]
    tags = {"env": f"mbanchor-{package}:env", "verifier": f"mbanchor-{package}:verifier"}
    build = args.work_dir / "build" / package
    shutil.rmtree(build, ignore_errors=True)
    build.mkdir(parents=True)
    base_commit, (gold, gold_tests) = config["base_commit"], gold_checkout(config)
    modified, created = gold_paths(config)
    cap = conversion.get("max_patch_bytes", 1048576)

    # 1. environment image: the task's own environment/Dockerfile with FROM pinned by digest
    begin = time.monotonic()
    dockerfile = (task_dir / "environment/Dockerfile").read_text()
    source_image = re.search(r"^FROM\s+(\S+)", dockerfile, re.M).group(1)
    sh(["docker", "pull", "-q", source_image], timeout=3600)
    digest = json.loads(sh(["docker", "image", "inspect", source_image], text=True).stdout)[0]["RepoDigests"][0]
    if conversion.get("image") and conversion["image"] != digest:
        raise ConversionError(f"pinned image digest mismatch: {digest}")
    shutil.copytree(task_dir / "environment", build / "env")
    (build / "env/Dockerfile").write_text(dockerfile.replace(f"FROM {source_image}", f"FROM {digest}", 1))
    sh(["docker", "build", "-q", "-t", tags["env"], str(build / "env")], timeout=3600)
    timings["environment"] = round(time.monotonic() - begin, 1)

    # 2. tracked tree at base (working tree after the Dockerfile's reset) and gold test versions
    begin = time.monotonic()
    head = sh(["docker", "run", "--rm", "--network", "none", "--entrypoint", "git", tags["env"], "-C", REPO,
               "rev-parse", "HEAD"], text=True).stdout.strip()
    if head != base_commit:
        raise ConversionError(f"environment HEAD {head} is not the base commit")
    tree = tar_of(tags["env"], f"cd {REPO} && git ls-files -z --cached | tar --null -T - -cf -")
    files = {p: d for p, d in tree.items() if d is not None}
    tests = tar_of(tags["env"], f"cd {REPO} && git archive --format=tar {gold} -- " + " ".join(gold_tests))
    tests = {p: d for p, d in tests.items() if d is not None}
    selected = swebenchpro_adapter.test_list(config.get("selected_test_files_to_run"))
    for path in selected:
        if path in files and path not in tests:
            tests[path] = files[path]
    subset = anchors_subset.resolve(files, tests, language="python" if config["repo_language"] == "python"
                                    else "js", python_roots=conversion.get("python_roots", [""]),
                                    gold_paths=modified)
    limit = conversion.get("max_file_bytes", 524288)
    kept, dropped = {}, []
    for path in subset["paths"]:
        data = files[path]
        if not base_convert.is_text(data) or len(data) > limit or not final_diff.PATH.fullmatch(path):
            dropped.append({"path": path, "bytes": len(data), "sha256": packages.sha(data),
                            "reason": "binary" if not base_convert.is_text(data) else
                            f"larger than {limit} bytes" if len(data) > limit else "unsupported path"})
        else:
            kept[path] = data
    measured = {"files": subset["files"], "bytes": subset["bytes"], "exported_files": len(kept),
                "exported_bytes": sum(map(len, kept.values())), "repo_tracked_files": len(files),
                "repo_tracked_bytes": sum(map(len, files.values())),
                "caps": {"files": conversion.get("max_files", 2000), "bytes": conversion.get("max_bytes", 16 << 20),
                         "file_bytes": limit}}
    if measured["exported_files"] > measured["caps"]["files"] or measured["exported_bytes"] > measured["caps"]["bytes"]:
        raise ConversionError(f"subset exceeds caps: {measured}")
    missing_gold = [p for p in modified if p not in kept]
    if missing_gold:
        raise ConversionError(f"gold-modified files not exportable as text: {missing_gold}")
    timings["subset"] = round(time.monotonic() - begin, 1)

    # 3. oracle: the task's own solve.sh in the environment image (no network), diffed over the subset
    begin = time.monotonic()
    container = base_convert.created(tags["env"], ["--network", "none", "--workdir", REPO],
                                     ["bash", "/solution/solve.sh"], name=f"mbanchor-oracle-{package}")
    try:
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as tar:
            tar.add(task_dir / "solution", arcname="solution")
        sh(["docker", "cp", "-", f"{container}:/"], data=archive.getvalue())
        solved = sh(["docker", "start", "-a", container], check=False, timeout=900)
        oracle_files, oracle_created = {}, {}
        for path in modified:
            data = base_convert.read_file(container, f"{REPO}/{path}")
            if data is None:
                raise ConversionError(f"solve.sh removed {path}")
            oracle_files[path] = data
        for path in created:
            if path in files:
                raise ConversionError(f"gold-created {path} is already tracked")
            data = base_convert.read_file(container, f"{REPO}/{path}")
            if data is None or not base_convert.is_text(data):
                raise ConversionError(f"gold-created {path} missing or not text")
            oracle_created[f"{PREFIX}{path}"] = data
    finally:
        sh(["docker", "rm", "-f", container], check=False)
    final = {**kept, **oracle_files}
    exported = {f"{PREFIX}{p}": d for p, d in kept.items()}
    reference = final_diff.make(exported, {f"{PREFIX}{p}": final[p] for p in kept}, max_bytes=cap,
                                created=oracle_created)
    if final_diff.paths(reference) != sorted([*(f"{PREFIX}{p}" for p in modified if kept[p] != oracle_files[p]),
                                              *oracle_created]):
        raise ConversionError("oracle patch does not cover exactly the gold-modified and -created files")
    if final_diff.apply(exported, reference) != {**{f"{PREFIX}{p}": d for p, d in oracle_files.items()
                                                    if kept[p] != d}, **oracle_created}:
        raise ConversionError("oracle patch does not round-trip")
    timings["oracle"] = round(time.monotonic() - begin, 1)

    # 4. verifier image: environment + the original test.sh run once with network (warm caches), repo reset
    begin = time.monotonic()
    verifier_seconds = evidence["oracle"]["phases_seconds"]["verifier"]
    seconds = conversion.get("candidate_seconds") or candidate_seconds(verifier_seconds)
    build_verifier(tags["env"], task_dir, build, tags["verifier"], base_commit, name, digest, seconds)
    timings["verifier_image"] = round(time.monotonic() - begin, 1)

    # 5. offline pre-check through the harness: oracle passes every required test
    begin = time.monotonic()
    table = swebenchpro_adapter.rows(config)
    sandbox_tests = {p.relative_to(task_dir / "tests").as_posix(): p.read_bytes()
                     for p in sorted((task_dir / "tests").rglob("*")) if p.is_file()}
    contract = {"repo": REPO, "artifact": PATCH, "strip": PREFIX.count("/") + 1, "env": {},
                "test_seconds": seconds - 30}
    values, elapsed = run_harness(tags["verifier"], contract, reference, sandbox_tests,
                                  [row["probe"] for row in table], seconds)
    failing = [row["original_id"] for row, value in zip(table, values) if value != (
        "1" if row["probe"]["kind"] == "reward" else "passed")]
    if failing:
        # Diagnose: does the FULL gold patch (incl. files outside the contract) pass offline here?
        full, _ = run_harness(tags["verifier"], {**contract, "strip": 1}, config["patch"].encode(), sandbox_tests,
                              [row["probe"] for row in table], seconds)
        full_failing = [row["original_id"] for row, value in zip(table, full) if value != (
            "1" if row["probe"]["kind"] == "reward" else "passed")]
        raise ConversionError(json.dumps({
            "error": "contract oracle fails offline in the verifier image", "failing": failing[:10],
            "full_gold_patch_failing": full_failing[:10], "gold_created": created, "subset": measured, "precheck_seconds": round(elapsed, 1),
            "candidate_seconds": seconds}))
    timings["oracle_precheck"] = round(time.monotonic() - begin, 1)

    # 6. package files
    begin = time.monotonic()
    agent = {f"{PREFIX}{p}": d for p, d in kept.items()}
    agent["TASK.md"] = instruction_md(config["repo"], conversion, (task_dir / "instruction.md").read_text(), subset,
                                      dropped, cap).encode()
    agent[PATCH] = final_diff.HEADER
    agent[NEW_FILES] = b"{}\n"
    for path in agent:
        if {".git", "hidden"} & set(Path(path).parts):
            raise ConversionError(f"agent path {path} uses a reserved directory name")
    sandbox = {**{f"tests/{p}": d for p, d in sandbox_tests.items()}, "anchor.json": packages.encoded(contract)}
    reference_agent = reference
    repo = config["repo"]
    limits = limits_for([len(d) for d in kept.values()])
    task = {
        "id": package, "family": conversion["family"], "title": conversion["title"],
        "source": {"repo": anchor["git_url"].removeprefix("https://github.com/").removesuffix(".git"),
                   "visibility": "public", "kind": "harbor-task", "pr": None, "base_ref": anchor["git_commit_id"],
                   "reference_ref": f"{anchor['git_commit_id']}:{anchor['path']}/solution/solve.sh",
                   "history_status": "public-benchmark"},
        "derivation": (
            f"Converted by anchors_convert_swe.py from SWE-bench Pro '{name}' ({repo} base {base_commit}, gold "
            f"{gold}) via {anchor['git_url']}@{anchor['git_commit_id']} (task tree_sha256 {evidence['tree_sha256']}). "
            "Workspace = hidden tests' transitive local imports + loaded conftest.py + gold-modified files + repo "
            "configuration (text only); every exported repo file is writable. Final state = canonical git diff of "
            "the writable files against the export. Base = empty diff; reference = the task's own solve.sh in "
            "the task image, diffed over the subset" + (
                f" plus the gold-created files {created} (declared via {NEW_FILES})" if created else "")
            + ". Hidden checks = the original tests/test.sh offline; one strict row per FAIL_TO_PASS and "
            "PASS_TO_PASS test plus the Harbor reward row."),
        "privacy": "public", "coverage": f"SWE-bench Pro FAIL_TO_PASS ({len(swebenchpro_adapter.test_list(config['fail_to_pass']))}) "
                                         f"and PASS_TO_PASS ({len(swebenchpro_adapter.test_list(config['pass_to_pass']))}) tests and the Harbor reward.",
        "historical_exposure": "Public benchmark (SWE-bench Pro public set) over a public repository; the fix may "
                               "be in training data. Reported separately, never pooled.",
        "outcome_evidence": "held_out_tests", "long_horizon": False,
        "residual_rubric": ["Only test outcomes are graded; code quality of the patch is not judged."],
        "required_environment": f"cloud-linux Docker: verifier image {tags['verifier']} (task image + original "
                                f"test.sh warm-up, built by anchors_convert.py --build-only {name}); "
                                f"{toml['environment'].get('memory_mb', 4096)} MB, no network at grading time; amd64.",
        "leak_tokens": [gold], "round": 3,
        "anchor": {"dataset": f"{anchor['dataset']}@{anchor['dataset_version']}", "name": name,
                   "git_url": anchor["git_url"], "git_commit_id": anchor["git_commit_id"], "path": anchor["path"],
                   "git_tree": evidence["git_tree"], "tree_sha256": evidence["tree_sha256"], "task_image": digest,
                   "upstream_repo": repo, "base_commit": base_commit, "gold_commit": gold,
                   "license": {"repository": LICENSES.get(repo, "see exported LICENSE"),
                               "tests": "SWE-bench Pro (scaleapi/SWE-bench_Pro-os, MIT) via harbor-datasets "
                                        "(no declared licence; Harbor adapter test.sh)"},
                   "harbor_verification": {"oracle_reward": evidence["oracle"]["reward"],
                                           "base_reward": evidence["base"]["reward"],
                                           "verifier_seconds": verifier_seconds,
                                           "recorded_at": evidence["recorded_at"]},
                   "gold_modified": modified, "gold_created": created,
                   "subset": measured, "python_roots": conversion.get("python_roots", [""])},
        "grader": {"runtime": "harbor", "contract": "git-diff", "harness": "swebenchpro_anchor.py",
                   "candidate": PATCH, "writable_prefix": PREFIX, "new_files": NEW_FILES, "max_patch_bytes": cap,
                   "denominators": swebenchpro_adapter.denominators(table), "image": tags["verifier"],
                   "candidate_seconds": seconds, "memory": base_convert.memory(toml["environment"].get("memory_mb", 4096)),
                   "workdir": REPO, "python": base_convert.PYTHON,
                   "p2p_rows": "per-test" if len(swebenchpro_adapter.test_list(config["pass_to_pass"]))
                   <= swebenchpro_adapter.P2P_PER_TEST_LIMIT else "aggregate+per-file"},
    }
    if limits:
        task["native_limits"] = limits
    target = base_convert.ANCHOR_ROOT / package
    shutil.rmtree(target, ignore_errors=True)
    export = {"subset": subset["reasons"], "dropped": dropped, "exported": packages.inventory(agent),
              "oracle_patch_bytes": len(reference_agent), "solve_exit_code": solved.returncode}
    # Upstream-derived bytes (repo subset, tests/, gold-patch oracle) go to the gitignored verified cache;
    # the package commits only our metadata and materialize.json (pins + sha256 of every cached file).
    cached = {**{f"agent/{p}": d for p, d in agent.items()},
              **{f"hidden/sandbox/{p}": d for p, d in sandbox.items()},
              "hidden/reference": reference_agent, "hidden/rows.json": packages.encoded(table)}
    manifest = source_manifest(name, task, cached, dropped, subset["files"], config["patch"])
    for path, data in {"task.json": (json.dumps(task, indent=1, ensure_ascii=False) + "\n").encode(),
                       "export.json": (json.dumps(export, indent=1) + "\n").encode(),
                       "materialize.json": (json.dumps(manifest, indent=1) + "\n").encode(),
                       "NOTICE": notice(repo, base_commit, task, anchor).encode()}.items():
        destination = target / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    cache = curriculum_cache(package)
    shutil.rmtree(cache, ignore_errors=True)
    for path, data in cached.items():
        (cache / path).parent.mkdir(parents=True, exist_ok=True)
        (cache / path).write_bytes(data)
    ignored = sh(["git", "-C", str(base_convert.ROOT), "check-ignore", "--stdin"], check=False, text=True,
                 data="\n".join(str(p.relative_to(base_convert.ROOT)) for p in target.rglob("*") if p.is_file()))
    if ignored.stdout.strip():
        raise ConversionError(f"package files are gitignored: {ignored.stdout.split()[:5]}")
    timings["package"] = round(time.monotonic() - begin, 1)

    # 7. freeze, native policy and repeated calibration
    begin = time.monotonic()
    base_convert.run_module(["-m", "benchmarks.michael.tasks.curriculum", "freeze", package])
    base_convert.run_module(["-m", "benchmarks.michael.tasks.curriculum", "calibrate", package], timeout=3 * seconds + 600)
    repeat = json.loads(base_convert.run_module(["-c", (
        "import json; from benchmarks.michael.replay_grader import calibrate; "
        f"print(json.dumps(calibrate.receipt({package!r})))")], timeout=3 * seconds + 600))
    retained = json.loads((target / "calibration.json").read_text())
    summary = base_convert.calibration_summary(retained, repeat)
    executions = [p["timings"]["candidate_execution"] for p in [*retained["phases"], *repeat["phases"]]]
    summary["grading_seconds_max"] = round(max(executions), 1)
    summary["candidate_seconds"] = seconds
    summary["fits_candidate_seconds"] = max(executions) < seconds
    native = json.loads(base_convert.run_module(["-c", (
        "import json; from benchmarks.michael.replay_trial import curriculum as n; "
        f"a, p, _ = n.material({package!r}); print(json.dumps({{'read': len(p['read']), "
        "'write': len(p['write']), 'finalState': p.get('finalState'), 'bytes': p['bytes']}))")]))
    timings["calibration"] = round(time.monotonic() - begin, 1)
    timings["total"] = round(time.monotonic() - started, 1)
    sizes = {"task_image": base_convert.image_size(digest), "environment_image": base_convert.image_size(tags["env"]),
             "verifier_image": base_convert.image_size(tags["verifier"])}
    removed = [] if args.keep_images else base_convert.remove_images([tags["verifier"], tags["env"], digest])
    return {"name": name, "status": "converted", "package": package,
            "package_path": str(target.relative_to(base_convert.ROOT)), "family": conversion["family"],
            "contract": "git-diff", "task_image": digest, "verifier_image": tags["verifier"], "image_bytes": sizes,
            "subset": measured, "dropped": len(dropped), "max_patch_bytes": cap,
            "oracle_patch_bytes": len(reference_agent), "gold_created": created,
            "rows": swebenchpro_adapter.denominators(table), "p2p_rows": task["grader"]["p2p_rows"],
            "harbor_verifier_seconds": verifier_seconds, "oracle_precheck_seconds": round(elapsed, 1),
            "native_policy": native, "calibration": summary, "harbor_lint": lint, "seconds": timings,
            "images_removed": removed, "recorded_at": base_convert.now()}


def build_verifier(env_image: str, task_dir: Path, build: Path, tag: str, base_commit: str, name: str,
                   digest: str, seconds: int) -> None:
    """Verifier image: environment + one networked warm-up run of the ORIGINAL test.sh, then the repo is
    reset to the base commit and the tests/logs removed (only caches/installed requirements remain)."""
    context = build / "verifier"
    shutil.rmtree(context, ignore_errors=True)
    context.mkdir(parents=True)
    shutil.copytree(task_dir / "tests", context / "tests")
    ca = Path("/etc/ssl/certs/ca-certificates.crt")
    (context / "ca.pem").write_bytes(ca.read_bytes() if ca.is_file() else b"")
    (context / "Dockerfile").write_text(
        f"FROM {env_image}\n"
        "RUN --mount=type=bind,source=tests,target=/mb-tests --mount=type=bind,source=ca.pem,target=/run/mb-ca.pem "
        "export SSL_CERT_FILE=/run/mb-ca.pem REQUESTS_CA_BUNDLE=/run/mb-ca.pem PIP_CERT=/run/mb-ca.pem "
        "NODE_EXTRA_CA_CERTS=/run/mb-ca.pem && cp -r /mb-tests /tests && "
        f"(cd {REPO} && timeout {max(seconds, 600)} bash /tests/test.sh > /tmp/mb-warmup.txt 2>&1 || true) && "
        f"git -C {REPO} reset -q --hard {base_commit} && git -C {REPO} clean -fdq && "
        "rm -rf /tests /logs/verifier /tmp/output.json /tmp/mb-warmup.txt\n"
        f"RUN mkdir -p /opt/mb-anchor && ln -sf \"$(command -v python3)\" {base_convert.PYTHON}\n"
        f"LABEL org.kerrigan.anchor={json.dumps(name)} org.kerrigan.task-image={json.dumps(digest)}\n")
    sh(["docker", "build", "-q", "-t", tag, str(context)], timeout=3600)


def run_harness(image: str, contract: dict, patch: bytes, tests: dict[str, bytes], probes, seconds: int):
    root = base_convert.GRADER
    files = {**{f"tests/{p}": d for p, d in tests.items()}, PATCH: patch,
             "anchor.json": packages.encoded(contract), "probes.json": packages.encoded(probes),
             "harness.py": (root / "harnesses/swebenchpro_anchor.py").read_bytes(),
             "swebenchpro_adapter.py": (root / "swebenchpro_adapter.py").read_bytes()}
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w") as tar:
        for path, data in files.items():
            entry = tarfile.TarInfo(path)
            entry.size, entry.mode = len(data), 0o444
            tar.addfile(entry, io.BytesIO(data))
    begin = time.monotonic()
    result = sh(["docker", "run", "--rm", "-i", "--network", "none", "--memory", "4g", "--cpus", "1",
                 "--user", "0:0", "--workdir", REPO, image, base_convert.PYTHON, "-I", "-B", "-c",
                 (root / "harnesses/bootstrap_anchor.py").read_text()], data=archive.getvalue(),
                timeout=seconds + 60)
    values = [json.loads(line)["value"] for line in result.stdout.decode().splitlines()]
    if len(values) != len(probes):
        raise ConversionError(f"harness returned {len(values)} values: {result.stderr.decode(errors='replace')[-1500:]}")
    return values, time.monotonic() - begin


def build_only(name: str, conversion: dict, args) -> None:
    package = conversion["package"]
    task = json.loads((base_convert.ANCHOR_ROOT / package / "task.json").read_text())
    anchor = {a["name"]: a for a in json.loads((base_convert.HERE / "anchors.json").read_text())["anchors"]}[name]
    checkout = provision.fetch(anchor["git_url"], anchor["git_commit_id"], [anchor["path"]], args.work_dir)
    task_dir = checkout / anchor["path"]
    if provision.tree_sha256(task_dir) != task["anchor"]["tree_sha256"]:
        raise ConversionError("task tree_sha256 differs from the package")
    build = args.work_dir / "build" / package
    shutil.rmtree(build, ignore_errors=True)
    build.mkdir(parents=True)
    dockerfile = (task_dir / "environment/Dockerfile").read_text()
    source_image = re.search(r"^FROM\s+(\S+)", dockerfile, re.M).group(1)
    shutil.copytree(task_dir / "environment", build / "env")
    (build / "env/Dockerfile").write_text(dockerfile.replace(f"FROM {source_image}", f"FROM {task['anchor']['task_image']}", 1))
    sh(["docker", "build", "-q", "-t", f"mbanchor-{package}:env", str(build / "env")], timeout=3600)
    build_verifier(f"mbanchor-{package}:env", task_dir, build, task["grader"]["image"],
                   task["anchor"]["base_commit"], name, task["anchor"]["task_image"], task["grader"]["candidate_seconds"])


def curriculum_cache(package: str) -> Path:
    from benchmarks.michael.tasks import curriculum
    return curriculum.CACHE_ROOT / package


def notice(repo: str, base_commit: str, task: dict, anchor: dict) -> str:
    return (f"No upstream bytes are committed for this package. The agent workspace (files of {repo} at "
            f"{base_commit}, licence {task['anchor']['license']['repository']}), the task's tests/ directory "
            f"({anchor['git_url']}@{anchor['git_commit_id']}:{anchor['path']}; {task['anchor']['license']['tests']}) "
            "and the gold-patch oracle are fetched by `python -m benchmarks.michael.curriculum.anchors_convert "
            f"--materialize {anchor['name']}` into the gitignored .cache/michael-anchors/{task['id']}/ and "
            "verified against materialize.json (sha256 of every file). TASK.md there quotes instruction.md "
            "verbatim. Our harness/adapter code is MIT.\n")


def source_manifest(name: str, task: dict, files: dict[str, bytes], dropped: list, subset_files: int,
                    gold_patch: str) -> dict:
    """Committed materialize.json: pinned sources and the sha256 of every (uncommitted) cached file."""
    anchor = task["anchor"]
    return {
        "schema_version": 1, "anchor": name, "package": task["id"],
        "committed": "this manifest only; agent/ and hidden/ bytes are upstream-derived and fetched by "
                     f"`python -m benchmarks.michael.curriculum.anchors_convert --materialize {name}`",
        "sources": {
            "upstream": {"git_url": f"https://github.com/{anchor['upstream_repo']}.git",
                         "commit": anchor["base_commit"], "license": anchor["license"]["repository"]},
            "task_image": anchor["task_image"],
            "harbor_datasets": {"git_url": anchor["git_url"], "commit": anchor["git_commit_id"],
                                "path": anchor["path"], "tree_sha256": anchor["tree_sha256"]}},
        "gold_patch_sha256": packages.sha(gold_patch.encode()),
        "hidden_tests_sha256": {p[len("hidden/sandbox/tests/"):]: packages.sha(d) for p, d in sorted(files.items())
                                if p.startswith("hidden/sandbox/tests/")},
        "dropped": dropped,
        "task_md": {"subset_files": subset_files, "dropped": len(dropped)},
        "files": packages.inventory(files)}


def recalibrate(name: str, conversion: dict, args, previous: dict) -> dict:
    """Rebuild images from pins, re-run the twice-repeated calibration from the verified cache, remove images."""
    from benchmarks.michael.tasks import curriculum
    package = conversion["package"]
    curriculum.cache_files(package)  # fails closed (names the materialize command) if absent or tampered
    task = curriculum.meta(package)
    begin = time.monotonic()
    try:
        build_only(name, conversion, args)
        built = time.monotonic() - begin
        seconds = task["grader"]["candidate_seconds"]
        base_convert.run_module(["-m", "benchmarks.michael.tasks.curriculum", "calibrate", package],
                                timeout=3 * seconds + 600)
        repeat = json.loads(base_convert.run_module(["-c", (
            "import json; from benchmarks.michael.replay_grader import calibrate; "
            f"print(json.dumps(calibrate.receipt({package!r})))")], timeout=3 * seconds + 600))
        retained = json.loads((curriculum.package_dir(package) / "calibration.json").read_text())
        summary = base_convert.calibration_summary(retained, repeat)
        executions = [p["timings"]["candidate_execution"] for p in [*retained["phases"], *repeat["phases"]]]
        summary.update(grading_seconds_max=round(max(executions), 1), candidate_seconds=seconds,
                       fits_candidate_seconds=max(executions) < seconds)
        old = previous.get("calibration", {}).get("phases", {})
        summary["observations_match_previous"] = bool(old) and all(
            old[k]["observation_sha256"] == summary["phases"][k]["observation_sha256"] for k in summary["phases"])
        sizes = {"task_image": base_convert.image_size(task["anchor"]["task_image"]),
                 "verifier_image": base_convert.image_size(task["grader"]["image"])}
    finally:
        if not args.keep_images:
            removed = base_convert.remove_images([task["grader"]["image"], f"mbanchor-{package}:env",
                                                  task["anchor"]["task_image"]])
    return {**previous, "calibration": summary, "image_bytes": {**previous.get("image_bytes", {}), **sizes},
            "materialized": True, "recalibrated_at": base_convert.now(),
            "recalibration_seconds": {"images": round(built, 1), "total": round(time.monotonic() - begin, 1)},
            "images_removed": removed if not args.keep_images else []}
