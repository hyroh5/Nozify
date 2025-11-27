// pbti_question_screen.dart
import 'package:flutter/material.dart';
import '../../widgets/topbar/appbar_ver2.dart';
import '../../widgets/custom_drawer.dart';
import 'pbti_intro_screen.dart';
import 'pbti_loading_screen.dart';

class PBTIQuestionScreen extends StatefulWidget {
  const PBTIQuestionScreen({super.key});

  @override
  State<PBTIQuestionScreen> createState() => _PBTIQuestionScreenState();
}

class _PBTIQuestionScreenState extends State<PBTIQuestionScreen> {
  final List<String> questions = [
    // 온도 축 (Fresh ↔ Warm)
    '레몬·민트·바람 같은 상쾌한 느낌의 향이 특히 끌린다',
    '앰버·우드·레진처럼 따뜻하고 포근한 향이 더 만족스럽다',
    '비나 바다를 떠올리는 물기 있는 향이 좋다',
    '가을·겨울에 어울리는 따뜻한 무드의 향을 더 선호한다',
    '그린·허브의 시원하고 선명한 느낌이 마음에 든다',
    '스모키·스위트한 따뜻함이 느껴지는 향에 더 마음이 간다',

    // 질감 축 (Light ↔ Heavy)
    '가까이에서만 은은하게 느껴지는 가벼운 향이 좋다',
    '분사 후 존재감이 강하고 밀도 있는 향을 선호한다',
    '상쾌한 첫인상이 지속력보다 더 중요하다',
    '하루 종일 진한 잔향이 남아야 만족한다',
    '적게 뿌려도 부담 없는 가벼운 질감을 선호한다',
    '무게감과 깊이가 느껴지는 진한 질감이 매력적이다',

    // 무드 축 (Sweet ↔ Spicy)
    '바닐라·카라멜·초콜릿 같은 달콤한 향이 좋다',
    '후추·시나몬·카다멈 등 향신료의 톡 쏘는 느낌을 더 좋아한다',
    '복숭아·베리·사과 등 과일의 달큰함이 매력적이다',
    '달달한 향은 금방 물리는 편이다',
    '허브·생강 같은 드라이하고 깔끔한 스파이스 무드가 좋다',
    '디저트 숍을 연상시키는 포근한 단향이 편안하다',

    // 자연성 축 (Natural ↔ Modern)
    '숲·풀·흙처럼 자연의 냄새에 끌린다',
    '오존·레더·머스크 등 현대적·합성 느낌이 세련되게 느껴진다',
    '에센셜 오일 기반의 자연스러운 향을 선호한다',
    '세제/샤워젤 같은 깨끗한 합성 향을 특히 좋아한다',
    '전통적/자연주의 향취가 실험적 향보다 더 마음에 든다',
    '합성적이더라도 창의적이고 니치한 향이면 더 끌린다',
  ];

  // 각 질문의 선택값 (1~5)
  List<int?> answers = List.filled(24, null);

  @override
  Widget build(BuildContext context) {
    int answeredCount = answers.where((e) => e != null).length;
    double progress = answeredCount / questions.length;

    return Scaffold(
      appBar: AppBarVer2(
        onBack: () {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const PBTIIntroScreen()),
          );
        },
      ),
      endDrawer: const CustomDrawer(),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 진행 바
            LinearProgressIndicator(
              value: progress,
              backgroundColor: Colors.grey.shade300,
              color: const Color(0xFF384C3B),
              minHeight: 8,
              borderRadius: BorderRadius.circular(8),
            ),
            const SizedBox(height: 16),

            // 질문 목록
            Expanded(
              child: ListView.builder(
                itemCount: questions.length,
                itemBuilder: (context, index) => _buildQuestionCard(index),
              ),
            ),

            const SizedBox(height: 20),

            // “분석하기” 버튼
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: answeredCount == questions.length
                    ? () {
                  // 서버로 보낼 payload 준비
                  final payload = <Map<String, int>>[];
                  for (int i = 0; i < questions.length; i++) {
                    final choice = answers[i];
                    if (choice == null) continue;
                    payload.add({
                      "question_id": i + 1, // 서버 QUESTION_META와 맞추기
                      "choice": choice,
                    });
                  }

                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(
                      builder: (_) => PBTILoadingScreen(
                        answers: payload,
                      ),
                    ),
                  );
                }
                    : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF384C3B),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: const Text(
                  '분석하기',
                  style: TextStyle(color: Colors.white),
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }

  // 질문 카드 위젯
  Widget _buildQuestionCard(int index) {
    final question = questions[index];
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            question,
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: List.generate(5, (i) {
              final sizes = [34.0, 30.0, 25.0, 30.0, 34.0];
              double yOffset = (i == 1 || i == 2 || i == 3) ? -6 : 0;

              return Transform.translate(
                offset: Offset(0, yOffset),
                child: GestureDetector(
                  onTap: () => setState(() => answers[index] = i + 1),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: sizes[i],
                        height: sizes[i],
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.black),
                          color: answers[index] == i + 1
                              ? Colors.black
                              : Colors.white,
                        ),
                        child: answers[index] == i + 1
                            ? const Icon(Icons.check,
                            color: Colors.white, size: 16)
                            : null,
                      ),
                      if (i == 0)
                        const Padding(
                          padding: EdgeInsets.only(top: 4),
                          child: Text('그렇지 않다', style: TextStyle(fontSize: 10)),
                        ),
                      if (i == 4)
                        const Padding(
                          padding: EdgeInsets.only(top: 4),
                          child:
                          Text('그렇다', style: TextStyle(fontSize: 10)),
                        ),
                    ],
                  ),
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}
