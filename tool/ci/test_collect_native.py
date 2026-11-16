"""Reject native artifact formats that would break the intended target."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import collect_native as collector


class ElfValidationTests(unittest.TestCase):
    def setUp(self):
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


if __name__ == "__main__":
    unittest.main()
