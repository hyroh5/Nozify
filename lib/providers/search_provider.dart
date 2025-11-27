// lib/providers/search_provider.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/api_client.dart';
import '../models/perfume_simple.dart';
import '../models/search_suggestion.dart';

class SearchProvider extends ChangeNotifier {
  bool isLoading = false;

  List<PerfumeSimple> results = [];
  List<SearchSuggestion> suggestions = [];

  // 🔍 검색 (이건 네 거 그대로 사용)
  Future<void> search(String query) async {
    query = query.trim();
    if (query.isEmpty) return;

    isLoading = true;
    notifyListeners();

    final res = await ApiClient.I.get(
      "/catalog/search",
      query: {"q": query, "limit": "50"},
    );

    final body = jsonDecode(res.body);

    List<dynamic> list;

    if (body is List) {
      list = body;
    } else if (body is Map<String, dynamic>) {
      list = body["results"] ?? body["items"] ?? [];
    } else {
      list = [];
    }

    results = list
        .map((e) => PerfumeSimple.fromJson(e as Map<String, dynamic>))
        .toList();

    isLoading = false;
    notifyListeners();
  }

  // 🔥 자동완성 (여기 완전 새로)
  Future<void> fetchSuggest(String query) async {
    query = query.trim();

    if (query.length < 2) {
      print("🔎 query 너무 짧음('$query') → suggestions 비움");
      suggestions = [];
      notifyListeners();
      return;
    }

    try {
      print("⚡ fetchSuggest('$query') 호출됨");

      final res = await ApiClient.I.get(
        "/catalog/suggest",
        query: {"q": query, "limit": "5"},
      );

      final body = jsonDecode(res.body);
      print("📌 raw body = $body");

      List<dynamic> list;

      if (body is List) {
        // 혹시라도 서버가 리스트로 줄 경우
        list = body;
      } else if (body is Map<String, dynamic>) {
        // ✅ 네가 준 응답: { q: "...", items: [ {...}, {...} ] }
        list = body["items"] ?? body["suggestions"] ?? body["results"] ?? [];
      } else {
        list = [];
      }

      print("📌 extracted list = $list");

      suggestions = list.map((e) {
        if (e is Map<String, dynamic>) {
          return SearchSuggestion.fromJson(e);
        } else {
          print("⚠️ 예상 밖 데이터: $e");
          return SearchSuggestion(
            name: e.toString(),
            type: "unknown",
            score: 0.0,
          );
        }
      }).toList();

      print("✅ suggestions length = ${suggestions.length}");
    } catch (e) {
      print("❌ Suggest error: $e");
      suggestions = [];
    }

    notifyListeners();
  }

  // 🔹 강제로 suggestions 비우기 (AppBar에서 씀)
  void clearSuggestions() {
    print("🧹 clearSuggestions() 호출 → suggestions 비움");
    suggestions = [];
    notifyListeners();
  }
}
