#!/usr/bin/env python3
"""Emit, dry-run and (guarded) apply the Go-only slice for shared assets.

Design goals (R8):
  * byte-precise: only the contiguous Go run inside ``entries`` is replaced; all
    other bytes, positions, key order and newline escaping are preserved,
  * safe: refuse unknown Go edits (compare against the expected baseline slice),
  * exclusive: hold real OS-level exclusive locks on both targets for the whole
    read-verify-backup-write sequence (no advisory lockfile),
  * recoverable: back up the exact previous Go slice and the original file
    hashes before writing; verify both files before writing either,
  * non-contiguous Go layout is an explicit failure (not silently reordered).

Modes:
  emit      write a reviewable patch dir (Go slice + manifest)
  dry-run   run the SAME transform + validation as apply but write nothing
  apply     splice the Go run; requires --confirm and exclusive locks
  rollback  restore ONLY the Go entries from a backup, keeping latest non-Go

Usage:
    python tool/go_curriculum/patch.py emit [--patch DIR]
    python tool/go_curriculum/patch.py dry-run --shared DIR [--patch DIR] [--baseline DIR]
    python tool/go_curriculum/patch.py apply   --shared DIR --patch DIR --baseline DIR --confirm
    python tool/go_curriculum/patch.py rollback --shared DIR --backup DIR --confirm
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_PATCH = TOOL_DIR / "patch-go"
DEFAULT_OUT = TOOL_DIR / "content" / "go"
DEFAULT_BASELINE = TOOL_DIR / "baseline"
DEFAULT_BACKUP = TOOL_DIR / "apply-backup"
# tool/go_curriculum/patch.py -> parents[2] == qfli_go ; shared is a sibling.
DEFAULT_SHARED = Path(__file__).resolve().parents[2].parent / "qfli_studio_core" / "assets" / "content"

TARGETS = {"tutorials.json": "go-tutorials.json", "examples.json": "go-examples.json"}


class PatchError(Exception):
    pass


# ---------------------------------------------------------------- byte helpers


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _split_go(entries: list) -> tuple[list, list]:
    go = [e for e in entries if str(e.get("type", "")).lower() == "go"]
    non_go = [e for e in entries if str(e.get("type", "")).lower() != "go"]
    return non_go, go


def _go_run_span(data: bytes, entries: list) -> tuple[int, int]:
    """Return the byte span covering the contiguous run of Go entries.

    Scans the ``entries`` array in raw bytes, tracking the span of each JSON
    value, then requires all ``type=="go"`` entries to occupy one contiguous run
    and no Go entry outside it. Returns ``(start, end)`` of that run's bytes
    (start = the '{' of the first Go object, end = the '}' of the last).
    """
    go_idx = [i for i, e in enumerate(entries) if str(e.get("type", "")).lower() == "go"]
    if not go_idx:
        raise PatchError("no Go entries found in target")
    if go_idx != list(range(go_idx[0], go_idx[-1] + 1)):
        raise PatchError("Go entries are not contiguous; refusing to reorder")

    spans = _entry_spans(data)
    if len(spans) != len(entries):
        raise PatchError(
            f"entry count mismatch: parsed {len(spans)} spans vs {len(entries)} entries"
        )
    start = spans[go_idx[0]][0]
    end = spans[go_idx[-1]][1]
    return start, end


def _entry_spans(data: bytes) -> list[tuple[int, int]]:
    """Return (start,end) byte offsets of each top-level object in entries[].

    A minimal JSON scanner that finds the ``entries`` array and yields the byte
    range of each immediate value (object), skipping strings and nested braces.
    """
    arr_start, arr_end = _array_span(data, b'"entries"')
    spans: list[tuple[int, int]] = []
    i = arr_start
    while i < arr_end:
        c = data[i]
        if c == ord('{'):
            j = _skip_value(data, i)
            spans.append((i, j))
            i = j
        elif c in (ord(','), ord('['), 0x20, 0x09, 0x0a, 0x0d):
            i += 1
        elif c == ord(']'):
            break
        else:
            raise PatchError(f"unexpected byte {c!r} at {i} inside entries")
    return spans


def _array_span(data: bytes, key: bytes) -> tuple[int, int]:
    # Walk root properties, never matching an "entries" string in metadata.
    i = data.index(b'{') + 1
    found = []
    while i < len(data):
        while data[i] in b' \t\r\n,':
            i += 1
        if data[i] == ord('}'):
            break
        end = _skip_string(data, i)
        matches = json.loads(data[i:end]) == json.loads(key)
        i = end
        while data[i] in b' \t\r\n:':
            i += 1
        end = _skip_value(data, i)
        if matches:
            if data[i] != ord('['):
                raise PatchError("entries is not an array")
            found.append((i + 1, end - 1))
        i = end
    if len(found) != 1:
        raise PatchError("expected exactly one root entries array")
    return found[0]


def _skip_value(data: bytes, i: int) -> int:
    """Return the offset just past the JSON value starting at ``i``."""
    c = data[i]
    if c == ord('"'):
        return _skip_string(data, i)
    if c in (ord('{'), ord('[')):
        depth = 0
        while i < len(data):
            c = data[i]
            if c == ord('"'):
                i = _skip_string(data, i)
                continue
            if c in (ord('{'), ord('[')):
                depth += 1
            elif c in (ord('}'), ord(']')):
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        raise PatchError("unterminated container")
    # number / true / false / null
    while i < len(data) and data[i] not in b",}] \t\r\n":
        i += 1
    return i


def _skip_string(data: bytes, i: int) -> int:
    i += 1
    while i < len(data):
        c = data[i]
        if c == ord('\\'):
            i += 2
            continue
        if c == ord('"'):
            return i + 1
        i += 1
    raise PatchError("unterminated string")


def _render_slice(entries: list, indent: str = "    ") -> bytes:
    """Serialize Go entries matching the source style (base indent 4 spaces).

    Each entry is dumped with 2-space indentation, then every line is prefixed
    with the 4-space array-element indent so the block drops cleanly between the
    surrounding `}` ,\n    `{` separators of the original array.
    """
    blocks: list[str] = []
    for entry in entries:
        body = json.dumps(entry, ensure_ascii=False, indent=2)
        indented = "\n".join(
            indent + line if line else line for line in body.split("\n")
        )
        blocks.append(indented)
    return (",\n".join(blocks)).removeprefix(indent).encode("utf-8")


def _baseline_go(baseline: Path, name: str) -> list:
    p = baseline / name
    if not p.is_file():
        raise PatchError(f"baseline missing: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


# ------------------------------------------------------------------- commands


def emit(out: Path, patch_dir: Path) -> int:
    tutorials = json.loads((out / "tutorials.json").read_text(encoding="utf-8"))
    examples = json.loads((out / "examples.json").read_text(encoding="utf-8"))
    patch_dir.mkdir(parents=True, exist_ok=True)
    (patch_dir / "go-tutorials.json").write_text(
        json.dumps(tutorials, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (patch_dir / "go-examples.json").write_text(
        json.dumps(examples, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (patch_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "goTutorialCount": len(tutorials),
                "goExampleCount": len(examples),
                "slices": ["go-tutorials.json", "go-examples.json"],
                "targets": TARGETS,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"PATCH EMIT OK: {len(tutorials)} tutorials, {len(examples)} examples -> {patch_dir}")
    return 0


def _plan_one(name: str, shared: Path, patch_dir: Path, baseline: Path, data: bytes | None = None) -> dict:
    target = shared / name
    if not target.is_file():
        raise PatchError(f"shared target missing: {target}")
    if data is None:
        data = target.read_bytes()
    doc = json.loads(data)
    entries = doc["entries"]
    non_go, old_go = _split_go(entries)
    expected_go = _baseline_go(baseline, name)
    if old_go != expected_go:
        raise PatchError(
            f"{name}: current Go entries differ from the expected baseline "
            f"(unknown Go edits); refusing. Re-capture the baseline if this is "
            f"an intended change."
        )
    new_go = json.loads((patch_dir / f"go-{name.replace('.json', '')}.json")
                        .read_text(encoding="utf-8"))
    return _transform(target, data, entries, non_go, old_go, new_go)


def _transform(target, data, entries, non_go, old_go, new_go) -> dict:
    if not isinstance(new_go, list) or not new_go or any(
        not isinstance(e, dict) or e.get("type") != "go" for e in new_go
    ):
        raise PatchError(f"{target.name}: replacement must be a non-empty Go-only list")
    start, end = _go_run_span(data, entries)
    new_block = _render_slice(new_go)
    new_data = data[:start] + new_block + data[end:]
    # Validate the transformed document parses and preserves non-Go exactly.
    check = json.loads(new_data)
    new_non_go, _ = _split_go(check["entries"])
    if new_non_go != non_go:
        raise PatchError(f"{target.name}: non-Go entries would change; aborting")
    if len(check["entries"]) != len(non_go) + len(new_go):
        raise PatchError(f"{target.name}: entry count would change unexpectedly")
    return {
        "target": target,
        "original": data,
        "new": new_data,
        "non_go": len(non_go),
        "old_go": len(old_go),
        "new_go": len(new_go),
        "orig_sha": _sha_bytes(data),
    }


def dry_run(patch_dir: Path, shared: Path, baseline: Path) -> int:
    for name in TARGETS:
        plan = _plan_one(name, shared, patch_dir, baseline)
        print(
            f"PATCH DRY-RUN {name}: non-Go kept={plan['non_go']}, "
            f"Go replaced {plan['old_go']} -> {plan['new_go']}, "
            f"bytes {len(plan['original'])} -> {len(plan['new'])} (no write)"
        )
    print("PATCH DRY-RUN OK (transform executed and validated; nothing written)")
    return 0


def _acquire_locks(shared: Path, names: list[str]):
    """Acquire real OS-exclusive locks on all targets, or fail.

    Windows: deny write/delete sharing, including non-cooperating writers.
    Mutating on other platforms is refused: advisory flock is insufficient.
    Returns open file handles kept for the duration of the write.
    """
    if sys.platform != "win32":
        raise PatchError("shared mutation requires Windows file sharing locks")
    import ctypes
    import msvcrt
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD,
                       wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handles = []
    try:
        for name in names:
            path = shared / name
            handle = create(str(path.resolve()), 0xC0000000, 1, None, 3, 0x80, None)
            if handle == wintypes.HANDLE(-1).value:
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                fd = msvcrt.open_osfhandle(handle, os.O_RDWR | os.O_BINARY)
            except OSError:
                kernel.CloseHandle(handle)
                raise
            handles.append(os.fdopen(fd, "r+b"))
    except OSError as error:
        for fh in handles:
            fh.close()
        raise PatchError(f"could not acquire exclusive lock: {error}") from error
    return handles


def _release_locks(handles) -> None:
    for fh in handles:
        fh.close()


def _write_bytes(fh, data: bytes) -> None:
    fh.seek(0)
    if fh.write(data) != len(data):
        raise OSError("short write")
    fh.truncate()
    fh.flush()
    os.fsync(fh.fileno())
    fh.seek(0)
    if fh.read() != data:
        raise OSError("read-back mismatch")


def _write_plans(plans, handles) -> None:
    attempted = []
    try:
        for plan, fh in zip(plans.values(), handles):
            attempted.append((plan, fh))  # include a partially written file
            _write_bytes(fh, plan["new"])
    except OSError as error:
        failures = []
        for plan, fh in attempted:
            try:
                _write_bytes(fh, plan["original"])
            except OSError as restore_error:
                failures.append(f"{plan['target']}: {restore_error}")
        if failures:
            raise PatchError(f"write failed: {error}; recovery failed: {failures}; use backup originals") from error
        raise PatchError(f"write failed, restored originals: {error}") from error


def apply(patch_dir: Path, shared: Path, baseline: Path, backup: Path, confirm: bool) -> int:
    if not confirm:
        print("PATCH APPLY: refusing without --confirm (authorization boundary)")
        return 2
    names = list(TARGETS)
    handles = _acquire_locks(shared, names)
    try:
        # Verify BOTH files before writing EITHER (all-or-nothing start).
        # Read each target through its held exclusive handle to avoid opening a
        # second writer handle on Windows.
        plans = {}
        for name in names:
            fh = handles[names.index(name)]
            fh.seek(0)
            plans[name] = _plan_one(name, shared, patch_dir, baseline, fh.read())
        if backup.exists() and any(backup.iterdir()):
            raise PatchError("backup directory is not empty; choose a new --backup")
        backup.mkdir(parents=True, exist_ok=True)
        # Backup exact previous Go slice + original file bytes.
        for name, plan in plans.items():
            (backup / f"old-go-{name}").write_text(
                json.dumps(
                    _split_go(json.loads(plan["original"])["entries"])[1],
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (backup / f"original-{name}").write_bytes(plan["original"])
            (backup / f"sha-{name}.txt").write_text(plan["orig_sha"] + "\n", encoding="utf-8")
            (backup / f"applied-go-{name}").write_text(
                json.dumps(_split_go(json.loads(plan["new"])["entries"])[1],
                           ensure_ascii=False), encoding="utf-8")
        # Write in place through the already-held exclusive handle so the lock
        # is authoritative (no temp+replace, which Windows denies on a locked
        # file). On any failure, restore already-written files from the
        # originals so the pair stays recoverable.
        _write_plans(plans, handles)
        for name, plan in plans.items():
            print(f"PATCH APPLY {name}: non-Go kept={plan['non_go']}, "
                  f"Go replaced {plan['old_go']} -> {plan['new_go']}")
    finally:
        _release_locks(handles)
    print(f"PATCH APPLY OK. Backup of previous Go slice + originals: {backup}")
    return 0


def rollback(shared: Path, backup: Path, confirm: bool) -> int:
    if not confirm:
        print("PATCH ROLLBACK: refusing without --confirm")
        return 2
    names = list(TARGETS)
    handles = _acquire_locks(shared, names)
    try:
        plans = {}
        for name in names:
            fh = handles[names.index(name)]
            fh.seek(0)
            data = fh.read()
            old_go = json.loads((backup / f"old-go-{name}").read_text(encoding="utf-8"))
            applied = json.loads((backup / f"applied-go-{name}").read_text(encoding="utf-8"))
            doc = json.loads(data)
            non_go, current_go = _split_go(doc["entries"])
            if current_go != applied:
                raise PatchError(f"{name}: unknown Go edits since apply; refusing rollback")
            plans[name] = _transform(shared / name, data, doc["entries"], non_go, current_go, old_go)
        _write_plans(plans, handles)
    finally:
        _release_locks(handles)
    print("PATCH ROLLBACK OK (non-Go entries preserved as-is)")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("emit")
    e.add_argument("--out", type=Path, default=DEFAULT_OUT)
    e.add_argument("--patch", type=Path, default=DEFAULT_PATCH)
    d = sub.add_parser("dry-run")
    d.add_argument("--patch", type=Path, default=DEFAULT_PATCH)
    d.add_argument("--shared", type=Path, default=DEFAULT_SHARED)
    d.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    a = sub.add_parser("apply")
    a.add_argument("--patch", type=Path, default=DEFAULT_PATCH)
    a.add_argument("--shared", type=Path, default=DEFAULT_SHARED)
    a.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    a.add_argument("--backup", type=Path, default=DEFAULT_BACKUP)
    a.add_argument("--confirm", action="store_true")
    r = sub.add_parser("rollback")
    r.add_argument("--shared", type=Path, default=DEFAULT_SHARED)
    r.add_argument("--backup", type=Path, default=DEFAULT_BACKUP)
    r.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "emit":
            return emit(args.out, args.patch)
        if args.cmd == "dry-run":
            return dry_run(args.patch, args.shared, args.baseline)
        if args.cmd == "apply":
            return apply(args.patch, args.shared, args.baseline, args.backup, args.confirm)
        return rollback(args.shared, args.backup, args.confirm)
    except (PatchError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"PATCH ERROR: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
