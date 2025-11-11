import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'auth_provider.dart';

/// ---------------------------------------
/// 📘 Record 모델
/// ---------------------------------------
class Record {
  final String perfume;
  final String situation;
  final String weather;
  final String mood;

  Record(this.perfume, this.situation, this.weather, this.mood);

  Map<String, dynamic> toJson() => {
    'perfume': perfume,
    'situation': situation,
    'weather': weather,
    'mood': mood,
  };

  factory Record.fromJson(Map<String, dynamic> json) => Record(
    json['perfume'],
    json['situation'],
    json['weather'],
    json['mood'],
  );
}

/// ---------------------------------------
/// 🗓 CalendarProvider (유저별 저장 지원)
/// ---------------------------------------
class CalendarProvider extends ChangeNotifier {
  Map<String, List<Record>> records = {}; // key: 'YYYY-MM-DD'

  AuthUser? _user; // 현재 로그인한 유저 정보
  AuthUser? get user => _user;

  /// ✅ 로그인한 유저 정보 설정
  void setUser(AuthUser? user) {
    _user = user;
  }

  /// ✅ 유저별 key 생성
  String _keyForUser(String baseKey) {
    if (_user == null) return baseKey;
    final emailSafe = _user!.email.replaceAll('.', '_');
    return '${baseKey}_$emailSafe';
  }

  /// ✅ 기록 추가
  Future<void> addRecord(DateTime date, Record record) async {
    if (_user == null) return; // 로그인 안 되어 있으면 무시
    final key = _key(date);
    records.putIfAbsent(key, () => []).add(record);
    await _saveToStorage();
    notifyListeners();
  }

  /// ✅ 기록 가져오기
  List<Record> getRecords(DateTime date) {
    final key = _key(date);
    return records[key] ?? [];
  }

  /// ✅ 기록 삭제
  Future<void> removeRecord(DateTime date, int index) async {
    if (_user == null) return;
    final key = _key(date);
    if (records[key] != null && index < records[key]!.length) {
      records[key]!.removeAt(index);
      if (records[key]!.isEmpty) records.remove(key);
      await _saveToStorage();
      notifyListeners();
    }
  }

  /// ✅ 로컬 저장
  Future<void> _saveToStorage() async {
    if (_user == null) return;
    final prefs = await SharedPreferences.getInstance();
    final encoded = jsonEncode(records.map(
          (key, list) => MapEntry(key, list.map((r) => r.toJson()).toList()),
    ));
    await prefs.setString(_keyForUser('calendar_records'), encoded);
  }

  /// ✅ 로컬 불러오기
  Future<void> loadFromStorage() async {
    if (_user == null) return;
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getString(_keyForUser('calendar_records'));
    if (data != null) {
      final decoded = jsonDecode(data) as Map<String, dynamic>;
      records = decoded.map((key, list) {
        final typedList = (list as List).map((e) => Record.fromJson(e)).toList();
        return MapEntry(key, typedList);
      });
    }
    notifyListeners();
  }

  /// ✅ 모든 기록 초기화 (로그아웃 시)
  Future<void> clearAll() async {
    records.clear();
    notifyListeners();
  }

  /// ✅ 날짜 키
  String _key(DateTime date) =>
      '${date.year.toString().padLeft(4, '0')}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';

  /// ✅ 특정 날짜에 기록이 있는지 여부
  bool hasRecord(DateTime date) {
    final key = _key(date);
    return records.containsKey(key) && records[key]!.isNotEmpty;
  }
}
