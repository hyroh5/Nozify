// lib/screens/perfume_detail_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:provider/provider.dart';

import '../widgets/topbar/appbar_ver2.dart';
import '../widgets/bottom_navbar.dart';
import '../widgets/custom_drawer.dart';
import 'home_screen.dart';
import 'storage/my_storage_main_screen.dart';

import '../services/api_client.dart';
import '../providers/auth_provider.dart';
import '../models/perfume_detail.dart';

class PerfumeDetailScreen extends StatefulWidget {
  final String perfumeId; // 서버의 perfume.id
  final bool fromStorage;

  const PerfumeDetailScreen({
    super.key,
    required this.perfumeId,
    this.fromStorage = false,
  });

  @override
  State<PerfumeDetailScreen> createState() => _PerfumeDetailScreenState();
}

class _PerfumeDetailScreenState extends State<PerfumeDetailScreen> {
  int _selectedIndex = 0;

  PerfumeDetailModel? _perfume;
  bool _loading = true;
  String? _error;

  bool _isFavorite = false;   // 위시 여부
  bool _isPurchased = false;  // 구매 여부

  // 색상 매핑
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
    _loadData();
  }

  // --------------------------
  // 🔥 향수 상세 + 위시/구매 여부 로딩
  // --------------------------
  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    final auth = context.read<AuthProvider>();
    final bool useAuth = auth.isLoggedIn;

    try {
      // 1) 상세 정보 로드
      final res = await ApiClient.I.get(
        "/catalog/perfumes/${widget.perfumeId}",
        auth: useAuth,
      );

      if (res.statusCode != 200) {
        throw Exception("status ${res.statusCode}");
      }

      final Map<String, dynamic> json = jsonDecode(res.body);
      final detail = PerfumeDetailModel.fromJson(json);

      bool fav = false;
      bool purchased = false;

      // 2) 로그인되어있으면 위시/구매도 체크
      if (auth.isLoggedIn) {
        // ⭐ 위시리스트
        final wRes = await ApiClient.I.get("/user/wishlist", auth: true);
        if (wRes.statusCode == 200) {
          final list = jsonDecode(wRes.body) as List<dynamic>;
          fav = list.any((item) {
            final p = item["perfume"] as Map<String, dynamic>?;
            return p != null && p["id"] == detail.id;
          });
        }

        // ⭐ 구매내역
        final pRes = await ApiClient.I.get("/user/purchase-history", auth: true);
        if (pRes.statusCode == 200) {
          final list = jsonDecode(pRes.body) as List<dynamic>;
          purchased = list.any((item) {
            final p = item["perfume"] as Map<String, dynamic>?;
            return p != null && p["id"] == detail.id;
          });
        }
      }

      setState(() {
        _perfume = detail;
        _isFavorite = fav;
        _isPurchased = purchased;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = "향수 정보를 불러오지 못했습니다.";
        _loading = false;
      });
    }
  }

  // --------------------------
  // ❤️ 위시리스트 토글
  // --------------------------
  Future<void> _toggleWishlist() async {
    final auth = context.read<AuthProvider>();
    if (!auth.isLoggedIn) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("로그인 후 이용할 수 있습니다.")),
      );
      return;
    }

    if (_perfume == null) return;

    try {
      if (_isFavorite) {
        // 🔥 삭제
        final res = await ApiClient.I.delete(
          "/user/wishlist/${_perfume!.id}",
          auth: true,
        );
        if (res.statusCode == 200) {
          setState(() => _isFavorite = false);
        }
      } else {
        // 🔥 추가 (perfume_id는 query)
        final res = await ApiClient.I.post(
          "/user/wishlist?perfume_id=${_perfume!.id}",
          auth: true,
        );
        if (res.statusCode == 200) {
          setState(() => _isFavorite = true);
        }
      }
    } catch (_) {}
  }

  // --------------------------
  // 👜 구매 토글
  // --------------------------
  Future<void> _togglePurchased() async {
    final auth = context.read<AuthProvider>();
    if (!auth.isLoggedIn) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("로그인 후 이용할 수 있습니다.")),
      );
      return;
    }

    if (_perfume == null) return;

    try {
      if (_isPurchased) {
        final res = await ApiClient.I.delete(
          "/user/purchase-history/${_perfume!.id}",
          auth: true,
        );
        if (res.statusCode == 200) {
          setState(() => _isPurchased = false);
        }
      } else {
        final res = await ApiClient.I.post(
          "/user/purchase-history?perfume_id=${_perfume!.id}",
          auth: true,
        );
        if (res.statusCode == 200) {
          setState(() => _isPurchased = true);
        }
      }
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final perfume = _perfume;

    return Scaffold(
      appBar: AppBarVer2(
        onBack: () {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (_) => widget.fromStorage
                  ? const MyStorageMainScreen()
                  : const HomeScreen(),
            ),
          );
        },
      ),
      endDrawer: const CustomDrawer(),
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : _error != null
          ? Center(child: Text(_error!))
          : perfume == null
          ? Center(child: Text("향수 정보를 찾을 수 없습니다."))
          : _buildDetail(perfume),
      bottomNavigationBar: BottomNavBar(
        currentIndex: 0,
        onTap: (index) {
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
        },
      ),
    );
  }

  // --------------------------
  // 🔥 실제 UI
  // --------------------------
  Widget _buildDetail(PerfumeDetailModel perfume) {
    return SingleChildScrollView(
      child: Column(
        children: [
          const SizedBox(height: 12),

          // 이미지
          Container(
            width: double.infinity,
            height: 264,
            color: Colors.grey[100],
            child: perfume.imageUrl != null
                ? Image.network(
              perfume.imageUrl!,
              width: 264,
              height: 264,
              fit: BoxFit.cover,
            )
                : Icon(Icons.image_not_supported, size: 80, color: Colors.grey),
          ),

          const SizedBox(height: 32),

          // 정보
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  perfume.brandName ?? '',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
                SizedBox(height: 8),
                Text(
                  perfume.name,
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 8),
                if (perfume.price != null)
                  Text(
                    "₩${(perfume.price! * 1300).toStringAsFixed(0)}",
                    style: TextStyle(fontSize: 15),
                  ),
                SizedBox(height: 12),

                // ❤️ + 👜
                Row(
                  children: [
                    IconButton(
                      icon: Icon(
                        _isFavorite
                            ? Icons.favorite
                            : Icons.favorite_border_outlined,
                        color: _isFavorite ? Colors.redAccent : Colors.grey[700],
                      ),
                      onPressed: _toggleWishlist,
                    ),
                    IconButton(
                      icon: Icon(
                        _isPurchased
                            ? Icons.add_circle
                            : Icons.add_circle_outline,
                        color:
                        _isPurchased ? Color(0xFF3C463A) : Colors.grey[700],
                      ),
                      onPressed: _togglePurchased,
                    ),
                  ],
                ),
              ],
            ),
          ),

          // 탭
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Column(
              children: [
                SizedBox(height: 32),
                _buildTabBar(),
                SizedBox(height: 24),
                if (_selectedIndex == 0) _buildAccordsTab(perfume),
                if (_selectedIndex == 1) _buildNotesTab(perfume),
                if (_selectedIndex == 2) _buildSillageTab(perfume),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // --------------------------
  // 탭 UI
  // --------------------------
  Widget _buildTabBar() {
    const tabs = ["계열", "노트", "발향"];

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: List.generate(tabs.length, (i) {
        final selected = _selectedIndex == i;
        return GestureDetector(
          onTap: () => setState(() => _selectedIndex = i),
          child: Column(
            children: [
              Text(
                tabs[i],
                style: TextStyle(
                  fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                  fontSize: 15,
                  color: selected ? Colors.black : Colors.grey,
                ),
              ),
              SizedBox(height: 4),
              if (selected)
                Container(width: 24, height: 2, color: Colors.black),
            ],
          ),
        );
      }),
    );
  }

  // --------------------------
  // 계열 탭
  // --------------------------
  Widget _buildAccordsTab(PerfumeDetailModel perfume) {
    final accords = perfume.mainAccords ?? [];
    final raw = perfume.mainAccordsPercentage as Map<String, dynamic>? ?? {};
    final percentages = raw.map((k, v) => MapEntry(k, v.toString()));

    // 그룹 매핑
    final Map<String, List<String>> groups = {
      "플로럴": ["floral", "rose", "jasmine", "violet"],
      "프루티": ["fruit", "apple", "pear"],
      "시트러스": ["citrus", "lemon", "bergamot"],
      "우디": ["wood", "cedar", "sandalwood"],
      "그린": ["green", "leaf", "grass"],
      "구르망": ["vanilla", "caramel", "coffee"],
      "아쿠아틱": ["aquatic", "marine"],
      "레더": ["leather", "tobacco"],
      "머스크": ["musk", "powdery"],
      "기타": [],
    };

    // 색상
    final Map<String, Color> colors = {
      "플로럴": Color(0xFFFFC1CC),
      "프루티": Color(0xFFFFE4B5),
      "시트러스": Color(0xFFFFFFB3),
      "우디": Color(0xFFD7B899),
      "그린": Color(0xFFB4E197),
      "구르망": Color(0xFFFFDAB9),
      "아쿠아틱": Color(0xFFB2EBF2),
      "레더": Color(0xFFE0C097),
      "머스크": Color(0xFFE6E6FA),
      "기타": Colors.grey.shade300,
    };

    Map<String, int> count = {for (var k in colors.keys) k: 0};

    for (var acc in accords) {
      final l = acc.toLowerCase();
      bool matched = false;

      for (var entry in groups.entries) {
        if (entry.value.any((x) => l.contains(x))) {
          count[entry.key] = count[entry.key]! + 1;
          matched = true;
          break;
        }
      }

      if (!matched) count["기타"] = count["기타"]! + 1;
    }

    final total =
    count.values.fold<int>(0, (a, b) => a + b).clamp(1, 999999);
    final valid = count.keys.where((k) => count[k]! > 0).toList();

    final sections = valid.map((g) {
      final pct = count[g]! / total * 100;
      return PieChartSectionData(
        color: colors[g],
        value: count[g]!.toDouble(),
        radius: 60,
        title: "$g\n${pct.toStringAsFixed(1)}%",
        titleStyle: TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
      );
    }).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("계열별 분포", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        SizedBox(height: 12),
        if (sections.isEmpty)
          Text("계열 정보가 없습니다.")
        else
          Center(
            child: SizedBox(
              height: 260,
              width: 260,
              child: PieChart(
                PieChartData(
                  startDegreeOffset: -90,
                  centerSpaceRadius: 50,
                  sections: sections,
                  sectionsSpace: 2,
                ),
              ),
            ),
          ),
        SizedBox(height: 24),
        Text("세부 어코드", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        SizedBox(height: 12),

        // 어코드 리스트
        Container(
          padding: EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.08),
                blurRadius: 6,
                offset: Offset(0, 3),
              )
            ],
          ),
          child: Column(
            children: accords.map((acc) {
              final color = accordColors[acc.toLowerCase()] ?? Colors.grey.shade300;
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
                      child: Text(acc, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 11)),
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
                            width: MediaQuery.of(context).size.width * percent / 156,
                            decoration: BoxDecoration(
                              color: color,
                              borderRadius: BorderRadius.circular(6),
                            ),
                          )
                        ],
                      ),
                    ),
                    SizedBox(width: 8),
                    Text("$percent%", style: TextStyle(fontSize: 11)),
                  ],
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }

  // --------------------------
  // 노트 탭
  // --------------------------
  Widget _buildNotesTab(PerfumeDetailModel p) {
    final top = p.topNotes ?? [];
    final mid = p.middleNotes ?? [];
    final base = p.baseNotes ?? [];

    final notes = {
      "Top": top,
      "Middle": mid,
      "Base": base,
    };

    final colors = {
      "Top": Color(0xFFE9EAE5),
      "Middle": Color(0xFFD1D4CB),
      "Base": Color(0xFFACAEA8),
    };

    Widget row(String key, List<dynamic> items) {
      if (items.isEmpty) return SizedBox.shrink();
      final color = colors[key] ?? Colors.grey.shade300;
      final label = switch (key) {
        "Top" => "탑 노트",
        "Middle" => "미들 노트",
        "Base" => "베이스 노트",
        _ => key,
      };

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(fontWeight: FontWeight.bold)),
          SizedBox(height: 8),
          Container(
            padding: EdgeInsets.symmetric(vertical: 12),
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border.all(color: Colors.grey.shade300),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: items.map((n) {
                final text = n is Map<String, dynamic> ? n["name"] ?? "" : n.toString();
                return Container(
                  width: 68,
                  height: 68,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(color: color, shape: BoxShape.circle),
                  child: Text(text, textAlign: TextAlign.center, style: TextStyle(fontSize: 10)),
                );
              }).toList(),
            ),
          ),
          SizedBox(height: 16),
        ],
      );
    }

    return Column(
      children: [
        row("Top", notes["Top"]!),
        row("Middle", notes["Middle"]!),
        row("Base", notes["Base"]!),
      ],
    );
  }

  // --------------------------
  // 발향(지속력/확산력)
  // --------------------------
  Widget _buildSillageTab(PerfumeDetailModel p) {
    final lonRaw = p.longevity ?? 0.0;
    final silRaw = p.sillage ?? 0.0;

    final lon = (lonRaw / 100).clamp(0.0, 1.0);
    final sil = (silRaw / 100).clamp(0.0, 1.0);

    Widget donut(String label, double value, double raw) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(fontWeight: FontWeight.bold)),
          SizedBox(height: 8),
          Container(
            height: 180,
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey.shade300),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Center(
              child: SizedBox(
                width: 120,
                height: 120,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    CircularProgressIndicator(
                      value: value,
                      strokeWidth: 12,
                      backgroundColor: Colors.grey.shade200,
                      valueColor: AlwaysStoppedAnimation(Color(0xFFD1D4CB)),
                    ),
                    Text("${raw.toStringAsFixed(1)}%", style: TextStyle(fontSize: 14)),
                  ],
                ),
              ),
            ),
          ),
          SizedBox(height: 20),
        ],
      );
    }

    return Column(
      children: [
        donut("지속력", lon, lonRaw),
        donut("확산력", sil, silRaw),
      ],
    );
  }
}
