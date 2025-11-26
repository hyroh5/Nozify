import 'dart:convert';
import 'package:flutter/material.dart';

import '../services/api_client.dart';
import 'auth_provider.dart';

import '../models/pbti_result.dart';
import '../models/perfume_simple.dart';
import '../models/pbti_history.dart';
import '../models/pbti_axis_recommendation.dart';

class PbtiProvider with ChangeNotifier {
  List<PbtiHistoryItem> _results = [];
  List<PbtiHistoryItem> get results => _results;
  bool get hasResult => _results.isNotEmpty;

  String? get latestCode =>
      hasResult ? _results.first.finalType : null;

  // ----------------------------------------
  // PBTI History
  // ----------------------------------------
  Future<void> loadResults(AuthProvider auth) async {
    await auth.waitUntilLoaded();

    if (!auth.isLoggedIn) {
      _results = [];
      notifyListeners();
      return;
    }

    final res = await ApiClient.I.get("/pbti/history", auth: true);

    if (res.statusCode == 200) {
      final list = jsonDecode(res.body) as List;
      _results = list.map((e) => PbtiHistoryItem.fromJson(e)).toList();
    } else {
      _results = [];
    }

    notifyListeners();
  }

  // ----------------------------------------
  // Test Submit
  // ----------------------------------------
  Future<PbtiResultModel> submitPbti(
      AuthProvider auth, List<Map<String, int>> answers) async {
    final res = await ApiClient.I.post(
      "/pbti/submit",
      auth: true,
      body: jsonEncode({"answers": answers}),
    );

    final json = jsonDecode(res.body);
    final result = PbtiResultModel.fromJson(json);

    await loadResults(auth);
    return result;
  }

  // ----------------------------------------
  // 기본 추천
  // ----------------------------------------
  Future<List<PerfumeSimple>> fetchRecommendations() async {
    final res = await ApiClient.I.get("/pbti/recommendations", auth: true);

    if (res.statusCode != 200) {
      throw Exception("추천 향수 불러오기 실패");
    }

    final items = jsonDecode(res.body)["items"] as List;
    return items.map((e) => PerfumeSimple.fromJson(e)).toList();
  }

  // ----------------------------------------
  // 축별 추천
  // ----------------------------------------
  Future<PbtiByTypeRecommendation> fetchByTypeRecommendations() async {
    final res =
    await ApiClient.I.get("/pbti/recommendations/by_type", auth: true);

    if (res.statusCode != 200) {
      throw Exception("축별 추천 불러오기 실패");
    }

    final data = jsonDecode(res.body);
    return PbtiByTypeRecommendation.fromJson(data);
  }

  // ----------------------------------------
  // 삭제
  // ----------------------------------------
  Future<void> deleteHistory(int resultId) async {
    final res =
    await ApiClient.I.delete("/pbti/result/$resultId", auth: true);

    if (res.statusCode != 200) {
      throw Exception("삭제 실패");
    }

    _results.removeWhere((item) => item.id == resultId);
    notifyListeners();
  }
}
