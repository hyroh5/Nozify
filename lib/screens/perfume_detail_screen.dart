import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:provider/provider.dart';
import '../widgets/topbar/appbar_ver2.dart';
import '../widgets/bottom_navbar.dart';
import '../widgets/custom_drawer.dart';
import 'home_screen.dart';
import 'storage/my_storage_main_screen.dart';
import '../providers/storage_manager.dart';
import '../providers/recent_perfume_provider.dart';
import '../providers/auth_provider.dart'; // ✅ 추가됨
import 'dart:math' as math;

class PerfumeDetailScreen extends StatefulWidget {
  final bool fromStorage;
  const PerfumeDetailScreen({super.key, this.fromStorage = false});

  @override
  State<PerfumeDetailScreen> createState() => _PerfumeDetailScreenState();
}

class _PerfumeDetailScreenState extends State<PerfumeDetailScreen> {
  int _selectedIndex = 0;
  bool isFavorite = false;
  bool isPurchased = false;

  // 더미 데이터
  final Map<String, dynamic> perfume = {
    "Name": "White Moss & Snowdrop Cologne",
    "Brand": "Jo Malone London",
    "ImageURL": "assets/images/snowdrop.png",
    "Price": "85.00",
    "Main Accords": [
      "sweet",
      "white floral",
      "caramel",
      "fruity",
      "vanilla",
      "citrus",
      "woody",
      "lactonic",
      "amber",
      "powdery"
    ],
    "Main Accords Percentage": {
      "sweet": "Dominant",
      "white floral": "Dominant",
      "caramel": "Prominent",
      "fruity": "Prominent",
      "vanilla": "Prominent",
      "citrus": "Prominent",
      "woody": "Moderate",
      "lactonic": "Moderate",
      "amber": "Subtle",
      "powdery": "Subtle"
    },
    "Notes": {
      "Top": ["프티그레인", "클레멘타인"],
      "Middle": ["네롤리", "스노드롭"],
      "Base": ["모스", "통카빈", "앰버"]
    },
    "Longevity": "75.2%",
    "Sillage": "66.0%",
  };

  final Map<String, Color> accordColors = {
    'sweet': Color(0xFFF8BBD0),
    'white floral': Color(0xFFF3E5F5),
    'floral': Color(0xFFF8BBD0),
    'fruity': Color(0xFFFFF59D),
    'citrus': Color(0xFFC5E1A5),
    'woody': Color(0xFFBCAAA4),
    'amber': Color(0xFFFFD180),
    'vanilla': Color(0xFFFFE082),
    'powdery': Color(0xFFE0E0E0),
    'spicy': Color(0xFFFFAB91),
    'musky': Color(0xFFCFD8DC),
    'green': Color(0xFFDCEDC8),
    'fresh': Color(0xFFB2EBF2),
    'aquatic': Color(0xFFBBDEFB),
    'gourmand': Color(0xFFFBE9E7),
    'leathery': Color(0xFFA1887F),
    'smoky': Color(0xFFB0BEC5),
    'oriental': Color(0xFFFFE0B2),
    'aromatic': Color(0xFFC8E6C9),
    'earthy': Color(0xFFA1887F),
  };

