// auth—provider。dart
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthUser {
  final String name;
  final String email;

  const AuthUser({required this.name, required this.email});

  Map<String, String> toMap() => {'name': name, 'email': email};
}

class AuthProvider with ChangeNotifier {
  AuthUser? _user;

  AuthUser? get user => _user;
  bool get isLoggedIn => _user != null;

  Future<void> loadFromStorage() async {
    final prefs = await SharedPreferences.getInstance();
    final name = prefs.getString('user_name');
    final email = prefs.getString('user_email');
    if (name != null && email != null) {
      _user = AuthUser(name: name, email: email);
      notifyListeners();
    }
  }

  Future<void> signIn(String email, String password) async {
    final prefs = await SharedPreferences.getInstance();
    final savedEmail = prefs.getString('user_email');
    final savedPw = prefs.getString('user_password');
    final savedName = prefs.getString('user_name');

    if (savedEmail == email && savedPw == password && savedName != null) {
      _user = AuthUser(name: savedName, email: email);
      await prefs.setBool('isLoggedIn', true);
      notifyListeners();
    } else {
      throw Exception('로그인 정보가 일치하지 않습니다.');
    }
  }

  Future<void> signUp(String name, String email, String password) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_name', name);
    await prefs.setString('user_email', email);
    await prefs.setString('user_password', password);
    await prefs.setBool('isLoggedIn', true);
    _user = AuthUser(name: name, email: email);
    notifyListeners();
  }

  Future<void> updateUser(String name, String email, String password) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_name', name);
    await prefs.setString('user_email', email);
    await prefs.setString('user_password', password);
    _user = AuthUser(name: name, email: email);
    notifyListeners();
  }

  Future<void> signOut() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('isLoggedIn');
    _user = null;
    notifyListeners();
  }
}
