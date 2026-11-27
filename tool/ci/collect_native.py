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
    "tool/build_desktop_go_runtime.ps1", "tool/build_macos_go_runtime.sh", "tool/build_ios_go_runtime.sh",
    "tool/ci/collect_native.py", "tool/ci/app_build.py", "tool/ci/install_ohos_sdk.ps1",
    "native/go_runtime/android-cc.cmd", "native/go_runtime/ohos-cc.cmd",
    "native/go_runtime/windows-cc.cmd", "native/go_runtime/desktop.cmake",
    "tool/go_curriculum/audit_native.py", "tool/go_curriculum/assemble.py",
    "tool/inspect_go_catalog_hap.py", ".github/workflows/native-runtime.yml",
    ".github/workflows/app-packages.yml",
)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def command(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def source_sha() -> str:
    value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Checked-out application source SHA is not a full Git commit")
    return value


def snapshot() -> dict:
    return {
        "sourceSha": source_sha(),
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


def inspect_pe(path: Path) -> dict:
    # Reuse the package verifier so producer and consumer apply identical PE rules.
    from app_build import pe_info

    info = pe_info(path.read_bytes(), path.name)
    missing = SYMBOLS - set(info["exports"])
    if missing:
        raise ValueError(f"Missing C ABI exports in {path}: {sorted(missing)}")
    unshipped = sorted(name for name in info["imports"]
                       if name.lower().startswith("lib"))
    if unshipped:
        raise ValueError(f"Windows runtime imports unbundled toolchain DLLs: {unshipped}")
    return {"abi": "x86_64", "requiredExports": sorted(SYMBOLS),
            "imports": info["imports"]}


PLATFORM_ABIS = {
    "android": ["arm64-v8a", "armeabi-v7a", "x86_64"],
    "ohos": ["arm64-v8a", "x86_64"],
    "windows": ["x86_64"], "linux": ["x86_64"],
    "macos-universal": ["arm64", "x86_64"],
    "ios-device": ["arm64"], "ios-simulator": ["arm64", "x86_64"],
}
LICENSE_PATHS = {"licenses/PROJECT-LICENSE", "licenses/GO-LICENSE", "licenses/YAEGI-LICENSE"}


def expected_runtime_paths(platform: str, abis: list[str]) -> set[str]:
    if platform not in PLATFORM_ABIS or sorted(abis) != sorted(PLATFORM_ABIS[platform]):
        raise ValueError("Native artifact ABI set does not match the platform contract")
    if platform in ("android", "ohos"):
        return {f"{abi}/libqfli_go_runtime.so" for abi in abis}
    name = {"windows": "qfli_go_runtime.dll", "linux": "libqfli_go_runtime.so",
            "macos-universal": "libqfli_go_runtime.dylib",
            "ios-device": "libqfli_go_runtime.a",
            "ios-simulator": "libqfli_go_runtime.a"}[platform]
    return {name}


def expected_artifact_paths(platform: str, abis: list[str]) -> set[str]:
    paths = expected_runtime_paths(platform, abis) | LICENSE_PATHS
    if platform in ("android", "ohos"):
        return paths | {f"{abi}/libqfli_go_runtime.h" for abi in abis} | {"bundled-go-runtime-build.json"}
    if platform == "macos-universal":
        return paths | {f"headers/{abi}/libqfli_go_runtime.h" for abi in abis}
    header = "qfli_go_runtime.h" if platform == "windows" else "libqfli_go_runtime.h"
    return paths | {header}


def run_context() -> tuple[str, str, str]:
    run_id, attempt = os.getenv("GITHUB_RUN_ID", ""), os.getenv("GITHUB_RUN_ATTEMPT", "")
    server, repository = os.getenv("GITHUB_SERVER_URL", ""), os.getenv("GITHUB_REPOSITORY", "")
    if (not re.fullmatch(r"[1-9][0-9]*", run_id) or not re.fullmatch(r"[1-9][0-9]*", attempt)
            or not server.startswith("https://")
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)):
        raise ValueError("Native artifacts require the current GitHub run identity")
    return run_id, attempt, f"{server.rstrip('/')}/{repository}/actions/runs/{run_id}"


def validate_runtime_binaries(root: Path, platform: str, abis: list[str]) -> None:
    """Inspect the consumed bytes, not just the producer's claimed checks."""
    from app_build import inspect_elf as inspect_packaged_elf, require_exports

    if platform == "windows":
        inspect_pe(root / "qfli_go_runtime.dll")
    elif platform in ("android", "ohos", "linux"):
        for abi in abis:
            relative = f"{abi}/libqfli_go_runtime.so" if platform != "linux" else "libqfli_go_runtime.so"
            info = inspect_packaged_elf((root / relative).read_bytes(), abi, android=platform == "android")
            require_exports(info["symbols"], relative)
            if platform == "android" and min(info["loadAlignments"]) < 16384:
                raise ValueError("Android runtime LOAD alignment is below 16 KiB")
    else:
        sdk = {"macos-universal": "macosx", "ios-device": "iphoneos",
               "ios-simulator": "iphonesimulator"}[platform]
        library = next(iter(expected_runtime_paths(platform, abis)))
        inspect_apple(root / library, abis, sdk)


def consume_mobile_artifact(args: argparse.Namespace) -> dict:
    expected_abis = (["arm64-v8a", "armeabi-v7a", "x86_64"] if args.platform == "android"
                     else ["arm64-v8a", "x86_64"])
    manifest = validate_artifact(args.artifact_dir, args.platform, source_sha(), expected_abis)
    target_root = ROOT / ("android/app/src/main/jniLibs" if args.platform == "android"
                          else "ohos/entry/libs")
    for abi in expected_abis:
        for filename in ("libqfli_go_runtime.so", "libqfli_go_runtime.h"):
            relative = f"{abi}/{filename}"
            source = args.artifact_dir / relative
            target = target_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return manifest


def validate_artifact(directory: Path, platform: str, expected_source_sha: str,
                      expected_abis: list[str]) -> dict:
    """Fail closed on missing, stale, incomplete or tampered native artifacts."""
    if not re.fullmatch(r"[0-9a-f]{40}", expected_source_sha):
        raise ValueError("Expected source SHA must be a full Git commit")
    expected_names = expected_runtime_paths(platform, expected_abis)
    run_id, run_attempt, expected_run_url = run_context()
    if directory.is_symlink():
        raise ValueError("Native artifact path must not be a symlink")
    root = directory.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Native artifact path is not a directory")
    manifest_path = root / "manifest.json"
    checksum_path = root / "SHA256SUMS"
    if not manifest_path.is_file() or not checksum_path.is_file():
        raise ValueError("Native artifact is missing manifest.json or SHA256SUMS")
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("Native artifact contains a symlink")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 2:
        raise ValueError("Unsupported native artifact manifest schema")
    if manifest.get("sourceSha") != expected_source_sha:
        raise ValueError("Native artifact application source SHA does not match this package")
    if manifest.get("commit") != expected_source_sha:
        raise ValueError("Native artifact commit does not match its source SHA")
    if manifest.get("platform") != platform:
        raise ValueError("Native artifact platform does not match this package")
    if manifest.get("sourceChecksConclusion") != "success":
        raise ValueError("Native artifact source checks did not succeed")
    if manifest.get("runId") != run_id or manifest.get("runAttempt") != run_attempt:
        raise ValueError("Native artifact is not from this GitHub run and attempt")
    if manifest.get("sourceChecksRunURL") != expected_run_url:
        raise ValueError("Native artifact source-check run URL does not match this run")
    try:
        finished = datetime.fromisoformat(manifest["finishedUtc"])
        if finished.utcoffset() is None:
            raise ValueError("Missing timezone")
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Native artifact completion timestamp is invalid") from error
    if manifest.get("abiSet") != sorted(expected_abis):
        raise ValueError("Native artifact ABI set does not match this package")
    if manifest.get("requiredExports") != sorted(SYMBOLS):
        raise ValueError("Native artifact required export set is incomplete")
    native_sha = native_source_hash()
    if manifest.get("nativeSourceSha256") != native_sha:
        raise ValueError("Native artifact native-source digest does not match this checkout")
    expected_build_inputs = {name: digest(ROOT / name) for name in BUILD_INPUTS}
    build = manifest.get("build")
    if (not isinstance(build, dict) or build.get("buildInputs") != expected_build_inputs
            or build.get("sourceSha") != expected_source_sha
            or build.get("nativeSourceSha256") != native_sha):
        raise ValueError("Native artifact build inputs or source identity do not match this checkout")

    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise ValueError("Native artifact file inventory is missing")
    declared: dict[str, dict] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Native artifact file inventory has an invalid record")
        relative = record.get("path")
        if not isinstance(relative, str) or relative in declared:
            raise ValueError("Native artifact file inventory has an invalid or duplicate path")
        candidate = Path(relative)
        if (candidate.is_absolute() or "\\" in relative or ":" in relative
                or any(part in ("", ".", "..") for part in relative.split("/"))):
            raise ValueError("Native artifact contains an unsafe file path")
        if (type(record.get("bytes")) is not int or record["bytes"] < 1
                or not isinstance(record.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"])):
            raise ValueError("Native artifact file inventory has an invalid size or digest")
        target = root / candidate
        if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(root):
            raise ValueError(f"Native artifact file is missing or unsafe: {relative}")
        if target.stat().st_size != record.get("bytes") or digest(target) != record.get("sha256"):
            raise ValueError(f"Native artifact file digest or size mismatch: {relative}")
        declared[relative] = record

    sums: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\r\n]+)", line)
        if not match or match.group(2) in sums:
            raise ValueError("Native artifact SHA256SUMS is malformed or contains duplicate paths")
        sums[match.group(2)] = match.group(1)
    expected_sums = {name: item["sha256"] for name, item in declared.items()}
    expected_sums["manifest.json"] = digest(manifest_path)
    if sums != expected_sums:
        raise ValueError("Native artifact SHA256SUMS does not match its file inventory")
    actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
                    and path.relative_to(root).as_posix() not in {"manifest.json", "SHA256SUMS"}}
    if actual_files != set(declared):
        raise ValueError("Native artifact contains unlisted or missing files")

    if set(declared) != expected_artifact_paths(platform, expected_abis):
        raise ValueError("Native artifact file inventory does not match the platform contract")
    runtime_records = {name for name in declared if Path(name).name in
                       {"libqfli_go_runtime.so", "qfli_go_runtime.dll", "libqfli_go_runtime.dylib", "libqfli_go_runtime.a"}}
    if runtime_records != expected_names:
        raise ValueError("Native artifact runtime library set is incomplete or unexpected")
    checks = manifest.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("Native artifact validation evidence is missing")
    checked_abis = []
    for item in checks:
        if not isinstance(item, dict) or item.get("requiredExports") != sorted(SYMBOLS):
            raise ValueError("Native artifact export validation evidence is incomplete")
        checked_abis.extend([item["abi"]] if item.get("abi") else item.get("architectures", []))
        if platform in ("android", "ohos", "linux"):
            alignments = item.get("loadAlignments")
            if (not isinstance(alignments, list) or not alignments
                    or any(type(value) is not int or value < 1 for value in alignments)
                    or (platform == "android" and min(alignments) < 16384)):
                raise ValueError("Native artifact LOAD alignment evidence is invalid")
    if sorted(checked_abis) != sorted(expected_abis):
        raise ValueError("Native artifact ABI validation evidence is incomplete or duplicated")
    validate_runtime_binaries(root, platform, expected_abis)
    return manifest


