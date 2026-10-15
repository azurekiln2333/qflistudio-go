#!/usr/bin/env python3
"""Verify every Go curriculum topic: compile and run its real code.

For each ``topics/T<NNN>.json``:

1. Assert ``tutorial.code`` is byte-identical to the body of the matching file
   in ``samples/T<NNN>/`` (the code shown in the UI must be the code that runs).
2. Compile and run the sample with the pinned official Go SDK using the topic's
   ``runCommand`` and assert the declared ``verification`` result.
3. Write a **separate** variant of ``example.code`` into a scratch dir and run it
   with the same assertion, so a variant example is verified on its own and never
   silently passed because the tutorial passed.

Standard library only. Prints one line per topic and a final summary. Exits
non-zero if any topic fails.

Usage:
    python tool/go_curriculum/verify.py [--only T001,T002] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
TOPICS_DIR = TOOL_DIR / "topics"
SAMPLES_DIR = TOOL_DIR / "samples"
DEFAULT_GO = Path(
    os.environ.get(
        "QFLI_GO_CURRICULUM_GO",
        str(Path(__file__).resolve().parents[2]
            / "native" / "build" / "go-sdk-1.27.1" / "go" / "bin" / "go.exe"),
    )
)

EVIDENCE_DIR = TOOL_DIR / "evidence"


class VerificationError(Exception):
    pass


def find_go(explicit: Path | None) -> Path:
    if explicit is not None:
        path = Path(explicit)
        # An explicit --go must be a real file: never silently fall back to the
        # default, or a typo would run a different SDK than the user asked for.
        # Resolve to an absolute path because run_command binds go.parent onto
        # PATH while the child runs with cwd=<sample dir>; a relative --go would
        # otherwise become an impossible PATH entry and every topic would fail
        # with "'go' is not recognized".
        if not path.is_file():
            raise VerificationError(f"--go SDK not found: {explicit}")
        return path.resolve()
    if DEFAULT_GO.is_file():
        return DEFAULT_GO.resolve()
    raise VerificationError(
        "official Go SDK not found; set QFLI_GO_CURRICULUM_GO or pass --go"
    )


def go_env() -> dict:
    env = dict(os.environ)
    env["GOMAXPROCS"] = "2"
    env["GOFLAGS"] = "-p=1"
    env["GOTOOLCHAIN"] = "local"
    env.setdefault("GOCACHE", str(TOOL_DIR / ".gocache"))
    return env


def sample_file_for(topic: dict) -> Path:
    files = topic.get("sampleFiles") or []
    if not files:
        raise VerificationError(f"{topic['id']}: sampleFiles is empty")
    tutorial_code = topic["tutorial"]["code"]
    sample_dir = SAMPLES_DIR / topic["id"]
    # Prefer a .go file whose bytes equal the tutorial code; else the first file.
    for name in files:
        candidate = sample_dir / name
        if candidate.is_file() and candidate.read_text(encoding="utf-8") == tutorial_code:
            return candidate
    first = sample_dir / files[0]
    if not first.is_file():
        raise VerificationError(f"{topic['id']}: sample {first} missing")
    return first


def check_code_matches_sample(topic: dict) -> None:
    tutorial_code = topic["tutorial"]["code"]
    sample_dir = SAMPLES_DIR / topic["id"]
    for name in topic.get("sampleFiles") or []:
        candidate = sample_dir / name
        if not candidate.is_file():
            # Non-Go support files (e.g. go.mod) may be listed; only require
            # that any listed file exists, and that some .go file equals code.
            if name.endswith(".go"):
                raise VerificationError(f"{topic['id']}: sampleFiles {name} missing")
    # Compare the JSON-decoded code (real newlines, no extra unescaping) against
    # the sample file read verbatim; a mismatch means the UI shows code that is
    # not what runs.
    matched = any(
        (sample_dir / name).is_file()
        and name.endswith(".go")
        and (sample_dir / name).read_text(encoding="utf-8") == tutorial_code
        for name in (topic.get("sampleFiles") or [])
    )
    if not matched and (sample_dir / "main.go").is_file():
        matched = (sample_dir / "main.go").read_text(encoding="utf-8") == tutorial_code
    if not matched:
        raise VerificationError(
            f"{topic['id']}: tutorial.code does not match any sampleFiles entry"
        )


def run_command(command: str, workdir: Path, go: Path) -> subprocess.CompletedProcess:
    # The declared command assumes `go` on PATH; bind the pinned SDK to it.
    env = go_env()
    env["PATH"] = str(go.parent) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        command,
        cwd=workdir,
        env=env,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )


def assert_result(topic: dict, proc: subprocess.CompletedProcess) -> str:
    kind = topic["verification"]["kind"]
    expected = topic["verification"].get("expected", "")
    if kind == "stdout-exact":
        actual = proc.stdout.replace("\r\n", "\n").strip()
        want = expected.replace("\r\n", "\n").strip()
        if proc.returncode != 0:
            raise VerificationError(f"exit {proc.returncode}: {proc.stderr.strip()}")
        if actual != want:
            raise VerificationError(f"stdout mismatch:\n--want--\n{want}\n--got--\n{actual}")
        return actual
    if kind in ("stdout-sorted", "stdout-normalized"):
        actual_lines = [
            line.strip()
            for line in proc.stdout.replace("\r\n", "\n").split("\n")
            if line.strip()
        ]
        want_lines = [
            line.strip()
            for line in expected.replace("\r\n", "\n").split("\n")
            if line.strip()
        ]
        if kind == "stdout-sorted":
            actual_lines.sort()
            want_lines.sort()
        if proc.returncode != 0:
            raise VerificationError(f"exit {proc.returncode}: {proc.stderr.strip()}")
        if actual_lines != want_lines:
            raise VerificationError(
                f"normalized mismatch: want {want_lines} got {actual_lines}"
            )
        return "\n".join(actual_lines)
    if kind == "test-pass":
        if proc.returncode != 0:
            raise VerificationError(f"go test failed: {proc.stderr.strip()}")
        return "test-pass"
    if kind == "bench-exists":
        if proc.returncode != 0 or "Benchmark" not in proc.stdout:
            raise VerificationError(
                f"benchmark did not run: exit {proc.returncode} {proc.stdout.strip()}"
            )
        return "bench-exists"
    raise VerificationError(f"unknown verification kind {kind}")


def verify_variant(topic: dict, go: Path) -> str:
    """Run example.code on its own, unless it equals the tutorial code.

    The variant is asserted against the example's own ``expectedOutput`` so a
    deliberately different example is verified on its own terms.
    """
    example = topic["example"]
    example_code = example["code"]
    if example_code == topic["tutorial"]["code"]:
        return "same-as-tutorial"
    with tempfile.TemporaryDirectory(prefix=f"qfli_{topic['id']}_") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "go.mod").write_text(
            "module qfli.example\n\ngo 1.21\n", encoding="utf-8"
        )
        (tmp_path / "main.go").write_text(example_code, encoding="utf-8")
        proc = run_command("go run .", tmp_path, go)
        # Assert the example's own expected output, not the tutorial's.
        kind = topic["verification"]["kind"]
        expected = example["expectedOutput"]
        if kind in ("stdout-exact", "stdout-sorted", "stdout-normalized"):
            return assert_result(
                {"verification": {"kind": kind, "expected": expected}}, proc
            )
        return assert_result(topic, proc)


def _first_token(command: str) -> str:
    return command.strip().split()[0] if command.strip() else ""


def validate_run_command(topic: dict, go: Path) -> None:
    """Prove the declared command actually invokes the Go compiler.

    Guards against a spoofed runCommand (shell echo etc.) that would let a topic
    pass verification without ever compiling. Requirements:
      * no shell metacharacters,
      * the first token is `go` or `go.exe` (the pinned SDK, bound via PATH),
      * the command contains a real Go build/run/test invocation.
    """
    command = topic["runCommand"]
    if any(meta in command for meta in ("&", "|", ";", ">", "<", "`", "$(")):
        raise VerificationError(
            f"{topic['id']}: runCommand must not use shell metacharacters: {command!r}"
        )
    first = _first_token(command)
    if first not in ("go", "go.exe"):
        raise VerificationError(
            f"{topic['id']}: runCommand must start with the Go SDK: {command!r}"
        )
    sub = command.strip().split()[1] if len(command.strip().split()) > 1 else ""
    if sub not in ("run", "test", "build", "vet", "generate"):
        raise VerificationError(
            f"{topic['id']}: runCommand must invoke a Go subcommand: {command!r}"
        )


def compile_sample(topic: dict, go: Path) -> None:
    """Force a real compilation of the sample, independent of runCommand.

    Uses `go build ./...` when the sample has a go.mod (module context), and
    falls back to `go build .` for module-less single-file samples so the
    compile proof never fails a sample that runs via `go run .`.
    """
    sample_dir = SAMPLES_DIR / topic["id"]
    env = go_env()
    has_module = (sample_dir / "go.mod").is_file()
    before = {p.name for p in sample_dir.iterdir()}
    with tempfile.TemporaryDirectory(prefix="qfli_build_") as tmp:
        out = Path(tmp) / "out.bin"
        if has_module:
            args = [str(go), "build", "./..."]
        else:
            # Module-less single-file samples run via `go run .`; prove
            # compilation with GOPATH mode and a temp output.
            env["GO111MODULE"] = "off"
            env["GOFLAGS"] = ""
            args = [str(go), "build", "-o", str(out), "."]
        proc = subprocess.run(
            args,
            cwd=sample_dir,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
    # Remove any binaries this compile created so samples stay source-only.
    keep_suffixes = {".go", ".mod", ".sum", ".txt", ".json", ".md"}
    for p in sample_dir.iterdir():
        if p.name in before or not p.is_file():
            continue
        if p.suffix.lower() not in keep_suffixes:
            try:
                p.unlink()
            except OSError:
                pass
    if proc.returncode != 0:
        raise VerificationError(
            f"{topic['id']}: compile failed: {proc.stderr.strip()}"
        )


def verify_topic(topic: dict, go: Path) -> dict:
    check_code_matches_sample(topic)
    validate_run_command(topic, go)
    compile_sample(topic, go)
    sample_dir = SAMPLES_DIR / topic["id"]
    proc = run_command(topic["runCommand"], sample_dir, go)
    result = assert_result(topic, proc)
    variant = verify_variant(topic, go)
    return {
        "id": topic["id"],
        "runtime": topic["runtime"],
        "importKind": topic["importKind"],
        "verification": topic["verification"]["kind"],
        "result": result,
        "exampleVariant": variant,
    }


def run_race_gate(topic_ids: list[str]) -> dict[str, str]:
    """Run the real `go test -race` gate via WSL for the given topics.

    Uses w8:p4's `mobile_check/run_race.sh` (project-pinned linux Go SDK +
    distro gcc, CGO_ENABLED=1). Returns topic id -> "RACE-OK"/"RACE-FAIL".

    Fail-closed: if the gate cannot be executed (missing script, WSL error,
    non-zero exit, timeout) this raises ``VerificationError`` so a caller can
    never mistake an un-run race gate for a passing one.
    """
    script = TOOL_DIR / "mobile_check" / "run_race.sh"
    if not script.is_file():
        raise VerificationError(f"race gate script missing: {script}")
    rel = "/mnt/d/MyNewProjects/qfli_go/tool/go_curriculum/mobile_check/run_race.sh"
    try:
        proc = subprocess.run(
            ["wsl", "-d", "qfli-java-build", "--", "bash", rel, *topic_ids],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1200,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise VerificationError(f"race gate could not run: {error}") from error
    results: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if line.startswith("RACE-OK"):
            results[line.split()[-1]] = "RACE-OK"
        elif line.startswith("RACE-FAIL"):
            results[line.split()[1]] = "RACE-FAIL"
    if proc.returncode != 0:
        raise VerificationError(
            f"race gate exited {proc.returncode}: "
            f"{proc.stderr.strip() or proc.stdout.strip()[:200]}"
        )
    return results


def main(argv: list[str], race_gate=None, verify_topic_fn=None,
         evidence_dir: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", default="", help="comma-separated topic ids")
    parser.add_argument("--go", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--race", action="store_true",
                        help="also run the real -race gate for every topic; "
                             "every topic must report RACE-OK or verification "
                             "fails")
    args = parser.parse_args(argv)

    gate = race_gate or run_race_gate
    verify_one = verify_topic_fn or verify_topic
    out_dir = evidence_dir or EVIDENCE_DIR

    try:
        go = find_go(args.go)
    except VerificationError as error:
        print(f"VERIFY FAIL: {error}")
        return 1

    wanted = {x.strip() for x in args.only.split(",") if x.strip()}
    paths = sorted(TOPICS_DIR.glob("T*.json"))
    if not paths:
        print("VERIFY FAIL: no topics found")
        return 1

    evidence: list[dict] = []
    failures: list[str] = []
    passed = 0
    for path in paths:
        topic = json.loads(path.read_text(encoding="utf-8"))
        if wanted and topic["id"] not in wanted:
            continue
        try:
            record = verify_one(topic, go)
        except VerificationError as error:
            failures.append(f"{topic['id']}: {error}")
            if not args.json:
                print(f"FAIL {topic['id']}: {error}")
            continue
        ok = True
        if args.race:
            # --race is a real gate, not an annotation: a topic only passes if
            # its race result is exactly RACE-OK. RACE-FAIL, a missing result,
            # or a gate error (WSL/non-zero exit/timeout) all fail the run.
            try:
                race = gate([topic["id"]]).get(topic["id"])
            except VerificationError as error:
                race = None
                record["raceError"] = str(error)
            record["race"] = race if race is not None else "RACE-MISSING"
            if race != "RACE-OK":
                ok = False
                failures.append(
                    f"{topic['id']}: race {record['race']}"
                    + (f" ({record['raceError']})" if "raceError" in record else "")
                )
        evidence.append(record)
        if ok:
            passed += 1
        if not args.json:
            print(f"{'OK  ' if ok else 'FAIL'} {record['id']} "
                  f"{record['verification']} variant={record['exampleVariant']}"
                  + (f" race={record['race']}" if args.race else ""))

    out_dir.mkdir(exist_ok=True)
    (out_dir / "verify-results.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if args.json:
        print(json.dumps({"passed": passed, "failed": failures},
                         ensure_ascii=False, indent=2))
    print(f"VERIFY: {passed} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
