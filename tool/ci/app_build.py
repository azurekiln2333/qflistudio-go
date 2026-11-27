#!/usr/bin/env python3
"""Build complete Flutter application packages and keep source-bound CI evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tool"))
from inspect_go_catalog_hap import SYMBOLS

APP_NAME = "qfligoshift"
CORE_COMMIT = "476a30acee21dc486ee2849dd8064a7be665e4d5"
CORE_DIRECTORY = "qflistudio-core"
FLUTTER_REPOSITORY = "https://gitcode.com/CPF-Flutter/flutter_flutter.git"
FLUTTER_TAG = "3.41.9+ohos-1.0.2"
FLUTTER_COMMIT = "62357a93d653bf844f730bb1f4b7cc9e2139d14e"
TOOLING_COMMIT = "9d2eaf45940e5042637b3387b18292ed39223a4a"
ENGINE_COMMIT = "42d3d75a56efe1a2e9902f52dc8006099c45d937"
OHOS_ENGINE_COMMIT = "4cbeea6a36f7aea39a60f2c5d57b1ffd84bfd106"
OHOS_SDK_RELEASE = "26.0.0.821"
OHOS_SDK_SHA256 = "0cbdf7ac5c1be1e42694d448ffaee0c0be0ba9a948197e2bc5b61ca5bdc481f2"
OHOS_PARTS = {
    "aa": "4321eb328558169e9531594139910a42b1c88057fb09f852be85ff2487e6adbc",
    "ab": "26e9ae251e761fbc9ec4e7ad780b5b291130e7824af2324167530941e11ad592",
}
GO_VERSION = "1.27.1"
# Go 1.27 no longer targets the 10.15 deployment target stored in the Xcode project.
MACOS_DEPLOYMENT_TARGET = "13.0"
MACHINES = {"x86_64": 62, "arm64": 183, "arm64-v8a": 183, "armeabi-v7a": 40}
ANDROID_ABIS = ("arm64-v8a", "armeabi-v7a", "x86_64")
RUNTIME_LIBRARY = "libqfli_go_runtime.so"
# These jobs compile the Go runtime while Flutter builds the application.
NATIVE_BUILD_PLATFORMS = ("macos", "ios")
MOBILE_RUNTIME_DIRS = {"android": "android/app/src/main/jniLibs", "ohos": "ohos/entry/libs"}
BUNDLES = {
    "windows": "build/windows/x64/runner/Release",
    "linux": "build/linux/x64/release/bundle",
    "macos": "build/macos/Build/Products/Release/QFLIGoShift.app",
    "ios": "build/ios/iphoneos/Runner.app",
}
SIGNING = {
    "android": "debug_key_for_testing_not_store_release",
    "ios": "unsigned_requires_signing_before_device_installation",
    "ohos": "unsigned_requires_signing_before_device_installation",
    "macos": "ad_hoc_not_notarized",
    "linux": "not_applicable",
    "windows": "unsigned_executable",
}


def digest(path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def annotate_command_failure(log: Path, returncode: int, output: str) -> None:
    """Keep a bounded compiler diagnostic available through the checks API."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    # Exclude the command heading. Redact before truncation so a long credential
    # cannot lose its identifying prefix and survive at the start of the tail.
    tail = output.split("\n\n", 1)[-1] if output.startswith("Command: ") else output
    tail = re.sub(r"(?s)-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----",
                  "[private key redacted]", tail)
    tail = re.sub(
        r"(?im)^.*(?:authorization\s*:|\b(?:[a-z_]*password|[a-z_]*token|"
        r"[a-z_]*secret|keypass|storepass|private[_-]?key)[\"']?\s*[:=]).*$",
        "[sensitive diagnostic line redacted]", tail)

    def redact_url(match):
        value = match.group(0)
        value = re.sub(r"(https?://)[^/@]+@", r"\1[redacted]@", value, flags=re.IGNORECASE)
        return value.split("?", 1)[0] + ("?[redacted]" if "?" in value else "")

    tail = re.sub(r"https?://[^\s<>\"']+", redact_url, tail, flags=re.IGNORECASE)
    tail = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", tail)
    message = f"Command failed ({returncode}); see {log.name}\n" + tail[-4000:]
    # Escape data, in this order, to prevent output from becoming workflow commands.
    message = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print("::error::" + message, flush=True)


def run(command, log: Path, *, cwd=ROOT, env=None, timeout=3600) -> str:
    """Keep the complete output and propagate a real command failure."""
    command = [str(part) for part in command]
    print("+ " + " ".join(command), flush=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as stream:
        stream.write("Command: " + repr(command) + "\n\n")
        stream.flush()
        try:
            result = subprocess.run(command, cwd=cwd, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=timeout, check=False)
        finally:
            stream.flush()
            output = log.read_text(encoding="utf-8", errors="replace")
            print(output[-12000:], flush=True)
    if result.returncode:
        annotate_command_failure(log, result.returncode, output)
        raise RuntimeError(f"Command failed ({result.returncode}); see {log.name}")
    # Exclude our command heading, for commands that print machine-readable JSON.
    return output.split("\n\n", 1)[1]


def run_with_retries(command, log: Path, *, attempts=3, delay=5, **options) -> str:
    """Repeat a network-bound command. Every attempt keeps its own complete log."""
    for attempt in range(1, attempts + 1):
        try:
            return run(command, log.with_name(f"{log.stem}-{attempt}{log.suffix}"), **options)
        except (RuntimeError, subprocess.TimeoutExpired):
            if attempt == attempts:
                raise
            time.sleep(delay)


def git_head(directory) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=directory,
                                   text=True).strip()


def flutter(args) -> Path:
    return args.flutter_root / "bin" / ("flutter.bat" if os.name == "nt" else "flutter")


def environment() -> dict:
    result = os.environ.copy()
    result.update({
        "FLUTTER_STORAGE_BASE_URL": "https://storage.googleapis.com",
        "FLUTTER_OHOS_STORAGE_BASE_URL": "https://flutter-ohos.obs.cn-south-1.myhuaweicloud.com",
        "PUB_HOSTED_URL": "https://pub.dev",
        "FLUTTER_SUPPRESS_ANALYTICS": "true",
        "CI": "true",
    })
    return result


def publish_environment(values: dict, paths=()) -> None:
    for key, value in values.items():
        os.environ[key] = str(value)
    if paths:
        os.environ["PATH"] = os.pathsep.join(map(str, paths)) + os.pathsep + os.environ["PATH"]
    if os.environ.get("GITHUB_ENV"):
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as stream:
            for key, value in values.items():
                stream.write(f"{key}={value}\n")
    if os.environ.get("GITHUB_PATH"):
        with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as stream:
            for path in paths:
                stream.write(str(path) + "\n")


