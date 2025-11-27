import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/api_client.dart';
import '../models/perfume_simple.dart';
import '../models/brand_simple.dart';

class BrandRecommendationProvider extends ChangeNotifier {
  List<BrandSimple> brands = [];
  List<PerfumeSimple> brandPerfumes = [];

  bool isLoadingBrands = false;
  bool isLoadingPerfumes = false;

  /// 1) 많이 본 브랜드 목록 가져오기
  Future<void> fetchBrandList() async {
    isLoadingBrands = true;
    notifyListeners();

    final res = await ApiClient.I.get("/recommendations/brands", auth: true);

    if (res.statusCode == 200) {
      final List items = jsonDecode(res.body)["items"];
      brands = items.map((e) => BrandSimple.fromJson(e)).toList();
    }

    isLoadingBrands = false;
    notifyListeners();
  }

  /// 2) 특정 브랜드 향수 추천 가져오기 (limit = 5 고정)
  Future<void> fetchBrandPerfumes(String brandId) async {
    isLoadingPerfumes = true;
    notifyListeners();

    final res = await ApiClient.I.get(
      "/recommendations/brands/$brandId/perfumes",
      auth: true,
      query: {"limit": "5"},
    );

    if (res.statusCode == 200) {
      final List items = jsonDecode(res.body)["items"];
      brandPerfumes =
          items.map((e) => PerfumeSimple.fromJson(e)).toList();
    }

    isLoadingPerfumes = false;
    notifyListeners();
  }
}
