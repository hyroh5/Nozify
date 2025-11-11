import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class StorageManager {
  static const String wishlistKey = 'wishlist';
  static const String purchasedKey = 'purchased';

  // 이메일로 키 네임스페이스 (로그인별 분리 저장)
  static String _ns(String baseKey, String email) => '$baseKey::$email';

  // 전체 리스트 불러오기 (계정별)
  static Future<List<Map<String, String>>> loadList(
      String baseKey, String email) async {
    final prefs = await SharedPreferences.getInstance();
    final key = _ns(baseKey, email);
    final jsonData = prefs.getString(key);
    if (jsonData == null) return [];
    final List<dynamic> decoded = jsonDecode(jsonData);
    return decoded.map((e) => Map<String, String>.from(e)).toList();
  }

  // 저장 (계정별)
  static Future<void> saveList(
      String baseKey, String email, List<Map<String, String>> data) async {
    final prefs = await SharedPreferences.getInstance();
    final key = _ns(baseKey, email);
    await prefs.setString(key, jsonEncode(data));
  }

  // 추가 (계정별)
  static Future<void> addItem(
      String baseKey, String email, Map<String, String> perfume) async {
    final list = await loadList(baseKey, email);
    final exists = list.any((p) => p['name'] == perfume['name']);
    if (!exists) {
      list.add(perfume);
      await saveList(baseKey, email, list);
    }
  }

  // 제거 (계정별)
  static Future<void> removeItem(
      String baseKey, String email, String perfumeName) async {
    final list = await loadList(baseKey, email);
    list.removeWhere((p) => p['name'] == perfumeName);
    await saveList(baseKey, email, list);
  }

  // 포함 여부 확인 (계정별)
  static Future<bool> contains(
      String baseKey, String email, String perfumeName) async {
    final list = await loadList(baseKey, email);
    return list.any((p) => p['name'] == perfumeName);
  }
}
