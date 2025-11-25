import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../screens/home_screen.dart';
import '../providers/auth_provider.dart';
import '../providers/recent_perfume_provider.dart';
import '../providers/calendar_provider.dart';
import '../providers/wishlist_provider.dart';
import '../providers/purchased_provider.dart';

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
    // 1) 유저 정보 로드 (SharedPreferences)
    await context.read<AuthProvider>().loadFromStorage();
    final auth = context.read<AuthProvider>();
    final user = auth.user;

    // 2) 최근 본 향수 (API)
    await context.read<RecentPerfumeProvider>().fetchRecent();

    // 3) 캘린더 로컬 저장된 데이터 불러오기
    final calendar = context.read<CalendarProvider>();
    calendar.setUser(user);
    await calendar.loadFromStorage();

    // 4) 로그인 되어 있을 때만 위시리스트 / 구매향수 로드
    if (user != null) {
      await context.read<WishlistProvider>().fetchWishlist();
      await context.read<PurchasedProvider>().fetchPurchased();
    }

    // 5) 로딩 딜레이 후 홈 이동
    Timer(const Duration(seconds: 5), () {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const HomeScreen()),
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
