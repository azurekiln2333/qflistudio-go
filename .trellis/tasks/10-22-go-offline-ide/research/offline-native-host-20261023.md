# Go offline native host repair

Date: 2026-10-23, Asia/Shanghai. JSON's read-only family host audit and the user's
forwarded steering identified real remaining OHOS `openAgreement` and arbitrary
`openUrl` handlers despite the offline Dart profile.

The smallest behavior change is in the owning EntryAbility platform channel:
both methods now return `OFFLINE_ONLY` directly. Unused router/Want imports and
the AgreementReader registered route are removed. Startup progress, picker and
system sharing remain functional. These product-owned ArkTS/profile files,
the existing catalog integration audit, inspector marker and local spec are
the complete change boundary.

The user explicitly separated authored-program network capability from host
navigation policy. No native Go stdlib exports, runtime networking policy or
INTERNET permission were changed. Existing unrelated manifest/signing/branding
edits are preserved. This does not establish a general network sandbox.

The existing packaged integration suite now invokes the actual native channel
with ten combinations (two methods, five URI forms), requires OFFLINE_ONLY and
checks startupProgress success. It appends `goOfflineHostAudit` to reportData
and logs `QFLI_GO_OFFLINE_HOST_AUDIT`; the HAP inspector requires that marker.
The test is skipped outside OHOS and has not executed on a target yet.

Verification so far: Dart formatting passed. ArkTS compilation and actual
native-channel/ordinary-app checks await the matching HAP build/device window.
No network request, external page launch or device mutation was used to test
this source change.
