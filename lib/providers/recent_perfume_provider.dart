import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class RecentPerfumeProvider with ChangeNotifier {
  static const _key = 'recent_perfumes';
  List<Map<String, String>> _recent = [];

  List<Map<String, String>> get recentPerfumes => _recent;

  Future<void> loadRecent() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonStr = prefs.getString(_key);
    if (jsonStr != null) {
      final List decoded = json.decode(jsonStr);
      _recent = decoded.map((e) => Map<String, String>.from(e)).toList();
    }
    notifyListeners();
  }

  Future<void> addPerfume(Map<String, String> perfume) async {
    _recent.removeWhere((p) => p['name'] == perfume['name']); // 중복 제거
    _recent.insert(0, perfume); // 최신 맨 앞
    if (_recent.length > 12) _recent = _recent.sublist(0, 12); // 12개 제한

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, json.encode(_recent));
    notifyListeners();
  }
}
