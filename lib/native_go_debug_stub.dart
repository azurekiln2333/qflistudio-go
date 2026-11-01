Future<String> invokeGoDebug({
  required String operation,
  required int sessionId,
  String requestJson = '{}',
  int afterSequence = 0,
}) async => '{"ok":false,"state":"unavailable","error":"当前平台无法加载本地 Go 调试器"}';
