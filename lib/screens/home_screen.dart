// home—screen。dart
import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart'; // 마우스 스크롤 허용
import '../widgets/topbar/appbar_ver1.dart';
import '../widgets/bottom_navbar.dart';
import '../widgets/custom_drawer.dart';
import '../screens/dummy_category_screen.dart';
import '../screens/perfume_detail_screen.dart';

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
      'brand': '딥디크',
      'name': '오에도 오 드 뚜왈렛',
      'image': 'assets/images/perfume001.png',
    },
    {
      'brand': '돌체앤가바나',
      'name': '라이트 블루',
      'image': 'assets/images/perfume002.png',
    },
    {
      'brand': '조말론 런던',
      'name': '라임 바질 앤 만다린',
      'image': 'assets/images/perfume003.png',
    }
  ];

  final List<Map<String, String>> categories = [
    {'name': '플로럴', 'image': 'assets/images/category01.png'},
    {'name': '프루티', 'image': 'assets/images/category02.png'},
    {'name': '시트러스', 'image': 'assets/images/category03.png'},
    {'name': '우디', 'image': 'assets/images/category04.png'},
    {'name': '그린', 'image': 'assets/images/category05.png'},
    {'name': '시프레', 'image': 'assets/images/category06.png'},
    {'name': '구르망', 'image': 'assets/images/category07.png'},
    {'name': '아쿠아틱', 'image': 'assets/images/category08.png'},
    {'name': '머스크', 'image': 'assets/images/category09.png'},
    {'name': '레더', 'image': 'assets/images/category10.png'},
  ];

  final List<Map<String, String>> myBTI = [
    {'brand': '톰 포드', 'name': '우드 우드', 'image': 'assets/images/perfume01.png'},
    {'brand': '디올', 'name': '소바쥬 엘릭서', 'image': 'assets/images/perfume02.png'},
    {'brand': '입생로랑', 'name': '라 뉘드롬므', 'image': 'assets/images/perfume03.png'},
  ];

  final List<Map<String, String>> oppositeBTI = [
    {'brand': '샤넬', 'name': '샹스 오땅드르 오드뚜왈렛', 'image': 'assets/images/perfume04.png'},
    {'brand': '돌체앤가바나', 'name': '라이트 블루', 'image': 'assets/images/perfume05.png'},
    {'brand': '디올', 'name': '미스 디올 블루밍 부케', 'image': 'assets/images/perfume06.png'},
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
              // ① 이달의 향수
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                child: const Text(
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
                      final perfume = monthlyPerfumes[index];
                      return GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const PerfumeDetailScreen(fromStorage: false),
                            ),
                          );
                        },
                        child: Align(
                          alignment: Alignment.center,
                          child: Container(
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
                                    perfume['image']!,
                                    height: 210,
                                    width: 140,
                                    fit: BoxFit.fill,
                                  ),
                                ),
                                const SizedBox(height: 16),
                                Text(perfume['brand'] ?? '',
                                    style: const TextStyle(color: Colors.grey, fontSize: 10)),
                                const SizedBox(height: 2),
                                Text(perfume['name']!,
                                    style: const TextStyle(fontWeight: FontWeight.w600)),
                                const SizedBox(height: 12),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // ② 계열별 추천
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                child: const Text(
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
                  crossAxisCount: 5, // 한 줄에 몇개?
                  mainAxisSpacing: 4, // 윗줄<->아랫줄 간격
                  crossAxisSpacing: 0, // 한 줄에서 요소간의 간격
                  childAspectRatio: 0.84, // 하나의 줄의 세로 크기?
                ),
                itemBuilder: (context, index) {
                  final cat = categories[index];
                  return GestureDetector(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => DummyCategoryScreen(categoryName: cat['name']!),
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

              // ③ 나의 향BTI 추천
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                child: const Text(
                  'Warm·Heavy한 당신에게는 오리엔탈 & 우디 계열이 잘 어울려요',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              const Divider(color: Colors.black12, thickness: 1),
              SizedBox(
                height: 180,
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
                    itemCount: myBTI.length,
                    itemBuilder: (context, index) {
                      final p = myBTI[index];
                      return GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const PerfumeDetailScreen(fromStorage: false),
                            ),
                          );
                        },
                        child: _buildPerfumeCard(p),
                      );
                    },
                  ),
                ),
              ),
              const Divider(color: Colors.black12, thickness: 1),

              const SizedBox(height: 24),

              // ④ 반대 성향 추천
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                child: const Text(
                  '시트러스 & 플로럴 계열도 시도해 보세요',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              const Divider(color: Colors.black12, thickness: 1),
              SizedBox(
                height: 180,
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
                    itemCount: oppositeBTI.length,
                    itemBuilder: (context, index) {
                      final p = oppositeBTI[index];
                      return GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const PerfumeDetailScreen(fromStorage: false),
                            ),
                          );
                        },
                        child: _buildPerfumeCard(p),
                      );
                    },
                  ),
                ),
              ),
              const Divider(color: Colors.black12, thickness: 1),
            ],
          ),
        ),
      ),
      bottomNavigationBar: BottomNavBar(
        currentIndex: _selectedIndex,
        onTap: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
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
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 11),
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










