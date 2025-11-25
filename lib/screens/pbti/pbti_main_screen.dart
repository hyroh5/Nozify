import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:carousel_slider/carousel_slider.dart';

import '../../providers/auth_provider.dart';
import '../../providers/pbti_provider.dart';
import '../../models/pbti_recommendation.dart';
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

  /// 추천 향수 리스트
  List<PbtiRecommendationItem> recommendations = [];

  bool isLoadingRecommendations = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final auth = context.read<AuthProvider>();
      final pbtiProvider = context.read<PbtiProvider>();

      // 1) 서버에서 PBTI 히스토리 로드
      await pbtiProvider.loadResults(auth);
      setState(() {
        pbtiResults = pbtiProvider.results;
      });

      // 2) 최근 PBTI 기반 추천 향수 요청 (파라미터 필요 없음!)
      try {
        final rec = await pbtiProvider.fetchRecommendations();
        setState(() {
          recommendations = rec;
          isLoadingRecommendations = false;
        });
      } catch (e) {
        setState(() => isLoadingRecommendations = false);
      }
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

                  // 🔥 로그인 상태 체크
                  final auth = context.watch<AuthProvider>();
                  final isLoggedIn = auth.isLoggedIn;

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
                              onTap: () {
                                if (isLoggedIn) {
                                  // 🔥 로그인한 경우 → PBtiIntroScreen 진입
                                  Navigator.pushReplacement(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => const PBTIIntroScreen(),
                                    ),
                                  );
                                } else {
                                  // 🔥 비로그인 → Snackbar + LoginScreen 이동
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text("로그인 후 이용할 수 있습니다."),
                                      duration: Duration(seconds: 2),
                                    ),
                                  );
                                }
                              },

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
                                      Text(
                                        "테스트하러 가기", // 항상 동일 문구 유지
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

              // 🔹 내 취향 추천 향수 (API 기반)
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
                      child: Builder(
                        builder: (_) {
                          if (isLoadingRecommendations) {
                            return const Center(
                                child: CircularProgressIndicator());
                          }

                          if (recommendations.isEmpty) {
                            return const Center(
                              child: Text(
                                "추천 결과가 없습니다.",
                                style: TextStyle(color: Colors.grey),
                              ),
                            );
                          }

                          return ListView.builder(
                            scrollDirection: Axis.horizontal,
                            itemCount: recommendations.length,
                            itemBuilder: (_, index) {
                              final item = recommendations[index];
                              return _buildPerfumeCard(item);
                            },
                          );
                        },
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
  Widget _buildPerfumeCard(PbtiRecommendationItem item) {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => PerfumeDetailScreen(
              perfumeId: item.perfumeId,
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
              child: item.imageUrl != null && item.imageUrl!.isNotEmpty
                  ? Image.network(
                item.imageUrl!,
                height: 108,
                width: 90,
                fit: BoxFit.cover,
              )
                  : Image.asset(
                'assets/images/dummy.jpg',
                height: 108,
                width: 90,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) {
                  return Image.asset(
                    'assets/images/dummy.jpg',
                    fit: BoxFit.fitHeight,
                  );
                },
              ),
            ),
            const SizedBox(height: 8),
            Text(
              item.brandName,
              style: const TextStyle(color: Colors.grey, fontSize: 10),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: Text(
                item.name,
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
  /// PBTI 코드 → 이미지 매핑
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
