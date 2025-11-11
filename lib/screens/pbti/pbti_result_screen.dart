import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../providers/auth_provider.dart';
import '../../providers/pbti_provider.dart';
import '../../widgets/topbar/appbar_ver2.dart';
import '../../widgets/bottom_navbar.dart';
import '../../widgets/custom_drawer.dart';
import '../home_screen.dart';
import 'pbti_main_screen.dart';

class PBTIResultScreen extends StatefulWidget {
  final Map<String, double>? result;

  const PBTIResultScreen({super.key, this.result});

  @override
  State<PBTIResultScreen> createState() => _PBTIResultScreenState();
}

class _PBTIResultScreenState extends State<PBTIResultScreen> {
  int _selectedIndex = 1;

  @override
  Widget build(BuildContext context) {
    final result = widget.result;
    final String pbtiCode = result != null ? _generatePbtiCode(result) : "----";

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
                      onPressed: () async {
                        if (result == null) return;
                        await _saveResultAndNavigate(pbtiCode);
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
                            fontWeight: FontWeight.w500),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 26),
              if (result != null)
                Column(
                  children: [
                    _buildAxisBar('온도', result['온도']!),
                    _buildAxisBar('질감', result['질감']!),
                    _buildAxisBar('무드', result['무드']!),
                    _buildAxisBar('자연성', result['자연성']!),
                  ],
                )
              else
                const Center(child: Text('결과 데이터를 불러올 수 없습니다.')),
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

  Future<void> _saveResultAndNavigate(String pbtiCode) async {
    final auth = context.read<AuthProvider>();
    final pbtiProvider = context.read<PbtiProvider>();
    final imagePath = getPbtiImage(pbtiCode);

    // 로그인 안 되어 있으면 저장 막기
    if (!auth.isLoggedIn) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("로그인 후 결과를 저장할 수 있습니다.")),
      );
      return;
    }

    await pbtiProvider.addResult(auth, pbtiCode, imagePath);

    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const PbtiMainScreen()),
    );
  }

  // 아래 부분은 전부 기존 그대로
  String getPbtiImage(String code) {
    const base = 'assets/images/PBTI';
    switch (code) {
      case 'FHPM':
        return '$base/FHPM.png';
      case 'FHPN':
        return '$base/FHPN.png';
      case 'FHSM':
        return '$base/FHSM.png';
      case 'FHSN':
        return '$base/FHSN.png';
      case 'FLPM':
        return '$base/FLPM.png';
      case 'FLPN':
        return '$base/FLPN.png';
      case 'FLSM':
        return '$base/FLSM.png';
      case 'FLSN':
        return '$base/FLSN.png';
      case 'WHPM':
        return '$base/WHPM.png';
      case 'WHPN':
        return '$base/WHPN.png';
      case 'WHSM':
        return '$base/WHSM.png';
      case 'WHSN':
        return '$base/WHSN.png';
      case 'WLPM':
        return '$base/WLPM.png';
      case 'WLPN':
        return '$base/WLPN.png';
      case 'WLSM':
        return '$base/WLSM.png';
      case 'WLSN':
        return '$base/WLSN.png';
      default:
        return '$base/FLSN.png';
    }
  }

  String _generatePbtiCode(Map<String, double> result) {
    String temp = result['온도']! >= 3 ? 'F' : 'W';
    String texture = result['질감']! >= 3 ? 'L' : 'H';
    String mood = result['무드']! >= 3 ? 'S' : 'P';
    String natural = result['자연성']! >= 3 ? 'N' : 'M';
    return '$temp$texture$mood$natural';
  }

  Widget _buildAxisBar(String axis, double score) {
    double leftPercent = ((score - 1) / 4).clamp(0.0, 1.0);
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
              widthFactor: isLeftDominant ? leftPercent : rightPercent,
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
