"""Isolated review fixture; never launches Flutter, Go, or a native build."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--dart", required=True, type=Path)
    parser.add_argument("--java", required=True, type=Path)
    parser.add_argument("--node", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    powershell = shutil.which("pwsh")
    if not powershell:
        raise RuntimeError("PowerShell 7 is required by this Windows fixture")
    original_script = (args.root / "tool/build_go_catalog_audit.ps1").read_bytes()
    results: dict = {
        "realFlutterOrGoInvoked": False,
        "wrapperSha256": hashlib.sha256(original_script).hexdigest(),
        "readers": {name: str(getattr(args, name)) for name in ("dart", "java", "node")},
    }
    with tempfile.TemporaryDirectory(prefix="go_profile_lock_review_") as directory:
        root = Path(directory)
        tool = root / "tool"
        tool.mkdir()
        wrapper = tool / "build_go_catalog_audit.ps1"
        wrapper.write_bytes(original_script)
        for relative in ("integration_test/go_catalog_test.dart",
                         "integration_test/go_native_ide_acceptance.dart",
                         "integration_test/go_product_ui_acceptance.dart"):
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(args.root / relative, destination)
        profile = root / "ohos/entry/build-profile.json5"
        profile.parent.mkdir(parents=True)
        original = b'\xef\xbb\xbf// \xe5\x8e\x9f\xe5\xa7\x8b\xe5\xad\x97\xe8\x8a\x82\r\n{"abiFilters": ["arm64-v8a"], "excludes": ["**/x86_64/**", "**/armeabi-v7a/**"]}\r\n'
        profile.write_bytes(original)
        (root / "reader.dart").write_text(
            'import "dart:io"; void main(List<String> args) { '
            'final text = File(args.single).readAsStringSync(); '
            'if (!text.contains(\'"abiFilters": ["x86_64"]\')) exit(4); '
            'stdout.write("dart-reader-ok"); }', encoding="utf-8")
        (root / "Reader.java").write_text(
            'import java.nio.file.*; class Reader { public static void main(String[] args) throws Exception { '
            'String text = Files.readString(Path.of(args[0])); '
            'if (!text.contains("\\\"abiFilters\\\": [\\\"x86_64\\\"]")) throw new Exception("wrong ABI"); '
            'System.out.print("java-reader-ok"); }}', encoding="utf-8")
        (root / "reader.js").write_text(
            'const text = require("fs").readFileSync(process.argv[2], "utf8"); '
            'if (!text.includes(\'"abiFilters": ["x86_64"]\')) process.exit(4); '
            'process.stdout.write("node-reader-ok");', encoding="utf-8")
        config = {
            "powershell": powershell, "python": sys.executable,
            "dart": str(args.dart), "java": str(args.java), "node": str(args.node),
        }
        (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
        (root / "second_flutter.cmd").write_text(
            '@echo off\r\n>"%~dp0second_flutter_called" echo forbidden\r\nexit /b 0\r\n', encoding="ascii")
        (root / "fake_flutter.py").write_text('''from pathlib import Path
import hashlib, json, subprocess, sys
root=Path(__file__).resolve().parent
config=json.loads((root/'config.json').read_text())
profile=root/'ohos/entry/build-profile.json5'
before=profile.read_bytes()
checks=[]
for name,command in (
 ('dart',[config['dart'],'--disable-dart-dev','--old_gen_heap_size=64',str(root/'reader.dart'),str(profile)]),
 ('java',[config['java'],'-Xms8m','-Xmx64m',str(root/'Reader.java'),str(profile)]),
 ('node',[config['node'],'--max-old-space-size=32',str(root/'reader.js'),str(profile)]),
):
 completed=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=25)
 checks.append({'reader':name,'exitCode':completed.returncode,'stdout':completed.stdout,'stderr':completed.stderr})
 if completed.returncode: raise RuntimeError(str(checks[-1]))
try:
 with profile.open('r+b') as writer:
  raise RuntimeError('second raw writer was incorrectly allowed')
except PermissionError:
 checks.append({'rawWriterRefused':True})
second=subprocess.run([config['powershell'],'-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'tool/build_go_catalog_audit.ps1'),'-FlutterExecutable',str(root/'second_flutter.cmd'),'-OutputDirectory',str(root/'second-output')],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=15)
checks.append({'secondWrapperRefused':second.returncode!=0,'secondFlutterInvoked':(root/'second_flutter_called').exists(),'exitCode':second.returncode,'stderr':second.stderr})
assert second.returncode != 0 and not (root/'second_flutter_called').exists()
assert before == profile.read_bytes()
out=root/('fake-check-'+str(len(list(root.glob('fake-check-*.json'))))+'.json')
out.write_text(json.dumps({'checks':checks,'temporaryProfileSha256':hashlib.sha256(before).hexdigest()},indent=2))
sys.exit(7)
''', encoding="utf-8")
        fake_flutter = root / "fake_flutter.cmd"
        fake_flutter.write_text(
            '@echo off\r\n"' + sys.executable + '" "%~dp0fake_flutter.py" %*\r\nexit /b %errorlevel%\r\n',
            encoding="utf-8")

        def invoke(script: Path, *, flutter: Path = fake_flutter,
                   output: Path | None = None) -> subprocess.CompletedProcess:
            return subprocess.run(
                [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
                 "-FlutterExecutable", str(flutter), "-OutputDirectory", str(output or root / "output")],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)

        runs = []
        for _ in range(2):
            completed = invoke(wrapper)
            restored = profile.read_bytes() == original
            assert completed.returncode != 0 and "build failed: 7" in completed.stderr, completed.stderr
            assert restored
            runs.append({"exitCode": completed.returncode, "fakeFlutterExitCode": 7,
                         "originalBytesRestored": restored})
        backups = sorted((root / "output").glob("entry-build-profile-original-*.json5"))
        assert len(backups) == 2 and all(path.read_bytes() == original for path in backups)
        results.update({"failedBuildRuns": runs, "uniqueRecoveryBackups": len(backups),
                        "fakeFlutterChecks": [json.loads(path.read_text()) for path in sorted(root.glob("fake-check-*.json"))]})

        fault_wrapper = tool / "build_go_catalog_fault.ps1"
        source = original_script.decode("utf-8-sig")
        needle = "$profileStream.Write($Bytes, 0, $Bytes.Length)"
        assert source.count(needle) == 1
        injected = '''if (-not $script:reviewFaultInjected) {
      $script:reviewFaultInjected = $true
      $profileStream.SetLength(13)
      throw 'review injected partial write'
    }
    '''
        fault_wrapper.write_text(source.replace(needle, needle + "\n    " + injected), encoding="utf-8")
        completed = invoke(fault_wrapper)
        assert completed.returncode != 0 and "review injected partial write" in completed.stderr
        assert profile.read_bytes() == original
        assert len(list(root.glob("fake-check-*.json"))) == 2
        results["injectedPartialWrite"] = {"reachedFlutter": False, "originalBytesRestored": True}
        # Authored source-binding controls. These produce only synthetic bytes;
        # none is a real Flutter/HAP, native, signing or target acceptance run.
        (root / "fake_binding_flutter.py").write_text('''from pathlib import Path
import json
root = Path(__file__).resolve().parent
mode = json.loads((root / "binding-mode.json").read_text())
if mode.get("drift"):
    source = root / "integration_test/go_native_ide_acceptance.dart"
    source.write_bytes(source.read_bytes() + b"\\n// source changed inside synthetic build\\n")
hap = root / "build/ohos/hap/entry-default-signed.hap"
hap.parent.mkdir(parents=True, exist_ok=True)
hap.write_bytes(b"synthetic-source-binding-fixture-only")
''', encoding="utf-8")
        binding_flutter = root / "fake_binding_flutter.cmd"
        binding_flutter.write_text(
            '@echo off\r\n"' + sys.executable + '" "%~dp0fake_binding_flutter.py" %*\r\nexit /b %errorlevel%\r\n',
            encoding="utf-8")
        mode_path = root / "binding-mode.json"
        mode_path.write_text(json.dumps({"drift": False}), encoding="utf-8")
        binding_output = root / "binding-output"
        completed = invoke(wrapper, flutter=binding_flutter, output=binding_output)
        assert completed.returncode == 0, completed.stderr
        evidence = json.loads((binding_output / "build.json").read_text(encoding="utf-8-sig"))
        expected_sources = {
            relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
            for relative in ("integration_test/go_catalog_test.dart",
                             "integration_test/go_native_ide_acceptance.dart",
                             "integration_test/go_product_ui_acceptance.dart")
        }
        assert evidence["schemaVersion"] == 2 and evidence["auditSources"] == expected_sources
        assert evidence["entryPoint"] == "integration_test/go_catalog_test.dart"
        assert hashlib.sha256(Path(evidence["hap"]).read_bytes()).hexdigest() == evidence["hapSha256"]
        assert profile.read_bytes() == original
        results["syntheticSourceBinding"] = {"schemaVersion": 2, "sourceCount": len(expected_sources),
                                             "hapHashBound": True, "originalBytesRestored": True}
        changed_source = root / "integration_test/go_native_ide_acceptance.dart"
        original_source = changed_source.read_bytes()
        drift_output = root / "source-drift-output"
        mode_path.write_text(json.dumps({"drift": True}), encoding="utf-8")
        try:
            completed = invoke(wrapper, flutter=binding_flutter, output=drift_output)
            assert completed.returncode != 0 and "Audit source changed during HAP build" in completed.stderr
            assert not (drift_output / "build.json").exists()
            assert profile.read_bytes() == original
        finally:
            changed_source.write_bytes(original_source)
        results["syntheticSourceDrift"] = {"accepted": False, "originalBytesRestored": True}
        no_exit_flutter = root / "fake_no_native_exit.ps1"
        no_exit_flutter.write_text("Write-Output 'synthetic command returned without native exit'\n", encoding="utf-8")
        no_exit_output = root / "missing-exit-output"
        completed = invoke(wrapper, flutter=no_exit_flutter, output=no_exit_output)
        assert completed.returncode != 0 and "Go catalog audit HAP build failed" in completed.stderr
        assert not (no_exit_output / "build.json").exists() and profile.read_bytes() == original
        results["missingNativeExit"] = {"accepted": False, "originalBytesRestored": True}
        results["success"] = True
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"success": results["success"], "out": str(args.out)}))


if __name__ == "__main__":
    main()