def initialize(args) -> dict:
    packages = args.output / "packages"
    if packages.exists() and any(packages.iterdir()):
        raise RuntimeError("Refusing to reuse existing application packages; choose a fresh output directory")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "reports").mkdir(exist_ok=True)
    return {
        "platform": args.platform, "architecture": args.arch,
        "sourceCommit": git_head(ROOT), "coreCommit": CORE_COMMIT,
        "entrypoint": "lib/main.dart", "buildMode": "release",
        "githubRunId": os.environ.get("GITHUB_RUN_ID"),
        "githubRunAttempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "status": "pending", "stage": "initialized", "applicationPackage": False,
        "verification": "not_completed", "runtimeTests": "not_run", "deviceTests": "not_run",
        "signing": SIGNING[args.platform],
        "goRuntime": ("source_matched_native_artifact" if args.platform in ("android", "ohos", "windows", "linux")
                      else "compiled_from_source_in_this_job"),
        "flutter": {"repository": FLUTTER_REPOSITORY, "tag": FLUTTER_TAG,
                    "commit": FLUTTER_COMMIT, "engine": ENGINE_COMMIT,
                    "ohosEngine": OHOS_ENGINE_COMMIT,
                    "toolingDependencyOverride": TOOLING_COMMIT},
        "packages": [],
    }


def validate_native(args, manifest: dict) -> None:
    """Validate the same-SHA desktop artifact before Flutter configures CMake."""
    if args.platform not in ("windows", "linux"):
        raise ValueError("Only Windows and Linux consume standalone native artifacts")
    artifact_value = os.environ.get("QFLI_NATIVE_ARTIFACT_DIR")
    if not artifact_value:
        raise RuntimeError("QFLI_NATIVE_ARTIFACT_DIR is required for desktop runtime consumption")
    artifact_dir = Path(artifact_value)
    if not artifact_dir.is_absolute():
        artifact_dir = ROOT / artifact_dir
    artifact_dir = artifact_dir.resolve(strict=True)
    if not artifact_dir.is_relative_to(ROOT.resolve()):
        raise RuntimeError("Native artifact must be inside the application checkout")
    sys.path.insert(0, str(ROOT / "tool/ci"))
    import collect_native

    source_commit = git_head(ROOT)
    native_manifest = collect_native.validate_artifact(artifact_dir, args.platform, source_commit, [args.arch])
    library_name = "qfli_go_runtime.dll" if args.platform == "windows" else "libqfli_go_runtime.so"
    library = artifact_dir / library_name
    build_env = {"QFLI_GO_RUNTIME_ARTIFACT": str(library.resolve())}
    for key, value in build_env.items():
        os.environ[key] = value
    if os.environ.get("GITHUB_ENV"):
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as stream:
            for key, value in build_env.items():
                stream.write(f"{key}={value}\n")
    record = {
        "sourceSha": native_manifest["sourceSha"],
        "nativeSourceSha256": native_manifest["nativeSourceSha256"],
        "platform": native_manifest["platform"],
        "abiSet": native_manifest["abiSet"],
        "requiredExports": native_manifest["requiredExports"],
        "sourceChecksRunURL": native_manifest["sourceChecksRunURL"],
        "runId": native_manifest["runId"], "runAttempt": native_manifest["runAttempt"],
        "artifactManifestSha256": digest(artifact_dir / "manifest.json"),
        "artifactPath": library.relative_to(ROOT.resolve()).as_posix(),
        "librarySha256": digest(library),
    }
    manifest["nativeRuntime"] = record
    manifest["goRuntime"] = "source_matched_native_artifact"
    write_json(args.output / "reports/native-runtime-consumption.json", record)


def consume_native(args, manifest: dict) -> None:
    """Validate and stage mobile native libraries from the same-run artifact."""
    if args.platform not in ("android", "ohos"):
        raise ValueError("Mobile native artifact consumption supports Android and OHOS only")
    artifact_value = os.environ.get("QFLI_NATIVE_ARTIFACT_DIR")
    if not artifact_value:
        raise RuntimeError("QFLI_NATIVE_ARTIFACT_DIR is required for mobile runtime consumption")
    artifact_dir = Path(artifact_value)
    if not artifact_dir.is_absolute():
        artifact_dir = ROOT / artifact_dir
    sys.path.insert(0, str(ROOT / "tool/ci"))
    import collect_native

    expected_abis = list(ANDROID_ABIS) if args.platform == "android" else ["arm64-v8a", "x86_64"]
    native_manifest = collect_native.validate_artifact(artifact_dir, args.platform, git_head(ROOT), expected_abis)
    target_root = ROOT / MOBILE_RUNTIME_DIRS[args.platform]
    library_records = []
    for abi in expected_abis:
        for filename in (RUNTIME_LIBRARY, "libqfli_go_runtime.h"):
            relative = f"{abi}/{filename}"
            source = artifact_dir / relative
            destination = target_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            entry = {"path": relative, "bytes": destination.stat().st_size,
                     "sha256": digest(destination)}
            if filename == RUNTIME_LIBRARY:
                entry["loadSha256"] = elf_load_digest(destination.read_bytes())
            library_records.append(entry)
    record = {
        "sourceSha": native_manifest["sourceSha"],
        "nativeSourceSha256": native_manifest["nativeSourceSha256"],
        "platform": native_manifest["platform"],
        "abiSet": native_manifest["abiSet"],
        "requiredExports": native_manifest["requiredExports"],
        "sourceChecksRunURL": native_manifest["sourceChecksRunURL"],
        "runId": native_manifest["runId"], "runAttempt": native_manifest["runAttempt"],
        "artifactManifestSha256": digest(artifact_dir / "manifest.json"),
        "files": library_records,
    }
    manifest["nativeRuntime"] = record
    manifest["goRuntime"] = "source_matched_native_artifact"
    write_json(args.output / "reports/native-runtime-consumption.json", record)


def setup_native(args, manifest: dict) -> None:
    """Expose the Go toolchain to the CMake and Xcode steps of the application build."""
    if args.platform not in NATIVE_BUILD_PLATFORMS:
        raise ValueError("This job consumes a native artifact and needs no Go toolchain")
    reports = args.output / "reports"
    go = shutil.which("go")
    if not go:
        raise RuntimeError("Go toolchain is unavailable")
    version = run([go, "version"], reports / "go-version.log").strip()
    if f"go{GO_VERSION}" not in version.split():
        raise RuntimeError(f"Expected Go {GO_VERSION}, found: {version}")
    values = {"QFLI_GO_EXECUTABLE": Path(go).as_posix()}
    publish_environment(values)
    manifest["goToolchain"] = {"version": version, **values}


