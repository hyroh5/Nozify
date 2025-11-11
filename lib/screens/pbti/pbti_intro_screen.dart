import 'package:flutter/material.dart';
import '../../widgets/topbar/appbar_ver2.dart';
import '../../widgets/custom_drawer.dart';
import 'pbti_question_screen.dart';
import '../home_screen.dart';

class PBTIIntroScreen extends StatefulWidget {
  const PBTIIntroScreen({super.key});

  @override
  State<PBTIIntroScreen> createState() => _PBTIIntroScreenState();
}

class _PBTIIntroScreenState extends State<PBTIIntroScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<Map<String, String>> _pages = [
    {
      'title': '복잡하고 어려운 \n향수의 세계',
      'subtitle': '',
    },
    {
      'title': '내게 맞는 향수를 \n찾고 싶으신가요?',
      'subtitle': '',
    },
    {
      'title': '이제 향기 취향 테스트를\n시작해볼까요?',
      'subtitle': '몇 가지 질문으로 당신의 향기 성향을 알아봐요',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBarVer2(
        onBack: () {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const HomeScreen()),
          );
        },
      ),
      endDrawer: const CustomDrawer(),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (index) {
                  setState(() => _currentPage = index);
                },
                itemCount: _pages.length,
                itemBuilder: (context, index) {
                  final page = _pages[index];
                  return Padding(
                    padding:
                    const EdgeInsets.symmetric(vertical: 140, horizontal: 30),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          page['title']!,
                          style: const TextStyle(
                            fontSize: 26,
                            fontWeight: FontWeight.w900,
                            height: 1.3,
                          ),
                        ),
                        if (page['subtitle']!.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          Text(
                            page['subtitle']!,
                            style: const TextStyle(
                              fontSize: 15,
                              color: Colors.black54,
                              height: 1.5,
                            ),
                          ),
                        ],
                      ],
                    ),
                  );
                },
              ),
            ),

            // 🔵 페이지 인디케이터
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(_pages.length, (i) => _dot(i == _currentPage)),
            ),
            const SizedBox(height: 24),

            // 마지막 페이지에만 "시작하기" 버튼 표시
            if (_currentPage == _pages.length - 1)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 30),
                child: SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(builder: (_) => PBTIQuestionScreen()),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF384C3B),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                    child: const Text(
                      '시작하기',
                      style: TextStyle(color: Colors.white, fontSize: 16),
                    ),
                  ),
                ),
              ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _dot(bool active) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 250),
      width: active ? 10 : 8,
      height: active ? 10 : 8,
      margin: const EdgeInsets.symmetric(horizontal: 4),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: active ? Color(0xFF384C3B) : Colors.grey.shade300,
      ),
    );
  }
}
