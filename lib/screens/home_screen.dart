import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/today_recommendation_provider.dart';
import '../providers/auth_provider.dart';
import '../providers/pbti_provider.dart';
import '../providers/brand_recommendation_provider.dart';
import '../providers/trending_provider.dart';
import '../providers/recent_view_provider.dart';

import '../widgets/topbar/appbar_ver1.dart';
import '../widgets/bottom_navbar.dart';
import '../widgets/custom_drawer.dart';
import '../widgets/home/home_section_title.dart';

import '../screens/perfume_detail_screen.dart';
import '../screens/accord_perfumes_screen.dart';

import '../models/perfume_simple.dart';
import '../models/pbti_axis_recommendation.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  PbtiByTypeRecommendation? _byType;
  bool _isLoadingByType = false;
  bool _pbtiAvailable = false;

  // ------------------------ 계열별 추천 ------------------------
  final List<Map<String, String>> categories = [
    {'name': '플로럴', 'image': 'assets/images/category01.png', 'key': 'floral'},
    {'name': '프루티', 'image': 'assets/images/category02.png', 'key': 'fruity'},
    {'name': '시트러스', 'image': 'assets/images/category03.png', 'key': 'citrus'},
    {'name': '우디', 'image': 'assets/images/category04.png', 'key': 'woody'},
    {'name': '그린', 'image': 'assets/images/category05.png', 'key': 'green'},
    {'name': '웜 스파이시', 'image': 'assets/images/category06.png', 'key': 'warm spicy'},
    {'name': '스위트', 'image': 'assets/images/category07.png', 'key': 'sweet'},
    {'name': '아쿠아틱', 'image': 'assets/images/category08.png', 'key': 'aquatic'},
    {'name': '머스크', 'image': 'assets/images/category09.png', 'key': 'musky'},
    {'name': '레더', 'image': 'assets/images/category10.png', 'key': 'leather'},
  ];

  // ------------------------------------------------------------
  // initState → 오늘의 향수 + PBTI 축별 추천 + 브랜드 리스트 + 트렌딩 로딩
  // ------------------------------------------------------------
  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final today = context.read<TodayRecommendationProvider>();
      final brand = context.read<BrandRecommendationProvider>();
      final trending = context.read<TrendingProvider>();
      final recent = context.read<RecentViewProvider>();


      today.fetchTodayRecommendations();
      trending.fetchTrending();
      recent.fetchRecentViews();

      final auth = context.read<AuthProvider>();
      final pbti = context.read<PbtiProvider>();

      await pbti.loadResults(auth);

      if (auth.isLoggedIn) {
        brand.fetchBrandList();
        recent.fetchRecentViews();
      }

      if (!auth.isLoggedIn || !pbti.hasResult) {
        setState(() => _pbtiAvailable = false);
        return;
      }

      setState(() {
        _pbtiAvailable = true;
        _isLoadingByType = true;
      });

      try {
        final result = await pbti.fetchByTypeRecommendations();
        setState(() {
          _byType = result;
          _isLoadingByType = false;
        });
      } catch (_) {
        setState(() => _isLoadingByType = false);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final todayProvider = context.watch<TodayRecommendationProvider>();
    final brandProvider = context.watch<BrandRecommendationProvider>();
    final isLoggedIn = context.watch<AuthProvider>().isLoggedIn;
    final trending = context.watch<TrendingProvider>();
    final recentProvider = context.watch<RecentViewProvider>();

    return Scaffold(
      appBar: const AppBarVer1(),
      endDrawer: const CustomDrawer(),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 16),

              // =======================================================
              // ① 오늘의 맞춤 향수
              // =======================================================
              const HomeSectionTitle(title: "오늘의 맞춤 향수"),
              const SizedBox(height: 8),
              _buildOccasionChips(todayProvider),
              const SizedBox(height: 12),

              SizedBox(
                height: 220,
                child: todayProvider.isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : todayProvider.items.isEmpty
                    ? const Center(child: Text("오늘의 추천 향수를 불러오지 못했어요."))
                    : Builder(
                  builder: (_) {
                    final reversed = todayProvider.items.reversed.toList();

                    return ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: reversed.length,
                      itemBuilder: (context, index) {
                        final simple = PerfumeSimple(
                          id: reversed[index].id,
                          name: reversed[index].name,
                          brandName: reversed[index].brandName,
                          imageUrl: reversed[index].imageUrl,
                        );

                        return _buildPerfumeCard(simple);
                      },
                    );
                  },
                ),
              ),

              // =======================================================
              // ② 계열별 추천
              // =======================================================
              const HomeSectionTitle(title: "계열별 추천"),
              const SizedBox(height: 12),

              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: categories.length,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 5,
                  mainAxisSpacing: 4,
                  childAspectRatio: 0.84,
                ),
                itemBuilder: (context, index) {
                  final cat = categories[index];
                  return GestureDetector(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) =>
                              AccordPerfumesScreen(accordName: cat['key']!),
                        ),
                      );
                    },
                    child: Column(
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(24),
                          child: Image.asset(
                            cat['image']!,
                            height: 70,
                            width: 70,
                            fit: BoxFit.cover,
                          ),
                        ),
                        Text(cat['name']!, style: const TextStyle(fontSize: 11)),
                      ],
                    ),
                  );
                },
              ),

              // =======================================================
              // ③ 자주 보는 브랜드별 추천 (로그인 시만)
              // =======================================================
              if (isLoggedIn) ...[
                const SizedBox(height: 32),
                const HomeSectionTitle(title: "자주 보는 브랜드별 추천"),
                const SizedBox(height: 12),

                _buildBrandSelector(brandProvider),
                const SizedBox(height: 16),
                _buildBrandPerfumeList(brandProvider),
              ],
              // =======================================================
              // ⑤ 최근 본 향수 기반 추천 (로그인 시만)
              // =======================================================
              if (isLoggedIn) ...[
                const SizedBox(height: 12),
                const HomeSectionTitle(title: "최근 본 향수"),
                const SizedBox(height: 24),

                // ----- 최근 본 향수 리스트 -----
                SizedBox(
                  height: 120,
                  child: recentProvider.isLoadingRecent
                      ? const Center(child: CircularProgressIndicator())
                      : recentProvider.recentViews.isEmpty
                      ? const Center(
                    child: Text("최근 본 향수가 없어요."),
                  )
                      : ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: recentProvider.recentViews.length,
                    itemBuilder: (_, i) {
                      final item = recentProvider.recentViews[i];

                      return GestureDetector(
                        onTap: () {
                          recentProvider.fetchSimilar(item.perfumeId);
                        },
                        child: Container(
                          width: 110,
                          margin: const EdgeInsets.only(right: 8),
                          child: Column(
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(12),
                                child: Image.network(
                                  item.imageUrl ?? "",
                                  height: 72,
                                  width: 72,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) => _dummy2(),
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                item.name,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(fontSize: 11),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),

                const SizedBox(height: 12),

                // ----- 유사 추천 리스트 -----
                if (recentProvider.similarPerfumes.isNotEmpty) ...[
                  const HomeSectionTitle(title: "이 향수와 비슷한 추천"),
                  const SizedBox(height: 12),

                  SizedBox(
                    height: 220,
                    child: recentProvider.isLoadingSimilar
                        ? const Center(child: CircularProgressIndicator())
                        : ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: recentProvider.similarPerfumes.length,
                      itemBuilder: (_, i) =>
                          _buildPerfumeCard(recentProvider.similarPerfumes[i].toSimple()),
                    ),
                  ),
                ],
              ],

              // =======================================================
              // ④ PBTI 축 기반 추천 (로그인 + PBti 결과 있을 때)
              // =======================================================
              if (_pbtiAvailable) ...[
                const SizedBox(height: 12),

                if (_isLoadingByType)
                  const Center(child: CircularProgressIndicator())

                else if (_byType != null) ...[
                  HomeSectionTitle(title: _forwardAxisLabel(_byType!.finalType)),
                  const SizedBox(height: 12),

                  SizedBox(
                    height: 196,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: _byType!.forward.length,
                      itemBuilder: (_, i) =>
                          _buildPerfumeCard(_byType!.forward[i]),
                    ),
                  ),

                  const SizedBox(height: 48),

                  HomeSectionTitle(title: _reverseAxisLabel(_byType!.finalType)),
                  const SizedBox(height: 12),

                  SizedBox(
                    height: 196,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: _byType!.reverse.length,
                      itemBuilder: (_, i) =>
                          _buildPerfumeCard(_byType!.reverse[i]),
                    ),
                  ),
                ],
              ],
              // =======================================================
              // ④ 요즘 트렌딩 중인 향수
              // =======================================================
              const SizedBox(height: 24),
              const HomeSectionTitle(title: "지금 트렌딩 중인 향수"),
              const SizedBox(height: 12),

              SizedBox(
                height: 196,
                child: trending.isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : trending.items.isEmpty
                    ? const Center(
                  child: Text("트렌딩 향수를 불러오지 못했어요.",
                      style: TextStyle(color: Colors.grey)),
                )
                    : ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: trending.items.length,
                  itemBuilder: (_, i) => _buildPerfumeCard(trending.items[i]),
                ),
              ),
            ],
          ),
        ),
      ),

      bottomNavigationBar: BottomNavBar(
        currentIndex: _selectedIndex,
        onTap: (i) => setState(() => _selectedIndex = i),
      ),
    );
  }

  // =======================================================
  // 브랜드 선택 원형 UI
  // =======================================================
  Widget _buildBrandSelector(BrandRecommendationProvider p) {
    if (p.isLoadingBrands) {
      return const SizedBox(
        height: 80,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (p.brands.isEmpty) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 32),
        child: Text("최근 본 브랜드 데이터가 부족합니다."),
      );
    }

    return SizedBox(
      height: 80,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: p.brands.length,
        itemBuilder: (_, i) {
          final brand = p.brands[i];
          return GestureDetector(
            onTap: () => p.fetchBrandPerfumes(brand.id),
            child: Container(
              margin: const EdgeInsets.only(right: 12),
              width: 70,
              height: 70,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white,
                border: Border.all(color: Colors.black12),
              ),
              child: Center(
                child: Image.asset(
                  _mapBrandLogo(brand.name),
                  width: 46,
                  height: 46,
                  fit: BoxFit.fill,
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  // 브랜드 로고 매핑
  String _mapBrandLogo(String name) {
    const base = 'assets/images/brand';
    switch (name) {
      case "Burberry": return "$base/burberry.png";
      case "Byredo": return "$base/byredo.png";
      case "Calvin Klein": return "$base/ck.png";
      case "Chanel": return "$base/chanel.png";
      case "Dior": return "$base/dior.png";
      case "Diptyque": return "$base/diptyque.png";
      case "Giorgio Armani": return "$base/giorgio_armani.png";
      case "Givenchy": return "$base/givenchy.png";
      case "Gucci": return "$base/gucci.png";
      case "Guerlain": return "$base/guerlain.png";
      case "Hermes": return "$base/hermes.png";
      case "Jo Malone London": return "$base/jomalone.png";
      case "Maison Francis Kurkdjian": return "$base/maison.png";
      case "Mugler": return "$base/mugler.png";
      case "Tom Ford": return "$base/tomford.png";
      case "Versace": return "$base/versace.png";
      case "Yves Saint Laurent": return "$base/ysl.png";
      case "Montblanc": return "$base/montblanc.png";
      default: return "$base/default.png";
    }
  }

  // =======================================================
  // 브랜드 추천 향수 카드 리스트
  // =======================================================
  Widget _buildBrandPerfumeList(BrandRecommendationProvider p) {
    if (p.isLoadingPerfumes) {
      return const SizedBox(
        height: 200,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (p.brandPerfumes.isEmpty) {
      return const SizedBox(
        height: 220,
        child: Center(child: Text("브랜드를 선택해보세요")),
      );
    }

    return SizedBox(
      height: 220,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: p.brandPerfumes.length,
        itemBuilder: (_, i) => _buildPerfumeCard(p.brandPerfumes[i]),
      ),
    );
  }

  // =======================================================
  // Perfume Card (공용)
  // =======================================================
  Widget _buildPerfumeCard(PerfumeSimple item) {
    return Container(
      width: 150,
      margin: const EdgeInsets.only(right: 10),
      child: GestureDetector(
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
        child: Column(
          children: [
            const SizedBox(height: 16),
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: item.imageUrl != null
                  ? Image.network(
                item.imageUrl!,
                height: 120,
                width: 100,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => _dummy(),
              )
                  : _dummy(),
            ),
            const SizedBox(height: 8),
            Text(item.brandName,
                style: const TextStyle(color: Colors.grey, fontSize: 10)),
            Text(
              item.name,
              style:
              const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _dummy() {
    return Image.asset(
      'assets/images/dummy.jpg',
      height: 120,
      width: 100,
      fit: BoxFit.cover,
    );
  }

  Widget _dummy2() {
    return Image.asset(
      'assets/images/dummy.jpg',
      height: 72,
      width: 72,
      fit: BoxFit.cover,
    );
  }

  // =======================================================
  // Occasion chips
  // =======================================================
  Widget _buildOccasionChips(TodayRecommendationProvider provider) {
    final options = [
      {'key': 'nightout', 'label': '나이트 아웃'},
      {'key': 'casual', 'label': '캐주얼'},
      {'key': 'professional', 'label': '포멀'},
    ];

    return Row(
      children: options.map((opt) {
        final selected = provider.occasion == opt['key'];
        return Padding(
          padding: const EdgeInsets.only(right: 8),
          child: GestureDetector(
            onTap: () => provider.setOccasion(opt['key']!),
            child: Container(
              padding:
              const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                color: selected ? Colors.black : Colors.white,
                border: Border.all(
                  color: selected ? Colors.black : Colors.grey.shade400,
                ),
              ),
              child: Text(
                opt['label']!,
                style: TextStyle(
                  fontSize: 12,
                  color: selected ? Colors.white : Colors.black,
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}

// =======================================================
// 정방향 축 라벨
// =======================================================
String _forwardAxisLabel(String type) {
  final c1 = type[0];
  final c2 = type[1];

  final a1 = c1 == 'F' ? 'FRESH' : 'WARM';
  final a2 = c2 == 'L' ? 'LIGHT' : 'HEAVY';

  return "$a1 & $a2한 향을 좋아하는 당신에게 추천드려요";
}

// =======================================================
// 역방향 축 라벨
// =======================================================
String _reverseAxisLabel(String type) {
  final c3 = type[2];
  final c4 = type[3];

  final a3 = c3 == 'S' ? 'SPICY' : 'SWEET';
  final a4 = c4 == 'N' ? 'MODERN' : 'NATURAL';

  return "$a3 & $a4 계열도 시도해보세요";
}



