"""Exercise the inspector on synthetic ZIP fixtures, never a real HAP build."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--readelf", required=True, type=Path)
    parser.add_argument("--strip", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    source_root = args.root.resolve()
    sys.dont_write_bytecode = True
    inspector_path = source_root / "tool/inspect_go_catalog_hap.py"
    spec = importlib.util.spec_from_file_location("reviewed_go_inspector", inspector_path)
    inspector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inspector)
    source_hash = inspector.native_source_hash()
    results: dict = {"syntheticArchiveOnly": True, "realBuildOrDeviceExecution": False,
                     "inspectorSha256": digest(inspector_path.read_bytes()),
                     "sourceDigestSnapshot": source_hash, "checks": []}

    with tempfile.TemporaryDirectory(prefix="go_inspector_binding_review_") as directory:
        root = Path(directory).resolve()
        inspector.ROOT = root
        # This synthetic provenance intentionally has no build claim. Freeze the
        # source-digest provider so negatives can test its comparison in isolation.
        inspector.native_source_hash = lambda: source_hash
        for name in ("topics", "samples"):
            shutil.copytree(source_root / "tool/go_curriculum" / name,
                            root / "tool/go_curriculum" / name)
        assets = root / "assets/curriculum"
        assets.mkdir(parents=True)
        for name in ("tutorials.json", "examples.json", "audit-manifest.json"):
            shutil.copyfile(source_root / "assets/curriculum" / name, assets / name)
        script_relative = "tool/build_go_runtime.ps1"
        shutil.copyfile(source_root / script_relative, root / script_relative)
        manifest_path = root / "synthetic-build-provenance.json"
        audit_build_path = root / "synthetic-audit-build.json"
        for relative in inspector.AUDIT_SOURCE_PATHS:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_root / relative, destination)
        records = []
        for platform, abis in (("android", ("arm64-v8a", "armeabi-v7a", "x86_64")),
                               ("openharmony", ("arm64-v8a", "x86_64"))):
            for abi in abis:
                relative = (f"ohos/entry/libs/{abi}/libqfli_go_runtime.so" if platform == "openharmony"
                            else f"android/app/src/main/jniLibs/{abi}/libqfli_go_runtime.so")
                local = root / relative
                local.parent.mkdir(parents=True)
                if platform == "openharmony":
                    shutil.copyfile(source_root / relative, local)
                else:
                    local.write_bytes(f"synthetic other ABI {abi}".encode())
                records.append({"platform": platform, "abi": abi, "path": relative,
                                "sha256": digest(local.read_bytes()), "bytes": local.stat().st_size})
        provenance = {"schemaVersion": 1, "nativeSourceSha256": source_hash,
                      "buildInputs": {script_relative: digest((root / script_relative).read_bytes())},
                      "toolchains": {"synthetic": {"noBuildClaim": True}}, "libraries": records}
        original_manifest = (assets / "audit-manifest.json").read_bytes()

        def write_provenance(value: dict = provenance) -> None:
            manifest_path.write_text(json.dumps(value), encoding="utf-8")

        def archive(abi: str, data: bytes, *, extra_runtime: bool = False,
                    include_ide_marker: bool = True, include_ui_marker: bool = True,
                    missing_source: str | None = None, stale_source: str | None = None,
                    missing_operation: str | None = None) -> Path:
            path = root / f"fixture-{abi}.zip"
            header = bytearray(64)
            header[:6] = b"\x7fELF\x02\x01"
            struct.pack_into("<H", header, 18, inspector.MACHINES[abi])
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as packed:
                for asset in ("tutorials.json", "examples.json", "audit-manifest.json"):
                    packed.write(assets / asset, "resources/rawfile/flutter_assets/assets/curriculum/" + asset)
                packed.writestr(f"libs/{abi}/libqfli_go_runtime.so", data)
                packed.writestr(f"libs/{abi}/libflutter.so", header)
                if extra_runtime:
                    packed.writestr("libs/unexpected/libqfli_go_runtime.so", b"extra")
                packed.writestr("module.json", json.dumps({"app": {"buildMode": "debug", "bundleName": "review.synthetic"}, "module": {}}))
                kernel = (b"integration_test/go_catalog_test.dart QFLI_GO_CATALOG_AUDIT "
                          b"QFLI_GO_OFFLINE_HOST_AUDIT "
                          b"every packaged Go catalog case runs through FFI")
                kernel += b" QFLI_GO_NATIVE_IDE_AUDIT QFLI_GO_PRODUCT_UI_AUDIT"
                for relative in inspector.AUDIT_SOURCE_PATHS:
                    payload = (root / relative).read_bytes()
                    kernel += b"\n" + relative.encode("utf-8") + b"\n"
                    if relative != missing_source:
                        kernel += (b"/" + payload[1:]) if relative == stale_source else payload
                if not include_ide_marker:
                    kernel = kernel.replace(b"QFLI_GO_NATIVE_IDE_AUDIT", b"QFLI_GO_NATIVE_IDE_REMOVED")
                if not include_ui_marker:
                    kernel = kernel.replace(b"QFLI_GO_PRODUCT_UI_AUDIT", b"QFLI_GO_PRODUCT_UI_REMOVED")
                if missing_operation is not None:
                    kernel = kernel.replace(missing_operation.encode("utf-8"), b"omitted-operation")
                packed.writestr("resources/rawfile/flutter_assets/kernel_blob.bin", kernel)
            audit_build_path.write_text(json.dumps({
                "schemaVersion": 2, "entryPoint": inspector.AUDIT_SOURCE_PATHS[0],
                "abi": abi, "hapSha256": digest(path.read_bytes()),
                "auditSources": {relative: digest((root / relative).read_bytes())
                                 for relative in inspector.AUDIT_SOURCE_PATHS},
            }), encoding="utf-8")
            return path

        def check(label: str, path: Path, abi: str, *, expected_success: bool,
                  expected_error: str | None = None, strip_tool: Path | None = args.strip,
                  audit_changes: dict | None = None) -> dict:
            original_audit = audit_build_path.read_bytes()
            if audit_changes is not None:
                changed_audit = json.loads(original_audit)
                changed_audit.update(audit_changes)
                audit_build_path.write_text(json.dumps(changed_audit), encoding="utf-8")
            try:
                report = inspector.inspect(path, abi, args.readelf,
                                           runtime_build_manifest=manifest_path, llvm_strip=strip_tool,
                                           audit_build_manifest=audit_build_path)
            finally:
                audit_build_path.write_bytes(original_audit)
            assert report["success"] == expected_success, (label, report["errors"])
            if expected_error:
                assert any(expected_error in message for message in report["errors"]), (label, report["errors"])
            results["checks"].append({"case": label, "expectedSuccess": expected_success,
                                      "actualSuccess": report["success"], "errors": report["errors"],
                                      "binding": report["libraries"]["libqfli_go_runtime.so"]["buildBinding"]})
            return report

        write_provenance()
        for abi in ("x86_64", "arm64-v8a"):
            local = root / f"ohos/entry/libs/{abi}/libqfli_go_runtime.so"
            staged = local.read_bytes()
            check(f"{abi}/identity", archive(abi, staged), abi, expected_success=True, strip_tool=None)
            transformed = root / f"sdk-stripped-{abi}.so"
            subprocess.run([str(args.strip), "--keep-section=.permission", str(local), "-o" + str(transformed)],
                           check=True, capture_output=True)
            stripped = transformed.read_bytes()
            assert staged != stripped
            report = check(f"{abi}/exact-sdk-transform", archive(abi, stripped), abi, expected_success=True)
            assert report["libraries"]["libqfli_go_runtime.so"]["buildBinding"]["transform"] == "hvigor-default-strip-keep-permission"
            check(f"{abi}/one-byte-mismatch", archive(abi, stripped + b"x"), abi,
                  expected_success=False, expected_error="matches neither")
            assert local.read_bytes() == staged

        abi = "x86_64"
        staged = (root / f"ohos/entry/libs/{abi}/libqfli_go_runtime.so").read_bytes()
        packed = archive(abi, staged)
        write_provenance({**provenance, "nativeSourceSha256": "0" * 64})
        check("negative/source-digest", packed, abi, expected_success=False, expected_error="current native sources")
        write_provenance({**provenance, "libraries": records[1:]})
        check("negative/missing-build-ABI", packed, abi, expected_success=False, expected_error="all five bundled ABIs")
        write_provenance()
        build_script = root / script_relative
        build_script.write_bytes(build_script.read_bytes() + b"\n# changed fixture\n")
        check("negative/build-script-drift", packed, abi, expected_success=False, expected_error="build input changed")
        shutil.copyfile(source_root / script_relative, build_script)
        manifest = json.loads(original_manifest)
        manifest["cases"].pop()
        (assets / "audit-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        check("negative/missing-catalog-case", archive(abi, staged), abi,
              expected_success=False, expected_error="120 topics/364 cases")
        (assets / "audit-manifest.json").write_bytes(original_manifest)
        check("negative/unexpected-packaged-ABI", archive(abi, staged, extra_runtime=True), abi,
              expected_success=False, expected_error="unexpected runtime ABI set")
        check("negative/missing-native-IDE-kernel-marker",
              archive(abi, staged, include_ide_marker=False), abi,
              expected_success=False, expected_error="QFLI_GO_NATIVE_IDE_AUDIT")
        check("negative/missing-product-UI-kernel-marker",
              archive(abi, staged, include_ui_marker=False), abi,
              expected_success=False, expected_error="QFLI_GO_PRODUCT_UI_AUDIT")
        for relative in inspector.AUDIT_SOURCE_PATHS:
            check(f"negative/missing-source/{relative}",
                  archive(abi, staged, missing_source=relative), abi,
                  expected_success=False, expected_error=f"source bytes/path missing from debug kernel: {relative}")
            check(f"negative/stale-source/{relative}",
                  archive(abi, staged, stale_source=relative), abi,
                  expected_success=False, expected_error=f"source bytes/path missing from debug kernel: {relative}")
        for group, operation_ids in inspector.AUDIT_OPERATIONS.items():
            for operation_id in operation_ids:
                check(f"negative/missing-{group}-operation/{operation_id}",
                      archive(abi, staged, missing_operation=operation_id), abi,
                      expected_success=False, expected_error=f"audit operation missing from debug kernel: {operation_id}")
        packed = archive(abi, staged)
        check("negative/audit-build-schema", packed, abi, expected_success=False,
              expected_error="audit build record does not bind", audit_changes={"schemaVersion": 1})
        check("negative/audit-build-hap-digest", packed, abi, expected_success=False,
              expected_error="audit build record does not bind", audit_changes={"hapSha256": "0" * 64})
        check("negative/audit-build-sources", packed, abi, expected_success=False,
              expected_error="exact current catalog/API/UI sources", audit_changes={"auditSources": {}})
        relative = inspector.AUDIT_SOURCE_PATHS[1]
        source_path = root / relative
        original_source = source_path.read_bytes()
        try:
            source_path.write_bytes(original_source + b"\n// changed after build\n")
            check("negative/audit-source-drift-after-build", packed, abi, expected_success=False,
                  expected_error="exact current catalog/API/UI sources")
        finally:
            source_path.write_bytes(original_source)
        results["success"] = True
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"success": True, "checks": len(results["checks"]), "out": str(args.out)}))


if __name__ == "__main__":
    main()
