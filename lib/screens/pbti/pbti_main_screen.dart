import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:carousel_slider/carousel_slider.dart';

import '../../providers/auth_provider.dart';
import '../../providers/pbti_provider.dart';
import '../../widgets/topbar/appbar_ver2.dart';
import '../../widgets/bottom_navbar.dart';
import '../../widgets/custom_drawer.dart';
import '../home_screen.dart';
import 'pbti_intro_screen.dart';
import '../perfume_detail_screen.dart';

class PbtiMainScreen extends StatefulWidget {
  const PbtiMainScreen({super.key});

  @override
  State<PbtiMainScreen> createState() => _PbtiMainScreenState();
}

class _PbtiMainScreenState extends State<PbtiMainScreen> {
  int _currentPage = 0;
  int _selectedIndex = 2;

  /// 서버에서 받아온 PBTI 코드 리스트 (최신순)
  List<String> pbtiResults = [];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final auth = context.read<AuthProvider>();
      await context.read<PbtiProvider>().loadResults(auth);

      final providerResults = context.read<PbtiProvider>().results;
      setState(() => pbtiResults = providerResults);
    });
  }

  Future<void> _deleteType(int index) async {
    setState(() {
      pbtiResults.removeAt(index);
    });
  }

  @override
  Widget build(BuildContext context) {
    final totalCards = pbtiResults.length + 1;

    return Scaffold(
      appBar: AppBarVer2(
        onBack: () {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const HomeScreen()),
          );
        },
      ),
      backgroundColor: Colors.white,
      endDrawer: const CustomDrawer(),

      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Column(
            children: [
              const SizedBox(height: 20),

              // 🔹 캐릭터 캐러셀
              CarouselSlider.builder(
                itemCount: totalCards,
                options: CarouselOptions(
                  height: 360,
                  enlargeCenterPage: true,
                  viewportFraction: 0.38,
                  enableInfiniteScroll: false,
                  onPageChanged: (index, reason) {
                    setState(() => _currentPage = index);
                  },
                ),
                itemBuilder: (context, index, realIdx) {
                  final bool isAddCard = index == pbtiResults.length;
                  final bool isCenter = _currentPage == index;

                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 250),
                    curve: Curves.easeOut,
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(24),
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          if (!isAddCard)
                            Container(
                              color: Colors.white,
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  ImageFiltered(
                                    imageFilter: ImageFilter.blur(
                                      sigmaX: isCenter ? 0 : 5,
                                      sigmaY: isCenter ? 0 : 5,
                                    ),
                                    child: Image.asset(
                                      getPbtiImage(pbtiResults[index]),
                                      height: isCenter ? 150 : 120,
                                      fit: BoxFit.contain,
                                    ),
                                  ),
                                  if (isCenter) ...[
                                    const SizedBox(height: 16),
                                    Text(
                                      pbtiResults[index],
                                      style: const TextStyle(
                                        fontSize: 36,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    const Text(
                                      "당신의 향수 성향 코드",
                                      style: TextStyle(color: Colors.grey),
                                    ),
                                  ],
                                ],
                              ),
                            )
                          else
                            GestureDetector(
                              onTap: () => Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => const PBTIIntroScreen(),
                                ),
                              ),
                              child: Container(
                                color: Colors.white,
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Image.asset(
                                      "assets/images/PBTI/newPBTI.png",
                                      height: isCenter ? 150 : 120,
                                      fit: BoxFit.contain,
                                    ),
                                    if (isCenter) ...[
                                      const SizedBox(height: 16),
                                      const Text(
                                        "테스트하러 가기",
                                        style: TextStyle(
                                          fontSize: 20,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.black87,
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                            ),

                          if (!isAddCard && isCenter)
                            Positioned(
                              top: 8,
                              right: 12,
                              child: IconButton(
                                icon: const Icon(
                                  Icons.close,
                                  color: Colors.black54,
                                ),
                                onPressed: () => _deleteType(index),
                              ),
                            ),
                        ],
                      ),
                    ),
                  );
                },
              ),

              const SizedBox(height: 40),

              // 🔹 내 취향 반영 추천 향수 (더미)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "내 취향을 반영한 추천 향수",
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Divider(color: Colors.black12, thickness: 1),

                    SizedBox(
                      height: 180,
                      child: ListView(
                        scrollDirection: Axis.horizontal,
                        children: [
                          _buildPerfumeCard({
                            'id': 'pbti001',
                            'brand': '딥디크',
                            'name': '오에도',
                            'image': 'assets/images/perfume001.png'
                          }),
                          _buildPerfumeCard({
                            'id': 'pbti002',
                            'brand': '디올',
                            'name': '소바쥬 엘릭서',
                            'image': 'assets/images/perfume002.png'
                          }),
                          _buildPerfumeCard({
                            'id': 'pbti003',
                            'brand': '입생로랑',
                            'name': '라 뉘드롬므',
                            'image': 'assets/images/perfume003.png'
                          }),
                        ],
                      ),
                    ),
                    const Divider(color: Colors.black12, thickness: 1),
                  ],
                ),
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

  /// ------------------------
  /// 향수 카드 위젯
  /// ------------------------
  Widget _buildPerfumeCard(Map<String, String> perfume) {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => PerfumeDetailScreen(
              perfumeId: perfume['id']!,  // 🔥 id 필수 전달
              fromStorage: false,
            ),
          ),
        );
      },
      child: Container(
        width: 150,
        margin: const EdgeInsets.only(right: 8),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.start,
          children: [
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.asset(
                perfume['image']!,
                height: 120,
                width: 100,
                fit: BoxFit.fill,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              perfume['brand'] ?? '',
              style: const TextStyle(color: Colors.grey, fontSize: 10),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: Text(
                perfume['name'] ?? '',
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 11,
                ),
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  /// ------------------------
  /// PBTI 코드 → 캐릭터 이미지 매핑
  /// ------------------------
  String getPbtiImage(String code) {
    const base = 'assets/images/PBTI';
    switch (code) {
      case 'FHPM': return '$base/FHPM.png';
      case 'FHPN': return '$base/FHPN.png';
      case 'FHSM': return '$base/FHSM.png';
      case 'FHSN': return '$base/FHSN.png';
      case 'FLPM': return '$base/FLPM.png';
      case 'FLPN': return '$base/FLPN.png';
      case 'FLSM': return '$base/FLSM.png';
      case 'FLSN': return '$base/FLSN.png';
      case 'WHPM': return '$base/WHPM.png';
      case 'WHPN': return '$base/WHPN.png';
      case 'WHSM': return '$base/WHSM.png';
      case 'WHSN': return '$base/WHSN.png';
      case 'WLPM': return '$base/WLPM.png';
      case 'WLPN': return '$base/WLPN.png';
      case 'WLSM': return '$base/WLSM.png';
      case 'WLSN': return '$base/WLSN.png';
      default: return '$base/FLSN.png';
    }
  }
}
