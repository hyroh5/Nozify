import 'dart:convert';
import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../models/recent_view.dart';
import '../models/similar_perfume.dart';

class RecentViewProvider with ChangeNotifier {
  bool isLoadingRecent = false;
  bool isLoadingSimilar = false;

  List<RecentViewItem> recentViews = [];
  List<SimilarPerfumeItem> similarPerfumes = [];

  /// ------------------------------------------------------------
  /// 1) 최근 본 향수 목록
  /// ------------------------------------------------------------
  Future<void> fetchRecentViews() async {
    isLoadingRecent = true;
    notifyListeners();

    final res = await ApiClient.I.get(
      "/recommendations/recent-views",
      query: {"limit": "5"},
      auth: true,
    );

    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      recentViews = (data["items"] as List)
          .map((e) => RecentViewItem.fromJson(e))
          .toList();
    }

    isLoadingRecent = false;
    notifyListeners();
  }

  /// ------------------------------------------------------------
  /// 2) 특정 향수의 유사 추천
  /// ------------------------------------------------------------
  Future<void> fetchSimilar(String perfumeId) async {
    isLoadingSimilar = true;
    notifyListeners();

    final res = await ApiClient.I.get(
      "/catalog/perfumes/$perfumeId/similar",
      query: {"limit": "5"},
      auth: false, // 공개 API
    );

    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      similarPerfumes = (data["results"] as List)
          .map((e) => SimilarPerfumeItem.fromJson(e))
          .toList();
    }

    isLoadingSimilar = false;
    notifyListeners();
  }

  void clearSimilar() {
    similarPerfumes = [];
    notifyListeners();
  }
}
