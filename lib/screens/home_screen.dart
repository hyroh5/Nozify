// lib/screens/home_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import '../widgets/topbar/appbar_ver1.dart';
import '../widgets/bottom_navbar.dart';
import '../widgets/custom_drawer.dart';
import '../screens/perfume_detail_screen.dart';
import 'package:sw_showcase/screens/accord_perfumes_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  // ------------------------ 더미 데이터 ------------------------
  final List<Map<String, String>> monthlyPerfumes = [
    {
      'id': '11111111',
      'brand': '딥디크',
      'name': '오에도 오 드 뚜왈렛',
      'image': 'assets/images/perfume001.png',
    },
    {
      'id': '22222222',
      'brand': '돌체앤가바나',
      'name': '라이트 블루',
      'image': 'assets/images/perfume002.png',
    },
    {
      'id': '33333333',
      'brand': '조말론 런던',
      'name': '라임 바질 앤 만다린',
      'image': 'assets/images/perfume003.png',
    }
  ];

  // Key를 영어로 -> 계열별 추천에서 api 요청의 계열이 영어로 전달되게 함
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const AppBarVer1(),
      endDrawer: const CustomDrawer(),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ---------------------------------------
              // ① 이달의 향수
              // ---------------------------------------
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 10),
                child: Text(
                  '이달의 향수',
                  style: TextStyle(
                    fontSize: 30,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              const SizedBox(height: 12),

              SizedBox(
                height: 348,
                child: ScrollConfiguration(
                  behavior: const MaterialScrollBehavior().copyWith(
                    dragDevices: {
                      PointerDeviceKind.touch,
                      PointerDeviceKind.mouse,
                      PointerDeviceKind.trackpad,
                    },
                  ),
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: monthlyPerfumes.length,
                    itemBuilder: (context, index) {
                      final p = monthlyPerfumes[index];
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
                        child: Align(
                          alignment: Alignment.center,
                          child: _buildMonthlyCard(p),
                        ),
                      );
                    },
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // ---------------------------------------
              // ② 계열별 추천
              // ---------------------------------------
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 10),
                child: Text(
                  '계열별 추천',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
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
                              AccordPerfumesScreen(accordName: categories[index]['key']!),
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
                        Text(cat['name']!, style: const TextStyle(fontSize: 11)),
                      ],
                    ),
                  );
                },
              ),

              const SizedBox(height: 24),

              // ---------------------------------------
              // ③ 나의 향BTI 추천
              // ---------------------------------------
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

              const SizedBox(height: 24),

              // ---------------------------------------
              // ④ 반대 성향 추천
              // ---------------------------------------
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
          ),
        ),
      ),

      bottomNavigationBar: BottomNavBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
      ),
    );
  }

  // -------------------------------------------------------
  // 카드 UI 위젯들
  // -------------------------------------------------------
  Widget _buildMonthlyCard(Map<String, String> p) {
    return Container(
      width: 220,
      height: 330,
      margin: const EdgeInsets.only(right: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.asset(
              p['image']!,
              height: 210,
              width: 140,
              fit: BoxFit.fill,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            p['brand'] ?? '',
            style: const TextStyle(color: Colors.grey, fontSize: 10),
          ),
          const SizedBox(height: 2),
          Text(
            p['name']!,
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  Widget _buildPerfumeCard(Map<String, String> perfume) {
    return Container(
      width: 150,
      margin: const EdgeInsets.only(right: 8),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.start,
        children: [
          const SizedBox(height: 8),
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
            perfume['brand'] ?? '',
            style: const TextStyle(color: Colors.grey, fontSize: 10),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Text(
              perfume['name'] ?? '',
              style:
              const TextStyle(fontWeight: FontWeight.w600, fontSize: 11),
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(height: 8),
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
