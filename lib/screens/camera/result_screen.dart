// lib/screens/camera/result_screen.dart
import 'package:flutter/material.dart';
import '../../widgets/topbar/appbar_ver2.dart';
import '../../widgets/custom_drawer.dart';
import '../perfume_detail_screen.dart';
import '../home_screen.dart';

class ResultScreen extends StatefulWidget {
  final String imagePath;
  final List<Map<String, dynamic>> candidates;  // 🔥 추가

  const ResultScreen({
    super.key,
    required this.imagePath,
    required this.candidates,
  });

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  @override
  Widget build(BuildContext context) {
    final results = widget.candidates;
    final resultCount = results.length;

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
              resultCount > 0
                  ? '$resultCount개의 연관 상품이 검색되었습니다'
                  : '연관 상품을 찾지 못했어요',
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),

            // 🔁 카드 슬라이더
            Expanded(
              child: resultCount > 0
                  ? PageView.builder(
                controller: _pageController,
                itemCount: resultCount,
                onPageChanged: (i) => setState(() => _currentPage = i),
                itemBuilder: (context, index) {
                  final perfume = results[index];

                  final brand = perfume['brand']?.toString() ?? '';
                  final name = perfume['product']?.toString() ?? '';
                  final perfumeId =
                      perfume['product_id']?.toString() ?? '';

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
                            // 일단 썸네일은 더미 이미지로
                            Image.asset(
                              'assets/images/dummy.jpg',
                              height: 210,
                              fit: BoxFit.contain,
                            ),
                            const SizedBox(height: 20),
                            Text(
                              brand,
                              style: const TextStyle(
                                fontSize: 10,
                                color: Colors.grey,
                              ),
                            ),
                            Text(
                              name,
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 60),

                            ElevatedButton(
                              onPressed: () {
                                // product_id를 그대로 PerfumeDetailScreen에 넘김
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => PerfumeDetailScreen(
                                      perfumeId: perfumeId,
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
              )
                  : const Center(
                child: Text(
                  '다른 각도에서 다시 촬영해볼까요?',
                  style: TextStyle(
                    color: Colors.black87,
                    fontSize: 14,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 16),

            // ⭕ 페이지 인디케이터
            if (resultCount > 0)
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(
                  resultCount,
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

