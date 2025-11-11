import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import '../home_screen.dart';
import 'camera_loading_screen.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  CameraController? _controller;
  bool _isInitialized = false;
  bool _isCapturing = false;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      final firstCamera = cameras.first;

      _controller = CameraController(
        firstCamera,
        ResolutionPreset.medium,
        enableAudio: false,
      );

      await _controller!.initialize();
      if (!mounted) return;

      setState(() => _isInitialized = true);
    } catch (e) {
      debugPrint("Camera init error: $e");
    }
  }

  Future<void> _captureImage() async {
    if (_controller == null || !_controller!.value.isInitialized || _isCapturing) return;

    setState(() => _isCapturing = true);

    try {
      await _controller!.stopImageStream().catchError((_) {});
      final image = await _controller!.takePicture();

      await _controller!.dispose();
      _controller = null;

      if (!mounted) return;

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => CameraLoadingScreen(imagePath: image.path),
        ),
      );
    } catch (e) {
      debugPrint("Capture error: $e");
    } finally {
      _isCapturing = false;
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    _controller = null;
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: _isInitialized
          ? Stack(
        fit: StackFit.expand,
        children: [
          // ✅ 카메라 미리보기
          CameraPreview(_controller!),

          // ✅ 상단 뒤로가기 버튼
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.only(left: 8.0, top: 8.0),
              child: Align(
                alignment: Alignment.topLeft,
                child: IconButton(
                  icon: const Icon(Icons.arrow_back, color: Colors.white, size: 24),
                  onPressed: () => Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(builder: (_) => const HomeScreen()),
                  ),
                ),
              ),
            ),
          ),

          // ✅ 중앙 흰색 네모 가이드라인
          Align(
            alignment: Alignment.center,
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.white, width: 2),
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          ),

          // ✅ 안내 문구
          Positioned(
            top: 200,
            left: 0,
            right: 0,
            child: Center(
              child: Text(
                "박스 안에 제품을 위치시켜주세요",
                style: TextStyle(
                  color: Colors.white.withOpacity(0.9),
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),

          // ✅ 하단 촬영 버튼
          Positioned(
            bottom: 60,
            left: 0,
            right: 0,
            child: Center(
              child: GestureDetector(
                onTap: _captureImage,
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 5),
                  ),
                  child: const Center(
                    child: Icon(Icons.circle, color: Colors.white, size: 70),
                  ),
                ),
              ),
            ),
          ),
        ],
      )
          : const Center(child: CircularProgressIndicator(color: Colors.white)),
    );
  }
}

