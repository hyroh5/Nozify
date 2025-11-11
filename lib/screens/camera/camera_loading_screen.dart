import 'package:flutter/material.dart';
import 'result_screen.dart';
import 'dart:async';

class CameraLoadingScreen extends StatefulWidget {
  final String imagePath; // 찍은 향수 사진의 경로 (나중에 이미지 분석 모델로 보내야 함)
  const CameraLoadingScreen({super.key, required this.imagePath});

  @override
  State<CameraLoadingScreen> createState() => _CameraLoadingScreenState();
}

class _CameraLoadingScreenState extends State<CameraLoadingScreen> {
  @override
  void initState() {
    super.initState();
    _navigateToResult();
  }

  Future<void> _navigateToResult() async {
    // 🔥 향수 분석 대기 (딜레이)
    await Future.delayed(const Duration(seconds: 3));

    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => ResultScreen(imagePath: widget.imagePath),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // 🌀 회전 애니메이션
            SizedBox(
              width: 60,
              height: 60,
              child: CircularProgressIndicator(
                strokeWidth: 5,
                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF384C3B)),
              ),
            ),
            const SizedBox(height: 30),

            // 🌿 텍스트
            const Text(
              '향수를 분석 중이에요...',
              style: TextStyle(
                color: Colors.black87,
                fontSize: 18,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