def checkout_flutter_release(sdk: Path, reports: Path) -> None:
    tag_ref = "refs/tags/" + FLUTTER_TAG
    # Flutter derives its public SDK version from the retained release tag.
    # Fetching only into FETCH_HEAD preserves the commit but loses that version.
    run_with_retries(["git", "fetch", "--depth", "1", "origin", f"{tag_ref}:{tag_ref}"],
                     reports / "sdk-fetch.log", cwd=sdk, timeout=900)
    tagged_commit = run(["git", "rev-parse", tag_ref + "^{commit}"],
                        reports / "sdk-tag-commit.log", cwd=sdk).strip()
    if tagged_commit != FLUTTER_COMMIT:
        raise RuntimeError("Flutter tag no longer matches the pinned commit")
    run(["git", "checkout", "--detach", tag_ref], reports / "sdk-checkout.log", cwd=sdk)
    if git_head(sdk) != FLUTTER_COMMIT:
        raise RuntimeError("Flutter checkout differs from the verified release tag")


def validate_flutter_version(version: dict) -> None:
    if (version.get("frameworkRevision") != FLUTTER_COMMIT
            or version.get("frameworkVersion") != FLUTTER_TAG
            or not version.get("dartSdkVersion", "").startswith("3.11.5")):
        raise RuntimeError("Bootstrapped Flutter/Dart version differs from the pinned release")


def setup_flutter(args, manifest: dict) -> None:
    sdk = args.flutter_root
    reports = args.output / "reports"
    sdk.mkdir(parents=True, exist_ok=True)
    if not (sdk / ".git").exists():
        run(["git", "init", sdk], reports / "sdk-init.log")
        run(["git", "remote", "add", "origin", FLUTTER_REPOSITORY],
            reports / "sdk-remote.log", cwd=sdk)
    checkout_flutter_release(sdk, reports)
    for name, expected in (("engine.version", ENGINE_COMMIT),
                           ("engine.ohos.version", OHOS_ENGINE_COMMIT),
                           ("engine.ohos.har.version", OHOS_ENGINE_COMMIT)):
        if (sdk / "bin/internal" / name).read_text().strip() != expected:
            raise RuntimeError(f"Unexpected Flutter engine identity: {name}")
    overrides = "dependency_overrides:\n"
    for package in ("code_assets", "hooks_runner"):
        overrides += (f"  {package}:\n    git:\n"
                      "      url: https://gitcode.com/openharmony-sig/fluttertpc_dart_native\n"
                      f"      path: pkgs/{package}\n      ref: {TOOLING_COMMIT}\n")
    (sdk / "packages/flutter_tools/pubspec_overrides.yaml").write_text(overrides, encoding="utf-8")
    (reports / "flutter-tool-pubspec-overrides.yaml").write_text(overrides, encoding="utf-8")
    sdk_env = environment()
    publish_environment({"QFLI_FLUTTER_ROOT": sdk}, [sdk / "bin"])
    # Pub get regenerates every enabled platform. Do not require an OHOS SDK in
    # a non-OHOS job merely because this application contains an ohos directory.
    ohos_flag = "--enable-ohos" if args.platform == "ohos" else "--no-enable-ohos"
    # The first Flutter command downloads the Dart SDK. Its curl call does not
    # repeat a failed name lookup, so one DNS failure on the runner would end the job.
    run_with_retries([flutter(args), "config", "--no-analytics", ohos_flag],
                     reports / "flutter-config.log", delay=20, env=sdk_env)
    version = run([flutter(args), "--version", "--machine"], reports / "flutter-version.log", env=sdk_env)
    version_data = json.loads(version)
    validate_flutter_version(version_data)
    manifest["flutter"]["version"] = version_data
    flag = {"windows": "--enable-windows-desktop", "linux": "--enable-linux-desktop",
            "macos": "--enable-macos-desktop"}.get(args.platform)
    if flag:
        run([flutter(args), "config", flag], reports / "flutter-platform-config.log", env=sdk_env)
    run([flutter(args), "config", "--list"], reports / "flutter-effective-config.log", env=sdk_env)
    run_with_retries([flutter(args), "precache", "--" + args.platform],
                     reports / "flutter-precache.log", delay=20, env=sdk_env)
    resolved_locks = []
    for source in (sdk / "pubspec.lock", sdk / "packages/flutter_tools/pubspec.lock"):
        if source.exists():
            name = "flutter-root-pubspec.lock" if source.parent == sdk else "flutter-tools-pubspec.lock"
            shutil.copy2(source, reports / name)
            resolved_locks.append(source.read_text(encoding="utf-8"))
    for package in ("code_assets", "hooks_runner"):
        blocks = [match.group(1) for lock in resolved_locks
                  for match in re.finditer(r"(?ms)^  " + package + r":\n(.*?)(?=^  [a-zA-Z_]|\Z)", lock)]
        if not any(re.search(r"resolved-ref:\s*[\"']?" + TOOLING_COMMIT, block) for block in blocks):
            raise RuntimeError(f"Flutter tooling lock did not resolve {package} to the pinned override")
    manifest["flutter"]["toolingOverridesVerifiedInLock"] = True


def validate_ohos_sdk_metadata(metadata) -> None:
    data = metadata.get("data", {}) if isinstance(metadata, dict) else {}
    if not isinstance(data, dict) or str(data.get("apiVersion")) != "26":
        raise RuntimeError("OHOS SDK does not contain the expected API26 release")


def setup_ohos(args, manifest: dict) -> None:
    if args.platform != "ohos":
        raise ValueError("OHOS setup is only valid for the OHOS job")
    reports = args.output / "reports"
    sdk_dir = Path(os.environ["RUNNER_TEMP"]) / "qfli-harmonyos-sdk"
    sdk_dir.mkdir(parents=True, exist_ok=True)
    archive = sdk_dir / "ohos-sdk-linux-amd64.tar.gz"
    base = f"https://github.com/ErBWs/ohos-sdk/releases/download/{OHOS_SDK_RELEASE}"
    with archive.open("wb") as combined:
        for part, expected in OHOS_PARTS.items():
            target = archive.with_name(archive.name + "." + part)
            run(["curl", "--fail", "--location", "--retry", "3", "--max-time", "1800",
                 base + "/" + target.name, "-o", target], reports / f"ohos-download-{part}.log")
            if digest(target) != expected:
                raise RuntimeError(f"OHOS SDK checksum mismatch: part {part}")
            with target.open("rb") as stream:
                shutil.copyfileobj(stream, combined, 1024 * 1024)
            target.unlink()
    if digest(archive) != OHOS_SDK_SHA256:
        raise RuntimeError("Combined OHOS SDK checksum mismatch")
    with tarfile.open(archive, "r:gz") as package:
        package.extractall(sdk_dir, filter="data")
    archive.unlink()
    tools = sdk_dir / "command-line-tools"
    metadata_path = tools / "sdk/default/sdk-pkg.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    validate_ohos_sdk_metadata(metadata)
    write_json(reports / "ohos-sdk-pkg.json", metadata)
    publish_environment({"HOS_SDK_HOME": tools / "sdk", "DEVECO_SDK_HOME": tools / "sdk",
                         "DEVECO_NODE_HOME": tools / "tool/node"},
                        [tools / "bin", tools / "tool/node/bin"])
    run([tools / "bin/ohpm", "--version"], reports / "ohpm-version.log")
    run([tools / "bin/hvigorw", "--version"], reports / "hvigor-version.log")
    manifest["ohosSdk"] = {"release": OHOS_SDK_RELEASE, "source": base,
                           "provenance": "third_party_repackaged_mirror",
                           "sha256": OHOS_SDK_SHA256, "metadata": metadata,
                           "effectiveCompileApi": int(metadata["data"]["apiVersion"]),
                           "compileSdkSelection": "bundled_default",
                           "targetSdkVersion": "6.1.1(24)",
                           "compatibleSdkVersion": "5.1.0(18)"}


