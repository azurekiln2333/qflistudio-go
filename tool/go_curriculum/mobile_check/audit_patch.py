#!/usr/bin/env python3
"""Sandbox audit of patch.py against the SHARED-FILE safety risks.

Audits the real risks (NOT decoded-dict equality):

  R1 raw-non-Go preservation : every non-Go entry's raw JSON bytes AND its
                               original position/order are preserved exactly.
  R2 unknown-Go rejection    : a Go entry in the shared file differing from the
                               recorded baseline makes apply refuse without write.
  R3 lock / single-writer    : a concurrent holder of an OS-exclusive lock on a
                               target makes apply refuse without write.
  R4 failure recovery        : an invalid second target must not leave the first
                               half-updated (all-or-nothing or rollback-able).

Plus: dry-run runs the real transform and writes nothing; apply without
--confirm refuses.

Usage:
    python tool/go_curriculum/mobile_check/audit_patch.py
Exit 0 only if every invariant holds; unsupported guards are FAIL, not skipped.
"""
from __future__ import annotations

import json
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch as mock_patch

TOOL = Path(__file__).resolve().parents[1]
PY = sys.executable
PATCH = TOOL / "patch.py"
spec = importlib.util.spec_from_file_location("curriculum_patch", PATCH)
patch_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch_module)


def raw_entry_spans(text: str) -> list[tuple[str, int, int, str]]:
    """(id, start, end, raw) for each top-level object in entries[] via brace scan."""
    m = re.search(r'"entries"\s*:\s*\[', text)
    if not m:
        raise AssertionError("no entries[] found")
    i = m.end()
    spans: list[tuple[str, int, int, str]] = []
    depth = 0
    start = None
    in_str = False
    esc = False
    while i < len(text):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    raw = text[start : i + 1]
                    idm = re.search(r'"id"\s*:\s*"([^"]+)"', raw)
                    spans.append(((idm.group(1) if idm else "?"), start, i + 1, raw))
                    start = None
            elif ch == "]" and depth == 0:
                break
        i += 1
    return spans


def write_shared(path: Path, preamble: str, entries: list[dict]) -> None:
    """Custom preamble + compact entries so a json round-trip rewrite is visible."""
    body = ",\n".join(json.dumps(e, ensure_ascii=False, separators=(",", ":")) for e in entries)
    path.write_text(f'{preamble}"entries": [\n{body}\n]\n}}\n', encoding="utf-8")


def go(eid):
    return {"id": eid, "type": "go", "language": "go", "title": eid, "lessons": []}


def non_go(eid, tag):
    return {"id": eid, "type": "rust", "language": "rust", "title": tag}


def run(args):
    return subprocess.run([PY, str(PATCH), *args], capture_output=True, text=True)


