#!/usr/bin/env python3
"""Inspect the bundled Go runtime ELF shared libraries and their APK/HAP copies.

Standard library only. Two phases:

1. ``libs`` (default): report SHA256, ELF class, ELF machine and every PT_LOAD
   alignment for each of the five bundled shared libraries. Android libraries
   must be 64-bit AArch64, 32-bit ARM or 64-bit x86-64 matching their ABI
   directory, and every PT_LOAD must be at least 16 KiB aligned.

2. ``packages``: additionally inspect the ``qfli_go_runtime.so`` entries inside
   the given APK and/or HAP. Member paths are discovered from the actual archive
   contents so the checker adapts to the observed layout. Every member must:

   * be a valid ELF with the class/machine matching its ABI directory (and the
     rebuilt file's class/machine),
   * satisfy the Android 16 KiB PT_LOAD rule when it is an Android member,
   * be equivalent to the matching rebuilt file for all ``SHF_ALLOC`` sections.

   Equivalence under stripping: package tooling may strip debug/symbol sections,
   changing the whole-file hash. Loaded code and data are the ``SHF_ALLOC``
   sections, so the checker requires every allocated section to match by name,
   type, flags, load address and size; ``SHT_NOBITS`` (``.bss``/``.tbss``)
   sections must match by metadata and size; every other allocated section must
   additionally have identical bytes (section content SHA256). A whole-file hash
   match is reported as a fast path but is not required. Any allocated-section
   mismatch fails that member.

A declared ``--apk`` or ``--hap`` path that does not exist is a failure. An
omitted optional argument is allowed and is skipped.

Exit code 0 means every performed check passed; 1 means at least one check
failed.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# ELF constants (subset).
ELFCLASS32 = 1
ELFCLASS64 = 2
ELFDATA2LSB = 1
ELFDATA2MSB = 2

EM_ARM = 40
EM_X86_64 = 62
EM_AARCH64 = 183

PT_LOAD = 1
SHT_NOBITS = 8
SHF_ALLOC = 0x2

# 16 KiB, the Android requirement enforced by the linker -z max-page-size flag.
ANDROID_MIN_LOAD_ALIGN = 16 * 1024

REPO_ROOT = Path(__file__).resolve().parents[4]

LIBRARY_NAME = "libqfli_go_runtime.so"

# (source path, expected ELF class, expected machine, requires 16 KiB alignment)
BUNDLED_LIBRARIES = (
    (
        "android arm64-v8a",
        "android/app/src/main/jniLibs/arm64-v8a/" + LIBRARY_NAME,
        ELFCLASS64,
        EM_AARCH64,
        True,
    ),
    (
        "android armeabi-v7a",
        "android/app/src/main/jniLibs/armeabi-v7a/" + LIBRARY_NAME,
        ELFCLASS32,
        EM_ARM,
        True,
    ),
    (
        "android x86_64",
        "android/app/src/main/jniLibs/x86_64/" + LIBRARY_NAME,
        ELFCLASS64,
        EM_X86_64,
        True,
    ),
    (
        "ohos arm64-v8a",
        "ohos/entry/libs/arm64-v8a/" + LIBRARY_NAME,
        ELFCLASS64,
        EM_AARCH64,
        False,
    ),
    (
        "ohos x86_64",
        "ohos/entry/libs/x86_64/" + LIBRARY_NAME,
        ELFCLASS64,
        EM_X86_64,
        False,
    ),
)

MACHINE_NAMES = {
    EM_ARM: "EM_ARM",
    EM_X86_64: "EM_X86_64",
    EM_AARCH64: "EM_AARCH64",
}


class ValidationError(Exception):
    """A concrete validation failure."""


@dataclass
class Section:
    name: str
    type: int
    flags: int
    addr: int
    offset: int
    size: int
    content_sha256: str | None  # None for SHT_NOBITS

    @property
    def allocated(self) -> bool:
        return bool(self.flags & SHF_ALLOC) and self.name != ""

    @property
    def is_nobits(self) -> bool:
        return self.type == SHT_NOBITS


@dataclass
class ElfInfo:
    elf_class: int
    data_encoding: int
    machine: int
    load_alignments: list[int] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_elf(data: bytes, origin: str) -> ElfInfo:
    if len(data) < 64 or data[:4] != b"\x7fELF":
        raise ValidationError(f"{origin}: not an ELF file")

    elf_class = data[4]
    data_encoding = data[5]
    if elf_class not in (ELFCLASS32, ELFCLASS64):
        raise ValidationError(f"{origin}: unknown ELF class {elf_class}")
    if data_encoding not in (ELFDATA2LSB, ELFDATA2MSB):
        raise ValidationError(f"{origin}: unknown ELF data encoding {data_encoding}")

    endian = "<" if data_encoding == ELFDATA2LSB else ">"

    if elf_class == ELFCLASS64:
        # e_machine, e_version, e_entry, e_phoff, e_shoff, e_flags,
        # e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx
        header = struct.unpack_from(endian + "HHIQQQIHHHHHH", data, 16)
    else:
        header = struct.unpack_from(endian + "HHIIIIIHHHHHH", data, 16)
    machine = header[1]
    program_offset = header[4]
    section_offset = header[5]
    program_entry_size = header[8]
    program_count = header[9]
    section_entry_size = header[10]
    section_count = header[11]
    section_names_index = header[12]

    load_alignments: list[int] = []
    for index in range(program_count):
        base = program_offset + index * program_entry_size
        if base + program_entry_size > len(data):
            raise ValidationError(f"{origin}: program header {index} is truncated")
        p_type = struct.unpack_from(endian + "I", data, base)[0]
        if p_type != PT_LOAD:
            continue
        if elf_class == ELFCLASS64:
            p_align = struct.unpack_from(endian + "Q", data, base + 48)[0]
        else:
            p_align = struct.unpack_from(endian + "I", data, base + 28)[0]
        load_alignments.append(p_align)

    sections = _parse_sections(
        data,
        origin,
        endian,
        elf_class,
        section_offset,
        section_entry_size,
        section_count,
        section_names_index,
    )

    return ElfInfo(
        elf_class=elf_class,
        data_encoding=data_encoding,
        machine=machine,
        load_alignments=load_alignments,
        sections=sections,
    )


def _parse_sections(
    data: bytes,
    origin: str,
    endian: str,
    elf_class: int,
    section_offset: int,
    entry_size: int,
    count: int,
    names_index: int,
) -> list[Section]:
    if count == 0 or section_offset == 0:
        return []
    raw: list[tuple[int, int, int, int, int, int]] = []
    for index in range(count):
        base = section_offset + index * entry_size
        if base + entry_size > len(data):
            raise ValidationError(f"{origin}: section header {index} is truncated")
        if elf_class == ELFCLASS64:
            name, s_type, flags, addr, offset, size = struct.unpack_from(
                endian + "IIQQQQ", data, base
            )
        else:
            name, s_type, flags, addr, offset, size = struct.unpack_from(
                endian + "IIIIII", data, base
            )
        raw.append((name, s_type, flags, addr, offset, size))

    if names_index >= len(raw):
        raise ValidationError(f"{origin}: invalid section name table index")
    _, _, _, _, names_off, names_size = raw[names_index]
    names = data[names_off : names_off + names_size]

    def resolve(offset: int) -> str:
        if offset >= len(names):
            return f"<bad-name-{offset}>"
        end = names.find(b"\x00", offset)
        if end < 0:
            end = len(names)
        return names[offset:end].decode("latin1")

    sections: list[Section] = []
    for name, s_type, flags, addr, offset, size in raw:
        content: str | None = None
        if s_type != SHT_NOBITS and size > 0:
            end = offset + size
            if end > len(data):
                raise ValidationError(
                    f"{origin}: section content out of range at {offset:#x}"
                )
            content = hashlib.sha256(data[offset:end]).hexdigest()
        sections.append(
            Section(
                name=resolve(name),
                type=s_type,
                flags=flags,
                addr=addr,
                offset=offset,
                size=size,
                content_sha256=content,
            )
        )
    return sections


def class_name(elf_class: int) -> str:
    return {ELFCLASS32: "ELF32", ELFCLASS64: "ELF64"}.get(elf_class, str(elf_class))


def check_library(
    label: str,
    path: Path,
    expected_class: int,
    expected_machine: int,
    require_alignment: bool,
) -> tuple[bool, str]:
    if not path.is_file():
        return False, f"FAIL {label}: missing {path}"

    data = path.read_bytes()
    size = len(data)
    digest = sha256_of(path)
    info = parse_elf(data, str(path))

    problems: list[str] = []
    if info.elf_class != expected_class:
        problems.append(
            f"class {class_name(info.elf_class)} != {class_name(expected_class)}"
        )
    if info.machine != expected_machine:
        problems.append(
            f"machine {MACHINE_NAMES.get(info.machine, info.machine)} != "
            f"{MACHINE_NAMES.get(expected_machine, expected_machine)}"
        )
    if not info.load_alignments:
        problems.append("no PT_LOAD segments")
    if require_alignment:
        weak = [a for a in info.load_alignments if a < ANDROID_MIN_LOAD_ALIGN]
        if weak:
            shown = ", ".join(hex(a) for a in weak)
            problems.append(
                f"PT_LOAD alignment below {ANDROID_MIN_LOAD_ALIGN} (0x4000): {shown}"
            )

    aligns = ", ".join(hex(a) for a in info.load_alignments)
    head = (
        f"{label}: {digest} {class_name(info.elf_class)} "
        f"{MACHINE_NAMES.get(info.machine, info.machine)} size={size} "
        f"LOAD_align=[{aligns}]"
    )
    if problems:
        return False, f"FAIL {head}\n      -> " + "; ".join(problems)
    return True, f"OK   {head}"


def match_rebuilt_library(zip_member: str) -> tuple[str, str] | None:
    """Map an archive member path to (name, source repo-relative path)."""
    normalized = zip_member.replace("\\", "/")
    if not normalized.endswith("/" + LIBRARY_NAME):
        return None
    parts = normalized.split("/")
    if len(parts) < 3:
        return None
    abi = parts[-2]
    for name, repo_path, _, _, _ in BUNDLED_LIBRARIES:
        if Path(repo_path).parent.name != abi:
            continue
        # Prefer the same product line: APK uses lib/, HAP uses libs/.
        origin = name.split(" ", 1)[0]
        if normalized.startswith("libs/") and origin != "ohos":
            continue
        if normalized.startswith("lib/") and origin != "android":
            continue
        return name, repo_path
    return None


def compare_allocated_sections(
    packaged: ElfInfo,
    rebuilt: ElfInfo,
    origin: str,
) -> tuple[bool, list[str]]:
    """Require every SHF_ALLOC section to be metadata- and content-equivalent."""
    packaged_alloc = {s.name: s for s in packaged.sections if s.allocated}
    rebuilt_alloc = {s.name: s for s in rebuilt.sections if s.allocated}

    problems: list[str] = []
    only_packaged = sorted(set(packaged_alloc) - set(rebuilt_alloc))
    only_rebuilt = sorted(set(rebuilt_alloc) - set(packaged_alloc))
    if only_packaged:
        problems.append(f"allocated sections only in archive: {only_packaged}")
    if only_rebuilt:
        problems.append(f"allocated sections only in rebuilt: {only_rebuilt}")

    for name in sorted(set(packaged_alloc) & set(rebuilt_alloc)):
        left = packaged_alloc[name]
        right = rebuilt_alloc[name]
        if left.type != right.type:
            problems.append(f".{name}: type {left.type} != {right.type}")
            continue
        if left.flags != right.flags:
            problems.append(f".{name}: flags {left.flags:#x} != {right.flags:#x}")
        if left.addr != right.addr:
            problems.append(f".{name}: addr {left.addr:#x} != {right.addr:#x}")
        if left.size != right.size:
            problems.append(f".{name}: size {left.size:#x} != {right.size:#x}")
        if left.is_nobits:
            # NOBITS carry size/addr only; no content to compare.
            continue
        if left.content_sha256 != right.content_sha256:
            problems.append(
                f".{name}: content {left.content_sha256} != {right.content_sha256}"
            )

    if problems:
        return False, [f"FAIL {origin}: allocated section mismatch:"] + [
            f"      -> {p}" for p in problems
        ]
    return True, [
        f"OK   {origin}: all {len(rebuilt_alloc)} allocated sections match the "
        f"rebuilt file (metadata + allocated bytes)"
    ]


def check_archive_member(
    bundle: zipfile.ZipFile,
    member: str,
    rebuilt_root: Path,
) -> tuple[bool, list[str]]:
    match = match_rebuilt_library(member)
    if match is None:
        return False, [f"FAIL {member}: unrecognized ABI path"]
    name, repo_path = match
    source = rebuilt_root / repo_path
    if not source.is_file():
        return False, [f"FAIL {member}: rebuilt {source} missing"]

    expected_class = next(
        cls for label, path, cls, _, _ in BUNDLED_LIBRARIES if path == repo_path
    )
    expected_machine = next(
        machine for label, path, _, machine, _ in BUNDLED_LIBRARIES if path == repo_path
    )
    is_android = name.startswith("android")

    packaged_bytes = bundle.read(member)
    rebuilt_bytes = source.read_bytes()
    packaged_info = parse_elf(packaged_bytes, f"{member}")
    rebuilt_info = parse_elf(rebuilt_bytes, repo_path)

    messages: list[str] = []
    ok = True

    # 1. Packaged ELF class/machine must match the ABI directory and the rebuilt.
    if packaged_info.elf_class != expected_class:
        ok = False
        messages.append(
            f"FAIL {member}: packaged class "
            f"{class_name(packaged_info.elf_class)} != {class_name(expected_class)}"
        )
    if packaged_info.machine != expected_machine:
        ok = False
        messages.append(
            f"FAIL {member}: packaged machine "
            f"{MACHINE_NAMES.get(packaged_info.machine, packaged_info.machine)} != "
            f"{MACHINE_NAMES.get(expected_machine, expected_machine)}"
        )
    if packaged_info.elf_class != rebuilt_info.elf_class or (
        packaged_info.machine != rebuilt_info.machine
    ):
        ok = False
        messages.append(f"FAIL {member}: packaged class/machine != rebuilt file")

    # 2. Packaged Android members must keep 16 KiB PT_LOAD alignment.
    if is_android:
        weak = [a for a in packaged_info.load_alignments if a < ANDROID_MIN_LOAD_ALIGN]
        if weak:
            ok = False
            shown = ", ".join(hex(a) for a in weak)
            messages.append(
                f"FAIL {member}: packaged PT_LOAD below 0x4000: {shown}"
            )

    # 3. Fast path: identical bytes.
    packaged_hash = hashlib.sha256(packaged_bytes).hexdigest()
    if packaged_hash == hashlib.sha256(rebuilt_bytes).hexdigest():
        messages.append(
            f"OK   {member}: byte-identical to rebuilt {name} ({packaged_hash})"
        )
        return ok, messages

    # 4. Stripped copy: require allocated-section equivalence to the rebuilt.
    section_ok, section_messages = compare_allocated_sections(
        packaged_info, rebuilt_info, member
    )
    ok = ok and section_ok
    messages.append(
        f"INFO {member}: hash differs from rebuilt {name} "
        f"(archive {packaged_hash} {len(packaged_bytes)} bytes; "
        f"rebuilt {hashlib.sha256(rebuilt_bytes).hexdigest()} {len(rebuilt_bytes)} bytes)"
    )
    messages.extend(section_messages)
    return ok, messages


def check_archive(archive: Path, rebuilt_root: Path) -> tuple[bool, list[str]]:
    if not archive.is_file():
        return False, [f"FAIL declared archive not found: {archive}"]

    messages: list[str] = []
    ok = True
    with zipfile.ZipFile(archive) as bundle:
        members = [m for m in bundle.namelist() if m.endswith(LIBRARY_NAME)]
        if not members:
            return False, [f"FAIL {archive}: no {LIBRARY_NAME} entries found"]
        messages.append(f"INFO {archive}: members {sorted(members)}")
        for member in sorted(members):
            member_ok, member_messages = check_archive_member(
                bundle, member, rebuilt_root
            )
            ok = ok and member_ok
            messages.extend(member_messages)
    return ok, messages


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repository root (default: %(default)s)",
    )
    parser.add_argument(
        "--phase",
        choices=("libs", "packages"),
        default="libs",
        help="libs: inspect rebuilt files only; packages: also inspect APK/HAP",
    )
    parser.add_argument("--apk", type=Path, default=None, help="APK to inspect")
    parser.add_argument("--hap", type=Path, default=None, help="HAP to inspect")
    args = parser.parse_args(argv)

    root: Path = args.root.resolve()
    all_ok = True
    lines: list[str] = []

    for label, repo_path, expected_class, expected_machine, align in BUNDLED_LIBRARIES:
        ok, message = check_library(
            label,
            root / repo_path,
            expected_class,
            expected_machine,
            align,
        )
        all_ok = all_ok and ok
        lines.append(message)

    if args.phase == "packages":
        for archive in (args.apk, args.hap):
            if archive is None:
                continue
            ok, messages = check_archive(archive, root)
            all_ok = all_ok and ok
            lines.extend(messages)

    print("\n".join(lines))
    if all_ok:
        print("\nRESULT: PASS")
        return 0
    print("\nRESULT: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