def unsigned_ohos_profile() -> None:
    """Change only a clean ephemeral Actions checkout, never a developer profile."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("Unsigned OHOS profile generation requires a GitHub Actions checkout")
    status = subprocess.check_output(["git", "status", "--porcelain", "--", "ohos/build-profile.json5"],
                                     cwd=ROOT, text=True)
    if status.strip():
        raise RuntimeError("Refusing to overwrite a modified OHOS build profile")
    import json5
    path = ROOT / "ohos/build-profile.json5"
    profile = json5.loads(path.read_text(encoding="utf-8"))
    app = profile["app"]
    app["signingConfigs"] = []
    for product in app["products"]:
        product.pop("signingConfig", None)
        if (product.get("targetSdkVersion") != "6.1.1(24)"
                or product.get("compatibleSdkVersion") != "5.1.0(18)"):
            raise RuntimeError("Unexpected OHOS SDK targets; review instead of silently changing them")
        # Hvigor selects the verified API26 SDK bundled with the command-line
        # tools. An explicit numeric API conflicts with its DevEco version check.
        product.pop("compileSdkVersion", None)
    path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")


def core_source_binding(core: Path) -> dict:
    """Require pub to resolve the shared core from the pinned sibling checkout."""
    config = json.loads((ROOT / ".dart_tool/package_config.json").read_text(encoding="utf-8"))
    roots = {package["name"]: package["rootUri"] for package in config["packages"]}
    binding = {}
    for name, expected in (("qfli_studio_core", core), ("re_editor", core / "vendor/re_editor"),
                           ("xterm", core / "vendor/xterm")):
        uri = roots.get(name)
        if uri is None:
            raise RuntimeError(f"Package configuration does not contain {name}")
        parsed = urlparse(uri)
        # Relative root URIs are relative to the package configuration file.
        actual = (Path(url2pathname(parsed.path)) if parsed.scheme == "file"
                  else ROOT / ".dart_tool" / unquote(uri))
        if os.path.normcase(actual.resolve()) != os.path.normcase(expected.resolve()):
            raise RuntimeError(f"{name} does not resolve to the pinned core checkout: {uri}")
        binding[name] = {"rootUri": uri, "resolvesToPinnedCheckout": True}
    return binding


def required_file(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Missing or empty application file: {path}")


def declared_assets() -> list[str]:
    """Read the `flutter: assets:` entries without requiring a YAML parser."""
    entries, section = [], None
    for line in (ROOT / "pubspec.yaml").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            section = line.split(":", 1)[0]
        elif section == "flutter" and line.rstrip() == "  assets:":
            section = "flutter.assets"
        elif section == "flutter.assets":
            match = re.fullmatch(r"\s{4}-\s+['\"]?([^'\"#\s]+)['\"]?\s*", line)
            if not match:
                section = "flutter"
                continue
            entries.append(match.group(1))
    return entries


def expected_assets() -> dict:
    assets = {}
    for entry in declared_assets():
        source = ROOT / entry
        if entry.endswith("/"):
            # A directory entry bundles its direct files only.
            assets.update({path.relative_to(ROOT).as_posix(): path for path in sorted(source.iterdir())
                           if path.is_file() and not path.name.startswith(".")})
        else:
            assets[entry] = source
    if not assets:
        raise RuntimeError("pubspec.yaml declares no application assets to verify")
    return assets


def inspect_assets(names, read) -> list:
    receipts = []
    for key, source in expected_assets().items():
        suffix = "/flutter_assets/" + key
        matches = [name for name in names if name.endswith(suffix)]
        if len(matches) != 1:
            raise RuntimeError(f"Expected one packaged asset {key}, found {len(matches)}")
        actual = hashlib.sha256(read(matches[0])).hexdigest()
        if actual != digest(source):
            raise RuntimeError(f"Packaged asset differs from source: {key}")
        receipts.append({"path": matches[0], "sha256": actual, "sourceMatches": True})
    return receipts


def elf_info(data: bytes) -> dict:
    """Parse the header, LOAD alignments and dynamic exports of a little-endian ELF."""
    if data[:4] != b"\x7fELF" or data[5] != 1 or data[4] not in (1, 2):
        raise RuntimeError("Expected little-endian ELF")
    wide = data[4] == 2
    try:
        kind, machine = struct.unpack_from("<HH", data, 16)
        if wide:
            phoff, shoff = struct.unpack_from("<QQ", data, 32)
            phsize, phnum, shsize, shnum = struct.unpack_from("<HHHH", data, 54)
        else:
            phoff, shoff = struct.unpack_from("<II", data, 28)
            phsize, phnum, shsize, shnum = struct.unpack_from("<HHHH", data, 42)
        alignments = []
        for index in range(phnum):
            offset = phoff + index * phsize
            if struct.unpack_from("<I", data, offset)[0] == 1:
                alignments.append(struct.unpack_from("<Q" if wide else "<I", data,
                                                     offset + (48 if wide else 28))[0])
        # Section fields: type, offset, size, link, entry size.
        sections = []
        for index in range(shnum if shoff else 0):
            offset = shoff + index * shsize
            if wide:
                kind_, = struct.unpack_from("<I", data, offset + 4)
                start, size, link = struct.unpack_from("<QQI", data, offset + 24)
                entry_size, = struct.unpack_from("<Q", data, offset + 56)
            else:
                kind_, = struct.unpack_from("<I", data, offset + 4)
                start, size, link = struct.unpack_from("<III", data, offset + 16)
                entry_size, = struct.unpack_from("<I", data, offset + 36)
            sections.append((kind_, start, size, link, entry_size))
        symbols = set()
        for kind_, start, size, link, entry_size in sections:
            if kind_ != 11 or not entry_size:  # SHT_DYNSYM
                continue
            names_start, names_size = sections[link][1:3]
            names = data[names_start:names_start + names_size]
            for offset in range(start, start + size, entry_size):
                if wide:
                    name, info, other, index = struct.unpack_from("<IBBH", data, offset)
                else:
                    name, _, _, info, other, index = struct.unpack_from("<IIIBBH", data, offset)
                # Defined, global or weak, default or protected visibility.
                if index and info >> 4 in (1, 2) and (other & 3) in (0, 3):
                    symbols.add(names[name:names.find(b"\0", name)].decode("utf-8", "replace"))
    except (struct.error, IndexError) as error:
        raise RuntimeError(f"Truncated or malformed ELF: {error}") from error
    return {"elfClass": 64 if wide else 32, "machine": machine, "type": kind,
            "loadAlignments": alignments, "symbols": sorted(symbols)}


def inspect_elf(data: bytes, abi: str, *, android: bool = False) -> dict:
    info = elf_info(data)
    if info["machine"] != MACHINES[abi]:
        raise RuntimeError(f"Wrong ELF machine {info['machine']} for {abi}")
    if info["elfClass"] != (32 if abi == "armeabi-v7a" else 64):
        raise RuntimeError(f"Unexpected ELF class for {abi}")
    if info["type"] != 3 or not info["loadAlignments"]:
        raise RuntimeError("Expected a loadable shared library")
    if android and abi != "armeabi-v7a" and min(info["loadAlignments"]) < 16384:
        raise RuntimeError("Android 64-bit library LOAD alignment is below 16 KiB")
    return info


def require_exports(symbols, name: str) -> None:
    missing = SYMBOLS - set(symbols)
    if missing:
        raise RuntimeError(f"Missing Go runtime exports in {name}: {', '.join(sorted(missing))}")


def pe_info(data: bytes, name: str) -> dict:
    """Parse the export names and imported DLL names of an x64 PE image."""
    try:
        header = struct.unpack_from("<I", data, 60)[0]
        machine, section_count = struct.unpack_from("<HH", data, header + 4)
        optional = header + 24
        if (data[:2] != b"MZ" or data[header:header + 4] != b"PE\0\0" or machine != 0x8664
                or struct.unpack_from("<H", data, optional)[0] != 0x20B):
            raise RuntimeError(f"Not an x64 PE image: {name}")
        optional_size = struct.unpack_from("<H", data, header + 20)[0]
        directory_count = min(struct.unpack_from("<I", data, optional + 108)[0], 16)
        directories = [struct.unpack_from("<I", data, optional + 112 + 8 * index)[0]
                       for index in range(directory_count)]
        sections = [struct.unpack_from("<IIII", data, optional + optional_size + 40 * index + 8)
                    for index in range(section_count)]

        def offset(rva):
            for virtual_size, virtual_address, raw_size, raw_pointer in sections:
                if virtual_address <= rva < virtual_address + max(virtual_size, raw_size):
                    return rva - virtual_address + raw_pointer
            raise RuntimeError(f"PE address is outside every section: {name}")

        def text(rva):
            start = offset(rva)
            return data[start:data.index(b"\0", start)].decode("ascii", "replace")

        exports, imports = set(), []
        if directory_count > 0 and directories[0]:
            table = offset(directories[0])
            name_count = struct.unpack_from("<I", data, table + 24)[0]
            names = offset(struct.unpack_from("<I", data, table + 32)[0])
            exports = {text(struct.unpack_from("<I", data, names + 4 * index)[0])
                       for index in range(name_count)}
        if directory_count > 1 and directories[1]:
            descriptor = offset(directories[1])
            while name_rva := struct.unpack_from("<I", data, descriptor + 12)[0]:
                imports.append(text(name_rva))
                descriptor += 20
    except (struct.error, ValueError) as error:
        raise RuntimeError(f"Truncated or malformed PE image: {name}: {error}") from error
    return {"exports": sorted(exports), "imports": imports}


def elf_load_digest(data: bytes) -> str:
    """Bind packaged ELF load bytes while permitting removal of debug sections."""
    elf_info(data)
    wide = data[4] == 2
    normalized = bytearray(data)
    # strip changes the section table, not the mapped program contents.
    start, size = (40, 8) if wide else (32, 4)
    normalized[start:start + size] = b"\0" * size
    start = 58 if wide else 46
    normalized[start:start + 6] = b"\0" * 6
    phoff = struct.unpack_from("<Q" if wide else "<I", data, 32 if wide else 28)[0]
    phsize, phnum = struct.unpack_from("<HH", data, 54 if wide else 42)
    result = hashlib.sha256()
    for index in range(phnum):
        offset = phoff + index * phsize
        if struct.unpack_from("<I", data, offset)[0] != 1:
            continue
        if wide:
            _, flags, start, address, _, size, memory, align = struct.unpack_from("<IIQQQQQQ", data, offset)
        else:
            _, start, address, _, size, memory, flags, align = struct.unpack_from("<IIIIIIII", data, offset)
        if start + size > len(data):
            raise RuntimeError("Truncated ELF LOAD segment")
        result.update(struct.pack("<QQQQQQ", start, address, size, memory, flags, align))
        result.update(normalized[start:start + size])
    return result.hexdigest()


def native_consumption_record(args, manifest: dict) -> dict:
    record = manifest.get("nativeRuntime")
    if (not isinstance(record, dict) or record.get("sourceSha") != manifest.get("sourceCommit")
            or record.get("platform") != args.platform
            or record.get("runId") != os.environ.get("GITHUB_RUN_ID")
            or record.get("runAttempt") != os.environ.get("GITHUB_RUN_ATTEMPT")):
        raise RuntimeError("Package is missing its validated same-SHA native artifact record")
    return record


def inspect_mobile(path: Path, args, expected_abis, manifest: dict | None = None) -> dict:
    android = args.platform == "android"
    prefix = "lib/" if android else "libs/"
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        libraries = [name for name in names if name.startswith(prefix) and name.endswith(".so")]
        actual_abis = {name[len(prefix):].split("/", 1)[0] for name in libraries}
        if actual_abis != set(expected_abis):
            raise RuntimeError(f"Unexpected package ABIs: {sorted(actual_abis)}")
        for abi in expected_abis:
            for library in ("libflutter.so", "libapp.so", RUNTIME_LIBRARY):
                if prefix + abi + "/" + library not in libraries:
                    raise RuntimeError(f"Missing {abi}/{library} in {path.name}")
        receipts = []
        for name in libraries:
            abi = name[len(prefix):].split("/", 1)[0]
            data = archive.read(name)
            info = inspect_elf(data, abi, android=android)
            receipt = {"path": name, "sha256": hashlib.sha256(data).hexdigest(),
                       "machine": info["machine"], "loadAlignments": info["loadAlignments"]}
            if name.endswith("/" + RUNTIME_LIBRARY):
                require_exports(info["symbols"], name)
                receipt["verification"] = "elf_and_go_runtime_exports_checked"
                record = native_consumption_record(args, manifest or {})
                relative = f"{abi}/{RUNTIME_LIBRARY}"
                matches = [item for item in record.get("files", []) if item.get("path") == relative]
                if len(matches) != 1:
                    raise RuntimeError(f"Missing validated native artifact library: {relative}")
                expected = matches[0]
                staged = ROOT / MOBILE_RUNTIME_DIRS[args.platform] / relative
                if not staged.is_file() or digest(staged) != expected.get("sha256"):
                    raise RuntimeError(f"Staged runtime differs from the validated native artifact: {relative}")
                if elf_load_digest(data) != expected.get("loadSha256"):
                    raise RuntimeError(f"Packaged runtime differs from the validated native artifact: {relative}")
                receipt.update(artifactSha256=expected["sha256"],
                               byteIdenticalToArtifact=receipt["sha256"] == expected["sha256"],
                               loadSegmentsMatchArtifact=True)
            receipts.append(receipt)
        assets = inspect_assets(names, archive.read)
        if ("AndroidManifest.xml" if android else "module.json") not in names:
            raise RuntimeError(f"Missing application manifest in {path.name}")
        return {"file": path.name, "libraries": receipts, "assets": assets,
                "deviceTests": "not_run"}


def inspect_flat_bundle(bundle: Path, args) -> list:
    """Check a Windows or Linux bundle directory."""
    windows = args.platform == "windows"
    runtime = "qfli_go_runtime.dll" if windows else "lib/" + RUNTIME_LIBRARY
    required = (["qfli_go.exe", "flutter_windows.dll", runtime, "data/app.so", "data/icudtl.dat"]
                if windows else
                ["qfli_go", "lib/libflutter_linux_gtk.so", "lib/libapp.so", runtime, "data/icudtl.dat"])
    for name in required:
        required_file(bundle / name)
    library = bundle / runtime
    if windows:
        for name in ("qfli_go.exe", "flutter_windows.dll"):
            pe_info((bundle / name).read_bytes(), name)
        inspect_elf((bundle / "data/app.so").read_bytes(), args.arch)
        info = pe_info(library.read_bytes(), library.name)
        require_exports(info["exports"], library.name)
        shipped = {path.name.lower() for path in bundle.iterdir() if path.is_file()}
        # MinGW runtime DLLs are named lib*.dll and exist on no clean Windows system.
        unshipped = sorted(name for name in info["imports"]
                           if name.lower().startswith("lib") and name.lower() not in shipped)
        if unshipped:
            raise RuntimeError(f"{library.name} imports toolchain DLLs that the bundle "
                               f"does not ship: {', '.join(unshipped)}")
        evidence = {"verification": "pe_exports_and_imports_checked", "imports": info["imports"]}
    else:
        for name in ("lib/libflutter_linux_gtk.so", "lib/libapp.so"):
            inspect_elf((bundle / name).read_bytes(), args.arch)
        info = inspect_elf(library.read_bytes(), args.arch)
        require_exports(info["symbols"], library.name)
        evidence = {"verification": "elf_and_go_runtime_exports_checked"}
    return [{"path": runtime, "sha256": digest(library), **evidence}]


def inspect_apple_bundle(bundle: Path, args) -> tuple:
    """Check a macOS or iOS application bundle with the Xcode command-line tools."""
    macos = args.platform == "macos"
    reports = args.output / "reports"
    with (bundle / ("Contents/Info.plist" if macos else "Info.plist")).open("rb") as stream:
        info = plistlib.load(stream)
    executable = bundle / ("Contents/MacOS" if macos else "") / info["CFBundleExecutable"]
    required_file(executable)
    frameworks = bundle / ("Contents/Frameworks" if macos else "Frameworks")
    engine_name = "FlutterMacOS" if macos else "Flutter"
    libraries = []
    for name in (engine_name, "App"):
        binary = frameworks / f"{name}.framework" / name
        required_file(binary)
        arches = run(["lipo", "-archs", binary], reports / f"{name}-architectures.log").strip().split()
        if args.arch not in arches:
            raise RuntimeError(f"{name} framework does not support {args.arch}: {arches}")
        libraries.append({"path": binary.relative_to(bundle).as_posix(), "sha256": digest(binary),
                          "architectures": arches, "verification": "requested_architecture_present"})
    architectures = run(["lipo", "-archs", executable], reports / "runner-architectures.log").strip().split()
    if architectures != [args.arch]:
        raise RuntimeError(f"Unexpected Runner architectures: {architectures}")
    if macos:
        runtime = frameworks / "libqfli_go_runtime.dylib"
        required_file(runtime)
        arches = run(["lipo", "-archs", runtime], reports / "go-runtime-architectures.log").strip().split()
        if args.arch not in arches:
            raise RuntimeError(f"Go runtime does not support {args.arch}: {arches}")
    else:
        # The iOS runtime is a static archive linked into the Runner executable.
        runtime, arches = executable, architectures
    exports = run(["nm", "-arch", args.arch, "-gU", runtime], reports / "go-runtime-exports.log")
    symbols = {line.split()[-1].removeprefix("_") for line in exports.splitlines() if line.split()}
    require_exports(symbols, runtime.name)
    libraries.append({"path": runtime.relative_to(bundle).as_posix(), "sha256": digest(runtime),
                      "architectures": arches, "verification": "go_runtime_exports_checked"})
    if macos:
        run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", bundle],
            reports / "codesign-verification.log")
        run(["codesign", "--display", "--verbose=4", bundle], reports / "codesign-identity.log")
        return libraries, "deep_strict_verification_passed_not_notarized"
    return libraries, "unsigned_device_signing_required"


def inspect_bundle(bundle: Path, args) -> dict:
    if not bundle.is_dir():
        raise RuntimeError(f"Flutter did not produce the application bundle: {bundle}")
    paths = [path for path in bundle.rglob("*") if path.is_file()]
    names = ["bundle/" + path.relative_to(bundle).as_posix() for path in paths]
    assets = inspect_assets(names, lambda name: (bundle / name.removeprefix("bundle/")).read_bytes())
    if args.platform in ("windows", "linux"):
        libraries, signing_verification = inspect_flat_bundle(bundle, args), "not_applicable"
    else:
        libraries, signing_verification = inspect_apple_bundle(bundle, args)
    return {"bundle": bundle.name, "libraries": libraries, "assets": assets,
            "deviceTests": "not_run", "runtimeTests": "not_run",
            "signingVerification": signing_verification}


def android_build_tool(name: str) -> Path:
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not sdk:
        raise RuntimeError("Android SDK location is unavailable")
    tools = sorted(Path(sdk).glob(f"build-tools/*/{name}"),
                   key=lambda path: tuple(int(part) for part in re.findall(r"\d+", path.parent.name)))
    if not tools:
        raise RuntimeError(f"Android SDK {name} is unavailable")
    return tools[-1]


def archive_directory(directory: Path, destination: Path, root_name: str) -> None:
    # Tar retains Apple framework symlinks and Unix executable modes through upload-artifact.
    with tarfile.open(destination, "w:gz", dereference=False) as archive:
        archive.add(directory, arcname=root_name)


def zip_directory(directory: Path, destination: Path, root_name: str) -> None:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                archive.write(path, (Path(root_name) / path.relative_to(directory)).as_posix())


def archive_ipa(bundle: Path, destination: Path, reports: Path) -> None:
    """Wrap the unsigned application in the Payload layout that signing tools expect."""
    with tempfile.TemporaryDirectory(prefix="ipa-", dir=destination.parent) as work:
        shutil.copytree(bundle, Path(work) / "Payload" / bundle.name, symlinks=True)
        run(["zip", "-qry", destination, "Payload"], reports / "ipa-archive.log", cwd=work)


def assert_bundle_runtime_matches_artifact(bundle: Path, args, manifest: dict) -> None:
    if args.platform not in ("windows", "linux"):
        return
    record = native_consumption_record(args, manifest)
    artifact = ROOT / record["artifactPath"]
    library_name = "qfli_go_runtime.dll" if args.platform == "windows" else "libqfli_go_runtime.so"
    packaged = bundle / (library_name if args.platform == "windows" else "lib/" + library_name)
    required_file(artifact)
    required_file(packaged)
    artifact_hash = digest(artifact)
    if artifact_hash != record.get("librarySha256") or digest(packaged) != artifact_hash:
        raise RuntimeError("Desktop bundle runtime differs from the validated native artifact")
    record["bundledLibrarySha256"] = digest(packaged)
    record["bundledArtifactMatch"] = True


def collect(args, manifest: dict) -> None:
    reports = args.output / "reports"
    packages = args.output / "packages"
    if packages.exists():
        raise RuntimeError("Refusing to stage into an existing packages directory")
    inventories = []
    pending = []
    if args.platform == "android":
        for abi in ANDROID_ABIS:
            path = ROOT / f"build/app/outputs/flutter-apk/app-{abi}-release.apk"
            required_file(path)
            inventories.append(inspect_mobile(path, args, [abi], manifest))
            run([android_build_tool("zipalign"), "-c", "-P", "16", "-v", "4", path],
                reports / f"{abi}-zipalign.log")
            run([android_build_tool("apksigner"), "verify", "--verbose", "--print-certs", path],
                reports / f"{abi}-apksigner.log")
            pending.append((path, f"{APP_NAME}-android-{abi}.apk"))
    elif args.platform == "ohos":
        choices = [ROOT / "build/ohos/hap/entry-default-unsigned.hap",
                   ROOT / "ohos/entry/build/default/outputs/default/entry-default-unsigned.hap"]
        path = next((choice for choice in choices if choice.is_file()), None)
        if path is None:
            raise RuntimeError("Flutter did not produce an unsigned HAP")
        inventories.append(inspect_mobile(path, args, [args.arch], manifest))
        pending.append((path, f"{APP_NAME}-ohos-{args.arch}-unsigned.hap"))
    else:
        bundle = ROOT / BUNDLES[args.platform]
        inventories.append(inspect_bundle(bundle, args))
        assert_bundle_runtime_matches_artifact(bundle, args, manifest)
        suffix = {"windows": ".zip", "ios": "-unsigned.ipa"}.get(args.platform, ".tar.gz")
        pending.append((bundle, f"{APP_NAME}-{args.platform}-{args.arch}{suffix}"))
    # Validate every output before publishing any package from this attempt.
    write_json(reports / "package-inspection.json", inventories)
    with tempfile.TemporaryDirectory(prefix="app-package-", dir=args.output.parent) as staging:
        staging = Path(staging)
        receipts = []
        for source, name in pending:
            destination = staging / name
            if source.is_file():
                shutil.copy2(source, destination)
            elif args.platform == "windows":
                zip_directory(source, destination, destination.stem)
            elif args.platform == "ios":
                archive_ipa(source, destination, reports)
            else:
                root_name = source.name if args.platform == "macos" else name.removesuffix(".tar.gz")
                archive_directory(source, destination, root_name)
            receipts.append({"path": "packages/" + name,
                             "bytes": destination.stat().st_size, "sha256": digest(destination)})
        # All outputs are complete before their final directory becomes uploadable.
        shutil.move(str(staging), packages)
    manifest["packages"] = receipts
    manifest["applicationPackage"] = True
    manifest["verification"] = "release_compiled_and_package_inspected"


def build(args, manifest: dict) -> None:
    core = ROOT.parent / CORE_DIRECTORY
    if git_head(core) != CORE_COMMIT:
        raise RuntimeError("Core checkout differs from the pinned revision")
    if git_head(args.flutter_root) != FLUTTER_COMMIT:
        raise RuntimeError("Flutter checkout differs from the pinned revision")
    reports = args.output / "reports"
    build_env = environment()
    if args.platform in ("windows", "linux"):
        record = native_consumption_record(args, manifest)
        artifact = build_env.get("QFLI_GO_RUNTIME_ARTIFACT")
        if (not artifact or Path(artifact).resolve() != (ROOT / record["artifactPath"]).resolve()
                or digest(artifact) != record.get("librarySha256")):
            raise RuntimeError("Validated desktop runtime artifact is unavailable; run validate-native before build")
        build_env["QFLI_GO_RUNTIME_ARTIFACT"] = str(Path(artifact).resolve())
    elif args.platform in ("android", "ohos"):
        native_consumption_record(args, manifest)
    elif args.platform in NATIVE_BUILD_PLATFORMS:
        go = build_env.get("QFLI_GO_EXECUTABLE")
        if not go:
            raise RuntimeError("Go toolchain is not provisioned; run setup-native before build")
        # Xcode phases prepend Homebrew to PATH; this setting retains our toolchain.
        build_env["FLUTTER_XCODE_QFLI_GO_EXECUTABLE"] = go
    if args.platform == "macos":
        build_env.update({"FLUTTER_XCODE_ARCHS": args.arch, "FLUTTER_XCODE_ONLY_ACTIVE_ARCH": "YES",
                          "FLUTTER_XCODE_CODE_SIGN_IDENTITY": "-", "FLUTTER_XCODE_CODE_SIGN_STYLE": "Manual",
                          "FLUTTER_XCODE_CODE_SIGNING_REQUIRED": "YES",
                          "FLUTTER_XCODE_MACOSX_DEPLOYMENT_TARGET": MACOS_DEPLOYMENT_TARGET})
    if args.platform == "ohos":
        unsigned_ohos_profile()
    run([flutter(args), "pub", "get"], reports / "pub-get.log", env=build_env)
    if (ROOT / "pubspec.lock").exists():
        shutil.copy2(ROOT / "pubspec.lock", reports / "app-pubspec.lock")
    write_json(reports / "core-source-binding.json", core_source_binding(core))
    common = ["--release", "--target", "lib/main.dart", "--no-pub"]
    # `flutter pub get` registers dev-only plugins (integration_test). With --no-pub
    # the build keeps that registrant, but release Gradle omits those plugins, so
    # javac fails. Without --no-pub the build regenerates the release registrant.
    command = {"android": ["apk", "--release", "--target", "lib/main.dart", "--split-per-abi"],
               "ios": ["ios", *common, "--no-codesign"],
               "ohos": ["hap", *common, "--no-codesign", "--target-platform", "ohos-arm64"],
               }.get(args.platform, [args.platform, *common])
    try:
        run([flutter(args), "build", *command], reports / f"build-{command[0]}.log", env=build_env)
    finally:
        # Android may resolve again while regenerating its release registrant.
        if (ROOT / "pubspec.lock").exists():
            shutil.copy2(ROOT / "pubspec.lock", reports / "app-pubspec.lock")
    write_json(reports / "core-source-binding.json", core_source_binding(core))
    collect(args, manifest)
    manifest["status"] = "passed"


def invalidate_packages(args, manifest: dict) -> None:
    """Revoke package success for every failure, including late evidence errors."""
    manifest["status"] = "failed"
    manifest["packages"] = []
    manifest["applicationPackage"] = False
    manifest["verification"] = "failed_see_reports"
    (args.output / "SHA256SUMS").unlink(missing_ok=True)
    packages = args.output / "packages"
    if packages.exists():
        # This is the output directory created by this attempt. Refuse link traversal.
        if packages.is_symlink() or packages.resolve().parent != args.output.resolve():
            raise RuntimeError("Refusing to clean packages outside this attempt's output directory")
        shutil.rmtree(packages)


def write_step_summary(args, manifest: dict) -> None:
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    lines = [f"### App package: {args.platform} / {args.arch}", "",
             f"- Status: `{manifest.get('status')}`",
             f"- Signing: `{manifest.get('signing')}`",
             f"- Go runtime: `{manifest.get('goRuntime')}`",
             "- Device tests: `not_run`", ""]
    if manifest.get("packages"):
        lines += ["| Package | Bytes | SHA-256 |", "| --- | ---: | --- |"]
        lines += [f"| `{package['path']}` | {package['bytes']} | `{package['sha256']}` |"
                  for package in manifest["packages"]]
    else:
        lines.append("No package was published. See `reports/` in the artifact.")
    with open(target, "a", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")


def finalize(args, manifest: dict) -> None:
    if args.job_status != "success" or manifest.get("status") != "passed":
        manifest.setdefault("error", "See the workflow step and retained reports for the failed prerequisite")
        invalidate_packages(args, manifest)
    licenses = args.output / "licenses"
    licenses.mkdir(exist_ok=True)
    for source, name in ((ROOT / "LICENSE", "LICENSE.txt"),
                         (ROOT / "native/go_runtime/LICENSE.go-standard-library", "Go-LICENSE.txt"),
                         (ROOT / "assets/licenses/yaegi.txt", "Yaegi-LICENSE.txt"),
                         (ROOT.parent / CORE_DIRECTORY / "LICENSE", "Core-LICENSE.txt")):
        if source.is_file():
            shutil.copy2(source, licenses / name)
    write_step_summary(args, manifest)


def write_checksums(output: Path) -> None:
    paths = sorted(path for path in output.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
    content = "".join(f"{digest(path)}  {path.relative_to(output).as_posix()}\n" for path in paths)
    (output / "SHA256SUMS").write_text(content, encoding="utf-8")


COMMANDS = {"setup-native": setup_native, "validate-native": validate_native,
            "consume-native": consume_native, "setup-ohos": setup_ohos,
            "setup-flutter": setup_flutter, "build": build, "finalize": finalize}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", *COMMANDS))
    parser.add_argument("--platform", default=os.environ.get("QFLI_PLATFORM"), choices=tuple(SIGNING))
    parser.add_argument("--arch", default=os.environ.get("QFLI_ARCH"))
    parser.add_argument("--output-dir", type=Path)
    default_flutter = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())) / "qfli-flutter-oh"
    parser.add_argument("--flutter-root", type=Path,
                        default=Path(os.environ.get("QFLI_FLUTTER_ROOT", str(default_flutter))))
    parser.add_argument("--job-status", default="success", choices=("success", "failure", "cancelled"))
    args = parser.parse_args()
    if not args.platform or not args.arch:
        parser.error("--platform and --arch (or QFLI_PLATFORM/QFLI_ARCH) are required")
    args.output = (args.output_dir or ROOT / f"build/app-artifacts/app-{args.platform}-{args.arch}").resolve()
    manifest_path = args.output / "manifest.json"
    # An init refusal has not acquired this output directory. Keep it outside the
    # current-attempt failure handler so an earlier successful run stays intact.
    if args.command == "init":
        manifest = initialize(args)
    else:
        manifest = (json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists()
                    else initialize(args))
    try:
        manifest["stage"] = args.command
        if args.command != "init":
            # Resolve at call time so a replaced step function takes effect.
            globals()[COMMANDS[args.command].__name__](args, manifest)
        write_json(manifest_path, manifest)
        if args.command == "finalize":
            write_checksums(args.output)
    except Exception as error:
        manifest["error"] = str(error)
        failure = traceback.format_exc()
        try:
            invalidate_packages(args, manifest)
        except Exception as cleanup_error:
            manifest["packageCleanupError"] = str(cleanup_error)
            failure += "\nPackage invalidation error:\n" + traceback.format_exc()
        report = args.output / "reports" / f"{args.command}-failure.txt"
        annotate_command_failure(report, 1, failure)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(failure, encoding="utf-8")
        write_json(manifest_path, manifest)
        raise


if __name__ == "__main__":
    main()