def stage(args: argparse.Namespace) -> None:
    before = json.loads(args.snapshot.read_text(encoding="utf-8-sig"))
    current = snapshot()
    if current != {key: before[key] for key in current}:
        raise ValueError("Application source, native sources, or build inputs changed during the build")
    source_checks = os.getenv("SOURCE_CHECKS_CONCLUSION")
    if source_checks != "success":
        raise ValueError("Native artifact production requires successful source checks")
    run_id, run_attempt, expected_run_url = run_context()
    source_check_url = os.getenv("SOURCE_CHECKS_RUN_URL")
    if source_check_url != expected_run_url:
        raise ValueError("Native artifact production requires this run's source-check run URL")
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError(f"Artifact staging directory must be empty: {args.output}")
    files: list[tuple[Path, str]] = []
    checks = []
    expected_abis: list[str]
    if args.platform in ("android", "ohos"):
        provenance = ROOT / f"native/build/bundled-go-runtime-build-{args.platform}.json"
        manifest = json.loads(provenance.read_text(encoding="utf-8-sig"))
        if datetime.fromisoformat(manifest["startedUtc"]) < datetime.fromisoformat(before["startedUtc"]):
            raise ValueError("Build provenance predates this build's source capture")
        if manifest["nativeSourceSha256"] != before["nativeSourceSha256"]:
            raise ValueError("Build provenance does not match the checked-out sources")
        expected = ["arm64-v8a", "armeabi-v7a", "x86_64"] if args.platform == "android" else ["arm64-v8a", "x86_64"]
        expected_abis = expected
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
    elif args.platform in ("windows", "linux"):
        expected_abis = ["x86_64"]
        library_name = "qfli_go_runtime.dll" if args.platform == "windows" else "libqfli_go_runtime.so"
        library = args.build / library_name
        header = args.build / ("qfli_go_runtime.h" if args.platform == "windows" else "libqfli_go_runtime.h")
        if args.platform == "windows":
            checks.append(inspect_pe(library))
        else:
            checks.append(inspect_elf(library, "x86_64", False, args.readelf))
        files.extend([(library, library_name), (header, header.name)])
    elif args.platform in ("macos-universal", "ios-device", "ios-simulator"):
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
        expected_abis = archs
    else:
        raise ValueError(f"Unsupported native artifact platform: {args.platform}")
    files.extend([(ROOT / "LICENSE", "licenses/PROJECT-LICENSE"),
                  (ROOT / "native/go_runtime/LICENSE.go-standard-library", "licenses/GO-LICENSE"),
                  (ROOT / "assets/licenses/yaegi.txt", "licenses/YAEGI-LICENSE")])
    names = [relative for _, relative in files]
    if len(names) != len(set(names)) or set(names) != expected_artifact_paths(args.platform, expected_abis):
        raise ValueError("Native producer file inventory does not match the platform contract")
    for source, _ in files:
        if source.is_symlink() or not source.is_file() or source.stat().st_size < 1:
            raise ValueError(f"Native producer file is missing, empty or unsafe: {source}")
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for source, relative in files:
        target = args.output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append({"path": relative, "bytes": target.stat().st_size, "sha256": digest(target)})
    report = {
        "schemaVersion": 2, "sourceSha": before["sourceSha"],
        "nativeSourceSha256": before["nativeSourceSha256"], "platform": args.platform,
        "abiSet": sorted(expected_abis), "requiredExports": sorted(SYMBOLS),
        "commit": before["sourceSha"], "runId": run_id,
        "runAttempt": run_attempt,
        "sourceChecksConclusion": source_checks,
        "sourceChecksRunURL": os.getenv("SOURCE_CHECKS_RUN_URL"),
        "finishedUtc": datetime.now(timezone.utc).isoformat(),
        "build": {key: value for key, value in before.items() if key != "startedUtc"},
        "deviceExecution": False, "checks": checks, "files": records,
    }
    report_path = args.output / "manifest.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    checksums = [(r["sha256"], r["path"]) for r in records] + [(digest(report_path), "manifest.json")]
    (args.output / "SHA256SUMS").write_text("".join(f"{sha}  {name}\n" for sha, name in checksums), encoding="utf-8")
    summary = f"### Native runtime: {args.platform}\n\n"
    summary += f"Source checks: **{report['sourceChecksConclusion']}**.\n\n"
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
    collect.add_argument("--platform", required=True,
                         choices=("android", "ohos", "macos-universal", "ios-device", "ios-simulator", "windows", "linux"))
    collect.add_argument("--snapshot", required=True, type=Path)
    collect.add_argument("--output", required=True, type=Path)
    collect.add_argument("--readelf", default="llvm-readelf")
    collect.add_argument("--build", type=Path)
    consume = sub.add_parser("consume")
    consume.add_argument("--platform", required=True, choices=("android", "ohos"))
    consume.add_argument("--artifact-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.action == "consume":
        manifest = consume_mobile_artifact(args)
        print(f"Validated {args.platform} native artifact for {manifest['sourceSha']}")
    elif args.action == "snapshot":
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
