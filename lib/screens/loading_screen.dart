import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../screens/home_screen.dart';
import '../providers/auth_provider.dart';
import '../providers/recent_perfume_provider.dart';
import '../providers/calendar_provider.dart';

class LoadingScreen extends StatefulWidget {
  const LoadingScreen({super.key});

  @override
  State<LoadingScreen> createState() => _LoadingScreenState();
}

class _LoadingScreenState extends State<LoadingScreen> {
  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    // ✅ Auth & Recent Load
    await context.read<AuthProvider>().loadFromStorage();
    await context.read<RecentPerfumeProvider>().loadRecent();

    // ✅ CalendarProvider에 로그인 유저 반영
    final auth = context.read<AuthProvider>();
    final calendar = context.read<CalendarProvider>();
    calendar.setUser(auth.user);
    await calendar.loadFromStorage();

    // ✅ 기존 5초 대기 후 홈 이동
    Timer(const Duration(seconds: 5), () {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const HomeScreen()),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Image.asset(
          'assets/images/loading_logo.png',
          width: 100,
        ),
      ),
    );
  }
}
