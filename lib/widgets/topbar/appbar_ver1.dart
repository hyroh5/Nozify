import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart'; // 마우스 스크롤 대응

class AppBarVer1 extends StatefulWidget implements PreferredSizeWidget {
  const AppBarVer1({super.key});

  @override
  Size get preferredSize => const Size.fromHeight(110); // 약간 줄임

  @override
  State<AppBarVer1> createState() => _AppBarVer1State();
}

class _AppBarVer1State extends State<AppBarVer1> {
  final TextEditingController searchController = TextEditingController();

  void _onSearch(String query) {
    if (query.trim().isEmpty) return;
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.grey.withOpacity(0.3),
              offset: const Offset(0, 2),
              blurRadius: 6,
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 🔹 로고 + 메뉴
            Container(
              color: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              // ↑ 기존 10 → 6 으로 축소
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Image.asset(
                    'assets/images/appbar_logo.png',
                    height: 26,
                    fit: BoxFit.contain,
                  ),
                  Builder(
                    builder: (innerContext) => IconButton(
                      icon: const Icon(Icons.menu, color: Colors.black),
                      onPressed: () =>
                          Scaffold.of(innerContext).openEndDrawer(),
                    ),
                  ),
                ],
              ),
            ),

            // 🔹 검색창
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 0),
              child: Transform.translate(
                offset: const Offset(0, -6), // 🔼 검색창을 위로 6px 올림 (음수 padding X)
                child: TextField(
                  controller: searchController,
                  onSubmitted: _onSearch,
                  decoration: InputDecoration(
                    prefixIcon: const Icon(Icons.search, color: Colors.grey),
                    hintText: '향수 이름, 브랜드 검색',
                    hintStyle: const TextStyle(color: Colors.grey),
                    filled: true,
                    fillColor: Colors.grey[100],
                    contentPadding: const EdgeInsets.symmetric(
                      vertical: 0,
                      horizontal: 12,
                    ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide.none,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
