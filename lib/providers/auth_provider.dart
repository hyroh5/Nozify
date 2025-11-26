// lib/providers/auth_provider.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_client.dart';
import '../models/user.dart';
import '../models/auth_response.dart';
import '../models/refresh_token.dart';

class AuthProvider with ChangeNotifier {
  User? _user;

  User? get user => _user;
  bool get isLoggedIn => _user != null;

  // --------------------------------------------------
  // 🔥 추가된 플래그: 로딩 완료 여부
  // --------------------------------------------------
  bool _isLoaded = false;
  bool get isLoaded => _isLoaded;

  // --------------------------------------------------
  // 🔥 추가된 함수: 완료될 때까지 기다림
  // --------------------------------------------------
  Future<void> waitUntilLoaded() async {
    while (!_isLoaded) {
      await Future.delayed(const Duration(milliseconds: 50));
    }
  }

  // --------------------------------------------------
  // 1) 앱 시작 시 자동 로그인 복구
  // --------------------------------------------------
  Future<void> loadFromStorage() async {
    final prefs = await SharedPreferences.getInstance();

    final accessToken = prefs.getString('access_token');
    if (accessToken == null) {
      _isLoaded = true;       // 🔥 로그인 안 된 상태도 로딩 완료로 처리
      notifyListeners();
      return;
    }

    final id = prefs.getString('user_id');
    final name = prefs.getString('user_name');
    final email = prefs.getString('user_email');

    if (id != null && name != null && email != null) {
      _user = User(id: id, name: name, email: email);
    }

    // 🔥 loadFromStorage() 끝 → 로딩 완료
    _isLoaded = true;
    notifyListeners();
  }

  // --------------------------------------------------
  // 2) 로그인
  // --------------------------------------------------
  Future<void> signIn(String email, String password) async {
    final res = await ApiClient.I.post(
      "/auth/login",
      body: jsonEncode({"email": email, "password": password}),
    );

    final json = jsonDecode(res.body);
    final auth = AuthResponse.fromJson(json);

    await _saveAuth(auth);

    // 로그인 완료 → 로딩 완료
    _isLoaded = true;
    notifyListeners();
  }

  // --------------------------------------------------
  // 3) 회원가입
  // --------------------------------------------------
  Future<void> signUp(String name, String email, String password) async {
    final res = await ApiClient.I.post(
      "/auth/signup",
      body: jsonEncode({"name": name, "email": email, "password": password}),
    );

    final json = jsonDecode(res.body);
    final auth = AuthResponse.fromJson(json);

    await _saveAuth(auth);

    // 회원가입 완료 → 로딩 완료
    _isLoaded = true;
    notifyListeners();
  }

  // --------------------------------------------------
  // 4) 프로필 수정
  // --------------------------------------------------
  Future<void> updateUser({
    String? name,
    String? email,
  }) async {
    final body = <String, dynamic>{};
    if (name != null && name.isNotEmpty) body['name'] = name;
    if (email != null && email.isNotEmpty) body['email'] = email;

    if (body.isEmpty) return;

    final res = await ApiClient.I.put(
      "/auth/update-profile",
      body: jsonEncode(body),
      auth: true,
    );

    final json = jsonDecode(res.body);
    final updatedUser = User.fromJson(json);

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_id', updatedUser.id);
    await prefs.setString('user_name', updatedUser.name);
    await prefs.setString('user_email', updatedUser.email);

    _user = updatedUser;
    notifyListeners();
  }

  // --------------------------------------------------
  // 5) 공통 저장 로직
  // --------------------------------------------------
  Future<void> _saveAuth(AuthResponse auth) async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.setString('access_token', auth.accessToken);
    await prefs.setString('refresh_token', auth.refreshToken);

    await prefs.setString('user_id', auth.user.id);
    await prefs.setString('user_name', auth.user.name);
    await prefs.setString('user_email', auth.user.email);

    _user = auth.user;
    notifyListeners();
  }

  // --------------------------------------------------
  // 6) access token 재발급
  // --------------------------------------------------
  Future<void> refreshAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    final refreshToken = prefs.getString('refresh_token');
    if (refreshToken == null) return;

    final res = await ApiClient.I.post(
      "/auth/refresh",
      body: jsonEncode({"refresh_token": refreshToken}),
    );

    final json = jsonDecode(res.body);
    final refresh = RefreshResponse.fromJson(json);

    if (refresh.accessToken.isNotEmpty) {
      await prefs.setString('access_token', refresh.accessToken);
    }
  }

  // --------------------------------------------------
  // 7) 로그아웃
  // --------------------------------------------------
  Future<void> signOut() async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
    await prefs.remove('user_id');
    await prefs.remove('user_name');
    await prefs.remove('user_email');

    _user = null;

    // 로그아웃 시에도 상태는 로딩 완료
    _isLoaded = true;

    notifyListeners();
  }
}
