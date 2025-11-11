import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'auth_provider.dart';  // 로그인 상태 확인용

class PbtiProvider with ChangeNotifier {
  List<Map<String, String>> _results = [];

  List<Map<String, String>> get results => _results;
  bool get hasResult => _results.isNotEmpty;

  /// 현재 PBTI 코드 (가장 최근 결과)
  String? get latestCode => hasResult ? _results.last['type'] : null;

  /// SharedPreferences에서 로그인된 유저의 PBTI 결과 로드
  Future<void> loadResults(AuthProvider auth) async {
    if (!auth.isLoggedIn) {
      _results = [];
      notifyListeners();
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    final key = 'pbtiResults_${auth.user!.email}';
    final saved = prefs.getStringList(key) ?? [];

    _results = saved.map((r) {
      final parts = r.split(',');
      return {'type': parts[0], 'image': parts[1]};
    }).toList();

    notifyListeners();
  }

  /// 새 결과 저장
  Future<void> addResult(AuthProvider auth, String code, String imagePath) async {
    if (!auth.isLoggedIn) return;

    final prefs = await SharedPreferences.getInstance();
    final key = 'pbtiResults_${auth.user!.email}';
    final saved = prefs.getStringList(key) ?? [];

    if (!saved.any((e) => e.startsWith(code))) {
      saved.add('$code,$imagePath');
      await prefs.setStringList(key, saved);
      _results.add({'type': code, 'image': imagePath});
      notifyListeners();
    }
  }

  /// 유저 로그아웃 시 초기화
  void clear() {
    _results = [];
    notifyListeners();
  }
}
