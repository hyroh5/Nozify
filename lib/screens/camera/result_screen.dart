import 'dart:io';
import 'package:flutter/material.dart';
import '../../widgets/topbar/appbar_ver2.dart';
import '../../widgets/custom_drawer.dart';
import '../perfume_detail_screen.dart';
import '../home_screen.dart';

class ResultScreen extends StatefulWidget {
  final String imagePath;

  const ResultScreen({super.key, required this.imagePath});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<Map<String, String>> dummyResults = [
    {
      'id': 'dummy001',
      "brand": "브랜드 001",
      "name": "향수 이름 001",
      "image": "assets/images/dummy.jpg"
    },
    {
      'id': 'dummy002',
      "brand": "브랜드 002",
      "name": "향수 이름 002",
      "image": "assets/images/dummy.jpg"
    },
    {
      'id': 'dummy003',
      "brand": "브랜드 003",
      "name": "향수 이름 003",
      "image": "assets/images/dummy.jpg"
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFBFBFBF),
      appBar: AppBarVer2(
        backgroundColor: Colors.transparent,
        iconColor: Colors.white,
        onBack: () => Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const HomeScreen()),
        ),
      ),
      endDrawer: const CustomDrawer(),
      body: Padding(
        padding: const EdgeInsets.symmetric(vertical: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const SizedBox(height: 20),
            Text(
              '${dummyResults.length}개의 연관 상품이 검색되었습니다',
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),

            // 🔁 카드 슬라이더
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                itemCount: dummyResults.length,
                onPageChanged: (i) => setState(() => _currentPage = i),
                itemBuilder: (context, index) {
                  final perfume = dummyResults[index];

                  return Center(
                    child: SizedBox(
                      width: 280,
                      height: 520,
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(20),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.1),
                              blurRadius: 8,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Image.asset(
                              perfume["image"]!,
                              height: 210,
                              fit: BoxFit.contain,
                            ),
                            const SizedBox(height: 20),
                            Text(
                              perfume["brand"]!,
                              style: const TextStyle(
                                fontSize: 10,
                                color: Colors.grey,
                              ),
                            ),
                            Text(
                              perfume["name"]!,
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 60),

                            // 🔥 수정된 부분: perfumeId 전달
                            ElevatedButton(
                              onPressed: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => PerfumeDetailScreen(
                                      perfumeId: perfume['id']!,
                                      fromStorage: false,
                                    ),
                                  ),
                                );
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.black,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(30),
                                ),
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 80,
                                  vertical: 12,
                                ),
                              ),
                              child: const Text(
                                '제품 보기',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),

            const SizedBox(height: 16),

            // ⭕ 페이지 인디케이터
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                dummyResults.length,
                    (i) => AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: _currentPage == i ? 10 : 6,
                  height: 6,
                  decoration: BoxDecoration(
                    color: _currentPage == i
                        ? Colors.white
                        : const Color(0xFFFFFFFF).withOpacity(0.4),
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
