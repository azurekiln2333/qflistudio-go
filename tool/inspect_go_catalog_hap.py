#!/usr/bin/env python3
"""Check exact Go assets, runtime bytes and ELF exports in an audit HAP.

This is archive evidence only. Signature and device execution are separate gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tool/go_curriculum"))
from audit_native import build_manifest, json_bytes, native_source_hash

SYMBOLS = {
    "QfliGoRun", "QfliGoCancel", "QfliGoFree", "QfliGoAnalyze", "QfliGoFormat",
    "QfliGoDebugStart", "QfliGoDebugPoll", "QfliGoDebugCommand", "QfliGoDebugClose",
}
MACHINES = {"x86_64": 62, "arm64-v8a": 183}
# Keep this three-source inventory aligned with build_go_catalog_audit.ps1.
AUDIT_SOURCE_PATHS = (
    "integration_test/go_catalog_test.dart",
    "integration_test/go_native_ide_acceptance.dart",
    "integration_test/go_product_ui_acceptance.dart",
)
AUDIT_OPERATIONS = {
    "api": (
        "analyze-unsaved-utf16", "format-and-inspect",
        "shared-debug-break-step-continue", "opaque-native-callback",
        "debug-stop-close-reopen",
    ),
    "ui": (
        "editor-unsaved-waves-problems", "editor-gutter-debug-panels",
        "direct-tools-real-source-projects", "named-multi-root-sidebar-retention",
    ),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect(hap: Path, abi: str, readelf: Path, *,
            runtime_build_manifest: Path, llvm_strip: Path | None = None,
            audit_build_manifest: Path | None = None,
            expected_topic_count: int = 120, expected_case_count: int = 364) -> dict:
    errors: list[str] = []
    assets: dict[str, str] = {}
    libraries: dict[str, dict] = {}
    hap_hash = sha256(hap.read_bytes())
    source_bytes = {relative: (ROOT / relative).read_bytes() for relative in AUDIT_SOURCE_PATHS}
    source_hashes = {relative: sha256(data) for relative, data in source_bytes.items()}
    if any(not data for data in source_bytes.values()):
        errors.append("required audit source must not be empty")
    audit_build_manifest = audit_build_manifest or hap.parent / "build.json"
    audit_build_bytes = audit_build_manifest.read_bytes()
    audit_build = json.loads(audit_build_bytes.decode("utf-8-sig"))
    if (audit_build.get("schemaVersion") != 2 or
            audit_build.get("entryPoint") != AUDIT_SOURCE_PATHS[0] or
            audit_build.get("abi") != abi or
            audit_build.get("hapSha256") != hap_hash):
        errors.append("audit build record does not bind this HAP, ABI and catalog entrypoint")
    if audit_build.get("auditSources") != source_hashes:
        errors.append("audit build record does not match exact current catalog/API/UI sources")
    provenance_bytes = runtime_build_manifest.read_bytes()
    provenance = json.loads(provenance_bytes.decode("utf-8-sig"))
    source_hash = native_source_hash()
    if provenance.get("schemaVersion") != 1 or provenance.get("nativeSourceSha256") != source_hash:
        errors.append("runtime build provenance does not match current native sources")
    expected_abis = {
        ("android", "arm64-v8a"), ("android", "armeabi-v7a"),
        ("android", "x86_64"), ("openharmony", "arm64-v8a"),
        ("openharmony", "x86_64"),
    }
    records = provenance.get("libraries", [])
    if (len(records) != len(expected_abis) or
            {(item["platform"], item["abi"]) for item in records} != expected_abis):
        errors.append("runtime build provenance does not cover exactly all five bundled ABIs")
    if not provenance.get("buildInputs"):
        errors.append("runtime build provenance has no build-input digests")
    for relative, expected in provenance.get("buildInputs", {}).items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or sha256(path.read_bytes()) != expected:
            errors.append(f"runtime build input changed: {relative}")
    for item in records:
        path = (ROOT / item["path"]).resolve()
        if (not path.is_relative_to(ROOT) or sha256(path.read_bytes()) != item["sha256"] or
                path.stat().st_size != item["bytes"]):
            errors.append(f"built runtime differs from provenance: {item['path']}")
    with zipfile.ZipFile(hap) as archive, tempfile.TemporaryDirectory(prefix="go_hap_elf_") as scratch:
        names = archive.namelist()
        if len(names) != len(set(names)):
            errors.append("duplicate ZIP entry names")
        for name in ("tutorials.json", "examples.json", "audit-manifest.json"):
            source = (ROOT / "assets/curriculum" / name).read_bytes()
            packed = archive.read("resources/rawfile/flutter_assets/assets/curriculum/" + name)
            assets[name] = sha256(packed)
            if packed != source:
                errors.append(f"packaged asset differs from current source: {name}")
        manifest = json.loads((ROOT / "assets/curriculum/audit-manifest.json").read_bytes())
        ids = [item["id"] for item in manifest["cases"]]
        if not ids or len(ids) != len(set(ids)) or manifest.get("inventoryIssues"):
            errors.append("invalid source audit inventory")
        expected_topics = {f"T{number:03d}" for number in range(1, expected_topic_count + 1)}
        if len(ids) != expected_case_count or {item["topic"] for item in manifest["cases"]} != expected_topics:
            errors.append(f"audit coverage must include exactly {expected_topic_count} topics/{expected_case_count} cases")
        regenerated = build_manifest(
            ROOT / "assets/curriculum/tutorials.json", ROOT / "assets/curriculum/examples.json",
            ROOT / "tool/go_curriculum/topics", ROOT / "tool/go_curriculum/samples",
        )
        if json_bytes(regenerated) != json_bytes(manifest):
            errors.append("audit manifest differs from the full regenerated source inventory")
        for kind, name in (("tutorial", "tutorials.json"), ("example", "examples.json")):
            if assets[name] != manifest["catalogs"][kind]["sha256"]:
                errors.append(f"manifest/catalog digest mismatch: {kind}")
        runtimes = [name for name in names if name.endswith("/libqfli_go_runtime.so")]
        if runtimes != [f"libs/{abi}/libqfli_go_runtime.so"]:
            errors.append(f"unexpected runtime ABI set: {runtimes}")
        for name in ("libqfli_go_runtime.so", "libflutter.so"):
            data = archive.read(f"libs/{abi}/{name}")
            if (len(data) < 64 or data[:6] != b"\x7fELF\x02\x01" or
                    struct.unpack_from("<H", data, 18)[0] != MACHINES[abi]):
                errors.append(f"wrong ELF machine/class/endianness: {name}")
            libraries[name] = {"sha256": sha256(data), "bytes": len(data)}
            if name == "libqfli_go_runtime.so":
                local = ROOT / "ohos/entry/libs" / abi / name
                staged = local.read_bytes()
                binding = {"stagedSha256": sha256(staged), "stagedBytes": len(staged),
                           "packagedSha256": sha256(data), "packagedBytes": len(data),
                           "transform": "identity", "verified": data == staged}
                if data != staged and llvm_strip is not None:
                    strip_input = Path(scratch) / "staged-runtime.so"
                    strip_input.write_bytes(staged)
                    transformed = Path(scratch) / "sdk-stripped-runtime.so"
                    # Hvigor's native-strip worker applies this exact command,
                    # even to the runtime already stripped by our build script.
                    arguments = ["--keep-section=.permission", str(strip_input), "-o" + str(transformed)]
                    strip_tool_hash = sha256(llvm_strip.read_bytes())
                    subprocess.run([str(llvm_strip), *arguments], check=True, capture_output=True)
                    transformed_bytes = transformed.read_bytes()
                    binding.update({"transform": "hvigor-default-strip-keep-permission",
                                    "tool": str(llvm_strip.resolve()),
                                    "toolSha256": strip_tool_hash,
                                    "stagedSource": str(local),
                                    "arguments": arguments,
                                    "transformedSha256": sha256(transformed_bytes),
                                    "transformedBytes": len(transformed_bytes),
                                    "verified": data == transformed_bytes})
                    if sha256(llvm_strip.read_bytes()) != strip_tool_hash:
                        errors.append("SDK strip tool changed during inspection")
                libraries[name]["buildBinding"] = binding
                if not binding["verified"]:
                    errors.append("packaged Go runtime matches neither the built library nor its exact SDK strip transform")
                matching = [item for item in records if item["platform"] == "openharmony" and item["abi"] == abi]
                if len(matching) != 1 or matching[0]["sha256"] != sha256(staged):
                    errors.append("packaged runtime has no unique matching source-bound build record")
                extracted = Path(scratch) / name
                extracted.write_bytes(data)
                symbols = subprocess.check_output(
                    [str(readelf), "--dyn-syms", "--wide", str(extracted)], text=True,
                )
                exported = {
                    line.split()[-1] for line in symbols.splitlines()
                    if re.search(r"\bGLOBAL\s+DEFAULT\s+(?!UND\b)\S+\s+\S+\s*$", line)
                }
                missing = sorted(SYMBOLS - exported)
                libraries[name]["requiredExports"] = sorted(SYMBOLS)
                if missing:
                    errors.append(f"missing Go ABI exports: {missing}")
        module = json.loads(archive.read("module.json"))
        kernel = archive.read("resources/rawfile/flutter_assets/kernel_blob.bin")
        for marker in (
            b"integration_test/go_catalog_test.dart",
            b"QFLI_GO_CATALOG_AUDIT",
            b"QFLI_GO_OFFLINE_HOST_AUDIT",
            b"QFLI_GO_NATIVE_IDE_AUDIT",
            b"QFLI_GO_PRODUCT_UI_AUDIT",
            b"every packaged Go catalog case runs through FFI",
        ):
            if marker not in kernel:
                errors.append(f"audit code marker missing from debug kernel: {marker.decode()}")
        audit_source_binding = {}
        for relative, data in source_bytes.items():
            path_present = relative.encode("utf-8") in kernel
            payload_present = bool(data) and data in kernel
            audit_source_binding[relative] = {
                "sha256": source_hashes[relative], "bytes": len(data),
                "kernelPathPresent": path_present, "exactKernelSourcePresent": payload_present,
            }
            if not path_present or not payload_present:
                errors.append(f"exact current audit source bytes/path missing from debug kernel: {relative}")
        for group, operation_ids in AUDIT_OPERATIONS.items():
            for operation_id in operation_ids:
                if operation_id.encode("utf-8") not in kernel:
                    errors.append(f"required {group} audit operation missing from debug kernel: {operation_id}")
        if module["app"].get("buildMode") != "debug":
            errors.append("audit package is not a debug build")
        permissions = [item["name"] for item in module["module"].get("requestPermissions", [])]
    if native_source_hash() != source_hash:
        errors.append("native source changed during package inspection")
    for relative, expected in source_hashes.items():
        if sha256((ROOT / relative).read_bytes()) != expected:
            errors.append(f"audit source changed during package inspection: {relative}")
    if sha256(hap.read_bytes()) != hap_hash:
        errors.append("HAP changed during package inspection")
    if audit_build_manifest.read_bytes() != audit_build_bytes:
        errors.append("audit build record changed during package inspection")
    return {
        "hap": str(hap.resolve()), "hapSha256": hap_hash,
        "abi": abi, "bundleName": module["app"]["bundleName"],
        "assets": assets, "caseCount": len(ids), "libraries": libraries,
        "auditKernelSha256": sha256(kernel),
        "auditBuildManifest": str(audit_build_manifest.resolve()),
        "auditBuildManifestSha256": sha256(audit_build_bytes),
        "auditSources": audit_source_binding,
        "requiredAuditOperations": {group: list(ids) for group, ids in AUDIT_OPERATIONS.items()},
        "nativeSourceSha256": source_hash,
        "runtimeBuildManifestSha256": sha256(provenance_bytes),
        "runtimeBuildManifest": str(runtime_build_manifest.resolve()),
        "expectedTopicCount": expected_topic_count, "expectedCaseCount": expected_case_count,
        "permissions": permissions, "errors": errors, "success": not errors,
        "evidenceLevel": "archive-bytes-and-elf", "signatureVerified": False,
        "deviceExecution": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hap", type=Path)
    parser.add_argument("--abi", required=True, choices=MACHINES)
    parser.add_argument("--readelf", required=True, type=Path)
    parser.add_argument("--llvm-strip", type=Path, help="Exact SDK strip tool used by Hvigor")
    parser.add_argument("--runtime-build-manifest", type=Path,
                        default=ROOT / "native/build/bundled-go-runtime-build.json")
    parser.add_argument("--audit-build-manifest", type=Path,
                        help="Source-bound build.json from build_go_catalog_audit.ps1; defaults beside the HAP")
    parser.add_argument("--expected-topic-count", type=int, default=120)
    parser.add_argument("--expected-case-count", type=int, default=364)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = inspect(args.hap, args.abi, args.readelf,
                         runtime_build_manifest=args.runtime_build_manifest,
                         llvm_strip=args.llvm_strip,
                         audit_build_manifest=args.audit_build_manifest,
                         expected_topic_count=args.expected_topic_count,
                         expected_case_count=args.expected_case_count)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
        report = {"success": False, "errors": [str(error)], "deviceExecution": False}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("success", "errors")}, ensure_ascii=False))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
