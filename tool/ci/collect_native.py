#!/usr/bin/env python3
"""Validate and stage only the requested native runtime build outputs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tool"))
from inspect_go_catalog_hap import SYMBOLS, native_source_hash

ABI_MACHINES = {"arm64-v8a": (2, 183), "armeabi-v7a": (1, 40), "x86_64": (2, 62)}
BUILD_INPUTS = (
    "tool/build_go_runtime.ps1", "tool/build_ohos_go_toolchain.ps1",
    "tool/build_macos_go_runtime.sh", "tool/build_ios_go_runtime.sh",
    "tool/ci/collect_native.py", "tool/ci/install_ohos_sdk.ps1",
    "tool/go_curriculum/audit_native.py", "tool/go_curriculum/assemble.py",
    "tool/inspect_go_catalog_hap.py", ".github/workflows/native-runtime.yml",
)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def command(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def snapshot() -> dict:
    return {
        "nativeSourceSha256": native_source_hash(),
        "buildInputs": {name: digest(ROOT / name) for name in BUILD_INPUTS},
    }


def inspect_elf(path: Path, abi: str, android: bool, readelf: str) -> dict:
    data = path.read_bytes()
    elf_class, machine = ABI_MACHINES[abi]
    if data[:4] != b"\x7fELF" or data[4:6] != bytes((elf_class, 1)):
        raise ValueError(f"Wrong ELF class or byte order: {path}")
    if struct.unpack_from("<HH", data, 16) != (3, machine):
        raise ValueError(f"Wrong ELF type or machine for {abi}: {path}")
    if elf_class == 2:
        phoff = struct.unpack_from("<Q", data, 32)[0]
        phentsize, phnum = struct.unpack_from("<HH", data, 54)
        alignment_offset, alignment_format = 48, "<Q"
    else:
        phoff = struct.unpack_from("<I", data, 28)[0]
        phentsize, phnum = struct.unpack_from("<HH", data, 42)
        alignment_offset, alignment_format = 28, "<I"
    alignments = []
    for index in range(phnum):
        offset = phoff + index * phentsize
        if struct.unpack_from("<I", data, offset)[0] == 1:
            alignments.append(struct.unpack_from(alignment_format, data, offset + alignment_offset)[0])
    if not alignments or (android and min(alignments) < 16384):
        raise ValueError(f"Invalid LOAD segment alignment: {path}: {alignments}")
    symbols = command(readelf, "--dyn-syms", "--wide", str(path))
    exported = {
        line.split()[-1] for line in symbols.splitlines()
        if re.search(r"\bGLOBAL\s+DEFAULT\s+(?!UND\b)\S+\s+\S+\s*$", line)
    }
    if missing := SYMBOLS - exported:
        raise ValueError(f"Missing C ABI exports in {path}: {sorted(missing)}")
    return {"abi": abi, "loadAlignments": alignments, "requiredExports": sorted(SYMBOLS)}


def inspect_apple(path: Path, architectures: list[str], sdk: str) -> dict:
    actual = command("xcrun", "--sdk", sdk, "lipo", "-archs", str(path)).split()
    if sorted(actual) != sorted(architectures):
        raise ValueError(f"Wrong Apple slices in {path}: {actual}")
    for arch in architectures:
        symbols = command("xcrun", "--sdk", sdk, "nm", "-arch", arch, "-gU", str(path))
        exported = {line.split()[-1].removeprefix("_") for line in symbols.splitlines() if line.split()}
        if missing := SYMBOLS - exported:
            raise ValueError(f"Missing {arch} C ABI exports in {path}: {sorted(missing)}")
    return {"architectures": architectures, "sdk": sdk, "requiredExports": sorted(SYMBOLS)}


def stage(args: argparse.Namespace) -> None:
    before = json.loads(args.snapshot.read_text(encoding="utf-8-sig"))
    current = snapshot()
    if current != {key: before[key] for key in current}:
        raise ValueError("Native sources or build inputs changed during the build")
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError(f"Artifact staging directory must be empty: {args.output}")
    files: list[tuple[Path, str]] = []
    checks = []
    if args.platform in ("android", "ohos"):
        provenance = ROOT / f"native/build/bundled-go-runtime-build-{args.platform}.json"
        manifest = json.loads(provenance.read_text(encoding="utf-8-sig"))
        if datetime.fromisoformat(manifest["startedUtc"]) < datetime.fromisoformat(before["startedUtc"]):
            raise ValueError("Build provenance predates this build's source capture")
        if manifest["nativeSourceSha256"] != before["nativeSourceSha256"]:
            raise ValueError("Build provenance does not match the checked-out sources")
        expected = ["arm64-v8a", "armeabi-v7a", "x86_64"] if args.platform == "android" else ["arm64-v8a", "x86_64"]
        platform = "android" if args.platform == "android" else "openharmony"
        records = manifest["libraries"]
        if len(records) != len(expected) or sorted(r["abi"] for r in records) != sorted(expected):
            raise ValueError("Build provenance must contain exactly the requested ABIs")
        for record in records:
            library = (ROOT / record["path"]).resolve()
            if not library.is_relative_to(ROOT) or record["platform"] != platform:
                raise ValueError("Unexpected provenance library path or platform")
            if digest(library) != record["sha256"] or library.stat().st_size != record["bytes"]:
                raise ValueError(f"Build provenance hash or size mismatch: {library}")
            checks.append(inspect_elf(library, record["abi"], args.platform == "android", args.readelf))
            files.extend([(library, f"{record['abi']}/{library.name}"),
                          (library.with_suffix(".h"), f"{record['abi']}/{library.with_suffix('.h').name}")])
        files.append((provenance, "bundled-go-runtime-build.json"))
    else:
        if args.platform == "macos-universal":
            library = args.build / "bundle/Frameworks/libqfli_go_runtime.dylib"
            headers = [(args.build / f"derived/qfli_go_runtime/{arch}/libqfli_go_runtime.h", f"headers/{arch}/libqfli_go_runtime.h") for arch in ("arm64", "x86_64")]
            archs, sdk = ["arm64", "x86_64"], "macosx"
        else:
            library = args.build / "derived/qfli_go_runtime/libqfli_go_runtime.a"
            headers = [(library.with_suffix(".h"), "libqfli_go_runtime.h")]
            archs = ["arm64"] if args.platform == "ios-device" else ["arm64", "x86_64"]
            sdk = "iphoneos" if args.platform == "ios-device" else "iphonesimulator"
        checks.append(inspect_apple(library, archs, sdk))
        files.extend([(library, library.name), *headers])
    files.extend([(ROOT / "LICENSE", "licenses/PROJECT-LICENSE"),
                  (ROOT / "native/go_runtime/LICENSE.go-standard-library", "licenses/GO-LICENSE"),
                  (ROOT / "assets/licenses/yaegi.txt", "licenses/YAEGI-LICENSE")])
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for source, relative in files:
        target = args.output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append({"path": relative, "bytes": target.stat().st_size, "sha256": digest(target)})
    report = {
        "schemaVersion": 1, "platform": args.platform, "commit": command("git", "rev-parse", "HEAD"),
        "runId": os.getenv("GITHUB_RUN_ID"), "runAttempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "sourceChecksConclusion": os.getenv("SOURCE_CHECKS_CONCLUSION", "not-run"),
        "sourceChecksRunURL": os.getenv("SOURCE_CHECKS_RUN_URL"),
        "finishedUtc": datetime.now(timezone.utc).isoformat(), "build": before,
        "deviceExecution": False, "checks": checks, "files": records,
    }
    report_path = args.output / "manifest.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    checksums = [(r["sha256"], r["path"]) for r in records] + [(digest(report_path), "manifest.json")]
    (args.output / "SHA256SUMS").write_text("".join(f"{sha}  {name}\n" for sha, name in checksums), encoding="utf-8")
    summary = f"### Native runtime: {args.platform}\n\n"
    summary += f"Source checks: **{report['sourceChecksConclusion']}**.\n\n"
    if report["sourceChecksConclusion"] != "success":
        summary += "**Compilation artifacts only: source checks have not passed.**\n\n"
    if report["sourceChecksRunURL"]:
        summary += f"[Open source-check run]({report['sourceChecksRunURL']})\n\n"
    summary += "| File | Bytes | SHA-256 |\n| --- | ---: | --- |\n"
    summary += "".join(f"| `{r['path']}` | {r['bytes']} | `{r['sha256']}` |\n" for r in records)
    summary += "\nDownload the artifact below this run summary. These are libraries, not application installers.\n"
    if summary_file := os.getenv("GITHUB_STEP_SUMMARY"):
        with open(summary_file, "a", encoding="utf-8") as stream:
            stream.write(summary)
    print(summary)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    capture = sub.add_parser("snapshot")
    capture.add_argument("output", type=Path)
    collect = sub.add_parser("stage")
    collect.add_argument("--platform", required=True, choices=("android", "ohos", "macos-universal", "ios-device", "ios-simulator"))
    collect.add_argument("--snapshot", required=True, type=Path)
    collect.add_argument("--output", required=True, type=Path)
    collect.add_argument("--readelf", default="llvm-readelf")
    collect.add_argument("--build", type=Path)
    args = parser.parse_args()
    if args.action == "snapshot":
        data = snapshot()
        data.update(startedUtc=datetime.now(timezone.utc).isoformat(), goVersion=command("go", "version"))
        data["goExecutableSha256"] = digest(Path(shutil.which("go")))
        if value := os.getenv("ANDROID_NDK_VERSION"):
            data["androidNdkVersion"] = value
        if value := os.getenv("OHOS_SDK_SHA256"):
            data["ohosSdkArchiveSha256"] = value.lower()
        if sys.platform == "darwin":
            data["xcodeVersion"] = command("xcodebuild", "-version")
            if value := os.getenv("MACOSX_DEPLOYMENT_TARGET"):
                data["macosDeploymentTarget"] = value
            if value := os.getenv("IPHONEOS_DEPLOYMENT_TARGET"):
                data["iosDeploymentTarget"] = value
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    else:
        stage(args)


if __name__ == "__main__":
    main()
