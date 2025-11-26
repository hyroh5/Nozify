import 'dart:convert';
import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../models/perfume_simple.dart';

class TrendingProvider extends ChangeNotifier {
  List<PerfumeSimple> items = [];
  bool isLoading = false;

  Future<void> fetchTrending() async {
    isLoading = true;
    notifyListeners();

    try {
      final res = await ApiClient.I.get(
        "/recommendations/trending",
        query: {"limit": "10"}, // ← 너가 요청한대로 고정
        auth: false,
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final list = data["items"] ?? [];

        items = list.map<PerfumeSimple>((e) => PerfumeSimple.fromJson(e)).toList();
      }
    } catch (_) {
      // 오류 시 items는 빈 배열 유지
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }
}