  @override
  void initState() {
    super.initState();
    _loadStatus();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<RecentPerfumeProvider>().addPerfume({
        'brand': perfume['Brand'],
        'name': perfume['Name'],
        'image': perfume['ImageURL'],
      });
    });
  }

  Future<void> _loadStatus() async {
    final auth = context.read<AuthProvider>();
    final email = auth.user?.email ?? 'guest';
    final name = perfume["Name"];
    final fav = await StorageManager.contains(StorageManager.wishlistKey, email, name);
    final buy = await StorageManager.contains(StorageManager.purchasedKey, email, name);
    setState(() {
      isFavorite = fav;
      isPurchased = buy;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBarVer2(
        onBack: () {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (_) =>
              widget.fromStorage ? const MyStorageMainScreen() : const HomeScreen(),
            ),
          );
        },
      ),
      endDrawer: const CustomDrawer(),
      body: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              height: 264,
              color: Colors.grey[100],
              alignment: Alignment.center,
              child: Image.asset(
                perfume["ImageURL"],
                width: 264,
                height: 264,
                fit: BoxFit.fill,
              ),
            ),
            const SizedBox(height: 32),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(perfume["Brand"],
                      style: const TextStyle(
                          fontSize: 12, fontWeight: FontWeight.w600, color: Colors.grey)),
                  const SizedBox(height: 8),
                  Text(perfume["Name"],
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Text(
                    '₩${(double.parse(perfume["Price"]) * 1300).toStringAsFixed(0)}',
                    style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      // ❤️ 위시리스트 버튼
                      IconButton(
                        icon: Icon(
                          isFavorite ? Icons.favorite : Icons.favorite_border_outlined,
                          color: isFavorite ? Colors.redAccent : Colors.grey.shade700,
                        ),
                        onPressed: () async {
                          final auth = context.read<AuthProvider>();
                          if (!auth.isLoggedIn) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text("로그인 후 이용할 수 있습니다.")),
                            );
                            return;
                          }

                          final email = auth.user!.email;
                          final name = perfume["Name"];
                          if (isFavorite) {
                            await StorageManager.removeItem(StorageManager.wishlistKey, email, name);
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text("위시리스트에서 제거했어요")),
                            );
                          } else {
                            await StorageManager.addItem(StorageManager.wishlistKey, email, {
                              "brand": perfume["Brand"]!,
                              "name": perfume["Name"]!,
                              "image": perfume["ImageURL"]!,
                            });
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text("위시리스트에 추가됐어요")),
                            );
                          }
                          setState(() => isFavorite = !isFavorite);
                        },
                      ),

                      // 👜 구매목록 버튼
                      IconButton(
                        icon: Icon(
                          isPurchased ? Icons.add_circle : Icons.add_circle_outline,
                          color: isPurchased ? Color(0xFF3C463A) : Colors.grey.shade700,
                        ),
                        onPressed: () async {
                          final auth = context.read<AuthProvider>();
                          if (!auth.isLoggedIn) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text("로그인 후 이용할 수 있습니다.")),
                            );
                            return;
                          }

                          final email = auth.user!.email;
                          final name = perfume["Name"];
                          if (isPurchased) {
                            await StorageManager.removeItem(StorageManager.purchasedKey, email, name);
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text("구매목록에서 제거했어요")),
                            );
                          } else {
                            await StorageManager.addItem(StorageManager.purchasedKey, email, {
                              "brand": perfume["Brand"]!,
                              "name": perfume["Name"]!,
                              "image": perfume["ImageURL"]!,
                            });
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text("구매목록에 추가됐어요")),
                            );
                          }
                          setState(() => isPurchased = !isPurchased);
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // ✅ 네가 만든 탭 UI 100% 유지
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                children: [
                  const SizedBox(height: 32),
                  _buildTabBar(),
                  const SizedBox(height: 24),
                  if (_selectedIndex == 0) _buildAccordsTab(),
                  if (_selectedIndex == 1) _buildNotesTab(),
                  if (_selectedIndex == 2) _buildSillageTab(),
                ],
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavBar(
        currentIndex: 0,
        onTap: (index) {
          setState(() {
            if (index == 0) {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (_) => const HomeScreen()),
              );
            } else if (index == 3) {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (_) => const MyStorageMainScreen()),
              );
            }
          });
        },
      ),
    );
  }

