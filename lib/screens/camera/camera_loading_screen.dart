// lib/screens/camera/camera_loading_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import '../../services/api_client.dart';
import 'result_screen.dart';
import 'camera_screen.dart'; // 🔥 추가

class CameraLoadingScreen extends StatefulWidget {
  final String imagePath;
  const CameraLoadingScreen({super.key, required this.imagePath});

  @override
  State<CameraLoadingScreen> createState() => _CameraLoadingScreenState();
}

class _CameraLoadingScreenState extends State<CameraLoadingScreen> {
  @override
  void initState() {
    super.initState();
    _sendImageAndNavigate();
  }

  Future<void> _sendImageAndNavigate() async {
    try {
      await Future.delayed(const Duration(milliseconds: 300));

      final res = await ApiClient.I.postMultipart(
        '/vision/scan',
        fileField: 'file',
        filePath: widget.imagePath,
        fields: {
          'request_id': 'mobile-${DateTime.now().millisecondsSinceEpoch}',
        },
        auth: false,
      );

      final body = jsonDecode(res.body) as Map<String, dynamic>;
      final match = body['match'] as Map<String, dynamic>?;
      final candidatesRaw = match?['candidates'] as List<dynamic>? ?? [];

      final candidates = candidatesRaw.whereType<Map<String, dynamic>>().toList();

      if (!mounted) return;

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => ResultScreen(
            imagePath: widget.imagePath,
            candidates: candidates,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('이미지 분석 중 오류가 발생했습니다. 다시 시도해주세요.'),
        ),
      );

      // ❌ Navigator.pop(context);  <-- 이거 지우고

      // ✅ 안전하게 다시 카메라 화면으로 교체
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => const CameraScreen(),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    // 기존 로딩 UI 그대로 사용
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 60,
              height: 60,
              child: CircularProgressIndicator(
                strokeWidth: 5,
                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF384C3B)),
              ),
            ),
            const SizedBox(height: 30),
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
