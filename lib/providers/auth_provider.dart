import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_client.dart';

class AuthUser {
  final String id;
  final String name;
  final String email;

  const AuthUser({
    required this.id,
    required this.name,
    required this.email,
  });
}

class AuthProvider with ChangeNotifier {
  AuthUser? _user;
  AuthUser? get user => _user;
  bool get isLoggedIn => _user != null;

  // ------------------ 자동 로그인 ------------------
  Future<void> loadFromStorage() async {
    final prefs = await SharedPreferences.getInstance();
    final id = prefs.getString('user_id');
    final name = prefs.getString('user_name');
    final email = prefs.getString('user_email');
    if (id != null && name != null && email != null) {
      _user = AuthUser(id: id, name: name, email: email);
      notifyListeners();
    }
  }

  // ------------------ 로그인 ------------------
  Future<void> signIn(String email, String password) async {
    final res = await ApiClient.I.post(
      "/auth/login",
      body: jsonEncode({"email": email, "password": password}),
    );
    final data = jsonDecode(res.body);
    await _saveAuth(data);
  }

  // ------------------ 회원가입 ------------------
  Future<void> signUp(String name, String email, String password) async {
    final res = await ApiClient.I.post(
      "/auth/signup",
      body: jsonEncode({"name": name, "email": email, "password": password}),
    );
    final data = jsonDecode(res.body);
    await _saveAuth(data);
  }

  // ------------------ updateUser 추가 (중요!) ------------------
  Future<void> updateUser({
    required String name,
    required String email,
    required String password,
  }) async {
    final body = jsonEncode({
      "name": name,
      "email": email,
      "password": password.isEmpty ? null : password, // 비번변경 안 하면 null
    });

    final res = await ApiClient.I.put(
      "/user/me",
      body: body,
      auth: true,
    );

    final data = jsonDecode(res.body);

    // SharedPreferences 업데이트
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_name', data['name']);
    await prefs.setString('user_email', data['email']);
    await prefs.setString('user_id', data['id']);

    // Provider 상태 업데이트
    _user = AuthUser(
      id: data['id'],
      name: data['name'],
      email: data['email'],
    );

    notifyListeners();
  }

  // ------------------ 공통 저장 로직 ------------------
  Future<void> _saveAuth(Map<String, dynamic> data) async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.setString('access_token', data['access_token']);
    await prefs.setString('refresh_token', data['refresh_token']);

    await prefs.setString('user_id', data['user']['id']);
    await prefs.setString('user_name', data['user']['name']);
    await prefs.setString('user_email', data['user']['email']);

    _user = AuthUser(
      id: data['user']['id'],
      name: data['user']['name'],
      email: data['user']['email'],
    );

    notifyListeners();
  }

  // ------------------ 로그아웃 ------------------
  Future<void> signOut() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    _user = null;
    notifyListeners();
  }
}
