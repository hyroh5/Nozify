// lib/screens/camera/camera_screen.dart
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
  bool _isPreviewOff = false;
  bool _isDisposed = false;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  @override
  void dispose() {
    _isDisposed = true;
    _controller?.dispose();
    super.dispose();
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

    if (_controller == null ||
        !_controller!.value.isInitialized ||
        _isCapturing) return;

    if (_isDisposed) return;

    setState(() => _isCapturing = true);

    try {
      final image = await _controller!.takePicture();

      // 1) Preview 완전 제거
      if (mounted) {
        setState(() {
          _isPreviewOff = true;
        });
      }

      // 2) LG 기기 안정화 딜레이
      await Future.delayed(const Duration(milliseconds: 250));

      // 여기서 이미 화면이 dispose됐을 수도 있음 → 반드시 체크
      if (!mounted) return;

      // 3) 안전하게 화면 이동
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return; // 이중 체크
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => CameraLoadingScreen(imagePath: image.path),
          ),
        );
      });

    } catch (e) {
      debugPrint("Capture error: $e");
    } finally {
      if (mounted) {
        setState(() => _isCapturing = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: _isInitialized
          ? Stack(
        children: [
          // FULL SCREEN CAMERA
          Positioned.fill(
            child: _isPreviewOff
                ? Container(color: Colors.black)
                : FittedBox(
              fit: BoxFit.cover,
              child: SizedBox(
                width: _controller!.value.previewSize!.height,
                height: _controller!.value.previewSize!.width,
                child: CameraPreview(_controller!),
              ),
            ),
          ),

          // 뒤로가기 버튼
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

          // 가이드 박스
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

          // 안내 문구
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

          // 촬영 버튼
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