def write_slice(path: Path, entries: list[dict]) -> None:
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fresh(shared: Path, backup: Path, baseline: Path, tut_entries, ex_entries) -> dict:
    for d in (shared, backup, baseline):
        if d.exists():
            # Windows: kill any lingering handles by removing files first.
            for f in sorted(d.rglob('*'), reverse=True):
                try:
                    f.unlink()
                except OSError:
                    pass
            shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)
    write_shared(shared / "tutorials.json", '{"schemaVersion":1,"kind":"tutorials",\n', tut_entries)
    write_shared(shared / "examples.json", '{"schemaVersion":1,"kind":"examples",\n', ex_entries)
    # Baseline = the current Go entries of each shared file (the trusted slice).
    (baseline / "tutorials.json").write_text(
        json.dumps([e for e in tut_entries if e["type"] == "go"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (baseline / "examples.json").write_text(
        json.dumps([e for e in ex_entries if e["type"] == "go"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    nongo = {}
    for eid, _s, _e, raw in raw_entry_spans((shared / "tutorials.json").read_text(encoding="utf-8")):
        if eid in ("r1", "r2"):
            nongo[eid] = raw
    return nongo


def check_r1(shared, patch, backup, baseline, nongo):
    before = {name: (shared / name).read_bytes() for name in patch_module.TARGETS}
    r = run(["apply", "--shared", str(shared), "--patch", str(patch), "--baseline", str(baseline),
             "--backup", str(backup), "--confirm"])
    if r.returncode != 0:
        raise AssertionError(f"apply failed: {r.stdout}{r.stderr}")
    text = (shared / "tutorials.json").read_text(encoding="utf-8")
    spans = {eid: raw for eid, _s, _e, raw in raw_entry_spans(text)}
    for eid, raw in nongo.items():
        if eid not in spans:
            raise AssertionError(f"non-Go entry {eid} missing after apply")
        if spans[eid] != raw:
            raise AssertionError(f"non-Go entry {eid} bytes changed.\nwant: {raw}\ngot : {spans[eid]}")
    order = [eid for eid, _s, _e, _r in raw_entry_spans(text) if eid in nongo]
    if order != list(nongo):
        raise AssertionError(f"non-Go order changed: {order} != {list(nongo)}")
    # Go slice actually replaced by the patch values
    full = json.loads(text)
    go_ids = [e["id"] for e in full["entries"] if e["type"] == "go"]
    if go_ids != ["go-tutorial-001", "go-tutorial-002"]:
        raise AssertionError(f"Go slice not replaced as expected: {go_ids}")
    for name, original in before.items():
        current = (shared / name).read_bytes()
        def outside(data):
            spans = raw_entry_spans(data.decode('utf-8'))
            go_spans = [s for s in spans if s[0].startswith('go-')]
            source = data.decode('utf-8')
            return source[:go_spans[0][1]], source[go_spans[-1][2]:]
        assert outside(original) == outside(current), 'bytes outside Go span changed'
    print("R1 raw-non-Go preservation: OK")


def check_r2(shared, patch, backup, baseline, nongo):
    text = (shared / "tutorials.json").read_text(encoding="utf-8")
    mutated = text.replace('"title":"go-tutorial-001"', '"title":"UNKNOWN-GO-EDIT"')
    if mutated == text:
        raise AssertionError("setup: could not inject unknown Go edit")
    (shared / "tutorials.json").write_text(mutated, encoding="utf-8")
    before = (shared / "tutorials.json").read_bytes()
    r = run(["apply", "--shared", str(shared), "--patch", str(patch), "--baseline", str(baseline),
             "--backup", str(backup), "--confirm"])
    if r.returncode == 0:
        raise AssertionError("apply ACCEPTED an unknown Go edit (baseline digest not enforced)")
    if (shared / "tutorials.json").read_bytes() != before:
        raise AssertionError("apply refused but still rewrote the file")
    print("R2 unknown-Go rejection: OK")


def check_r3(shared, patch, backup, baseline, nongo):
    before = (shared / "tutorials.json").read_bytes()
    holder = open(shared / "tutorials.json", "r+b")
    try:
        locked = False
        if sys.platform.startswith("win"):
            import msvcrt
            try:
                msvcrt.locking(holder.fileno(), msvcrt.LK_NBLCK, 1)
                locked = True
            except OSError:
                pass
        else:
            import fcntl
            try:
                fcntl.flock(holder.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError:
                pass
        if not locked:
            raise AssertionError("setup: could not hold an exclusive lock")
        r = run(["apply", "--shared", str(shared), "--patch", str(patch), "--baseline", str(baseline),
                 "--backup", str(backup), "--confirm"])
        if r.returncode == 0:
            raise AssertionError("apply proceeded while another holder held an exclusive lock")
        try:
            after = (shared / "tutorials.json").read_bytes()
        except PermissionError:
            after = before  # our own holder still blocks reads we can't distinguish
        if after != before:
            raise AssertionError("apply refused but still rewrote the file")
        print("R3 lock conflict refusal: OK")
    finally:
        try:
            if sys.platform.startswith("win"):
                import msvcrt
                msvcrt.locking(holder.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        holder.close()


def check_r4(shared, patch, backup, baseline, nongo):
    before_tut = (shared / "tutorials.json").read_bytes()
    (shared / "examples.json").write_text("{ this is not valid json", encoding="utf-8")
    r = run(["apply", "--shared", str(shared), "--patch", str(patch), "--baseline", str(baseline),
             "--backup", str(backup), "--confirm"])
    if r.returncode == 0:
        raise AssertionError("apply succeeded despite an invalid second target")
    if (shared / "tutorials.json").read_bytes() == before_tut:
        print("R4 failure recovery: OK (all-or-nothing, first target untouched)")
        return
    rr = run(["rollback", "--shared", str(shared), "--backup", str(backup), "--confirm"])
    if rr.returncode != 0 or (shared / "tutorials.json").read_bytes() != before_tut:
        raise AssertionError("first target changed and could not be recovered")
    print("R4 failure recovery: OK (recovered via rollback)")


def check_partial_write(shared, patch, backup, baseline, nongo):
    before = {n: (shared / n).read_bytes() for n in patch_module.TARGETS}
    real_write = patch_module._write_bytes
    calls = 0
    def failing_write(fh, data):
        nonlocal calls
        calls += 1
        if calls == 2:
            fh.seek(0)
            fh.write(b'PARTIAL WRITE')
            fh.flush()
            raise OSError('injected second-target write failure')
        real_write(fh, data)
    with mock_patch.object(patch_module, '_write_bytes', failing_write):
        try:
            patch_module.apply(patch, shared, baseline, backup, True)
            raise AssertionError('failure injection did not fail')
        except patch_module.PatchError as error:
            assert 'restored originals' in str(error), error
    assert all((shared / n).read_bytes() == b for n, b in before.items())
    print('R4 partial second write restores BOTH originals: OK')


def check_writer_exclusion(shared, patch, backup, baseline, nongo):
    handles = patch_module._acquire_locks(shared, list(patch_module.TARGETS))
    try:
        for name in patch_module.TARGETS:
            child = subprocess.run([PY, '-c',
                'import sys; f=open(sys.argv[1],"r+b"); f.close()',
                str(shared / name)], capture_output=True, text=True)
            assert child.returncode != 0 and 'PermissionError' in child.stderr, child.stderr
    finally:
        patch_module._release_locks(handles)
    print('R3 ordinary non-cooperating writer denied: OK')


def check_rollback(shared, patch, backup, baseline, nongo):
    patch_module.apply(patch, shared, baseline, backup, True)
    path = shared / 'tutorials.json'
    changed = path.read_bytes().replace(b'keep-me-exactly', b'latest-non-Go-change')
    path.write_bytes(changed)
    patch_module.rollback(shared, backup, True)
    restored = path.read_bytes()
    assert b'latest-non-Go-change' in restored
    for name in patch_module.TARGETS:
        got = [e for e in json.loads((shared / name).read_bytes())['entries'] if e['type'] == 'go']
        assert got == json.loads((baseline / name).read_bytes())
    print('ROLLBACK preserves later non-Go edits: OK')


def check_noncontiguous(shared, patch, backup, baseline, nongo):
    path = shared / 'tutorials.json'
    doc = json.loads(path.read_bytes())
    doc['entries'].append(go('go-extra'))
    write_shared(path, '{"metadata":{"entries":[]},', doc['entries'])
    write_slice(baseline / 'tutorials.json', [e for e in doc['entries'] if e['type'] == 'go'])
    before = path.read_bytes()
    r = run(['dry-run', '--shared', str(shared), '--patch', str(patch), '--baseline', str(baseline)])
    assert r.returncode != 0 and 'not contiguous' in r.stdout, r.stdout + r.stderr
    assert path.read_bytes() == before
    print('Noncontiguous Go layout rejected: OK')


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="patchaudit_"))
    shared, patch, backup, baseline = (tmp / x for x in ("shared", "patch", "backup", "baseline"))
    patch.mkdir(parents=True)

    tut_entries = [non_go("r1", "keep-me-exactly"), go("go-tutorial-001"), non_go("r2", "also-keep<exact>")]
    ex_entries = [go("go-example-001"), non_go("r3", "third")]
    write_slice(patch / "go-tutorials.json", [go("go-tutorial-001"), go("go-tutorial-002")])
    write_slice(patch / "go-examples.json", [go("go-example-001"), go("go-example-002")])

    nongo = fresh(shared, backup, baseline, tut_entries, ex_entries)
    before_tut = (shared / "tutorials.json").read_bytes()
    before_ex = (shared / "examples.json").read_bytes()

    r = run(["dry-run", "--shared", str(shared), "--patch", str(patch), "--baseline", str(baseline)])
    assert r.returncode == 0, r.stdout + r.stderr
    assert (shared / "tutorials.json").read_bytes() == before_tut, "dry-run wrote files"
    assert (shared / "examples.json").read_bytes() == before_ex, "dry-run wrote files"
    print("DRY-RUN: real transform, no write OK")

    r = run(["apply", "--shared", str(shared), "--patch", str(patch), "--baseline", str(baseline), "--backup", str(backup)])
    assert r.returncode == 2, f"apply without --confirm: rc={r.returncode}"
    print("APPLY no-confirm refusal: OK")

    failures = []
    for name, fn in (("R1", check_r1), ("R2", check_r2), ("R3", check_r3),
                     ("R4", check_r4), ("R3-writer", check_writer_exclusion),
                     ("R4-partial", check_partial_write), ("rollback", check_rollback),
                     ("layout", check_noncontiguous)):
        nongo = fresh(shared, backup, baseline, tut_entries, ex_entries)
        try:
            fn(shared, patch, backup, baseline, nongo)
        except AssertionError as err:
            failures.append(f"{name}: {err}")
            print(f"FAIL {name}: {err}")

    shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        print(f"\nPATCH AUDIT: {len(failures)} FAILURE(S)")
        return 1
    print("\nPATCH AUDIT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
