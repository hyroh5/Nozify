// lib/providers/pbti_provider.dart
import 'dart:convert';
import 'package:flutter/material.dart';

import '../services/api_client.dart';
import 'auth_provider.dart';

import '../models/pbti_result.dart';
import '../models/perfume_simple.dart';
import '../models/pbti_axis_recommendation.dart';

class PbtiProvider with ChangeNotifier {
  List<String> _results = [];

  List<String> get results => _results;
  bool get hasResult => _results.isNotEmpty;

  String? get latestCode => hasResult ? _results.first : null;

  /// 로그인된 유저의 PBTI 히스토리 로드
  Future<void> loadResults(AuthProvider auth) async {
    // 🔥 1) AuthProvider 초기 로딩이 끝날 때까지 기다리기
    await auth.waitUntilLoaded();   // ← 여기 추가

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
          .map<String>((e) =>
      (e as Map<String, dynamic>)['final_type'] as String? ?? '----')
          .toList();

      notifyListeners();
    } catch (e) {
      _results = [];
      notifyListeners();
    }
  }

  /// 설문 제출
  Future<PbtiResultModel> submitPbti(
      AuthProvider auth,
      List<Map<String, int>> answers,
      ) async {
    if (!auth.isLoggedIn) {
      throw Exception("로그인 후 이용 가능합니다.");
    }

    final body = jsonEncode({"answers": answers});

    final res = await ApiClient.I.post(
      "/pbti/submit",
      auth: true,
      body: body,
    );

    if (res.statusCode != 201 && res.statusCode != 200) {
      throw Exception("PBTI 제출 실패 (status: ${res.statusCode})");
    }

    final Map<String, dynamic> json = jsonDecode(res.body);
    final result = PbtiResultModel.fromJson(json);

    await loadResults(auth);

    return result;
  }

  void clear() {
    _results = [];
    notifyListeners();
  }

  /// 기본 추천 API
  Future<List<PerfumeSimple>> fetchRecommendations() async {
    final res = await ApiClient.I.get(
      "/pbti/recommendations",
      auth: true,
    );

    if (res.statusCode != 200) {
      throw Exception("추천 향수 불러오기 실패");
    }

    final Map<String, dynamic> data = jsonDecode(res.body);
    final items = data['items'] ?? [];

    return items.map((e) => PerfumeSimple.fromJson(e)).toList();
  }

  /// 축별 추천 API
  Future<PbtiByTypeRecommendation> fetchByTypeRecommendations() async {
    final res = await ApiClient.I.get(
      "/pbti/recommendations/by_type",
      auth: true,
    );

    if (res.statusCode != 200) {
      throw Exception("축별 추천 불러오기 실패 (status: ${res.statusCode})");
    }

    final Map<String, dynamic> data = jsonDecode(res.body);
    return PbtiByTypeRecommendation.fromJson(data);
  }
}
