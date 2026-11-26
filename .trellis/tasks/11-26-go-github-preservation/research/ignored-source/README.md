# Historical ignored-source preservation

Task: `11-26-go-github-preservation`. Owner: `w5V:p5`.

This is a bounded historical archive, not active tooling or current validation.
All originals remain at their source paths. Nothing here authorizes deletion,
cleanup, patch application or execution of an archived helper.

## Contents and authoritative inventory

- `provenance.json`: all 49 snapshots, with exact source/destination paths,
  byte counts, SHA-256 hashes, observation times, purpose and review limitations.
- `dispositions.json`: three verified reachable-history duplicates, 27 individual
  HOLD records, and explicit SDK/binary/raw-evidence exclusions and default holds.
- `FILES.sha256`: final frozen archive inventory of raw-byte SHA-256 hashes.
  It covers every other archive file, including the controls, but not itself.
  Its self-hash is reported separately to the coordinator.
- `.gitattributes`: sets `-text` for `historical/**` and each of the six controls
  (`.gitattributes`, `.gitignore`, `provenance.json`, `dispositions.json`,
  `README.md`, `FILES.sha256`). Git preserves their raw bytes through staging
  and checkout regardless of `core.autocrlf`; inventory hashes remain applicable.
- `.gitignore`: exposes only the 49 reviewed snapshot paths and their required
  ancestor directories. Unlisted historical files remain ignored.

There are **47 byte-exact snapshots (1,289,474 bytes)** and **two redacted
curriculum derivatives (5,528,019 bytes)**, totaling **6,817,493 snapshot bytes**.
Their 49 original inputs total 6,817,421 bytes. The 72-byte difference belongs
only to the explicitly documented email replacement markers.

The five previously created helper/patch snapshots were retained and verified,
not recopied. Additional exact snapshots cover reviewed native probes/fixtures,
CI research source, curriculum source/backups/dumps, and five compact historical
classification/package/native-hash records. Executable source has a `.txt`
suffix. Patches also remain inert `.patch.txt` files and were never applied.

## Privacy and historical-use boundary

Focused source/content review and marker checks found no embedded secret in the
selected snapshots. Credential-related strings in three CI helpers refer to
runtime credential acquisition, not literal credentials. Never execute those
helpers: they may access credentials, use the network, write reports or inspect
packages. Other archived sources may run builds, create fixtures or send agent
prompts if made executable. They were not executed during preservation.

Reserved example-domain emails in Go topic 090 and injected configuration IPs
in topic 117 are reviewed synthetic teaching fixtures, not device evidence.
They remain byte-exact in the applied backups and chapter dump.

The two `original-*.json.redacted.txt` snapshots retain each full 1,620-entry
multi-language wrapper. Only two occurrences per file of a nonreserved
example contact in Python topic 073 were replaced with
`[EXAMPLE_EMAIL_REDACTED]`. UTF-8 byte roundtrips and the replacement scope were
checked. Both raw originals remain on **HOLD**, with original hashes recorded.
The derivatives are explicitly **not byte-exact** copies of those originals.
License labels are retained. This is not independent legal clearance.

A telephone-pattern match in `diagnose_download.py.txt` is the numeric GitHub
artifact identifier in its API path, not a telephone number. No raw device,
actor, screenshot, UI XML or diagnostic log content was copied by this batch.
Focused review is not a comprehensive security audit.

## Duplicate and HOLD dispositions

Exact reachable local-history blobs already preserve these inputs, so no
redundant archive copy was created:

- `.artifacts/release-integrity/android-app-gradle.original`
- `.artifacts/native-startup/baseline/lib/main.dart`
- `.artifacts/native-startup/baseline/ohos/entry/src/main/ets/pages/Index.ets`

The unreviewed OHOS `EntryAbility.ets` baseline, raw CI/API evidence, device
scripts/records, logs, screenshots, UI XML, SDK trees, binaries, packages,
dependency installations, caches and reparse targets remain explicitly held or
excluded from this archive. Exclusion means **not copied**, not disposable.
The unknown state of extracted Windows/Linux SDK modifications is unresolved.
The earlier clean nested OHOS checkout observation is recorded as historical
metadata, not a complete SDK audit. Nothing was moved or deleted.

Anything not explicitly preserved or classified in the two JSON records stays
on **HOLD** by default. This archive is not a complete inventory of those trees.

## Git visibility and staging handoff

Ancestor rules `**/build/` and `**/native/build/` hid the two helper snapshots.
The archive-local `.gitignore` now negates those required directories and exact
reviewed files without modifying root ignore policy. Final read-only
`git check-ignore --no-index` and `git ls-files --others --exclude-standard`
metadata must show every frozen file visible without force-add. Unreviewed
control paths remain ignored.

The comparison baseline is local HEAD
`b65d38362d4a51297025e6d1a401c7c8c8b51eba`, tree
`90eb39051866db27e090487ad8bd537b014cce54`. It covered currently reachable
local refs only, with optional locks and lazy fetching disabled. No remote
refresh was performed by this worker. Missing exact local blobs do not prove
absence from every remote, unreachable object or external archive.

After final hash/read-back verification the worker freezes this subtree and
reports only to `w5V:p1`. `w5V:p2` owns explicit staging, index/refs, commits and
publication. The task itself is not marked complete by this archive. Historical
PASS text and old local results are not current GitHub-hosted acceptance.

No Git mutation, build, test, lint/analyze, installation, dependency setup,
download, code generation, archived-source execution or cleanup was performed.
