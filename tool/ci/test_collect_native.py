"""Reject native artifact formats that would break the intended target."""
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import collect_native as collector
from test_app_build import make_elf, make_pe

SOURCE_SHA = "a" * 40
RUN_URL = "https://github.com/example/project/actions/runs/123"
RUN_ENV = {"GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "2",
           "GITHUB_SERVER_URL": "https://github.com", "GITHUB_REPOSITORY": "example/project",
           "SOURCE_CHECKS_CONCLUSION": "success", "SOURCE_CHECKS_RUN_URL": RUN_URL}


class ElfValidationTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, RUN_ENV)
        environment.start()
        self.addCleanup(environment.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = Path(self.temp.name) / "runtime.so"

    def elf(self, machine=183, alignment=16384):
        data = bytearray(120)
        data[:6] = b"\x7fELF\x02\x01"
        struct.pack_into("<HH", data, 16, 3, machine)
        struct.pack_into("<Q", data, 32, 64)
        struct.pack_into("<HH", data, 54, 56, 1)
        struct.pack_into("<I", data, 64, 1)
        struct.pack_into("<Q", data, 112, alignment)
        self.library.write_bytes(data)

    def symbols(self):
        return "\n".join(f"1: 0 1 FUNC GLOBAL DEFAULT 1 {name}" for name in collector.SYMBOLS)

    def test_accepts_android_arm64_with_all_exports_and_16k_alignment(self):
        self.elf()
        with patch.object(collector, "command", return_value=self.symbols()):
            result = collector.inspect_elf(self.library, "arm64-v8a", True, "readelf")
        self.assertEqual(result["loadAlignments"], [16384])

    def test_rejects_wrong_abi_even_with_correct_filename(self):
        self.elf(machine=62)
        with self.assertRaisesRegex(ValueError, "machine"):
            collector.inspect_elf(self.library, "arm64-v8a", True, "readelf")

    def test_rejects_android_4k_alignment(self):
        self.elf(alignment=4096)
        with self.assertRaisesRegex(ValueError, "alignment"):
            collector.inspect_elf(self.library, "arm64-v8a", True, "readelf")

    def test_rejects_undefined_ffi_symbol(self):
        self.elf()
        symbols = self.symbols().replace("DEFAULT 1 QfliGoDebugClose", "DEFAULT UND QfliGoDebugClose")
        with patch.object(collector, "command", return_value=symbols):
            with self.assertRaisesRegex(ValueError, "QfliGoDebugClose"):
                collector.inspect_elf(self.library, "arm64-v8a", True, "readelf")

    def test_does_not_apply_android_alignment_rule_to_ohos(self):
        self.elf(alignment=4096)
        with patch.object(collector, "command", return_value=self.symbols()):
            collector.inspect_elf(self.library, "arm64-v8a", False, "readelf")

    def test_checks_arm32_program_header_alignment(self):
        data = bytearray(84)
        data[:6] = b"\x7fELF\x01\x01"
        struct.pack_into("<HH", data, 16, 3, 40)
        struct.pack_into("<I", data, 28, 52)
        struct.pack_into("<HH", data, 42, 32, 1)
        struct.pack_into("<I", data, 52, 1)
        struct.pack_into("<I", data, 80, 16384)
        self.library.write_bytes(data)
        with patch.object(collector, "command", return_value=self.symbols()):
            collector.inspect_elf(self.library, "armeabi-v7a", True, "readelf")
        struct.pack_into("<I", data, 80, 4096)
        self.library.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "alignment"):
            collector.inspect_elf(self.library, "armeabi-v7a", True, "readelf")

    def test_rejects_apple_archive_with_missing_architecture(self):
        with patch.object(collector, "command", return_value="arm64"):
            with self.assertRaisesRegex(ValueError, "slices"):
                collector.inspect_apple(self.library, ["arm64", "x86_64"], "iphonesimulator")

    def test_requires_exports_in_every_apple_slice(self):
        complete = "\n".join(f"000000 T _{name}" for name in collector.SYMBOLS)
        incomplete = complete.replace("_QfliGoDebugClose", "_OtherFunction")
        with patch.object(collector, "command", side_effect=["arm64 x86_64", complete, incomplete]):
            with self.assertRaisesRegex(ValueError, "x86_64 C ABI exports"):
                collector.inspect_apple(self.library, ["arm64", "x86_64"], "iphonesimulator")

    def test_rejects_changed_sources_before_staging(self):
        captured = Path(self.temp.name) / "source.json"
        captured.write_text(json.dumps({"nativeSourceSha256": "old", "buildInputs": {}}))
        args = SimpleNamespace(snapshot=captured, output=Path(self.temp.name) / "artifact")
        with patch.object(collector, "snapshot", return_value={"nativeSourceSha256": "new", "buildInputs": {}}):
            with self.assertRaisesRegex(ValueError, "changed during"):
                collector.stage(args)
        self.assertFalse(args.output.exists())

    def test_rejects_stale_provenance_before_copying_libraries(self):
        root = Path(self.temp.name)
        source = {"nativeSourceSha256": "same", "buildInputs": {}}
        captured = root / "source.json"
        captured.write_text(json.dumps(dict(source, startedUtc="2026-11-17T01:00:00+00:00")))
        manifest = root / "native/build/bundled-go-runtime-build-android.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"startedUtc": "2026-11-16T01:00:00+00:00"}))
        args = SimpleNamespace(snapshot=captured, output=root / "artifact", platform="android")
        with patch.object(collector, "ROOT", root), patch.object(collector, "snapshot", return_value=source):
            with self.assertRaisesRegex(ValueError, "predates"):
                collector.stage(args)
        self.assertFalse(args.output.exists())

    def test_rejects_unsuccessful_source_checks_before_staging(self):
        source = {"sourceSha": SOURCE_SHA, "nativeSourceSha256": "same", "buildInputs": {}}
        captured = Path(self.temp.name) / "source.json"
        captured.write_text(json.dumps(source))
        output = Path(self.temp.name) / "artifact"
        args = SimpleNamespace(snapshot=captured, output=output)
        for conclusion in ("failure", "cancelled", "skipped", ""):
            with self.subTest(conclusion=conclusion), patch.object(collector, "snapshot", return_value=source):
                with patch.dict(os.environ, {"SOURCE_CHECKS_CONCLUSION": conclusion}):
                    with self.assertRaisesRegex(ValueError, "requires successful source checks"):
                        collector.stage(args)
            self.assertFalse(output.exists())


class ArtifactContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in ("LICENSE", "native/go_runtime/LICENSE.go-standard-library",
                         "assets/licenses/yaegi.txt", "build-input"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture", encoding="utf-8")
        for mocked in (patch.dict(os.environ, RUN_ENV), patch.object(collector, "ROOT", self.root),
                       patch.object(collector, "BUILD_INPUTS", ("build-input",)),
                       patch.object(collector, "source_sha", return_value=SOURCE_SHA),
                       patch.object(collector, "native_source_hash", return_value="b" * 64),
                       patch("builtins.print")):
            mocked.start()
            self.addCleanup(mocked.stop)
        os.environ.pop("GITHUB_STEP_SUMMARY", None)

    def write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def produce(self, platform):
        captured = self.root / f"{platform}-source.json"
        before = dict(collector.snapshot(), startedUtc="2026-11-27T01:00:00+00:00")
        captured.write_text(json.dumps(before), encoding="utf-8")
        build = self.root / platform
        abis = collector.PLATFORM_ABIS[platform]
        if platform in ("android", "ohos"):
            libraries = []
            for abi in abis:
                data = make_elf(collector.ABI_MACHINES[abi][1], wide=abi != "armeabi-v7a",
                                symbols=sorted(collector.SYMBOLS))
                library = self.write(f"built/{platform}/{abi}/libqfli_go_runtime.so", data)
                library.with_suffix(".h").write_text("runtime header", encoding="utf-8")
                libraries.append({"abi": abi, "path": library.relative_to(self.root).as_posix(),
                                  "platform": "android" if platform == "android" else "openharmony",
                                  "sha256": collector.digest(library), "bytes": len(data)})
            provenance = {"startedUtc": "2026-11-27T02:00:00+00:00",
                          "nativeSourceSha256": before["nativeSourceSha256"], "libraries": libraries}
            self.write(f"native/build/bundled-go-runtime-build-{platform}.json",
                       json.dumps(provenance).encode())
        elif platform in ("windows", "linux"):
            library = "qfli_go_runtime.dll" if platform == "windows" else "libqfli_go_runtime.so"
            data = (make_pe(exports=sorted(collector.SYMBOLS), imports=["KERNEL32.dll"])
                    if platform == "windows" else make_elf(62, symbols=sorted(collector.SYMBOLS)))
            path = self.write(f"{platform}/{library}", data)
            path.with_suffix(".h").write_text("runtime header", encoding="utf-8")
        elif platform == "macos-universal":
            self.write(f"{platform}/bundle/Frameworks/libqfli_go_runtime.dylib", b"Mach-O fixture")
            for abi in abis:
                self.write(f"{platform}/derived/qfli_go_runtime/{abi}/libqfli_go_runtime.h", b"header")
        else:
            self.write(f"{platform}/derived/qfli_go_runtime/libqfli_go_runtime.a", b"archive fixture")
            self.write(f"{platform}/derived/qfli_go_runtime/libqfli_go_runtime.h", b"header")
        output = self.root / f"artifact-{platform}"
        args = SimpleNamespace(snapshot=captured, output=output, platform=platform,
                               build=build, readelf="readelf")
        symbols = "\n".join(f"1: 0 1 FUNC GLOBAL DEFAULT 1 {name}" for name in collector.SYMBOLS)
        apple_check = {"architectures": abis, "requiredExports": sorted(collector.SYMBOLS)}
        with patch.object(collector, "command", return_value=symbols):
            with patch.object(collector, "inspect_apple", return_value=apple_check):
                collector.stage(args)
        return output

    def validate(self, output, platform="linux"):
        return collector.validate_artifact(output, platform, SOURCE_SHA, collector.PLATFORM_ABIS[platform])

    def rewrite(self, output, mutate):
        path = output / "manifest.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        mutate(report)
        path.write_text(json.dumps(report) + "\n", encoding="utf-8")
        records = [(item["sha256"], item["path"]) for item in report["files"]]
        records.append((collector.digest(path), "manifest.json"))
        (output / "SHA256SUMS").write_text("".join(f"{sha}  {name}\n" for sha, name in records),
                                          encoding="utf-8")

    def test_all_platforms_stage_schema_two_and_exact_inventories(self):
        for platform, abis in collector.PLATFORM_ABIS.items():
            with self.subTest(platform=platform):
                output = self.produce(platform)
                with patch.object(collector, "inspect_apple", return_value={}):
                    manifest = self.validate(output, platform)
                self.assertEqual(manifest["schemaVersion"], 2)
                self.assertEqual(manifest["sourceSha"], SOURCE_SHA)
                self.assertEqual(manifest["sourceChecksRunURL"], RUN_URL)
                self.assertEqual(manifest["sourceChecksConclusion"], "success")
                self.assertEqual(manifest["runAttempt"], "2")
                self.assertEqual({item["path"] for item in manifest["files"]},
                                 collector.expected_artifact_paths(platform, abis))
                self.assertFalse(manifest["deviceExecution"])

    def test_rejects_wrong_source_run_abi_exports_and_build_identity(self):
        cases = [("sourceSha", "c" * 40, "source SHA"), ("commit", "c" * 40, "commit"),
                 ("platform", "windows", "platform"), ("runId", "122", "run and attempt"),
                 ("runAttempt", "1", "run and attempt"), ("sourceChecksRunURL", RUN_URL + "9", "run URL"),
                 ("sourceChecksConclusion", "failure", "did not succeed"),
                 ("abiSet", ["arm64"], "ABI set"), ("requiredExports", [], "export set"),
                 ("nativeSourceSha256", "c" * 64, "native-source digest"),
                 ("finishedUtc", "invalid", "timestamp"), ("build", {}, "build inputs")]
        output = self.produce("linux")
        original = json.loads((output / "manifest.json").read_text())
        for key, value, error in cases:
            with self.subTest(key=key):
                self.rewrite(output, lambda report: report.update(original))
                self.rewrite(output, lambda report: report.update({key: value}))
                with self.assertRaisesRegex(ValueError, error):
                    self.validate(output)
        self.rewrite(output, lambda report: report.update(original))
        for key in ("sourceSha", "nativeSourceSha256", "buildInputs"):
            with self.subTest(build=key):
                self.rewrite(output, lambda report: report.update(json.loads(json.dumps(original))))
                self.rewrite(output, lambda report: report["build"].update({key: None}))
                with self.assertRaisesRegex(ValueError, "build inputs"):
                    self.validate(output)

    def test_rejects_tampering_even_when_inventory_is_rehashed(self):
        output = self.produce("linux")
        library = output / "libqfli_go_runtime.so"
        library.write_bytes(make_elf(183, symbols=sorted(collector.SYMBOLS)))
        with self.assertRaisesRegex(ValueError, "digest or size mismatch"):
            self.validate(output)
        def rehash(report):
            item = next(item for item in report["files"] if item["path"] == library.name)
            item.update(bytes=library.stat().st_size, sha256=collector.digest(library))
        self.rewrite(output, rehash)
        with self.assertRaisesRegex(RuntimeError, "Wrong ELF machine"):
            self.validate(output)
        library.write_bytes(make_elf(62))
        self.rewrite(output, rehash)
        with self.assertRaisesRegex(RuntimeError, "Missing Go runtime exports"):
            self.validate(output)

    def test_rejects_unlisted_missing_duplicate_and_unsafe_files(self):
        output = self.produce("linux")
        unexpected = output / "extra.so"
        unexpected.write_bytes(b"unexpected")
        with self.assertRaisesRegex(ValueError, "unlisted"):
            self.validate(output)
        unexpected.unlink()
        original = (output / "SHA256SUMS").read_text()
        (output / "SHA256SUMS").write_text(original + original.splitlines()[0] + "\n")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.validate(output)
        (output / "SHA256SUMS").write_text(original)
        manifest = json.loads((output / "manifest.json").read_text())
        for path in ("../outside", "/absolute", "a\\b", "a//b", "./file", "C:drive"):
            with self.subTest(path=path):
                self.rewrite(output, lambda report: report.update(json.loads(json.dumps(manifest))))
                self.rewrite(output, lambda report: report["files"][0].update(path=path))
                with self.assertRaisesRegex(ValueError, "unsafe"):
                    self.validate(output)
        self.rewrite(output, lambda report: report.update(manifest))
        self.rewrite(output, lambda report: report["files"].append(report["files"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.validate(output)
        self.rewrite(output, lambda report: report.update(manifest))
        (output / "libqfli_go_runtime.so").unlink()
        with self.assertRaisesRegex(ValueError, "missing or unsafe"):
            self.validate(output)

    def test_rejects_missing_headers_licenses_checks_and_checksums(self):
        output = self.produce("linux")
        manifest = json.loads((output / "manifest.json").read_text())
        for field, value, message in (("checks", [], "validation evidence"),
                                      ("checks", [{"abi": "x86_64", "requiredExports": []}], "export validation")):
            self.rewrite(output, lambda report: report.update(manifest))
            self.rewrite(output, lambda report: report.update({field: value}))
            with self.assertRaisesRegex(ValueError, message):
                self.validate(output)
        self.rewrite(output, lambda report: report.update(manifest))
        header = output / "libqfli_go_runtime.h"
        header.unlink()
        self.rewrite(output, lambda report: report.update(files=[item for item in report["files"]
                                                                if item["path"] != header.name]))
        with self.assertRaisesRegex(ValueError, "platform contract"):
            self.validate(output)
        (output / "SHA256SUMS").unlink()
        with self.assertRaisesRegex(ValueError, "missing manifest.json or SHA256SUMS"):
            self.validate(output)

    def test_production_requires_current_run_url(self):
        with patch.dict(os.environ, {"SOURCE_CHECKS_RUN_URL": RUN_URL + "9"}):
            with self.assertRaisesRegex(ValueError, "this run's source-check"):
                self.produce("linux")

    def test_consumer_requires_current_run_environment(self):
        output = self.produce("linux")
        with patch.dict(os.environ, {"GITHUB_RUN_ID": ""}):
            with self.assertRaisesRegex(ValueError, "current GitHub run identity"):
                self.validate(output)

    def test_mobile_consumer_copies_only_after_validation(self):
        output = self.produce("android")
        target = self.root / "android/app/src/main/jniLibs/arm64-v8a/libqfli_go_runtime.so"
        args = SimpleNamespace(platform="android", artifact_dir=output)
        (output / "arm64-v8a/libqfli_go_runtime.so").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "digest or size"):
            collector.consume_mobile_artifact(args)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
