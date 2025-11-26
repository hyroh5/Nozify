import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:carousel_slider/carousel_slider.dart';

import '../../providers/auth_provider.dart';
import '../../providers/pbti_provider.dart';

import '../../models/pbti_history.dart';
import '../../models/perfume_simple.dart';

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

  /// 히스토리
  List<PbtiHistoryItem> pbtiResults = [];

  /// 추천 향수
  List<PerfumeSimple> recommendations = [];
  bool isLoadingRecommendations = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final auth = context.read<AuthProvider>();
      final pbtiProvider = context.read<PbtiProvider>();

      // 1) 히스토리 불러오기
      await pbtiProvider.loadResults(auth);
      setState(() => pbtiResults = pbtiProvider.results);

      // 2) 추천 불러오기 (기본 추천)
      try {
        final rec = await pbtiProvider.fetchRecommendations();
        setState(() {
          recommendations = rec;
          isLoadingRecommendations = false;
        });
      } catch (_) {
        setState(() => isLoadingRecommendations = false);
      }
    });
  }

  // ------------------------------
  // 삭제
  // ------------------------------
  Future<void> _deleteType(PbtiHistoryItem item) async {
    final pbti = context.read<PbtiProvider>();

    try {
      await pbti.deleteHistory(item.id);

      setState(() {
        pbtiResults.removeWhere((e) => e.id == item.id);
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("삭제 실패: $e")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final totalCards = pbtiResults.length + 1;
    final isLoggedIn = context.watch<AuthProvider>().isLoggedIn;

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

              // 🔹 캐러셀
              CarouselSlider.builder(
                itemCount: totalCards,
                options: CarouselOptions(
                  height: 360,
                  enlargeCenterPage: true,
                  viewportFraction: 0.38,
                  enableInfiniteScroll: false,
                  onPageChanged: (index, _) =>
                      setState(() => _currentPage = index),
                ),
                itemBuilder: (context, index, _) {
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
                          // 기존 카드
                          if (!isAddCard)
                            _buildHistoryCard(pbtiResults[index], isCenter)

                          // 새 카드
                          else
                            _buildAddCard(isCenter, isLoggedIn),

                          // 삭제 버튼
                          if (!isAddCard && isCenter)
                            Positioned(
                              top: 8,
                              right: 12,
                              child: IconButton(
                                icon: const Icon(Icons.close,
                                    color: Colors.black54),
                                onPressed: () =>
                                    _deleteType(pbtiResults[index]),
                              ),
                            ),
                        ],
                      ),
                    ),
                  );
                },
              ),

              const SizedBox(height: 40),

              // 🔹 추천 향수 리스트
              _buildRecommendationSection(),
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

  // ----------------------------------------------------
  // 히스토리 카드
  // ----------------------------------------------------
  Widget _buildHistoryCard(PbtiHistoryItem item, bool isCenter) {
    return Container(
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
              getPbtiImage(item.finalType),
              height: isCenter ? 150 : 120,
              fit: BoxFit.contain,
            ),
          ),
          if (isCenter) ...[
            const SizedBox(height: 16),
            Text(
              item.finalType,
              style: const TextStyle(
                  fontSize: 36, fontWeight: FontWeight.bold),
            ),
            const Text("당신의 향수 성향 코드",
                style: TextStyle(color: Colors.grey)),
          ],
        ],
      ),
    );
  }

  // ----------------------------------------------------
  // 새 카드
  // ----------------------------------------------------
  Widget _buildAddCard(bool isCenter, bool isLoggedIn) {
    return GestureDetector(
      onTap: () {
        if (!isLoggedIn) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("로그인 후 이용할 수 있습니다.")),
          );
          return;
        }

        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const PBTIIntroScreen()),
        );
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
              const Text(
                "테스트하러 가기",
                style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87),
              ),
            ]
          ],
        ),
      ),
    );
  }

  // ----------------------------------------------------
  // 추천 향수 섹션
  // ----------------------------------------------------
  Widget _buildRecommendationSection() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            "내 취향을 반영한 추천 향수",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          const Divider(color: Colors.black12, thickness: 1),

          SizedBox(
            height: 180,
            child: Builder(
              builder: (_) {
                if (isLoadingRecommendations) {
                  return const Center(child: CircularProgressIndicator());
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
    );
  }

  // ----------------------------------------------------
  // 향수 카드 공용 컴포넌트
  // ----------------------------------------------------
  Widget _buildPerfumeCard(PerfumeSimple item) {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => PerfumeDetailScreen(
              perfumeId: item.id,
              fromStorage: false,
            ),
          ),
        );
      },
      child: Container(
        width: 150,
        margin: const EdgeInsets.only(right: 8),
        child: Column(
          children: [
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.network(
                item.imageUrl ?? '',
                height: 108,
                width: 90,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) =>
                    Image.asset('assets/images/dummy.jpg',
                        height: 108,
                        width: 90,
                        fit: BoxFit.cover),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              item.brandName,
              style: const TextStyle(
                  color: Colors.grey, fontSize: 10),
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
            ),
            Text(
              item.name,
              style: const TextStyle(
                  fontWeight: FontWeight.w600, fontSize: 11),
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              maxLines: 1,
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  // ----------------------------------------------------
  // PBti 이미지 매핑
  // ----------------------------------------------------
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
