import 'package:flutter/material.dart';

import '../../providers/pbti_provider.dart';
import '../../widgets/topbar/appbar_ver2.dart';
import '../../widgets/bottom_navbar.dart';
import '../../widgets/custom_drawer.dart';
import '../home_screen.dart';
import 'pbti_main_screen.dart';

class PBTIResultScreen extends StatefulWidget {
  final PbtiResultModel result;

  const PBTIResultScreen({super.key, required this.result});

  @override
  State<PBTIResultScreen> createState() => _PBTIResultScreenState();
}

class _PBTIResultScreenState extends State<PBTIResultScreen> {
  int _selectedIndex = 1;

  @override
  Widget build(BuildContext context) {
    final result = widget.result;
    final String pbtiCode = result.finalType;

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
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 6),
              Center(
                child: Column(
                  children: [
                    const Text(
                      'PBTI 결과 분석이 완료되었습니다!',
                      textAlign: TextAlign.center,
                      style:
                      TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      pbtiCode,
                      style: const TextStyle(
                        fontSize: 48,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF384C3B),
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      '당신의 향수 성향 코드',
                      style: TextStyle(color: Colors.grey),
                    ),
                    const SizedBox(height: 30),
                    ElevatedButton(
                      onPressed: () {
                        // 이미 서버에 저장된 상태이므로, 그냥 메인으로 이동
                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const PbtiMainScreen(),
                          ),
                        );
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.black,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(30),
                        ),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 40, vertical: 12),
                      ),
                      child: const Text(
                        '결과 저장 및 보기',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 26),
              Column(
                children: [
                  _buildAxisBar('온도', result.temperatureScore.toDouble()),
                  _buildAxisBar('질감', result.textureScore.toDouble()),
                  _buildAxisBar('무드', result.moodScore.toDouble()),
                  _buildAxisBar('자연성', result.natureScore.toDouble()),
                ],
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: BottomNavBar(
        currentIndex: _selectedIndex,
        onTap: (index) {
          setState(() => _selectedIndex = index);
          if (index == 0) {
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (_) => const HomeScreen()),
            );
          }
        },
      ),
    );
  }

  /// 서버 점수는 0~100이므로 그대로 퍼센트로 사용
  Widget _buildAxisBar(String axis, double score) {
    double leftPercent = (score / 100).clamp(0.0, 1.0);
    double rightPercent = 1 - leftPercent;

    String leftLabel = _leftSide(axis);
    String rightLabel = _rightSide(axis);

    Color leftColor;
    Color rightColor;
    switch (axis) {
      case '온도':
        leftColor = const Color(0xFF00FFC8);
        rightColor = const Color(0xFFF94C46);
        break;
      case '질감':
        leftColor = const Color(0xFFF2FF00);
        rightColor = const Color(0xFF5842FE);
        break;
      case '무드':
        leftColor = const Color(0xFFFF007B);
        rightColor = const Color(0xFF843032);
        break;
      case '자연성':
        leftColor = const Color(0xFFA6FF00);
        rightColor = const Color(0xFF7C00C3);
        break;
      default:
        leftColor = Colors.grey;
        rightColor = Colors.grey;
    }

    bool isLeftDominant = leftPercent >= 0.5;
    Color activeColor = isLeftDominant ? leftColor : rightColor;
    Color leftTextColor = isLeftDominant ? leftColor : Colors.grey;
    Color rightTextColor = isLeftDominant ? Colors.grey : rightColor;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(axis,
              style:
              const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          Stack(
            children: [
              Container(
                height: 14,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              Align(
                alignment: isLeftDominant
                    ? Alignment.centerLeft
                    : Alignment.centerRight,
                child: FractionallySizedBox(
                  widthFactor:
                  isLeftDominant ? leftPercent : rightPercent,
                  alignment: isLeftDominant
                      ? Alignment.centerLeft
                      : Alignment.centerRight,
                  child: Container(
                    height: 14,
                    decoration: BoxDecoration(
                      color: activeColor,
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${(leftPercent * 100).round()}% $leftLabel',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: leftTextColor,
                ),
              ),
              Text(
                '${(rightPercent * 100).round()}% $rightLabel',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: rightTextColor,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _leftSide(String axis) {
    switch (axis) {
      case '온도':
        return 'Fresh';
      case '질감':
        return 'Light';
      case '무드':
        return 'Sweet';
      case '자연성':
        return 'Natural';
      default:
        return '';
    }
  }

  String _rightSide(String axis) {
    switch (axis) {
      case '온도':
        return 'Warm';
      case '질감':
        return 'Heavy';
      case '무드':
        return 'Spicy';
      case '자연성':
        return 'Modern';
      default:
        return '';
    }
  }
}
