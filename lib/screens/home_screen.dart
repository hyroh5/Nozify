import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:provider/provider.dart';

import '../providers/today_recommendation_provider.dart';
import '../providers/auth_provider.dart';
import '../widgets/topbar/appbar_ver1.dart';
import '../widgets/bottom_navbar.dart';
import '../widgets/custom_drawer.dart';
import '../widgets/home/home_section_title.dart';
import '../screens/perfume_detail_screen.dart';
import 'package:sw_showcase/screens/accord_perfumes_screen.dart';
import '../models/today_recommendation.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

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

  // ------------------------ 더미 BTI 추천(로그인 시만 표시) ------------------------
  final List<Map<String, String>> myBTI = [
    {
      'id': 'bti001',
      'brand': '톰 포드',
      'name': '우드 우드',
      'image': 'assets/images/perfume01.png',
    },
    {
      'id': 'bti002',
      'brand': '디올',
      'name': '소바쥬 엘릭서',
      'image': 'assets/images/perfume02.png',
    },
    {
      'id': 'bti003',
      'brand': '입생로랑',
      'name': '라 뉘드롬므',
      'image': 'assets/images/perfume03.png',
    },
  ];

  final List<Map<String, String>> oppositeBTI = [
    {
      'id': 'opp001',
      'brand': '샤넬',
      'name': '샹스 오땅드르 오드뚜왈렛',
      'image': 'assets/images/perfume04.png',
    },
    {
      'id': 'opp002',
      'brand': '돌체앤가바나',
      'name': '라이트 블루',
      'image': 'assets/images/perfume05.png',
    },
    {
      'id': 'opp003',
      'brand': '디올',
      'name': '미스 디올 블루밍 부케',
      'image': 'assets/images/perfume06.png',
    },
  ];

  // ------------------------------------------------------------
  // initState → 오늘의 추천 향수 최초 로딩
  // ------------------------------------------------------------
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<TodayRecommendationProvider>().fetchTodayRecommendations();
    });
  }

  // ------------------------------------------------------------
  // 빌드
  // ------------------------------------------------------------
  @override
  Widget build(BuildContext context) {
    final isLoggedIn = context.watch<AuthProvider>().isLoggedIn;
    final todayProvider = context.watch<TodayRecommendationProvider>();

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
              // ① 오늘의 맞춤 향수 (이달의 향수 대신!)
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
                    ? const Center(
                  child: Text("오늘의 추천 향수를 불러오지 못했어요."),
                )
                    : ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: todayProvider.items.length,
                  itemBuilder: (context, index) {
                    final item = todayProvider.items[index];
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
                      child: _buildTodayCard(item),
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
                          builder: (_) => AccordPerfumesScreen(
                            accordName: categories[index]['key']!,
                          ),
                        ),
                      );
                    },
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
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
                        Text(cat['name']!,
                            style: const TextStyle(fontSize: 11)),
                      ],
                    ),
                  );
                },
              ),
              // =======================================================
              // ③ 나의 향 BTI 추천 (로그인 시에만 표시)
              // =======================================================
              if (isLoggedIn) ...[
                const SizedBox(height: 24),
                const _SectionTitle(
                    'Warm·Heavy한 당신에게는 오리엔탈 & 우디 계열이 잘 어울려요'),

                SizedBox(
                  height: 180,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: myBTI.length,
                    itemBuilder: (context, index) {
                      final p = myBTI[index];
                      return GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => PerfumeDetailScreen(
                                perfumeId: p['id']!,
                                fromStorage: false,
                              ),
                            ),
                          );
                        },
                        child: _buildPerfumeCard(p),
                      );
                    },
                  ),
                ),

                // =======================================================
                // ④ 반대 성향 추천
                // =======================================================
                const SizedBox(height: 24),
                const _SectionTitle('시트러스 & 플로럴 계열도 시도해 보세요'),

                SizedBox(
                  height: 180,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: oppositeBTI.length,
                    itemBuilder: (context, index) {
                      final p = oppositeBTI[index];
                      return GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => PerfumeDetailScreen(
                                perfumeId: p['id']!,
                                fromStorage: false,
                              ),
                            ),
                          );
                        },
                        child: _buildPerfumeCard(p),
                      );
                    },
                  ),
                ),
              ],
            ],
          ),
        ),
      ),

      bottomNavigationBar: BottomNavBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
      ),
    );
  }

  // =======================================================
  // 오늘의 맞춤 향수 카드 (네트워크 이미지)
  // =======================================================
  Widget _buildTodayCard(TodayRecommendationItem item) {
    return Container(
      width: 150,
      margin: const EdgeInsets.only(right: 10),
      child: Column(
        children: [
          const SizedBox(height: 16),
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.network(
              item.imageUrl,
              height: 120,
              width: 100,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) {
                return Image.asset(
                  'assets/images/dummy.jpg',
                  height: 120,
                  width: 100,
                  fit: BoxFit.cover,
                );
              },
            ),
          ),
          const SizedBox(height: 8),
          Text(item.brandName,
              style: const TextStyle(color: Colors.grey, fontSize: 10)),
          Text(
            item.name,
            style: const TextStyle(
                fontSize: 11, fontWeight: FontWeight.w600),
            maxLines: 2,
            textAlign: TextAlign.center,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  // =======================================================
  // Occasion 선택 버튼
  // =======================================================
  Widget _buildOccasionChips(TodayRecommendationProvider provider) {
    final options = [
      {'key': 'nightout', 'label': '나이트 아웃'},
      {'key': 'casual', 'label': '캐주얼'},
      {'key': 'professional', 'label': '포멀'},
    ];

    return Row(
      children: options.map((opt) {
        final bool selected = provider.occasion == opt['key'];

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
                  color: selected
                      ? Colors.black
                      : Colors.grey.shade400,
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

  // =======================================================
  // 기존 Perfume 카드 위젯 (BTI 추천용)
  // =======================================================
  Widget _buildPerfumeCard(Map<String, String> perfume) {
    return Container(
      width: 150,
      margin: const EdgeInsets.only(right: 8),
      child: Column(
        children: [
          ClipRRect(
            child: Image.asset(
              perfume['image']!,
              height: 120,
              width: 100,
              fit: BoxFit.fill,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            perfume['brand']!,
            style: const TextStyle(color: Colors.grey, fontSize: 10),
          ),
          Text(
            perfume['name']!,
            style: const TextStyle(
                fontWeight: FontWeight.w600, fontSize: 11),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
        const SizedBox(height: 8),
        const Divider(color: Colors.black12, thickness: 1),
      ],
    );
  }
}
