import 'dart:async';
import 'package:flutter/material.dart';
import 'pbti_result_screen.dart';

class PBTILoadingScreen extends StatefulWidget {
  final Map<String, double> result; // 결과를 받는 필드

  const PBTILoadingScreen({super.key, required this.result});

  @override
  State<PBTILoadingScreen> createState() => _PBTILoadingScreenState();
}

class _PBTILoadingScreenState extends State<PBTILoadingScreen> {
  @override
  void initState() {
    super.initState();
    // 3초 후 결과 페이지로 이동하면서 동일 result 전달
    Timer(const Duration(seconds: 3), () {
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => PBTIResultScreen(result: widget.result),
          // 전달 (question -> loading -> result 순으로 결과가 전달됨)
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // 회전 로딩 인디케이터
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
