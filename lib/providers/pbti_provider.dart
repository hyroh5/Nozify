import 'dart:convert';
import 'package:flutter/material.dart';

import '../services/api_client.dart';
import 'auth_provider.dart';
import '../models/pbti_result.dart';

class PbtiProvider with ChangeNotifier {
  /// 서버에서 가져온 PBTI 코드 리스트 (최신순)
  List<String> _results = [];

  List<String> get results => _results;
  bool get hasResult => _results.isNotEmpty;

  /// 가장 최근 코드
  String? get latestCode => hasResult ? _results.first : null;

  /// 로그인된 유저의 PBTI 히스토리를 서버에서 로드
  Future<void> loadResults(AuthProvider auth) async {
    if (!auth.isLoggedIn) {
      _results = [];
      notifyListeners();
      return;
    }

    try {
      final res = await ApiClient.I.get(
        "/pbti/history",
        auth: true,
      );

      if (res.statusCode != 200) {
        _results = [];
        notifyListeners();
        return;
      }

      final List<dynamic> jsonList = jsonDecode(res.body);
      _results = jsonList
          .map<String>((e) => (e as Map<String, dynamic>)['final_type'] as String? ?? '----')
          .toList();

      notifyListeners();
    } catch (e) {
      _results = [];
      notifyListeners();
    }
  }

  /// 설문 답안을 서버에 제출
  /// answers: [{ "question_id": 1, "choice": 5 }, ...]
  Future<PbtiResultModel> submitPbti(
      AuthProvider auth,
      List<Map<String, int>> answers,
      ) async {
    if (!auth.isLoggedIn) {
      throw Exception("로그인 후 이용 가능합니다.");
    }

    final body = jsonEncode({
      "answers": answers,
    });

    final res = await ApiClient.I.post(
      "/pbti/submit",
      auth: true,
      body: body,
    );

    if (res.statusCode != 201 && res.statusCode != 200) {
      throw Exception("PBTI 제출 실패 (status: ${res.statusCode})");
    }

    final Map<String, dynamic> json = jsonDecode(res.body);

    /// 🔥 여기서 항상 안전하게 파싱됨 (오류 안 남)
    final result = PbtiResultModel.fromJson(json);

    /// 히스토리 새로고침
    await loadResults(auth);

    return result;
  }

  void clear() {
    _results = [];
    notifyListeners();
  }
}
