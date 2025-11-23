import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/auth_provider.dart';
import '../../providers/pbti_provider.dart';
import 'pbti_result_screen.dart';
import 'pbti_intro_screen.dart';

class PBTILoadingScreen extends StatefulWidget {
  /// [{ "question_id": 1, "choice": 5 }, ...]
  final List<Map<String, int>> answers;

  const PBTILoadingScreen({super.key, required this.answers});

  @override
  State<PBTILoadingScreen> createState() => _PBTILoadingScreenState();
}

class _PBTILoadingScreenState extends State<PBTILoadingScreen> {
  @override
  void initState() {
    super.initState();
    _submit();
  }

  Future<void> _submit() async {
    final auth = context.read<AuthProvider>();
    final pbti = context.read<PbtiProvider>();

    if (!auth.isLoggedIn) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('로그인 후 테스트를 진행할 수 있습니다.')),
      );
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const PBTIIntroScreen()),
      );
      return;
    }

    try {
      final result = await pbti.submitPbti(auth, widget.answers);

      if (!mounted) return;
      // 성공하면 결과 화면으로
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => PBTIResultScreen(result: result),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('PBTI 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'),
        ),
      );
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const PBTIIntroScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 60,
              height: 60,
              child: CircularProgressIndicator(
                color: Color(0xFF384C3B),
                strokeWidth: 5,
              ),
            ),
            SizedBox(height: 30),
            Text(
              '당신의 향을 분석 중이에요...',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w500,
                color: Colors.black87,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
