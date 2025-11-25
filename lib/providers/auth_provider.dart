// lib/providers/auth_provider.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_client.dart';
import '../models/user.dart';              // 백엔드 UserBase 대응
import '../models/auth_response.dart';    // 로그인/회원가입 응답
import '../models/refresh_token.dart';    // 토큰 재발급 응답

class AuthProvider with ChangeNotifier {
  /// 현재 로그인된 유저 정보 (백엔드 UserBase와 동일 구조)
  User? _user;

  User? get user => _user;
  bool get isLoggedIn => _user != null;

  // --------------------------------------------------
  // 1) 앱 시작 시 자동 로그인 복구
  // --------------------------------------------------
  Future<void> loadFromStorage() async {
    final prefs = await SharedPreferences.getInstance();

    // 토큰이 없으면 로그인 상태로 복구하지 않음
    final accessToken = prefs.getString('access_token');
    if (accessToken == null) return;

    final id = prefs.getString('user_id');
    final name = prefs.getString('user_name');
    final email = prefs.getString('user_email');

    if (id != null && name != null && email != null) {
      _user = User(id: id, name: name, email: email);
      notifyListeners();
    }
  }

  // --------------------------------------------------
  // 2) 로그인 (서버 기반)
  //    POST /auth/login -> AuthResponse
  // --------------------------------------------------
  Future<void> signIn(String email, String password) async {
    final res = await ApiClient.I.post(
      "/auth/login",
      body: jsonEncode({
        "email": email,
        "password": password,
      }),
    );

    final Map<String, dynamic> json = jsonDecode(res.body);
    final auth = AuthResponse.fromJson(json); // ✅ 여기서 모델 사용

    await _saveAuth(auth);
  }

  // --------------------------------------------------
  // 3) 회원가입 (서버 기반)
  //    POST /auth/signup -> AuthResponse
  // --------------------------------------------------
  Future<void> signUp(String name, String email, String password) async {
    final res = await ApiClient.I.post(
      "/auth/signup",
      body: jsonEncode({
        "name": name,
        "email": email,
        "password": password,
      }),
    );

    final Map<String, dynamic> json = jsonDecode(res.body);
    final auth = AuthResponse.fromJson(json); // ✅ 모델 사용

    await _saveAuth(auth);
  }

  // --------------------------------------------------
  // 4) 프로필 수정
  //    백엔드: PATCH /auth/update-profile (response: UserBase)
  // --------------------------------------------------
  Future<void> updateUser({
    String? name,
    String? email,
  }) async {
    final body = <String, dynamic>{};
    if (name != null && name.isNotEmpty) body['name'] = name;
    if (email != null && email.isNotEmpty) body['email'] = email;

    if (body.isEmpty) return; // 변경할 내용 없으면 호출 안 함

    // ⚠ ApiClient에 patch 메서드가 없다면, 임시로 put 사용 중
    final res = await ApiClient.I.put(
      "/auth/update-profile",
      body: jsonEncode(body),
      auth: true, // access_token을 Authorization 헤더로 자동 첨부
    );

    final Map<String, dynamic> json = jsonDecode(res.body);

    // 백엔드 응답은 UserBase 구조: {id, name, email}
    final updatedUser = User.fromJson(json);

    // SharedPreferences 업데이트
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_id', updatedUser.id);
    await prefs.setString('user_name', updatedUser.name);
    await prefs.setString('user_email', updatedUser.email);

    // Provider 상태 업데이트
    _user = updatedUser;
    notifyListeners();
  }

  // --------------------------------------------------
  // 5) 공통 저장 로직
  //    로그인/회원가입 성공 시: 토큰 + 유저 정보를
  //    SharedPreferences + Provider 상태에 반영
  // --------------------------------------------------
  Future<void> _saveAuth(AuthResponse auth) async {
    final prefs = await SharedPreferences.getInstance();

    // 1) 토큰 저장
    await prefs.setString('access_token', auth.accessToken);
    await prefs.setString('refresh_token', auth.refreshToken);

    // 2) 유저 정보 저장
    await prefs.setString('user_id', auth.user.id);
    await prefs.setString('user_name', auth.user.name);
    await prefs.setString('user_email', auth.user.email);

    // 3) Provider 상태에 반영
    _user = auth.user;
    notifyListeners();
  }

  // --------------------------------------------------
  // 6) access token 재발급
  //    POST /auth/refresh
  // --------------------------------------------------
  Future<void> refreshAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    final refreshToken = prefs.getString('refresh_token');
    if (refreshToken == null) return;

    final res = await ApiClient.I.post(
      "/auth/refresh",
      body: jsonEncode({
        "refresh_token": refreshToken,
      }),
      // refresh 요청은 Authorization 헤더 필요 없음
    );

    final Map<String, dynamic> json = jsonDecode(res.body);
    final refresh = RefreshResponse.fromJson(json); // ✅ 모델 사용

    if (refresh.accessToken.isNotEmpty) {
      await prefs.setString('access_token', refresh.accessToken);
    }
  }

  // --------------------------------------------------
  // 7) 로그아웃
  // --------------------------------------------------
  Future<void> signOut() async {
    final prefs = await SharedPreferences.getInstance();

    // 로그인 관련 키만 삭제 (앱 전체 설정은 유지)
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
    await prefs.remove('user_id');
    await prefs.remove('user_name');
    await prefs.remove('user_email');

    _user = null;
    notifyListeners();
  }
}
