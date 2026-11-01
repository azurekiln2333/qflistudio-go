#!/usr/bin/env python3
"""Audit every displayed Go code block and its canonical sample separately.

The native backend compiles a test-only overlay into the shipped native module,
then invokes runGoWithContext in a fresh, bounded process for EVERY case. Missing
main functions and unsupported test packages are failures, never skipped cases.
Host reports are explicitly not OHOS/device evidence.

Examples (all paths can be overridden):
  python tool/go_curriculum/audit_native.py --backend inventory
  python tool/go_curriculum/audit_native.py --backend native
  python tool/go_curriculum/audit_native.py --backend official
  python tool/go_curriculum/audit_native.py --self-test

--manifest-out assets/curriculum/audit-manifest.json produces the identical
source/fixture inventory consumed by integration_test/go_catalog_test.dart.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import signal
import subprocess
import tempfile
import time
import unittest
from unittest import mock

from assemble import imported_entry_file, support_fixtures

ROOT = Path(__file__).resolve().parents[2]
TOOL = Path(__file__).resolve().parent
NATIVE = ROOT / "native/go_runtime"
DEFAULT_GO = ROOT / "native/build/go-sdk-1.27.1/go/bin/go.exe"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalize_output(value: str) -> str:
    """Ignore CRLF and one final newline; preserve authored whitespace."""
    value = value.replace("\r\n", "\n")
    return value[:-1] if value.endswith("\n") else value


def safe_path(value: str) -> str:
    path = PurePosixPath(value)
    parts = value.split("/")
    if (not value or "\\" in value or path.is_absolute()
            or any(not part or part in (".", "..") or part != part.strip() or part.endswith(".")
                   or re.search(r'[\x00-\x1f<>:"|?*]', part)
                   or re.match(r'(?i)^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)', part) for part in parts)
            or parts[0].lower() in (".git", ".qfli")):
        raise ValueError(f"unsafe fixture path: {value!r}")
    return path.as_posix()


def encoded_file(name: str, content: bytes) -> dict:
    return {"path": safe_path(name), "contentBase64": base64.b64encode(content).decode("ascii"), "sha256": digest(content)}


def catalog_path(explicit: Path | None, name: str) -> Path:
    if explicit is not None:
        return explicit.resolve(strict=True)
    app_owned = ROOT / "assets/curriculum" / f"{name}.json"
    if app_owned.is_file():
        return app_owned
    return ROOT.parent / "qfli_studio_core/assets/content" / f"{name}.json"


def build_manifest(tutorials: Path, examples: Path, topics: Path, samples: Path) -> dict:
    issues: list[str] = []
    cases: list[dict] = []
    topic_map: dict[str, dict] = {}
    source_hashes: dict[str, str] = {}
    for path in sorted(topics.glob("T*.json")):
        data = path.read_bytes()
        topic = json.loads(data)
        topic_id = topic["id"]
        if topic_id in topic_map:
            issues.append(f"duplicate topic {topic_id}")
        topic_map[topic_id] = topic
        source_hashes[topic_id] = digest(data)
    if not topic_map:
        issues.append("authoring topic inventory is empty")
    catalogs = {}
    seen_blocks: set[str] = set()
    covered_topics: set[str] = set()
    for kind, path in (("tutorial", tutorials), ("example", examples)):
        content = path.read_bytes()
        catalogs[kind] = {"sha256": digest(content), "fileName": path.name}
        entries = json.loads(content)["entries"]
        seen_entries: set[str] = set()
        count = 0
        for entry in entries:
            if entry.get("type", "").lower() != "go" and entry.get("language", "").lower() != "go" and not str(entry.get("id", "")).startswith("go-"):
                continue
            count += 1
            entry_id = entry["id"]
            if entry.get("type") != "go" or entry.get("language") != "go":
                issues.append(f"{entry_id}: language/type must both be go")
            if entry_id in seen_entries:
                issues.append(f"duplicate {kind} id {entry_id}")
            seen_entries.add(entry_id)
            match = re.fullmatch(rf"go-{kind}-(\d+)", entry_id)
            topic_id = f"T{int(match[1]):03d}" if match else ""
            topic = topic_map.get(topic_id)
            if topic is None:
                issues.append(f"{entry_id}: missing authoring topic")
            else:
                covered_topics.add(topic_id)
            blocks = entry.get("lessons", []) if kind == "tutorial" else [entry]
            if not blocks:
                issues.append(f"{entry_id}: no lessons/code blocks")
            for block in blocks:
                block_id = f"{kind}/{entry_id}/{block['id']}" if kind == "tutorial" else f"{kind}/{entry_id}"
                if block_id in seen_blocks:
                    issues.append(f"duplicate code block {block_id}")
                seen_blocks.add(block_id)
                code = block.get("code", "")
                if not isinstance(code, str) or not code.strip():
                    issues.append(f"{block_id}: empty/missing displayed code")
                    code = code if isinstance(code, str) else ""
                expected = block.get("output", "") if kind == "tutorial" else block.get("expectedOutput", "")
                verification = dict(topic.get("verification", {})) if topic else {"kind": "stdout-exact"}
                verification["expected"] = expected
                authored = topic.get(kind, {}).get("code") if topic else None
                if authored != code:
                    issues.append(f"{block_id}: displayed code differs from authoring source")
                fixtures = block.get("inputFixtures", {})
                if not isinstance(fixtures, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in fixtures.items()):
                    issues.append(f"{block_id}: invalid inputFixtures")
                    fixtures = {}
                if topic and fixtures != support_fixtures(topic, samples):
                    issues.append(f"{block_id}: imported fixtures differ from canonical support files")
                entry_file = imported_entry_file(topic) if topic else "src/main.go"
                imported_files = [encoded_file(entry_file, code.encode("utf-8"))]
                for name, content in sorted(fixtures.items()):
                    name = "input.txt" if name == "stdin" else safe_path(name)
                    if name.lower() == entry_file.lower():
                        issues.append(f"{block_id}: fixture conflicts with selected source")
                    imported_files.append(encoded_file(name, content.encode("utf-8")))
                is_test = entry_file.endswith("_test.go")
                cases.append({
                    "id": block_id, "topic": topic_id, "entryId": entry_id,
                    "shape": "displayed-import", "operation": "test" if is_test else "program",
                    "declaredImportKind": topic.get("importKind") if topic else None,
                    "entryFile": entry_file,
                    "command": ["test", "-bench", ".", "-benchtime=1x", "."] if is_test and verification["kind"] == "bench-exists" else ["test" if is_test else "run", "."],
                    "files": imported_files,
                    "stdin": "", "verification": verification,
                    "expectedExitCode": 0, "expectedStderr": "",
                    "contentSha256": digest(code.encode("utf-8")),
                    "authoringSha256": source_hashes.get(topic_id),
                    "projectSha256": digest(json_bytes(imported_files)),
                })
        catalogs[kind]["goEntries"] = count
        if count == 0:
            issues.append(f"{kind}: no Go entries")
        for topic_id, topic in topic_map.items():
            if topic[kind]["id"] not in seen_entries:
                issues.append(f"{topic_id}: missing displayed {kind} {topic[kind]['id']}")
    for topic_id, topic in sorted(topic_map.items()):
        if topic_id not in covered_topics:
            issues.append(f"{topic_id}: absent from displayed catalog")
        files = []
        sample_dir = samples / topic_id
        actual_files = sorted(p for p in sample_dir.rglob("*") if p.is_file())
        if not actual_files:
            issues.append(f"{topic_id}: canonical sample directory is empty/missing")
        names = {p.relative_to(sample_dir).as_posix() for p in actual_files}
        for name in topic.get("sampleFiles", []):
            safe_path(name)
            if name not in names:
                issues.append(f"{topic_id}: declared sample/fixture missing: {name}")
        for path in actual_files:
            files.append(encoded_file(path.relative_to(sample_dir).as_posix(), path.read_bytes()))
        code = topic["tutorial"]["code"]
        matching = [f["path"] for f in files if f["path"].endswith(".go") and base64.b64decode(f["contentBase64"]).decode("utf-8") == code]
        if not matching:
            issues.append(f"{topic_id}: tutorial code has no exact canonical source file")
        command = shlex.split(topic["runCommand"])
        if not command or command[0] not in ("go", "go.exe") or len(command) < 2 or command[1] not in ("run", "test"):
            raise ValueError(f"{topic_id}: unsupported/unsafe Go command {command!r}")
        if any(re.search(r"[;&|<>`\n\r]", arg) for arg in command):
            raise ValueError(f"{topic_id}: shell syntax is forbidden")
        cases.append({
            "id": f"canonical/{topic_id}", "topic": topic_id,
            "shape": "canonical-sample", "operation": "test" if command[1] == "test" else "program",
            "declaredImportKind": topic["importKind"],
            "entryFile": matching[0] if matching else "main.go", "command": command[1:],
            "files": files, "stdin": topic.get("stdin", ""),
            "verification": topic["verification"], "expectedExitCode": 0, "expectedStderr": "",
            "contentSha256": digest(json_bytes(files)), "authoringSha256": source_hashes[topic_id],
        })
        test_files = [f for f in files if f["path"].endswith("_test.go")]
        if test_files and command[1] != "test":
            has_benchmark = any(re.search(rb"(?m)^func\s+Benchmark\w+\s*\(", base64.b64decode(f["contentBase64"])) for f in test_files)
            cases.append({
                **cases[-1], "id": f"canonical-tests/{topic_id}",
                "shape": "canonical-support-test", "operation": "test",
                "entryFile": test_files[0]["path"],
                "command": ["test", "-bench", ".", "-benchtime=1x", "./..."] if has_benchmark else ["test", "./..."],
                "verification": {"kind": "bench-exists" if has_benchmark else "test-pass", "expected": ""},
            })
    ids = [case["id"] for case in cases]
    for case in cases:
        case["workingDirectory"] = PurePosixPath(case["entryFile"]).parent.as_posix()
        case["projectSha256"] = digest(json_bytes(case["files"]))
        if case["operation"] == "test":
            directory = PurePosixPath(case["entryFile"]).parent
            sources = [base64.b64decode(f["contentBase64"]).decode("utf-8") for f in case["files"]
                       if f["path"].endswith("_test.go") and PurePosixPath(f["path"]).parent == directory]
            text = "\n".join(sources)
            case["expectedTestNames"] = re.findall(r"(?m)^func\s+((?:Test|Fuzz)[A-Z]\w*)\s*\(", text)
            case["expectedBenchmarkNames"] = re.findall(r"(?m)^func\s+(Benchmark[A-Z]\w*)\s*\(", text)
            case["minimumFuzzSeeds"] = len(re.findall(r"\bf\.Add\s*\(", text))
    if len(ids) != len(set(ids)):
        issues.append("case inventory contains duplicate ids")
    manifest = {"schemaVersion": 1, "catalogs": catalogs, "cases": cases, "inventoryIssues": issues}
    manifest["inventorySha256"] = digest(json_bytes(manifest))
    return manifest


def assertion_errors(case: dict, result: dict) -> list[str]:
    errors = []
    if result.get("timedOut"):
        errors.append("execution timed out")
    if result.get("exitCode") != case["expectedExitCode"]:
        errors.append(f"exit: expected {case['expectedExitCode']}, got {result.get('exitCode')}")
    stderr = normalize_output(result.get("stderr", ""))
    if stderr != normalize_output(case.get("expectedStderr", "")):
        errors.append(f"stderr mismatch: {stderr}")
    kind = case["verification"]["kind"]
    actual = normalize_output(result.get("stdout", ""))
    expected = normalize_output(case["verification"].get("expected", ""))
    if kind == "stdout-exact":
        if actual != expected:
            errors.append(f"stdout mismatch: expected {expected!r}, got {actual!r}")
    elif kind in ("stdout-sorted", "stdout-normalized"):
        got = [s.strip() for s in actual.splitlines() if s.strip()]
        want = [s.strip() for s in expected.splitlines() if s.strip()]
        if kind == "stdout-sorted":
            got.sort()
            want.sort()
        if got != want:
            errors.append(f"normalized stdout mismatch: expected {want!r}, got {got!r}")
    elif kind == "test-pass":
        # A zero-exit program is NOT evidence that a test function executed.
        if case["operation"] != "test":
            errors.append("test operation was not executed by a test-capable backend")
        elif result.get("backend") == "native":
            errors.extend(test_execution_errors(case, result))
        elif result.get("backend") != "official" or "--- SKIP:" in actual or "--- PASS:" not in actual or not re.search(r"^ok\s", actual, re.MULTILINE):
            errors.append("no successful test-package execution in stdout")
    elif kind == "bench-exists":
        if case["operation"] == "test" and result.get("backend") == "native":
            errors.extend(test_execution_errors(case, result))
        elif case["operation"] != "test" or result.get("backend") != "official" or "Benchmark" not in actual:
            errors.append("benchmark operation was not executed by a benchmark-capable backend")
    else:
        errors.append(f"unknown verification kind {kind!r}")
    return errors


def test_execution_errors(case: dict, result: dict) -> list[str]:
    execution = result.get("testExecution")
    if not isinstance(execution, dict) or execution.get("engine") != "qfli-embedded-testing-v1":
        return ["missing genuine embedded test execution metadata"]
    keys = ("testsRun", "testsPassed", "testsFailed", "testsSkipped", "benchmarksRun", "fuzzSeedsRun")
    if any(type(execution.get(k)) is not int or execution[k] < 0 for k in keys):
        return ["invalid embedded test execution counts"]
    errors = []
    if execution["testsRun"] != sum(execution[k] for k in ("testsPassed", "testsFailed", "testsSkipped")):
        errors.append("inconsistent embedded test execution counts")
    if execution["testsFailed"] or execution["testsSkipped"]:
        errors.append("embedded tests failed or were skipped")
    expected_tests = case.get("expectedTestNames", [])
    if execution["testsPassed"] < len(expected_tests):
        errors.append("not every declared test/fuzz function executed successfully")
    if execution["fuzzSeedsRun"] < case.get("minimumFuzzSeeds", 0):
        errors.append("not every declared fuzz seed executed")
    if case["verification"]["kind"] == "bench-exists":
        if execution["benchmarksRun"] < max(1, len(case.get("expectedBenchmarkNames", []))):
            errors.append("not every declared benchmark executed")
    elif execution["testsPassed"] == 0:
        errors.append("no successful test function execution")
    output = result.get("stdout", "")
    for name in expected_tests:
        if not re.search(rf"(?m)^--- PASS: {re.escape(name)}(?:\s|$)", output):
            errors.append(f"missing passing transcript for {name}")
    if not re.search(r"(?m)^PASS$", output):
        errors.append("no final embedded test PASS")
    return errors


def coverage_errors(cases: list[dict], records: list[dict]) -> list[str]:
    expected = {c["id"] for c in cases}
    actual = [r["id"] for r in records]
    errors = []
    if len(actual) != len(set(actual)):
        errors.append("duplicate result ids")
    if set(actual) != expected:
        errors.append(f"coverage mismatch: missing={sorted(expected-set(actual))}, unexpected={sorted(set(actual)-expected)}")
    return errors


def materialize(case: dict, project: Path) -> None:
    for file in case["files"]:
        target = project / safe_path(file["path"])
        content = base64.b64decode(file["contentBase64"], validate=True)
        if digest(content) != file["sha256"]:
            raise ValueError(f"{case['id']}: fixture hash mismatch: {file['path']}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def bounded_run(command: list[str], *, cwd: Path, env: dict, timeout: float, input: str = "") -> subprocess.CompletedProcess:
    """Kill the owned process tree on timeout, including compiler children."""
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", **options)
    try:
        stdout, stderr = process.communicate(input=input, timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            try:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                pass  # Still terminate the process handle we own below.
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # The process completed between timeout and termination.
        if process.poll() is None:
            process.kill()
        stdout, stderr = process.communicate(timeout=5)
        raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr) from None
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def native_source_hash() -> str:
    paths = sorted(p for p in NATIVE.rglob("*") if p.is_file() and (p.suffix in (".go", ".c", ".h", ".s", ".S", ".syso") or p.name in ("go.mod", "go.sum", "modules.txt")))
    return digest(json_bytes([(p.relative_to(NATIVE).as_posix(), digest(p.read_bytes())) for p in paths]))


def run_audit(manifest: dict, go: Path, backend: str, timeout: float, only: set[str]) -> dict:
    if not go.is_file():
        raise ValueError(f"SDK executable not found: {go}")
    go = go.resolve()
    env = dict(os.environ, GOMAXPROCS="2", GOFLAGS="-p=1", GOTOOLCHAIN="local", GOPROXY="off", GOSUMDB="off")
    cases = [c for c in manifest["cases"] if not only or c["topic"] in only or c["id"] in only]
    if not cases:
        raise ValueError("selected case inventory is empty")
    if only - {c["topic"] for c in cases} - {c["id"] for c in cases}:
        raise ValueError("--only contains unknown cases/topics")
    report = {
        "schemaVersion": 1, "evidenceLevel": "official-host" if backend == "official" else "host-native-shipped-source",
        "deviceExecution": False, "backend": backend, "inventorySha256": manifest["inventorySha256"],
        "catalogs": manifest["catalogs"], "nativeSourceSha256": native_source_hash(),
        "exhaustive": not only, "inventoryIssues": manifest["inventoryIssues"], "records": [],
    }
    with tempfile.TemporaryDirectory(prefix="qfli_catalog_audit_") as scratch:
        temp = Path(scratch)
        binary = temp / ("catalog-audit.test.exe" if os.name == "nt" else "catalog-audit.test")
        if backend == "native":
            overlay = temp / "overlay.json"
            overlay.write_text(json.dumps({"Replace": {str(NATIVE / "catalog_audit_test.go"): str(TOOL / "mobile_check/catalog_audit_test.go")}}), encoding="utf-8")
            command = [str(go), "test", "-c", "-mod=vendor", "-tags=hostcheck", "-overlay", str(overlay), "-o", str(binary), "."]
            build = bounded_run(command, cwd=NATIVE, env=env, timeout=240)
            if build.returncode:
                raise RuntimeError(f"native overlay build failed:\n{build.stdout}\n{build.stderr}")
            if native_source_hash() != report["nativeSourceSha256"]:
                raise RuntimeError("native source changed while the overlay binary was compiling; rerun for an attributable runtime hash")
            report["testBinarySha256"] = digest(binary.read_bytes())
        for index, case in enumerate(cases):
            project = temp / f"case-{index:04d}"
            project.mkdir()
            materialize(case, project)
            started = time.monotonic()
            result = {"backend": backend, "stdout": "", "stderr": "", "exitCode": None, "timedOut": False}
            try:
                if backend == "native":
                    request, response = temp / "request.json", temp / "response.json"
                    response.unlink(missing_ok=True)
                    request.write_text(json.dumps({"id": case["id"], "project": str(project), "entryFile": case["entryFile"], "timeoutMs": int(timeout*1000)}), encoding="utf-8")
                    child_env = dict(env, QFLI_GO_AUDIT_REQUEST=str(request), QFLI_GO_AUDIT_RESPONSE=str(response))
                    # Run outside the fixture: production must supply a project
                    # environment without relying on the host process cwd.
                    proc = bounded_run([str(binary), "-test.run=^TestCatalogAuditCase$", f"-test.timeout={timeout+3}s"], cwd=temp, env=child_env, input=case.get("stdin", ""), timeout=timeout+5)
                    if response.is_file():
                        payload = json.loads(response.read_text(encoding="utf-8"))
                        if payload["id"] != case["id"]:
                            raise ValueError("native response id mismatch")
                        result.update(payload["result"], timedOut=payload["timedOut"])
                    else:
                        result.update(exitCode=proc.returncode if proc.returncode else 125, stderr=f"native harness produced no response\n{proc.stdout}\n{proc.stderr}")
                else:
                    child_env = dict(env)
                    if not (project / "go.mod").is_file():
                        child_env["GO111MODULE"] = "off"
                    command = case["command"]
                    if command[0] == "test":
                        # Bypass the compiler's test-result cache and preserve
                        # evidence that test functions, rather than only the
                        # package loader, ran in this invocation.
                        command = ["test", "-count=1", "-v", *command[1:]]
                    # Match GoToolchain.execute(run): the selected package is
                    # the process cwd, even when go.mod lives in its parent.
                    working_directory = project / PurePosixPath(case["entryFile"]).parent
                    proc = bounded_run([str(go), *command], cwd=working_directory, env=child_env, input=case.get("stdin", ""), timeout=timeout)
                    result.update(stdout=proc.stdout, stderr=proc.stderr, exitCode=proc.returncode)
            except subprocess.TimeoutExpired as error:
                result.update(exitCode=124, timedOut=True, stdout=error.output or "", stderr=(error.stderr or "") + f"\n{error}")
            except Exception as error:
                result.update(exitCode=125, stderr=f"harness error: {error}")
            errors = assertion_errors(case, result)
            record = {"id": case["id"], "topic": case["topic"], "shape": case["shape"], "operation": case["operation"], "workingDirectory": PurePosixPath(case["entryFile"]).parent.as_posix(), "contentSha256": case["contentSha256"], "projectSha256": case["projectSha256"], "verification": case["verification"], "expectedExitCode": case["expectedExitCode"], "expectedStderr": case["expectedStderr"], **result, "durationMs": round((time.monotonic()-started)*1000), "passed": not errors, "assertionErrors": errors}
            report["records"].append(record)
            print(f"{'PASS' if not errors else 'FAIL'} {case['id']}" + (f" — {errors[0]}" if errors else ""), flush=True)
    report["coverageIssues"] = coverage_errors(cases, report["records"])
    report["total"] = len(cases)
    report["passed"] = sum(r["passed"] for r in report["records"])
    report["failed"] = report["total"] - report["passed"]
    report["success"] = not report["failed"] and not report["inventoryIssues"] and not report["coverageIssues"]
    return report


def self_test() -> bool:
    class AuditTests(unittest.TestCase):
        def setUp(self):
            self.case = {"id": "example/test", "operation": "program", "expectedExitCode": 0, "expectedStderr": "", "verification": {"kind": "stdout-exact", "expected": "ready"}}
            self.result = {"stdout": "ready\n", "stderr": "", "exitCode": 0, "backend": "native"}

        def test_nonzero_and_mismatch_fail(self):
            self.assertFalse(assertion_errors(self.case, self.result))
            for change in ({"stdout": "wrong"}, {"stdout": " ready"}, {"stdout": "ready\n\n"}, {"exitCode": 1}, {"stderr": "panic"}, {"timedOut": True}):
                self.assertTrue(assertion_errors(self.case, self.result | change))

        def test_missing_and_duplicate_results_fail(self):
            self.assertTrue(coverage_errors([self.case], []))
            self.assertTrue(coverage_errors([self.case], [self.case, self.case]))

        def test_test_package_does_not_pass_as_program(self):
            self.case["verification"] = {"kind": "test-pass"}
            self.assertTrue(assertion_errors(self.case, self.result))

        def test_native_uses_neutral_cwd_while_official_uses_entry_package(self):
            case = self.case | {
                "topic": "T001", "shape": "displayed-import", "entryFile": "src/main.go",
                "command": ["run", "."], "contentSha256": "source", "projectSha256": "project",
                "files": [encoded_file("src/main.go", b"package main\nfunc main() {}\n")],
            }
            manifest = {"cases": [case], "catalogs": {}, "inventorySha256": "inventory", "inventoryIssues": []}
            with tempfile.TemporaryDirectory() as directory:
                go = Path(directory)/"go"
                go.touch()

                def run(command, *, cwd, env, timeout, input=""):
                    if "-c" in command:
                        Path(command[command.index("-o")+1]).write_bytes(b"test binary")
                    elif "QFLI_GO_AUDIT_REQUEST" in env:
                        request = json.loads(Path(env["QFLI_GO_AUDIT_REQUEST"]).read_text(encoding="utf-8"))
                        project = Path(request["project"])
                        self.assertNotEqual(cwd, project)
                        self.assertTrue(project.is_relative_to(cwd))
                        Path(env["QFLI_GO_AUDIT_RESPONSE"]).write_text(json.dumps({
                            "id": case["id"], "result": self.result, "timedOut": False,
                        }), encoding="utf-8")
                    else:
                        self.assertEqual(cwd.name, "src")
                        self.assertTrue((cwd/"main.go").is_file())
                    return subprocess.CompletedProcess(command, 0, "ready\n", "")

                with mock.patch(__name__+".bounded_run", side_effect=run), mock.patch(__name__+".native_source_hash", return_value="native"):
                    for backend in ("native", "official"):
                        self.assertTrue(run_audit(manifest, go, backend, 1, set())["success"])

        def test_package_data_and_embed_layout_follow_selected_source(self):
            with tempfile.TemporaryDirectory() as directory:
                samples = Path(directory)
                sample = samples/"T001"
                files = {
                    "main.go": 'package main\nimport _ "embed"\n//go:embed data/message.txt\nvar message string\nfunc main(){}\n',
                    "helper.go": "package main\n",
                    "go.mod": "module local\ngo 1.21\n",
                    "data/message.txt": "entry-data\r\n",
                    "testdata/input.txt": "entry-test-data\n",
                    "internal/helper/helper.go": 'package helper\nimport _ "embed"\n//go:embed data/value.txt\nvar Value string\n',
                    "internal/helper/data/value.txt": "subpackage-data\n",
                }
                for name, content in files.items():
                    path = sample/name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content.encode("utf-8"))
                topic = {"id": "T001", "importKind": "module-project", "tutorial": {"code": files["main.go"]}}
                fixtures = support_fixtures(topic, samples)
                self.assertEqual(fixtures, {
                    "src/helper.go": files["helper.go"], "go.mod": files["go.mod"],
                    "src/data/message.txt": files["data/message.txt"],
                    "src/testdata/input.txt": files["testdata/input.txt"],
                    "internal/helper/helper.go": files["internal/helper/helper.go"],
                    "internal/helper/data/value.txt": files["internal/helper/data/value.txt"],
                })

        def test_embedded_counts_and_transcript_are_required(self):
            case = self.case | {"operation": "test", "verification": {"kind": "test-pass"}, "expectedTestNames": ["TestReady"]}
            execution = {"engine": "qfli-embedded-testing-v1", "testsRun": 1, "testsPassed": 1, "testsFailed": 0, "testsSkipped": 0, "benchmarksRun": 0, "fuzzSeedsRun": 0}
            result = self.result | {"stdout": "--- PASS: TestReady\nPASS\n", "testExecution": execution}
            self.assertFalse(assertion_errors(case, result))
            for change in ({"engine": "fake"}, {"testsPassed": 0}, {"testsFailed": 1}, {"testsRun": -1}, {"testsRun": True}, {"testsRun": 2}, {"testsSkipped": 1}, {"testsPassed": 0, "testsSkipped": 1}):
                self.assertTrue(assertion_errors(case, result | {"testExecution": execution | change}))
            self.assertTrue(assertion_errors(case, result | {"stdout": "PASS\n"}))
            self.assertTrue(assertion_errors(case | {"minimumFuzzSeeds": 1}, result))
            bench = case | {"verification": {"kind": "bench-exists"}, "expectedBenchmarkNames": ["BenchmarkOne", "BenchmarkTwo"]}
            self.assertTrue(assertion_errors(bench, result))
            self.assertFalse(assertion_errors(bench, result | {"testExecution": execution | {"benchmarksRun": 2}}))

        def test_manifest_enumerates_lessons_and_requires_both_surfaces(self):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                topics, samples = root/"topics", root/"samples"
                topics.mkdir()
                (samples/"T001").mkdir(parents=True)
                code = 'package main\nfunc main() {}\n'
                (samples/"T001/main.go").write_bytes(code.encode("utf-8"))
                topic = {"id": "T001", "importKind": "single-file", "sampleFiles": ["main.go"], "runCommand": "go run .", "verification": {"kind": "stdout-exact", "expected": ""}, "tutorial": {"id": "go-tutorial-001", "code": code}, "example": {"id": "go-example-001", "code": code}}
                (topics/"T001.json").write_text(json.dumps(topic), encoding="utf-8")
                tutorial = root/"tutorials.json"
                example = root/"examples.json"
                tutorial.write_text(json.dumps({"entries": [{"id": "go-tutorial-001", "type": "go", "language": "go", "lessons": [{"id": "one", "code": code}, {"id": "two", "code": code}]}]}), encoding="utf-8")
                example.write_text(json.dumps({"entries": [{"id": "go-example-001", "type": "go", "language": "go", "code": code}]}), encoding="utf-8")
                manifest = build_manifest(tutorial, example, topics, samples)
                self.assertEqual(len(manifest["cases"]), 4)
                self.assertFalse(manifest["inventoryIssues"])
                example.write_text('{"entries": []}', encoding="utf-8")
                manifest = build_manifest(tutorial, example, topics, samples)
                self.assertTrue(any("missing displayed example" in issue for issue in manifest["inventoryIssues"]))

        def test_fixture_hash_and_containment(self):
            with tempfile.TemporaryDirectory() as directory:
                item = encoded_file("fixture/input.txt", b"bytes\r\n")
                materialize({"id": "fixture", "files": [item]}, Path(directory))
                self.assertEqual((Path(directory)/"fixture/input.txt").read_bytes(), b"bytes\r\n")
                item["sha256"] = "wrong"
                with self.assertRaises(ValueError):
                    materialize({"id": "fixture", "files": [item]}, Path(directory))
            for path in ("../outside", "/absolute", "C:/outside", "a\\b", "a/./b", "a//b", "a. ", ".git/config", "CON.go", "nul", "src/file.go/"):
                with self.assertRaises(ValueError):
                    safe_path(path)
    return unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AuditTests)).wasSuccessful()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tutorials", type=Path)
    parser.add_argument("--examples", type=Path)
    parser.add_argument("--topics", type=Path, default=TOOL / "topics")
    parser.add_argument("--samples", type=Path, default=TOOL / "samples")
    parser.add_argument("--go", type=Path, default=DEFAULT_GO)
    parser.add_argument("--backend", choices=("inventory", "native", "official"), default="native")
    parser.add_argument("--manifest-out", type=Path, default=TOOL / "evidence/catalog-audit-manifest.json")
    parser.add_argument("--out", type=Path, default=TOOL / "evidence/catalog-audit-native.json")
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--only", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return 0 if self_test() else 1
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    manifest = build_manifest(catalog_path(args.tutorials, "tutorials"), catalog_path(args.examples, "examples"), args.topics, args.samples)
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if args.backend == "inventory":
        print(f"inventoried {len(manifest['cases'])} cases; {len(manifest['inventoryIssues'])} issues")
        for issue in manifest["inventoryIssues"]:
            print(issue)
        return int(bool(manifest["inventoryIssues"]))
    report = run_audit(manifest, args.go, args.backend, args.timeout, set(filter(None, args.only.split(","))))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"{report['passed']}/{report['total']} passed; {report['failed']} failed; exhaustive={report['exhaustive']}")
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
