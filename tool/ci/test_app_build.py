"""Regression tests for package rejection and non-destructive CI boundaries."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import plistlib
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import app_build as ci

EXPORTS = sorted(ci.SYMBOLS)


def make_elf(machine, *, wide=True, alignment=16384, symbols=(), imported=(), kind=3) -> bytes:
    """Create a minimal shared object: one LOAD segment and a dynamic symbol table."""
    names = b"\0"
    entries = [(0, 0, 0)]
    for group, section in ((symbols, 1), (imported, 0)):
        for symbol in group:
            entries.append((len(names), 0x12, section))
            names += symbol.encode() + b"\0"
    header_size, program_size, section_size = (64, 56, 64) if wide else (52, 32, 40)
    table = b"".join(struct.pack("<IBBHQQ", name, info, 0, section, 0, 0) if wide
                     else struct.pack("<IIIBBH", name, 0, 0, info, 0, section)
                     for name, info, section in entries)
    names_offset = header_size + program_size
    table_offset = names_offset + len(names)
    sections_offset = table_offset + len(table)
    data = bytearray(sections_offset + 3 * section_size)
    data[:6] = b"\x7fELF" + bytes([2 if wide else 1, 1])
    struct.pack_into("<HH", data, 16, kind, machine)
    struct.pack_into("<QQ" if wide else "<II", data, 32 if wide else 28, header_size, sections_offset)
    struct.pack_into("<HHHH", data, 54 if wide else 42, program_size, 1, section_size, 3)
    struct.pack_into("<I", data, header_size, 1)
    struct.pack_into("<Q" if wide else "<I", data, header_size + (48 if wide else 28), alignment)
    data[names_offset:table_offset] = names
    data[table_offset:sections_offset] = table
    for index, (kind_, start, size, link, entry) in enumerate((
            (0, 0, 0, 0, 0),
            (11, table_offset, len(table), 2, len(table) // len(entries)),
            (3, names_offset, len(names), 0, 0))):
        offset = sections_offset + index * section_size
        struct.pack_into("<I", data, offset + 4, kind_)
        struct.pack_into("<QQI" if wide else "<III", data, offset + (24 if wide else 16), start, size, link)
        struct.pack_into("<Q" if wide else "<I", data, offset + (56 if wide else 36), entry)
    return bytes(data)


def make_pe(*, exports=(), imports=(), machine=0x8664) -> bytes:
    """Create a minimal PE32+ image with one section holding both directories."""
    section = bytearray(40)
    struct.pack_into("<I", section, 24, len(exports))
    struct.pack_into("<I", section, 32, 0x1000 + 40)
    pointers, strings = bytearray(), bytearray()
    for name in exports:
        pointers += struct.pack("<I", 0x1000 + 40 + 4 * len(exports) + len(strings))
        strings += name.encode() + b"\0"
    section += pointers + strings
    import_table = len(section)
    descriptors, strings = bytearray(20 * (len(imports) + 1)), bytearray()
    for index, name in enumerate(imports):
        struct.pack_into("<I", descriptors, 20 * index + 12,
                         0x1000 + import_table + len(descriptors) + len(strings))
        strings += name.encode() + b"\0"
    section += descriptors + strings
    data = bytearray(0x400) + section
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 60, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HH", data, 0x84, machine, 1)
    struct.pack_into("<H", data, 0x94, 240)
    optional = 0x98
    struct.pack_into("<H", data, optional, 0x20B)
    struct.pack_into("<I", data, optional + 108, 16)
    struct.pack_into("<II", data, optional + 112, 0x1000 if exports else 0, 40)
    struct.pack_into("<II", data, optional + 120, 0x1000 + import_table if imports else 0, len(descriptors))
    struct.pack_into("<IIII", data, optional + 240 + 8, len(section), 0x1000, len(section), 0x400)
    return bytes(data)


def write_mobile_package(path: Path, prefix: str, abi: str, *, runtime=None) -> bytes:
    wide = abi != "armeabi-v7a"
    if runtime is None:
        runtime = make_elf(ci.MACHINES[abi], wide=wide, symbols=EXPORTS)
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for library in ("libflutter.so", "libapp.so"):
            archive.writestr(f"{prefix}{abi}/{library}", make_elf(ci.MACHINES[abi], wide=wide))
        archive.writestr(f"{prefix}{abi}/{ci.RUNTIME_LIBRARY}", runtime)
        archive.writestr("AndroidManifest.xml" if prefix == "lib/" else "module.json", b"manifest")
    return runtime


def write_windows_bundle(root: Path, *, imports=("KERNEL32.dll",), shipped=()) -> Path:
    bundle = root / ci.BUNDLES["windows"]
    (bundle / "data").mkdir(parents=True)
    for name in ("qfli_go.exe", "flutter_windows.dll", *shipped):
        (bundle / name).write_bytes(make_pe())
    (bundle / "qfli_go_runtime.dll").write_bytes(make_pe(exports=EXPORTS, imports=imports))
    (bundle / "data/app.so").write_bytes(make_elf(62))
    (bundle / "data/icudtl.dat").write_bytes(b"icu")
    return bundle


def write_linux_bundle(root: Path, *, symbols=EXPORTS) -> Path:
    bundle = root / ci.BUNDLES["linux"]
    for name in ("lib", "data"):
        (bundle / name).mkdir(parents=True)
    (bundle / "qfli_go").write_bytes(b"\x7fELF fixture executable")
    for name in ("libflutter_linux_gtk.so", "libapp.so"):
        (bundle / "lib" / name).write_bytes(make_elf(62))
    (bundle / "lib" / ci.RUNTIME_LIBRARY).write_bytes(make_elf(62, symbols=symbols))
    (bundle / "data/icudtl.dat").write_bytes(b"icu")
    return bundle


def write_apple_bundle(root: Path, platform_name: str) -> Path:
    bundle = root / ci.BUNDLES[platform_name]
    macos = platform_name == "macos"
    contents = bundle / "Contents" if macos else bundle
    executable = "QFLIGoShift" if macos else "Runner"
    files = [("MacOS/" if macos else "") + executable, "Frameworks/App.framework/App",
             "Frameworks/FlutterMacOS.framework/FlutterMacOS" if macos
             else "Frameworks/Flutter.framework/Flutter"]
    if macos:
        files.append("Frameworks/libqfli_go_runtime.dylib")
    for name in files:
        path = contents / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture Mach-O")
    (contents / "Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": executable}))
    return bundle


def apple_tools(arch: str, *, symbols=EXPORTS, signed=True):
    """Stand in for lipo, nm, codesign and zip on a runner without Xcode."""
    def tool(command, log, **kwargs):
        if command[0] == "lipo":
            return arch + "\n"
        if command[0] == "nm":
            return "".join(f"0000000000001000 T _{symbol}\n" for symbol in symbols)
        if command[:2] == ["codesign", "--verify"] and not signed:
            raise RuntimeError("App.framework is not signed at all")
        if command[0] == "zip":
            payload = Path(kwargs["cwd"]) / "Payload/Runner.app/Runner"
            Path(command[2]).write_bytes(b"ipa:" + payload.read_bytes())
        return "valid on disk\n"
    return tool


class ApplicationPackageTests(unittest.TestCase):
    def setUp(self):
        # Keep the suite hermetic when a workflow job runs it with job variables set.
        environment = patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        for name in ("GITHUB_ACTIONS", "GITHUB_ENV", "GITHUB_PATH", "GITHUB_STEP_SUMMARY",
                     "QFLI_GO_EXECUTABLE", "QFLI_GO_CC", "CGO_LDFLAGS", "MSYS2_LOCATION",
                     "QFLI_PLATFORM", "QFLI_ARCH", "QFLI_FLUTTER_ROOT"):
            os.environ.pop(name, None)

    def arguments(self, root: Path, platform_name: str, arch: str, **extra) -> argparse.Namespace:
        output = root / "artifact"
        (output / "reports").mkdir(parents=True, exist_ok=True)
        return argparse.Namespace(platform=platform_name, arch=arch, output=output,
                                  flutter_root=root / "sdk", **extra)

    def test_failed_command_annotation_escapes_workflow_data(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "build.log"

            def failed(*args, **kwargs):
                kwargs["stdout"].write("Compiler failed at 50%\n::warning::literal source\n")
                return subprocess.CompletedProcess(args[0], 7)

            with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
                with patch.object(ci.subprocess, "run", side_effect=failed), patch("builtins.print") as printed:
                    with self.assertRaisesRegex(RuntimeError, "Command failed \\(7\\)"):
                        ci.run(["fixture-compiler"], log)
            annotations = [call.args[0] for call in printed.call_args_list
                           if call.args[0].startswith("::error::")]
            self.assertEqual(len(annotations), 1)
            self.assertIn("Compiler failed at 50%25%0A::warning::literal source%0A", annotations[0])
            self.assertNotIn("\n", annotations[0])
            self.assertIn("Compiler failed", log.read_text(encoding="utf-8"))

    def test_failure_annotation_redacts_before_truncation_and_stays_bounded(self):
        output = ("Command: fixture\n\n" + "earlier diagnostics\n" * 500
                  + "password=" + "PRIVATE_VALUE" * 500 + "\n"
                  + "Authorization: Bearer private-bearer\n"
                  + '"storePassword": "private-signing-password"\n'
                  + "https://user:private-userinfo@example.invalid/path?sig=private-signature\n"
                  + "-----BEGIN PRIVATE KEY-----\nprivate-key-body\n-----END PRIVATE KEY-----\n"
                  + "final failure 100%\r\n")
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), patch("builtins.print") as printed:
            ci.annotate_command_failure(Path("compiler.log"), 1, output)
        annotation = printed.call_args.args[0]
        for secret in ("PRIVATE_VALUE", "private-bearer", "private-signing-password",
                       "private-userinfo", "private-signature", "private-key-body"):
            self.assertNotIn(secret, annotation)
        decoded = annotation.removeprefix("::error::").replace("%0D", "\r").replace("%0A", "\n").replace("%25", "%")
        self.assertLessEqual(len(decoded), 4100)
        self.assertTrue(annotation.endswith("final failure 100%25%0D%0A"))

    def test_successful_and_local_commands_do_not_emit_failure_annotations(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "build.log"

            def succeeded(*args, **kwargs):
                kwargs["stdout"].write("Build succeeded\n")
                return subprocess.CompletedProcess(args[0], 0)

            with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
                with patch.object(ci.subprocess, "run", side_effect=succeeded), patch("builtins.print") as printed:
                    self.assertEqual(ci.run(["fixture-compiler"], log), "Build succeeded\n")
            self.assertFalse(any(call.args[0].startswith("::error::") for call in printed.call_args_list))
            with patch("builtins.print") as printed:
                ci.annotate_command_failure(log, 1, "Local failure")
            printed.assert_not_called()

    def test_init_refusal_preserves_an_existing_successful_run(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "artifact"
            (output / "packages").mkdir(parents=True)
            (output / "packages/previous.tar.gz").write_bytes(b"previous successful package")
            (output / "manifest.json").write_bytes(b'{"status":"passed","applicationPackage":true}\n')
            (output / "SHA256SUMS").write_bytes(b"previous checksums\n")
            before = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
            argv = ["app_build.py", "init", "--platform", "android", "--arch", "universal",
                    "--output-dir", str(output)]
            with patch.object(sys, "argv", argv), patch.object(ci, "annotate_command_failure") as annotate:
                with self.assertRaisesRegex(RuntimeError, "Refusing to reuse existing application packages"):
                    ci.main()
            annotate.assert_not_called()
            after = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
            self.assertEqual(after, before)

    def test_init_manifest_states_signing_and_runtime_origin(self):
        expected = {"android": "tracked_prebuilt_library_not_rebuilt_in_this_job",
                    "ohos": "tracked_prebuilt_library_not_rebuilt_in_this_job",
                    "windows": "compiled_from_source_in_this_job",
                    "linux": "compiled_from_source_in_this_job",
                    "macos": "compiled_from_source_in_this_job",
                    "ios": "compiled_from_source_in_this_job"}
        self.assertEqual(set(expected), set(ci.SIGNING))
        for platform_name, origin in expected.items():
            with self.subTest(platform=platform_name), tempfile.TemporaryDirectory() as directory:
                args = argparse.Namespace(platform=platform_name, arch="fixture",
                                          output=Path(directory) / "artifact")
                with patch.object(ci, "git_head", return_value="0" * 40):
                    manifest = ci.initialize(args)
                self.assertEqual(manifest["goRuntime"], origin)
                self.assertEqual(manifest["signing"], ci.SIGNING[platform_name])
                self.assertEqual((manifest["status"], manifest["deviceTests"], manifest["runtimeTests"]),
                                 ("pending", "not_run", "not_run"))
                self.assertFalse(manifest["applicationPackage"])
                self.assertTrue((args.output / "reports").is_dir())

    def test_main_validation_failure_emits_sanitized_annotation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "artifact"
            (output / "reports").mkdir(parents=True)
            manifest_path = output / "manifest.json"
            ci.write_json(manifest_path, {"status": "pending", "packages": []})
            argv = ["app_build.py", "build", "--platform", "windows", "--arch", "x86_64",
                    "--output-dir", str(output)]
            error = ValueError("Missing native runtime 50%\npassword=private-fixture-value")
            with patch.object(sys, "argv", argv), patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
                with patch.object(ci, "build", side_effect=error), patch("builtins.print") as printed:
                    with self.assertRaisesRegex(ValueError, "Missing native runtime"):
                        ci.main()
            annotations = [call.args[0] for call in printed.call_args_list
                           if call.args[0].startswith("::error::")]
            self.assertEqual(len(annotations), 1)
            self.assertIn("build-failure.txt", annotations[0])
            self.assertIn("Missing native runtime 50%25%0A", annotations[0])
            self.assertNotIn("private-fixture-value", annotations[0])
            self.assertNotIn("\n", annotations[0])
            self.assertEqual(json.loads(manifest_path.read_text())["status"], "failed")
            self.assertIn("Missing native runtime", (output / "reports/build-failure.txt").read_text())

    def test_sdk_fetch_preserves_release_tag_for_git_version_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upstream = root / "upstream"
            sdk = root / "sdk"
            upstream.mkdir()
            sdk.mkdir()

            def git(cwd, *args):
                return subprocess.check_output(["git", *args], cwd=cwd, text=True,
                                               stderr=subprocess.STDOUT).strip()

            git(upstream, "init")
            git(upstream, "-c", "user.name=CI Test", "-c", "user.email=ci@example.invalid",
                "commit", "--allow-empty", "-m", "Create release fixture")
            git(upstream, "tag", ci.FLUTTER_TAG)
            expected = git(upstream, "rev-parse", "HEAD")
            git(sdk, "init")
            git(sdk, "remote", "add", "origin", str(upstream))
            with patch.object(ci, "FLUTTER_COMMIT", expected):
                ci.checkout_flutter_release(sdk, root / "reports")
            self.assertEqual(git(sdk, "describe", "--tags", "--exact-match"), ci.FLUTTER_TAG)
            self.assertEqual(git(sdk, "rev-parse", "refs/tags/" + ci.FLUTTER_TAG + "^{commit}"), expected)
            self.assertEqual(ci.git_head(sdk), expected)

    def test_sdk_version_rejects_unknown_despite_correct_revision(self):
        version = {"frameworkRevision": ci.FLUTTER_COMMIT,
                   "frameworkVersion": "0.0.0-unknown", "dartSdkVersion": "3.11.5"}
        with self.assertRaisesRegex(RuntimeError, "differs from the pinned release"):
            ci.validate_flutter_version(version)
        version["frameworkVersion"] = ci.FLUTTER_TAG
        ci.validate_flutter_version(version)

    def test_native_setup_requires_the_pinned_go_release(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.arguments(Path(directory), "linux", "x86_64")
            with patch.object(ci.shutil, "which", side_effect=lambda name: "/usr/bin/" + name):
                with patch.object(ci, "publish_environment") as publish:
                    with patch.object(ci, "run", return_value="go version go1.26.0 linux/amd64\n"):
                        with self.assertRaisesRegex(RuntimeError, "Expected Go 1.27.1"):
                            ci.setup_native(args, {})
                    publish.assert_not_called()
                    manifest = {}
                    with patch.object(ci, "run", return_value="go version go1.27.1 linux/amd64\n"):
                        ci.setup_native(args, manifest)
            publish.assert_called_once_with({"QFLI_GO_EXECUTABLE": "/usr/bin/go",
                                             "QFLI_GO_CC": "/usr/bin/gcc"})
            self.assertEqual(manifest["goToolchain"]["version"], "go version go1.27.1 linux/amd64")
            with self.assertRaisesRegex(ValueError, "needs no Go toolchain"):
                ci.setup_native(self.arguments(Path(directory), "android", "universal"), {})

    def test_windows_native_setup_links_the_mingw_runtime_statically(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.arguments(root, "windows", "x86_64")
            go_version = "go version go1.27.1 windows/amd64\n"
            with patch.object(ci.shutil, "which", return_value="C:/go/bin/go.exe"):
                with patch.object(ci, "run", return_value=go_version), \
                        patch.object(ci, "publish_environment") as publish:
                    with self.assertRaisesRegex(RuntimeError, "MSYS2_LOCATION is required"):
                        ci.setup_native(args, {})
                    compiler = root / "msys64/ucrt64/bin/gcc.exe"
                    compiler.parent.mkdir(parents=True)
                    compiler.write_bytes(b"fixture compiler")
                    with patch.dict(os.environ, {"MSYS2_LOCATION": str(root / "msys64")}):
                        ci.setup_native(args, {})
            values = publish.call_args.args[0]
            self.assertEqual(values["QFLI_GO_CC"], compiler.as_posix())
            self.assertNotIn("\\", values["QFLI_GO_EXECUTABLE"])
            self.assertEqual(values["CGO_LDFLAGS"], "-static")

    def test_elf_exports_are_read_for_both_classes(self):
        for abi, wide in (("arm64-v8a", True), ("x86_64", True), ("armeabi-v7a", False)):
            with self.subTest(abi=abi):
                data = make_elf(ci.MACHINES[abi], wide=wide, alignment=16384 if wide else 4096,
                                symbols=EXPORTS, imported=["malloc"])
                info = ci.inspect_elf(data, abi, android=True)
                self.assertEqual(info["symbols"], EXPORTS)
                self.assertEqual(info["elfClass"], 64 if wide else 32)
                ci.require_exports(info["symbols"], "fixture")

    def test_elf_rejects_wrong_machine_alignment_and_truncation(self):
        with self.assertRaisesRegex(RuntimeError, "Wrong ELF machine 62 for arm64-v8a"):
            ci.inspect_elf(make_elf(62), "arm64-v8a")
        with self.assertRaisesRegex(RuntimeError, "Unexpected ELF class"):
            ci.inspect_elf(make_elf(183, wide=False), "arm64-v8a")
        with self.assertRaisesRegex(RuntimeError, "loadable shared library"):
            ci.inspect_elf(make_elf(183, kind=2), "arm64-v8a")
        small = make_elf(183, alignment=4096)
        with self.assertRaisesRegex(RuntimeError, "below 16 KiB"):
            ci.inspect_elf(small, "arm64-v8a", android=True)
        self.assertEqual(ci.inspect_elf(small, "arm64-v8a")["machine"], 183)
        with self.assertRaisesRegex(RuntimeError, "Truncated or malformed ELF"):
            ci.elf_info(make_elf(183, symbols=EXPORTS)[:-10])
        with self.assertRaisesRegex(RuntimeError, "Expected little-endian ELF"):
            ci.elf_info(make_pe())

    def test_tracked_runtime_libraries_satisfy_the_package_checks(self):
        libraries = [(ci.ROOT / ci.TRACKED_RUNTIMES["android"] / abi / ci.RUNTIME_LIBRARY, abi, True)
                     for abi in ci.ANDROID_ABIS]
        libraries.append((ci.ROOT / ci.TRACKED_RUNTIMES["ohos"] / "arm64-v8a" / ci.RUNTIME_LIBRARY,
                          "arm64-v8a", False))
        for path, abi, android in libraries:
            with self.subTest(path=path.relative_to(ci.ROOT).as_posix()):
                info = ci.inspect_elf(path.read_bytes(), abi, android=android)
                ci.require_exports(info["symbols"], path.name)

    def test_runtime_export_check_names_the_missing_symbols(self):
        with self.assertRaisesRegex(RuntimeError, "Missing Go runtime exports in fixture: QfliGoDebugClose"):
            ci.require_exports([name for name in EXPORTS if name != "QfliGoDebugClose"], "fixture")

    def test_pe_exports_and_imports_are_read(self):
        info = ci.pe_info(make_pe(exports=EXPORTS, imports=["KERNEL32.dll", "libwinpthread-1.dll"]), "fixture.dll")
        self.assertEqual(info["exports"], EXPORTS)
        self.assertEqual(info["imports"], ["KERNEL32.dll", "libwinpthread-1.dll"])
        self.assertEqual(ci.pe_info(make_pe(), "empty.dll"), {"exports": [], "imports": []})
        with self.assertRaisesRegex(RuntimeError, "Not an x64 PE image: x86.dll"):
            ci.pe_info(make_pe(machine=0x14C), "x86.dll")
        with self.assertRaisesRegex(RuntimeError, "Truncated or malformed PE image"):
            ci.pe_info(make_pe(exports=EXPORTS)[:0x420], "short.dll")
        with self.assertRaisesRegex(RuntimeError, "PE image"):
            ci.pe_info(make_elf(62), "app.so")

    @unittest.skipUnless(os.name == "nt" and platform.machine().lower() in ("amd64", "x86_64"),
                         "needs an x64 Windows interpreter")
    def test_pe_parser_reads_a_real_windows_image(self):
        executable = Path(sys.executable)
        imports = ci.pe_info(executable.read_bytes(), executable.name)["imports"]
        self.assertIn("kernel32.dll", [name.lower() for name in imports])
        library = Path(sys.base_prefix) / f"python{sys.version_info.major}{sys.version_info.minor}.dll"
        if library.is_file():
            self.assertIn("Py_Initialize", ci.pe_info(library.read_bytes(), library.name)["exports"])

    def test_declared_assets_follow_the_pubspec_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pubspec.yaml").write_text(
                "name: fixture\n"
                "dependencies:\n"
                "  assets:\n"
                "    - not/an/asset.txt\n"
                "flutter:\n"
                "  uses-material-design: true\n"
                "  assets:\n"
                "    # A comment between entries.\n"
                "    - assets/icon.png\n"
                "    - 'assets/lessons/'\n"
                "  fonts:\n"
                "    - family: Fixture\n", encoding="utf-8")
            (root / "assets/lessons/nested").mkdir(parents=True)
            for name in ("icon.png", "lessons/a.json", "lessons/.hidden", "lessons/nested/b.json"):
                (root / "assets" / name).write_bytes(b"fixture")
            with patch.object(ci, "ROOT", root):
                self.assertEqual(ci.declared_assets(), ["assets/icon.png", "assets/lessons/"])
                self.assertEqual(sorted(ci.expected_assets()), ["assets/icon.png", "assets/lessons/a.json"])
        declared = ci.declared_assets()
        self.assertIn("assets/curriculum/", declared)
        assets = ci.expected_assets()
        self.assertGreater(len(assets), len(declared))
        self.assertTrue(all(path.is_file() for path in assets.values()))

    def test_packaged_assets_must_match_current_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "lesson.json"
            source.write_text("current", encoding="utf-8")
            with patch.object(ci, "expected_assets", return_value={"assets/lesson.json": source}):
                name = "data/flutter_assets/assets/lesson.json"
                with self.assertRaisesRegex(RuntimeError, "differs from source"):
                    ci.inspect_assets([name], lambda _: b"old")
                with self.assertRaisesRegex(RuntimeError, "Expected one packaged asset"):
                    ci.inspect_assets([], lambda _: b"current")
                receipt = ci.inspect_assets([name], lambda _: b"current")
            self.assertEqual(receipt, [{"path": name, "sha256": ci.digest(source), "sourceMatches": True}])

    def test_core_binding_requires_the_pinned_sibling_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "qfli_go"
            core = Path(directory) / "qfli_studio_core"
            (root / ".dart_tool").mkdir(parents=True)
            (core / "vendor/re_editor").mkdir(parents=True)
            config = root / ".dart_tool/package_config.json"

            def configure(core_uri, editor_uri):
                ci.write_json(config, {"packages": [{"name": "qfli_studio_core", "rootUri": core_uri},
                                                    {"name": "re_editor", "rootUri": editor_uri}]})

            with patch.object(ci, "ROOT", root):
                configure("../../qfli_studio_core", "../../qfli_studio_core/vendor/re_editor")
                self.assertTrue(all(entry["resolvesToPinnedCheckout"]
                                    for entry in ci.core_source_binding(core).values()))
                configure(core.resolve().as_uri(), (core / "vendor/re_editor").resolve().as_uri())
                self.assertEqual(set(ci.core_source_binding(core)), {"qfli_studio_core", "re_editor"})
                configure("../../qfli_studio_core", "file:///pub-cache/hosted/pub.dev/re_editor-0.8.0")
                with self.assertRaisesRegex(RuntimeError, "re_editor does not resolve to the pinned core"):
                    ci.core_source_binding(core)
                ci.write_json(config, {"packages": []})
                with self.assertRaisesRegex(RuntimeError, "does not contain qfli_studio_core"):
                    ci.core_source_binding(core)

    def test_mobile_package_rejects_missing_runtime_before_staging(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "app-arm64-v8a-release.apk"
            with zipfile.ZipFile(package, "w") as archive:
                for library in ("libflutter.so", "libapp.so"):
                    archive.writestr("lib/arm64-v8a/" + library, b"not-yet-inspected")
            with self.assertRaisesRegex(RuntimeError, "Missing arm64-v8a/libqfli_go_runtime.so"):
                ci.inspect_mobile(package, argparse.Namespace(platform="android"), ["arm64-v8a"])

    def test_mobile_package_rejects_unrequested_abi(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "app.apk"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("lib/x86_64/libflutter.so", b"not-yet-inspected")
            with self.assertRaisesRegex(RuntimeError, "Unexpected package ABIs"):
                ci.inspect_mobile(package, argparse.Namespace(platform="android"), ["arm64-v8a"])

    def test_mobile_package_rejects_runtime_without_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "entry-default-unsigned.hap"
            write_mobile_package(package, "libs/", "arm64-v8a",
                                 runtime=make_elf(183, symbols=EXPORTS[:-1], imported=EXPORTS[-1:]))
            with patch.object(ci, "inspect_assets", return_value=[]):
                with self.assertRaisesRegex(RuntimeError, "Missing Go runtime exports"):
                    ci.inspect_mobile(package, argparse.Namespace(platform="ohos"), ["arm64-v8a"])

    def test_mobile_report_compares_packaged_and_tracked_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "app-arm64-v8a-release.apk"
            runtime = write_mobile_package(package, "lib/", "arm64-v8a")
            tracked = root / ci.TRACKED_RUNTIMES["android"] / "arm64-v8a" / ci.RUNTIME_LIBRARY
            tracked.parent.mkdir(parents=True)
            for content, identical in ((runtime, True), (runtime + b"debug sections", False)):
                tracked.write_bytes(content)
                with patch.object(ci, "ROOT", root), patch.object(ci, "inspect_assets", return_value=[]):
                    report = ci.inspect_mobile(package, argparse.Namespace(platform="android"), ["arm64-v8a"])
                receipt = next(item for item in report["libraries"]
                               if item["path"].endswith(ci.RUNTIME_LIBRARY))
                self.assertEqual(receipt["byteIdenticalToTracked"], identical)
                self.assertEqual(receipt["trackedSha256"], ci.digest(tracked))
                self.assertEqual(receipt["verification"], "elf_and_go_runtime_exports_checked")

    def test_android_job_stages_one_verified_package_per_abi(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for abi in ci.ANDROID_ABIS:
                write_mobile_package(root / f"build/app/outputs/flutter-apk/app-{abi}-release.apk", "lib/", abi)
            args = self.arguments(root, "android", "universal")
            manifest = {}
            with patch.object(ci, "ROOT", root), patch.object(ci, "inspect_assets", return_value=[]):
                with patch.object(ci, "android_build_tool", side_effect=lambda name: Path(name)):
                    with patch.object(ci, "run", return_value="") as run:
                        ci.collect(args, manifest)
            self.assertEqual(sorted(path.name for path in (args.output / "packages").iterdir()),
                             [f"qfligoshift-android-{abi}.apk" for abi in ci.ANDROID_ABIS])
            self.assertEqual([package["path"] for package in manifest["packages"]],
                             [f"packages/qfligoshift-android-{abi}.apk" for abi in ci.ANDROID_ABIS])
            commands = [call.args[0] for call in run.call_args_list]
            self.assertEqual(sum(command[:4] == [Path("zipalign"), "-c", "-P", "16"] for command in commands), 3)
            self.assertEqual(sum(command[:2] == [Path("apksigner"), "verify"] for command in commands), 3)
            self.assertTrue(manifest["applicationPackage"])

    def test_android_build_tool_selects_the_newest_numeric_version(self):
        with tempfile.TemporaryDirectory() as directory:
            for version in ("9.0.0", "35.0.0", "34.0.0"):
                tool = Path(directory) / "build-tools" / version / "zipalign"
                tool.parent.mkdir(parents=True)
                tool.write_bytes(b"fixture")
            with patch.dict(os.environ, {"ANDROID_HOME": directory}):
                self.assertEqual(ci.android_build_tool("zipalign").parent.name, "35.0.0")
                with self.assertRaisesRegex(RuntimeError, "apksigner is unavailable"):
                    ci.android_build_tool("apksigner")

    def test_ohos_job_stages_an_unsigned_hap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.arguments(root, "ohos", "arm64-v8a")
            with patch.object(ci, "ROOT", root), patch.object(ci, "inspect_assets", return_value=[]):
                with self.assertRaisesRegex(RuntimeError, "did not produce an unsigned HAP"):
                    ci.collect(args, {})
                write_mobile_package(root / "build/ohos/hap/entry-default-unsigned.hap", "libs/", "arm64-v8a")
                manifest = {}
                ci.collect(args, manifest)
            self.assertEqual([package["path"] for package in manifest["packages"]],
                             ["packages/qfligoshift-ohos-arm64-v8a-unsigned.hap"])

    def test_windows_bundle_rejects_unshipped_toolchain_dll(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_windows_bundle(root, imports=("KERNEL32.dll", "libwinpthread-1.dll"))
            args = self.arguments(root, "windows", "x86_64")
            manifest = {"packages": [], "applicationPackage": False}
            with patch.object(ci, "ROOT", root), patch.object(ci, "inspect_assets", return_value=[]):
                with self.assertRaisesRegex(RuntimeError, "does not ship: libwinpthread-1.dll"):
                    ci.collect(args, manifest)
            self.assertFalse((args.output / "packages").exists())
            self.assertFalse(manifest["applicationPackage"])

    def test_windows_job_stages_a_portable_zip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_windows_bundle(root, imports=("KERNEL32.dll", "libwinpthread-1.dll"),
                                 shipped=("LIBWINPTHREAD-1.DLL",))
            args = self.arguments(root, "windows", "x86_64")
            manifest = {}
            with patch.object(ci, "ROOT", root), patch.object(ci, "inspect_assets", return_value=[]):
                ci.collect(args, manifest)
            package = args.output / "packages/qfligoshift-windows-x86_64.zip"
            with zipfile.ZipFile(package) as archive:
                names = archive.namelist()
            self.assertIn("qfligoshift-windows-x86_64/qfli_go.exe", names)
            self.assertIn("qfligoshift-windows-x86_64/data/app.so", names)
            self.assertTrue(all(name.startswith("qfligoshift-windows-x86_64/") for name in names))
            self.assertEqual(manifest["packages"][0]["sha256"], ci.digest(package))
            report = json.loads((args.output / "reports/package-inspection.json").read_text())[0]
            self.assertEqual(report["libraries"][0]["verification"], "pe_exports_and_imports_checked")

    def test_linux_job_stages_a_portable_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_linux_bundle(root)
            args = self.arguments(root, "linux", "x86_64")
            manifest = {}
            with patch.object(ci, "ROOT", root), patch.object(ci, "inspect_assets", return_value=[]):
                ci.collect(args, manifest)
                with self.assertRaisesRegex(RuntimeError, "existing packages directory"):
                    ci.collect(args, manifest)
            with tarfile.open(args.output / "packages/qfligoshift-linux-x86_64.tar.gz") as archive:
                names = archive.getnames()
            self.assertIn("qfligoshift-linux-x86_64/qfli_go", names)
            self.assertIn("qfligoshift-linux-x86_64/lib/" + ci.RUNTIME_LIBRARY, names)
            self.assertEqual(manifest["verification"], "release_compiled_and_package_inspected")

    def test_linux_bundle_rejects_runtime_without_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_linux_bundle(root, symbols=EXPORTS[:3])
            args = self.arguments(root, "linux", "x86_64")
            with patch.object(ci, "ROOT", root), patch.object(ci, "inspect_assets", return_value=[]):
                with self.assertRaisesRegex(RuntimeError, "Missing Go runtime exports"):
                    ci.collect(args, {})
                (root / ci.BUNDLES["linux"] / "lib" / ci.RUNTIME_LIBRARY).unlink()
                with self.assertRaisesRegex(RuntimeError, "Missing or empty application file"):
                    ci.collect(args, {})
            self.assertFalse((args.output / "packages").exists())

    def test_ohos_profile_refuses_local_developer_execution(self):
        with self.assertRaisesRegex(RuntimeError, "requires a GitHub Actions checkout"):
            ci.unsigned_ohos_profile()

    def test_ohos_metadata_requires_structured_api26(self):
        for version in (26, "26"):
            ci.validate_ohos_sdk_metadata({"data": {"apiVersion": version}})
        for metadata in ({"data": {"apiVersion": 24}, "description": "API26"},
                         {"apiVersion": 26}, {"data": []}, {}, None):
            with self.subTest(metadata=metadata):
                with self.assertRaisesRegex(RuntimeError, "expected API26"):
                    ci.validate_ohos_sdk_metadata(metadata)

    def test_ohos_unsigned_profile_preserves_targets_and_unrelated_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "ohos/build-profile.json5"
            path.parent.mkdir()
            profile = {
                "app": {
                    "signingConfigs": [{"name": "fixture", "material": "synthetic-only"}],
                    "products": [
                        {"name": "default", "signingConfig": "fixture",
                         "targetSdkVersion": "6.1.1(24)", "compatibleSdkVersion": "5.1.0(18)",
                         "runtimeOS": "HarmonyOS", "buildOption": {"strictMode": True}},
                        {"name": "alternate", "compileSdkVersion": "6.1.1(24)",
                         "targetSdkVersion": "6.1.1(24)", "compatibleSdkVersion": "5.1.0(18)"},
                    ],
                    "buildModeSet": [{"name": "release"}],
                },
                "modules": [{"name": "entry", "srcPath": "./entry"}],
            }
            ci.write_json(path, profile)
            expected = json.loads(json.dumps(profile))
            expected["app"]["signingConfigs"] = []
            for product in expected["app"]["products"]:
                product.pop("signingConfig", None)
                product.pop("compileSdkVersion", None)
            # Fixtures use JSON, a JSON5 subset. Keep non-OHOS test runners free
            # of the parser installed only in the real OHOS build job.
            with patch.dict(sys.modules, {"json5": json}), patch.object(ci, "ROOT", root):
                with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
                    with patch.object(ci.subprocess, "check_output", return_value="") as status:
                        ci.unsigned_ohos_profile()
            status.assert_called_once_with(
                ["git", "status", "--porcelain", "--", "ohos/build-profile.json5"],
                cwd=root, text=True)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), expected)

    def test_ohos_profile_rejection_preserves_existing_bytes(self):
        for modified in (True, False):
            with self.subTest(modified=modified), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / "ohos/build-profile.json5"
                path.parent.mkdir()
                before = (b'{"app":{"signingConfigs":[{"name":"synthetic"}],"products":['
                          b'{"targetSdkVersion":"5.1.0(18)","compatibleSdkVersion":"5.1.0(18)"}]}}\r\n')
                path.write_bytes(before)
                status = " M ohos/build-profile.json5\n" if modified else ""
                error = "modified OHOS build profile" if modified else "Unexpected OHOS SDK targets"
                with patch.dict(sys.modules, {"json5": json}), patch.object(ci, "ROOT", root):
                    with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
                        with patch.object(ci.subprocess, "check_output", return_value=status):
                            with self.assertRaisesRegex(RuntimeError, error):
                                ci.unsigned_ohos_profile()
                self.assertEqual(path.read_bytes(), before)

    def run_build(self, root: Path, platform_name: str, arch: str):
        args = self.arguments(root, platform_name, arch)
        manifest = {}
        with patch.object(ci, "ROOT", root), patch.object(ci, "collect") as collect:
            with patch.object(ci, "git_head", side_effect=[ci.CORE_COMMIT, ci.FLUTTER_COMMIT]):
                with patch.object(ci, "core_source_binding", return_value={}):
                    with patch.object(ci, "run", return_value="") as run:
                        try:
                            ci.build(args, manifest)
                        finally:
                            self.build_commands = [call.args[0] for call in run.call_args_list]
        collect.assert_called_once_with(args, manifest)
        self.assertEqual(manifest["status"], "passed")
        build_call = next(call for call in run.call_args_list if "build" in call.args[0])
        return build_call.args[0], build_call.kwargs["env"]

    def test_native_builds_refuse_to_start_without_the_go_toolchain(self):
        for platform_name in ci.NATIVE_BUILD_PLATFORMS:
            with self.subTest(platform=platform_name), tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(RuntimeError, "run setup-native before build"):
                    self.run_build(Path(directory), platform_name, "x86_64")
                self.assertEqual(self.build_commands, [])
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"QFLI_GO_EXECUTABLE": "C:/go/bin/go.exe"}):
                with self.assertRaisesRegex(RuntimeError, "Windows cgo compiler is not provisioned"):
                    self.run_build(Path(directory), "windows", "x86_64")

    def test_macos_build_requires_ad_hoc_signing_and_the_provisioned_go(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"QFLI_GO_EXECUTABLE": "/opt/go/bin/go"}):
                command, env = self.run_build(Path(directory), "macos", "x86_64")
            self.assertEqual(command[1:], ["build", "macos", "--release", "--target", "lib/main.dart", "--no-pub"])
            self.assertEqual(env["FLUTTER_XCODE_CODE_SIGNING_REQUIRED"], "YES")
            self.assertEqual(env["FLUTTER_XCODE_CODE_SIGN_IDENTITY"], "-")
            self.assertEqual(env["FLUTTER_XCODE_CODE_SIGN_STYLE"], "Manual")
            self.assertEqual(env["FLUTTER_XCODE_ARCHS"], "x86_64")
            self.assertEqual(env["FLUTTER_XCODE_MACOSX_DEPLOYMENT_TARGET"], "13.0")
            self.assertEqual(env["FLUTTER_XCODE_QFLI_GO_EXECUTABLE"], "/opt/go/bin/go")

    def test_platform_build_commands_match_the_package_contract(self):
        compiler = "C:/msys64/ucrt64/bin/gcc.exe"
        with patch.dict(os.environ, {"QFLI_GO_EXECUTABLE": "/opt/go/bin/go", "QFLI_GO_CC": compiler}):
            with tempfile.TemporaryDirectory() as directory:
                command, env = self.run_build(Path(directory), "windows", "x86_64")
                self.assertEqual(command[2], "windows")
                self.assertTrue(env["PATH"].startswith(str(Path(compiler).parent) + os.pathsep))
                self.assertNotIn("FLUTTER_XCODE_QFLI_GO_EXECUTABLE", env)
            with tempfile.TemporaryDirectory() as directory:
                command, env = self.run_build(Path(directory), "ios", "arm64")
                self.assertEqual(command[2:], ["ios", "--release", "--target", "lib/main.dart",
                                               "--no-pub", "--no-codesign"])
                self.assertEqual(env["FLUTTER_XCODE_QFLI_GO_EXECUTABLE"], "/opt/go/bin/go")
                self.assertNotIn("FLUTTER_XCODE_CODE_SIGN_IDENTITY", env)
        with tempfile.TemporaryDirectory() as directory:
            command, _ = self.run_build(Path(directory), "android", "universal")
            self.assertEqual(command[2:], ["apk", "--release", "--target", "lib/main.dart",
                                           "--no-pub", "--split-per-abi"])

    def test_macos_package_requires_deep_signature_verification(self):
        for signed in (False, True):
            with self.subTest(signed=signed), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                bundle = write_apple_bundle(root, "macos")
                args = self.arguments(root, "macos", "x86_64")
                manifest = {"packages": [], "applicationPackage": False}
                with patch.object(ci, "ROOT", root), patch.object(ci, "inspect_assets", return_value=[]):
                    with patch.object(ci, "run", side_effect=apple_tools("x86_64", signed=signed)) as run:
                        if signed:
                            ci.collect(args, manifest)
                        else:
                            with self.assertRaisesRegex(RuntimeError, "not signed at all"):
                                ci.collect(args, manifest)
                verify = next(call for call in run.call_args_list
                              if call.args[0][:2] == ["codesign", "--verify"])
                self.assertEqual(verify.args[0], ["codesign", "--verify", "--deep", "--strict",
                                                "--verbose=2", bundle])
                self.assertEqual(verify.args[1], args.output / "reports/codesign-verification.log")
                self.assertEqual((args.output / "packages").exists(), signed)
                self.assertEqual(manifest["applicationPackage"], signed)
                if signed:
                    report = json.loads((args.output / "reports/package-inspection.json").read_text())[0]
                    self.assertEqual(report["signingVerification"],
                                     "deep_strict_verification_passed_not_notarized")
                    with tarfile.open(args.output / "packages/qfligoshift-macos-x86_64.tar.gz") as archive:
                        self.assertIn("QFLIGoShift.app/Contents/Frameworks/libqfli_go_runtime.dylib",
                                      archive.getnames())

    def test_apple_bundle_rejects_foreign_architecture_and_missing_exports(self):
        for arch, symbols, error in (("arm64", EXPORTS, "framework does not support x86_64"),
                                     ("x86_64 arm64", EXPORTS, "Unexpected Runner architectures"),
                                     ("x86_64", EXPORTS[1:], "Missing Go runtime exports")):
            with self.subTest(error=error, arch=arch), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                write_apple_bundle(root, "macos")
                args = self.arguments(root, "macos", "x86_64")
                with patch.object(ci, "ROOT", root), patch.object(ci, "inspect_assets", return_value=[]):
                    with patch.object(ci, "run", side_effect=apple_tools(arch, symbols=symbols)):
                        with self.assertRaisesRegex(RuntimeError, error):
                            ci.collect(args, {})
                self.assertFalse((args.output / "packages").exists())

    def test_ios_job_checks_the_runner_executable_and_stages_an_unsigned_ipa(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = write_apple_bundle(root, "ios")
            args = self.arguments(root, "ios", "arm64")
            manifest = {}
            with patch.object(ci, "ROOT", root), patch.object(ci, "inspect_assets", return_value=[]):
                with patch.object(ci, "run", side_effect=apple_tools("arm64")) as run:
                    ci.collect(args, manifest)
            commands = [call.args[0] for call in run.call_args_list]
            self.assertIn(["nm", "-arch", "arm64", "-gU", bundle / "Runner"], commands)
            self.assertFalse(any(command[0] == "codesign" for command in commands))
            package = args.output / "packages/qfligoshift-ios-arm64-unsigned.ipa"
            self.assertEqual(package.read_bytes(), b"ipa:fixture Mach-O")
            report = json.loads((args.output / "reports/package-inspection.json").read_text())[0]
            self.assertEqual(report["signingVerification"], "unsigned_device_signing_required")
            self.assertEqual([path.name for path in root.iterdir() if path.name.startswith("app-package-")], [])

    def test_failed_job_retains_reports_without_success_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "artifact"
            (output / "packages").mkdir(parents=True)
            (output / "packages/app.apk").write_bytes(b"partial")
            (output / "reports").mkdir()
            report = output / "reports/build.log"
            report.write_text("actual failure", encoding="utf-8")
            summary = Path(directory) / "summary.md"
            manifest = {"status": "passed", "applicationPackage": True,
                        "packages": [{"path": "packages/app.apk"}], "verification": "passed"}
            args = argparse.Namespace(output=output, job_status="failure", platform="android", arch="universal")
            with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}):
                ci.finalize(args, manifest)
            self.assertFalse((output / "packages").exists())
            self.assertEqual(report.read_text(), "actual failure")
            self.assertEqual(manifest["packages"], [])
            self.assertFalse(manifest["applicationPackage"])
            self.assertEqual(manifest["status"], "failed")
            self.assertTrue((output / "licenses/Go-LICENSE.txt").is_file())
            self.assertIn("No package was published", summary.read_text(encoding="utf-8"))

    def test_successful_job_summary_lists_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "artifact"
            (output / "packages").mkdir(parents=True)
            (output / "packages/app.zip").write_bytes(b"package")
            summary = Path(directory) / "summary.md"
            manifest = {"status": "passed", "applicationPackage": True, "signing": "unsigned_executable",
                        "goRuntime": "compiled_from_source_in_this_job",
                        "packages": [{"path": "packages/app.zip", "bytes": 7, "sha256": "ab" * 32}]}
            args = argparse.Namespace(output=output, job_status="success", platform="windows", arch="x86_64")
            with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}):
                ci.finalize(args, manifest)
            ci.write_checksums(output)
            self.assertTrue((output / "packages/app.zip").is_file())
            text = summary.read_text(encoding="utf-8")
            self.assertIn("| `packages/app.zip` | 7 | `" + "ab" * 32 + "` |", text)
            self.assertIn("unsigned_executable", text)
            checksums = (output / "SHA256SUMS").read_text(encoding="utf-8")
            self.assertIn(ci.digest(output / "packages/app.zip") + "  packages/app.zip\n", checksums)
            self.assertNotIn("SHA256SUMS\n", checksums)

    def assert_late_finalization_failure(self, fault):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "LICENSE").write_text("License fixture", encoding="utf-8")
            output = root / "artifact"
            (output / "packages").mkdir(parents=True)
            (output / "packages/app.apk").write_bytes(b"candidate package")
            (output / "reports").mkdir()
            (output / "reports/build.log").write_text("Build succeeded", encoding="utf-8")
            (output / "SHA256SUMS").write_text("stale checksums", encoding="utf-8")
            manifest_path = output / "manifest.json"
            ci.write_json(manifest_path, {"status": "passed", "applicationPackage": True,
                                         "packages": [{"path": "packages/app.apk"}],
                                         "verification": "release_compiled_and_package_inspected"})
            argv = ["app_build.py", "finalize", "--platform", "android", "--arch", "universal",
                    "--output-dir", str(output)]
            target = ci.shutil if fault == "copy2" else ci
            with patch.object(ci, "ROOT", root), patch.object(sys, "argv", argv):
                with patch.object(target, fault, side_effect=OSError("injected " + fault + " failure")):
                    with self.assertRaisesRegex(OSError, "injected " + fault + " failure"):
                        ci.main()
            actual = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(actual["status"], "failed")
            self.assertFalse(actual["applicationPackage"])
            self.assertEqual(actual["verification"], "failed_see_reports")
            self.assertEqual(actual["packages"], [])
            self.assertFalse((output / "packages").exists())
            self.assertFalse((output / "SHA256SUMS").exists())
            self.assertIn("injected " + fault + " failure", (output / "reports/finalize-failure.txt").read_text())
            self.assertEqual((output / "reports/build.log").read_text(), "Build succeeded")

    def test_license_copy_failure_revokes_package_success(self):
        self.assert_late_finalization_failure("copy2")

    def test_checksum_failure_revokes_package_success(self):
        self.assert_late_finalization_failure("digest")


if __name__ == "__main__":
    unittest.main()
