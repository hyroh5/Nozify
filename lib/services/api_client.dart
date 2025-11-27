// lib/services/api_client.dart
// 목적: Flutter에서 FastAPI 서버를 쉽게 호출하도록 만든 통합 HTTP 모듈

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/env.dart';

// 생성자
class ApiClient {
  ApiClient._();
  static final ApiClient I = ApiClient._();

  // 서버 URL 자동 조립
  Uri _uri(String path, [Map<String, dynamic>? query]) =>
      Uri.parse("${Env.baseUrl}${Env.apiPrefix}$path").replace(queryParameters: query);

  /// 🔥 외부에서 호출 가능한 debug용 public 메서드 추가
  Uri buildUri(String path, [Map<String, dynamic>? query]) => _uri(path, query);

  // 요청 헤더
  Future<Map<String, String>> _headers({bool auth = false}) async {
    final headers = <String, String>{"Content-Type": "application/json"};
    if (auth) {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token');
      if (token != null) headers["Authorization"] = "Bearer $token";
    }
    return headers;
  }

  // GET 요청: 데이터 가져오기(서버에서 조회)
  Future<http.Response> get(String path, {Map<String, dynamic>? query, bool auth = false}) async {
    final res = await http.get(_uri(path, query), headers: await _headers(auth: auth));
    _throwOnError(res);
    return res;
  }

  // POST 요청: 데이터 생성하기(서버에 데이터 추가)
  Future<http.Response> post(String path, {Object? body, bool auth = false}) async {
    final res = await http.post(_uri(path), headers: await _headers(auth: auth), body: body);
    _throwOnError(res);
    return res;
  }

  // PUT 요청: 데이터 수정하기(서버의 데이터 대체)
  Future<http.Response> put(String path, {Object? body, bool auth = false,}) async {
    final res = await http.put(_uri(path), headers: await _headers(auth: auth), body: body,
    );
    _throwOnError(res);
    return res;
  }

  // DELETE 요청: 데이터 삭제(서버의 데이터 삭제)
  Future<http.Response> delete(String path, {bool auth = false,}) async {
    final res = await http.delete(_uri(path), headers: await _headers(auth: auth),
    );
    _throwOnError(res);
    return res;
  }

  // 에러 처리
  void _throwOnError(http.Response res) {
    if (res.statusCode >= 400) {
      throw Exception("HTTP ${res.statusCode}: ${res.body}");
    }
  }
}
