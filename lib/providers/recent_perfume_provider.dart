// lib/providers/recent_perfume_provider.dart
import 'dart:convert';
import 'package:flutter/material.dart';

import '../services/api_client.dart';

class RecentPerfume {
  final String id;
  final String name;
  final String brandName;
  final String? imageUrl;
  final String? gender;
  final DateTime? viewedAt;
  final List<String> mainAccords;

  RecentPerfume({
    required this.id,
    required this.name,
    required this.brandName,
    this.imageUrl,
    this.gender,
    this.viewedAt,
    required this.mainAccords,
  });

  factory RecentPerfume.fromJson(Map<String, dynamic> json) {
    final perfume = json['perfume'] as Map<String, dynamic>;
    return RecentPerfume(
      id: perfume['id'] as String,
      name: perfume['name'] as String,
      brandName: perfume['brand_name'] as String? ?? '',
      imageUrl: perfume['image_url'] as String?,
      gender: perfume['gender'] as String?,
      viewedAt: json['viewed_at'] != null
          ? DateTime.tryParse(json['viewed_at'] as String)
          : null,
      mainAccords: (perfume['main_accords'] as List<dynamic>?)
          ?.map((e) => e.toString())
          .toList() ??
          const [],
    );
  }
}

class RecentPerfumeProvider with ChangeNotifier {
  List<RecentPerfume> _items = [];
  bool _isLoading = false;
  bool _loadedOnce = false;

  List<RecentPerfume> get items => _items;
  bool get isLoading => _isLoading;
  bool get loadedOnce => _loadedOnce;

  Future<void> fetchRecent({int limit = 10}) async {
    _isLoading = true;
    notifyListeners();

    try {
      // limit은 서버에서 기본값 처리 가능해서 쿼리 안 붙여도 됨
      final res = await ApiClient.I.get(
        "/user/recent-views",
        auth: true,
      );

      if (res.statusCode == 200) {
        final List<dynamic> list = jsonDecode(res.body) as List<dynamic>;
        _items = list
            .map((e) => RecentPerfume.fromJson(e as Map<String, dynamic>))
            .toList();
      } else if (res.statusCode == 401) {
        // 비로그인 → 그냥 빈 리스트
        _items = [];
      }
      _loadedOnce = true;
    } catch (_) {
      _items = [];
      _loadedOnce = true;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 예전에 쓰던 이름 호환용
  Future<void> loadRecent() => fetchRecent();

  void clear() {
    _items = [];
    _loadedOnce = false;
    notifyListeners();
  }
}
