// lib/providers/pbti_provider.dart
import 'dart:convert';
import 'package:flutter/material.dart';

import '../services/api_client.dart';
import 'auth_provider.dart';

import '../models/pbti_result.dart';
import '../models/perfume_simple.dart';
import '../models/pbti_axis_recommendation.dart';   // 🔥 축별 추천 전체 모델

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

  /// 로그아웃 시 초기화
  void clear() {
    _results = [];
    notifyListeners();
  }

  /// 🔥 기존 추천 API (그냥 리스트)
  Future<List<PerfumeSimple>> fetchRecommendations() async {
    final res = await ApiClient.I.get(
      "/pbti/recommendations",
      auth: true,
    );

    if (res.statusCode != 200) {
      throw Exception("추천 향수 불러오기 실패");
    }

    final Map<String, dynamic> data = jsonDecode(res.body);
    List<dynamic> items = data['items'] ?? [];

    return items
        .map((e) => PerfumeSimple.fromJson(e))
        .toList();
  }

  /// 🔥 PBti 축별 추천 API
  Future<PbtiByTypeRecommendation> fetchByTypeRecommendations() async {
    final res = await ApiClient.I.get(
      "/pbti/recommendations/by_type",
      auth: true,
    );

    if (res.statusCode != 200) {
      throw Exception("축별 추천 불러오기 실패 (status: ${res.statusCode})");
    }

    final Map<String, dynamic> data = jsonDecode(res.body);

    /// 🔥 축 전체 모델로 파싱해야 정상!
    return PbtiByTypeRecommendation.fromJson(data);
  }
}
