// lib/providers/today_recommendation_provider.dart
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:location/location.dart';

import '../services/api_client.dart';
import '../models/perfume_simple.dart';

class TodayRecommendationProvider with ChangeNotifier {
  final Location _location = Location();

  String _occasion = 'nightout'; // 기본값
  String get occasion => _occasion;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  List<PerfumeSimple> _items = [];
  List<PerfumeSimple> get items => _items;

  // occasion 변경 + 재조회
  Future<void> setOccasion(String value) async {
    if (_occasion == value) return;
    _occasion = value;
    notifyListeners(); // 버튼 UI 업데이트
    await fetchTodayRecommendations();
  }

  Future<void> fetchTodayRecommendations() async {
    _isLoading = true;
    notifyListeners();

    // 기본값: 서울 시청 근처
    double lat = 37.56;
    double lon = 126.97;

    try {
      bool serviceEnabled = await _location.serviceEnabled();
      if (!serviceEnabled) {
        serviceEnabled = await _location.requestService();
      }

      PermissionStatus permission = await _location.hasPermission();
      if (permission == PermissionStatus.denied) {
        permission = await _location.requestPermission();
      }

      if (permission == PermissionStatus.granted ||
          permission == PermissionStatus.grantedLimited) {
        final data = await _location.getLocation();
        if (data.latitude != null && data.longitude != null) {
          lat = data.latitude!;
          lon = data.longitude!;
        }
      }
    } catch (_) {
      // 위치 실패시 그냥 기본 lat/lon 사용
    }

    try {
      final res = await ApiClient.I.get(
        "/recommendations/today"
            "?occasion=$_occasion&lat=$lat&lon=$lon&limit=10",
        auth: true, // 토큰 있으면 붙고, 게스트면 is_guest=true로 처리될 거라 가정
      );

      if (res.statusCode != 200) {
        _items = [];
      } else {
        final Map<String, dynamic> jsonMap =
        jsonDecode(res.body) as Map<String, dynamic>;
        final List<dynamic> list = jsonMap['items'] as List<dynamic>;
        _items = list
            .map((e) =>
            PerfumeSimple.fromJson(e as Map<String, dynamic>))
            .toList();
      }
    } catch (_) {
      _items = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
