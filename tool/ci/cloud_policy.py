#!/usr/bin/env python3
"""Check active cloud-only instructions and Trellis task context references."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_NAMES = ("check.jsonl", "implement.jsonl")
ACTIVE_TASK_STATES = frozenset({"planning", "in_progress"})

_ACTION = re.compile(
    r"(?:\b(?:build(?:s|ing)?|test(?:s|ing)?|lint(?:s|ing)?|"
    r"analy[sz](?:e|es|ing|is)?|type[ -]?check(?:s|ing)?|"
    r"install(?:s|ed|ing|ation)?|download(?:s|ed|ing)?|"
    r"generat(?:e|es|ed|ing|ion)|packag(?:e|es|ed|ing)|"
    r"verif(?:y|ies|ied|ying|ication)|check(?:s|ed|ing)?|"
    r"compil(?:e|es|ed|ing|ation)|restor(?:e|es|ed|ing)|"
    r"dependenc(?:y|ies)\s+(?:resolut(?:ion|e)|install(?:ation)?)|"
    r"sdk\s+(?:setup|installation|download)|"
    r"run(?:s|ning)?\s+(?:them|(?:the\s+)?commands?)|"
    r"vet(?:s|ted|ting)?|benchmark(?:s|ing)?|emulat(?:or(?:s)?|e|es|ed|ing))\b|"
    r"构建|编译|测试|检查|分析|安装|下载|生成|打包|验证|运行|基准测试|模拟器)",
    re.IGNORECASE,
)
_LOCAL = re.compile(
    r"(?:\blocally\b|\blocal(?=\s+(?:build|test|lint|check|benchmark|emulator|"
    r"analy[sz]|compil|install|download|execution|machine|computer|workstation|runner|go\b))\b|"
    r"\bdeveloper[- ](?:machine|workstation|computer)\b|"
    r"\boutside\s+(?:of\s+)?(?:github\s+)?actions\b|"
    r"\bfrom\s+(?:your\s+)?(?:local\s+)?workstation\b|"
    r"\bon\s+(?:your\s+|the\s+|a\s+)?(?:local\s+)?"
    r"(?:machines?|computers?|workstations?|hosts?|runners?)\b|"
    r"本地|本机|开发机)",
    re.IGNORECASE,
)
_NEGATION = re.compile(
    r"(?:\b(?:no|do\s+not|don['’]t|never|must\s+not|should\s+not|cannot|can['’]t|"
    r"may\s+not|not\s+allowed|not\s+permitted|not\s+authorized|not\s+safe|"
    r"not\s+(?:a\s+)?permission|does\s+not\s+authorize|is\s+not\s+a\s+permission|"
    r"prohibit(?:s|ed)?|forbid(?:s|den)?|disallow(?:s|ed)?|avoid)\b|"
    r"禁止|不得|不允许|不能)",
    re.IGNORECASE,
)
_AFFIRMATIVE = re.compile(
    r"(?:\b(?:may|can|must|should|allowed|permitted|authorized|permission|allow|require)\b|"
    r"^(?:please\s+)?(?:run|execute|perform|use|build|test|lint|install|download|"
    r"analy[sz]e|verify|compile|benchmark|emulate|go\s+(?:vet|test|build))\b|"
    r"^(?:可以|允许|请|在)?(?:本地|本机|开发机).*(?:运行|构建|编译|测试|检查|安装)|"
    r"(?:运行|构建|编译|测试|检查|安装).*(?:本地|本机|开发机))",
    re.IGNORECASE,
)
_HISTORICAL_HEADING = re.compile(
    r"^\s{0,3}#{1,6}\s+.*\b(?:historical|history|past\s+evidence|"
    r"previous\s+results|prior\s+run\s+results|archived\s+evidence)\b",
    re.IGNORECASE,
)
_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+")
_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass(frozen=True)
class _Line:
    number: int
    text: str


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _instruction_files(root: Path) -> tuple[Path, ...]:
    """Find maintained guidance and current task instructions, not archived records."""
    candidates: set[Path] = set()
    for pattern in ("AGENTS.md", "README*.md"):
        candidates.update(root.glob(pattern))
    candidates.update((root / ".agents").glob("**/*.md"))
    workflow = root / ".trellis/workflow.md"
    if workflow.is_file():
        candidates.add(workflow)
    candidates.update((root / ".trellis/spec").glob("**/*.md"))

    tasks = root / ".trellis/tasks"
    if tasks.is_dir():
        for manifest in sorted(tasks.glob("*/task.json")):
            try:
                task = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if not isinstance(task, dict) or task.get("status") not in ACTIVE_TASK_STATES:
                continue
            for name in ("prd.md", "design.md", "implement.md"):
                document = manifest.parent / name
                if document.is_file():
                    candidates.add(document)
    return tuple(sorted(
        (path for path in candidates if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    ))


def _active_lines(text: str) -> Iterable[_Line]:
    """Yield prose outside examples, comments, quoted text, and history sections."""
    text = _HTML_COMMENT.sub(lambda match: "\n" * match.group(0).count("\n"), text)
    in_fence = False
    fence_char = ""
    fence_width = 0
    historical_depth: int | None = None
    for number, raw in enumerate(text.splitlines(), 1):
        fence = _FENCE.match(raw)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence, fence_char, fence_width = True, marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_width:
                in_fence = False
            continue
        if in_fence or raw.lstrip().startswith("|"):
            continue
        heading = _HEADING.match(raw)
        if heading:
            depth = len(heading.group(1))
            if historical_depth is not None and depth <= historical_depth:
                historical_depth = None
            if _HISTORICAL_HEADING.match(raw):
                historical_depth = depth
                continue
        if historical_depth is not None:
            continue
        stripped = raw.lstrip()
        if stripped.startswith(">"):
            continue
        prose = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", stripped)
        if prose:
            yield _Line(number, prose)


def _segments(line: str) -> Iterable[str]:
    """Split independent sentences/clauses before matching permission language."""
    for segment in re.split(
        r"(?<=[.!?。！？;；])\s*|[;；]|\b(?:but|however)\b", line, flags=re.IGNORECASE
    ):
        if segment.strip():
            yield segment.strip()


def _negates_pair(segment: str, action: re.Match[str],
                  location: re.Match[str]) -> bool:
    if action.start() < location.start():
        # The instruction verb occurs before its local-execution qualifier.
        relation = segment[max(0, action.start() - 90):location.end()]
        gap = segment[action.end():location.start()]
        suffix = segment[location.end():location.end() + 70]
        if _NEGATION.search(relation) or re.search(r"\bnot\s*$", gap, re.IGNORECASE):
            return True
        return bool(re.search(
            r"\b(?:is|are|be|remains?)\s+(?:not\s+allowed|not\s+permitted|"
            r"forbidden|prohibited)\b",
            suffix, re.IGNORECASE,
        ))
    # Include a preceding denial, as in "Do not run local benchmarks".
    relation = segment[max(0, location.start() - 90):min(len(segment), action.end() + 70)]
    return bool(_NEGATION.search(relation))


def _authorizes_local_execution(segment: str) -> bool:
    clauses = tuple(_segments(segment))
    if len(clauses) > 1:
        return any(_authorizes_local_execution(clause) for clause in clauses)
    if re.match(r"^(?:wrong|bad|example|counterexample)\s*:", segment, re.IGNORECASE):
        return False
    if re.match(r"^(?:historical|previous|prior|past|archived)\b", segment, re.IGNORECASE):
        return False
    if re.search(r"\b(?:generic|upstream|historical|archived)\s+"
                 r"(?:instructions?|guidance|commands?)\b", segment, re.IGNORECASE):
        return False
    # A location/action mention alone is not authorization (for example an SDK
    # flag, a build description, or settings "local to verification").
    if not _AFFIRMATIVE.search(segment):
        return False
    for action in _ACTION.finditer(segment):
        for location in _LOCAL.finditer(segment):
            if abs(action.start() - location.start()) > 180:
                continue
            if not _negates_pair(segment, action, location):
                return True
    return False


def _policy_findings(root: Path) -> list[str]:
    findings: list[str] = []
    for path in _instruction_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            findings.append(f"{_relative(path, root)}: cannot read instruction document: {error}")
            continue
        for line in _active_lines(text):
            for segment in _segments(line.text):
                if _authorizes_local_execution(segment):
                    findings.append(
                        f"{_relative(path, root)}:{line.number}: active instruction authorizes "
                        f"local project execution: {segment}"
                    )
    return findings


def _manifest_files(root: Path) -> tuple[Path, ...]:
    """Check only current active-task manifests, not completed or archived tasks."""
    tasks = root / ".trellis/tasks"
    if not tasks.is_dir():
        return ()
    manifests: list[Path] = []
    for task_json in sorted(tasks.glob("*/task.json")):
        try:
            task = json.loads(task_json.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(task, dict) or task.get("status") not in ACTIVE_TASK_STATES:
            continue
        manifests.extend(
            manifest for name in MANIFEST_NAMES
            if (manifest := task_json.parent / name).is_file()
        )
    return tuple(sorted(manifests, key=lambda path: path.relative_to(root).as_posix().casefold()))


def _manifest_findings(root: Path) -> list[str]:
    findings: list[str] = []
    checkout = root.resolve()
    for manifest in _manifest_files(root):
        relative_manifest = _relative(manifest, root)
        seen: dict[str, int] = {}
        try:
            lines = manifest.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as error:
            findings.append(f"{relative_manifest}: cannot read manifest: {error}")
            continue
        for line_number, raw in enumerate(lines, 1):
            if not raw.strip():
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as error:
                findings.append(f"{relative_manifest}:{line_number}: invalid JSON: {error.msg}")
                continue
            if not isinstance(record, dict) or not isinstance(record.get("file"), str):
                findings.append(f"{relative_manifest}:{line_number}: expected a string 'file' path")
                continue
            value = record["file"]
            candidate = PurePosixPath(value)
            if (not value or candidate.is_absolute() or ".." in candidate.parts
                    or "." in candidate.parts or re.match(r"^[A-Za-z]:", value)
                    or "\\" in value or "\x00" in value):
                findings.append(f"{relative_manifest}:{line_number}: unsafe or non-portable path: {value}")
                continue
            key = candidate.as_posix().casefold()
            if key in seen:
                findings.append(
                    f"{relative_manifest}:{line_number}: duplicate path '{value}' "
                    f"(first listed on line {seen[key]})"
                )
                continue
            seen[key] = line_number
            target = root.joinpath(*candidate.parts)
            try:
                resolved = target.resolve(strict=True)
                resolved.relative_to(checkout)
            except (OSError, RuntimeError, ValueError):
                findings.append(
                    f"{relative_manifest}:{line_number}: referenced file is missing or escapes checkout: {value}"
                )
                continue
            if not resolved.is_file():
                findings.append(f"{relative_manifest}:{line_number}: referenced path is not a file: {value}")
    return findings


def validate_repository(root: Path = ROOT) -> list[str]:
    """Return deterministic policy and Trellis-reference findings for a checkout."""
    root = root.resolve()
    if not root.is_dir():
        return [f"repository root is not a directory: {root}"]
    return sorted(_policy_findings(root) + _manifest_findings(root))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="check cloud policy and Trellis references")
    check.add_argument("--root", type=Path, default=ROOT, help="repository checkout root")
    args = parser.parse_args(argv)
    findings = validate_repository(args.root)
    if findings:
        print("Cloud policy/reference check failed:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print("Cloud policy and Trellis references passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
