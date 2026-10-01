/// Execution backend used by each native platform.
enum GoRuntimeBackend {
  embeddedInterpreter('embedded-go-runtime', 'available'),
  officialSdk('official-go-sdk', 'requires-sdk'),
  unavailable('unavailable', 'unavailable');

  const GoRuntimeBackend(this.kind, this.status);

  final String kind;
  final String status;
}

GoRuntimeBackend goRuntimeBackendFor(String operatingSystem) =>
    switch (operatingSystem) {
      'android' || 'ohos' || 'ios' => GoRuntimeBackend.embeddedInterpreter,
      'windows' || 'linux' || 'macos' => GoRuntimeBackend.officialSdk,
      _ => GoRuntimeBackend.unavailable,
    };