Widget _buildTabBar() {
    const tabs = ["계열", "노트", "발향"];
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: List.generate(tabs.length, (i) {
        final selected = i == _selectedIndex;
        return GestureDetector(
          onTap: () => setState(() => _selectedIndex = i),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                tabs[i],
                style: TextStyle(
                  fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                  color: selected ? Colors.black : Colors.grey,
                  fontSize: 15,
                ),
              ),
              const SizedBox(height: 4),
              if (selected)
                Container(width: 24, height: 2, color: Colors.black),
            ],
          ),
        );
      }),
    );
  }

  // ✅ 계열 탭 (도넛 그래프 + 세부 어코드)
  Widget _buildAccordsTab() {
    final accords = perfume["Main Accords"] as List;
    final Map<String, String> percentages =
    Map<String, String>.from(perfume["Main Accords Percentage"]);

    // 🔹 계열 분류 기준
    final Map<String, List<String>> accordGroups = {
      "플로럴": ["floral", "rose", "jasmine", "violet", "iris", "peony", "lily"],
      "프루티": ["fruit", "apple", "pear", "peach", "berry", "cherry", "mango"],
      "시트러스": ["citrus", "lemon", "bergamot", "lime", "orange", "grapefruit"],
      "우디": ["wood", "cedar", "sandalwood", "vetiver", "oak", "patchouli"],
      "그린": ["green", "leaf", "grass", "tea", "herbal", "basil"],
      "시프레": ["chypre", "moss", "oakmoss"],
      "구르망": ["vanilla", "caramel", "chocolate", "coffee", "tonka"],
      "아쿠아틱": ["aquatic", "marine", "sea", "water"],
      "레더": ["leather", "suede", "tobacco"],
      "머스크": ["musk", "musky", "powdery", "amber"],
    };

    // 🔹 파스텔톤 색상
    final Map<String, Color> pastelColors = {
      "플로럴": const Color(0xFFFFC1CC),
      "프루티": const Color(0xFFFFE4B5),
      "시트러스": const Color(0xFFFFFFB3),
      "우디": const Color(0xFFD7B899),
      "그린": const Color(0xFFB4E197),
      "시프레": const Color(0xFFC5E1A5),
      "구르망": const Color(0xFFFFDAB9),
      "아쿠아틱": const Color(0xFFB2EBF2),
      "레더": const Color(0xFFE0C097),
      "머스크": const Color(0xFFE6E6FA),
      "기타": Colors.grey.shade300,
    };

    // 🔹 계열별 카운트 계산
    final Map<String, int> groupCount = {for (var k in pastelColors.keys) k: 0};

    for (final acc in accords) {
      final lower = acc.toLowerCase();
      bool matched = false;
      for (final entry in accordGroups.entries) {
        if (entry.value.any((kw) => lower.contains(kw))) {
          groupCount[entry.key] = groupCount[entry.key]! + 1;
          matched = true;
          break;
        }
      }
      if (!matched) {
        groupCount["기타"] = (groupCount["기타"] ?? 0) + 1;
      }
    }

    final total = groupCount.values.fold<int>(0, (a, b) => a + b);
    final groupList =
    groupCount.keys.where((k) => groupCount[k]! > 0).toList();

    // 🔹 도넛 그래프 데이터
    final List<PieChartSectionData> data = groupList.map((group) {
      final percent = (groupCount[group]! / total) * 100;
      return PieChartSectionData(
        color: pastelColors[group],
        value: groupCount[group]!.toDouble(),
        radius: 60,
        title: "$group\n${percent.toStringAsFixed(1)}%",
        titleStyle: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.bold,
          color: Colors.black87,
        ),
      );
    }).toList();

    // 🔹 UI
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "계열별 분포",
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        const SizedBox(height: 12),

        Center(
          child: SizedBox(
            height: 260,
            width: 260,
            child: PieChart(
              PieChartData(
                startDegreeOffset: -90,
                centerSpaceRadius: 50,
                sectionsSpace: 2,
                sections: data,
                pieTouchData: PieTouchData(enabled: false),
              ),
            ),
          ),
        ),

        const SizedBox(height: 24),
        const Text(
          "세부 어코드",
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        const SizedBox(height: 12),

        // 🟢 세부 어코드 막대그래프
        Container(
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
          margin: const EdgeInsets.only(top: 8, bottom: 8),
          decoration: BoxDecoration(
            color: Colors.white, // 흰색 배경
            borderRadius: BorderRadius.circular(16), // 둥근 모서리
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.08), // 약한 그림자
                blurRadius: 6,
                offset: const Offset(0, 3),
              ),
            ],
            border: Border.all(color: Colors.grey.shade200), // 외곽선
          ),
          child: Column(
            children: accords.map((acc) {
              final color =
                  accordColors[acc.toLowerCase()] ?? Colors.grey.shade300;
              final level = percentages[acc] ?? 'Moderate';
              final percent = switch (level) {
                "Dominant" => 90,
                "Prominent" => 70,
                "Moderate" => 50,
                "Subtle" => 30,
                _ => 50
              };
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 5),
                child: Row(
                  children: [
                    Container(
                      width: 70,
                      alignment: Alignment.centerLeft,
                      child: Text(
                        acc,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Expanded(
                      child: Stack(
                        children: [
                          Container(
                            height: 14,
                            decoration: BoxDecoration(
                              color: Colors.grey.shade100,
                              borderRadius: BorderRadius.circular(6),
                            ),
                          ),
                          Container(
                            height: 14,
                            width:
                            MediaQuery.of(context).size.width * percent / 156,
                            decoration: BoxDecoration(
                              color: color,
                              borderRadius: BorderRadius.circular(6),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      "$percent%",
                      style: const TextStyle(fontSize: 11, color: Colors.grey),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 20),
      ],
    );
  }

  // -------------------------------
  // 🔹 노트 탭
  // -------------------------------
  Widget _buildNotesTab() {
    final notes = perfume["Notes"] as Map<String, dynamic>;

    // 🟢 단계별 색상 정의
    final Map<String, Color> noteColors = {
      "Top": const Color(0xFFE9EAE5),
      "Middle": const Color(0xFFD1D4CB),
      "Base": const Color(0xFFACAEA8),
    };

    // 🟢 한글 라벨 매핑
    final Map<String, String> noteLabels = {
      "Top": "탑 노트",
      "Middle": "미들 노트",
      "Base": "베이스 노트",
    };

    Widget buildNoteRow(String key, List<dynamic> items) {
      final circleColor = noteColors[key] ?? Colors.grey.shade400;
      final label = noteLabels[key] ?? key;

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label, // ✅ 한글 라벨 사용
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border.all(color: Colors.grey.shade300),
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: items.map((n) {
                return Container(
                  width: 68,
                  height: 68,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: circleColor,
                    shape: BoxShape.circle,
                  ),
                  child: Text(
                    n is Map ? (n["name"] ?? '') : n.toString(),
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 16),
        ],
      );
    }

    return Column(
      children: [
        buildNoteRow("Top", notes["Top"]),
        buildNoteRow("Middle", notes["Middle"]),
        buildNoteRow("Base", notes["Base"]),
      ],
    );
  }

  // -------------------------------
  // 🔹 발향 탭
  // -------------------------------
  Widget _buildSillageTab() {
    final longevity =
        double.parse(perfume["Longevity"].replaceAll('%', '')) / 100;
    final sillage =
        double.parse(perfume["Sillage"].replaceAll('%', '')) / 100;

    Widget buildDonut(String title, double value) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          ),
          const SizedBox(height: 8),

          // 박스
          Container(
            width: double.infinity,
            height: 180,
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey.shade300),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Center(
              child: SizedBox(
                width: 120,   // 👈 원 전체 지름
                height: 120,  // 👈 원 전체 지름
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    // ❗❗ 바로 이놈을 한 번 더 싸줘야 한다
                    SizedBox(
                      width: 180,
                      height: 180,
                      child: CircularProgressIndicator(
                        value: value,
                        strokeWidth: 12, // 두께
                        backgroundColor: Colors.grey.shade200,
                        valueColor: const AlwaysStoppedAnimation(
                          Color(0xFFD1D4CB),
                        ),
                      ),
                    ),
                    Text(
                      "${(value * 100).toStringAsFixed(1)}%",
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 20),
        ],
      );
    }

    return Column(
      children: [
        buildDonut("지속력", longevity),
        buildDonut("확산력", sillage),
      ],
    );
  }

}

