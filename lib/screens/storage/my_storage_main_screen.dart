// my—storage—main—screen。dart
import 'package:flutter/material.dart';
import '../../widgets/topbar/appbar_ver2.dart';
import '../../widgets/bottom_navbar.dart';
import '../home_screen.dart';
import 'my_wishlist_screen.dart';
import 'my_purchased_screen.dart';
import 'my_calendar_screen.dart';
import '../perfume_detail_screen.dart';
import 'package:provider/provider.dart';
import '../../providers/calendar_provider.dart';
import '../../providers/auth_provider.dart';
import '../../providers/storage_manager.dart';
import '../../widgets/custom_drawer.dart';

class MyStorageMainScreen extends StatefulWidget {
  const MyStorageMainScreen({super.key});

  @override
  State<MyStorageMainScreen> createState() => _MyStorageMainScreenState();
}

class _MyStorageMainScreenState extends State<MyStorageMainScreen> {
  int _selectedIndex = 3;

  List<Map<String, String>> wishlist = [];
  List<Map<String, String>> purchased = [];

  @override
  void initState() {
    super.initState();
    _loadStorage();
  }

  Future<void> _loadStorage() async {
    final auth = context.read<AuthProvider>();
    final email = auth.user?.email;
    final wish = await StorageManager.loadList(StorageManager.wishlistKey, email ?? 'guest');
    final buy = await StorageManager.loadList(StorageManager.purchasedKey, email ?? 'guest');
    setState(() {
      wishlist = wish;
      purchased = buy;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBarVer2(
        onBack: () {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const HomeScreen()),
          );
        },
      ),
      endDrawer: const CustomDrawer(),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSection(
              title: '내 위시리스트',
              items: wishlist,
              onMore: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MyWishlistScreen()),
              ),
            ),
            const SizedBox(height: 20),
            _buildSection(
              title: '내가 구매한 향수',
              items: purchased,
              onMore: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MyPurchasedScreen()),
              ),
            ),
            const SizedBox(height: 20),
            _buildCalendarPreview(context),
          ],
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

  // 📦 공통 섹션 (위시리스트, 구매)
  Widget _buildSection({
    required String title,
    required List<Map<String, String>> items,
    required VoidCallback onMore,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 제목 + 더보기
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title,
                style: const TextStyle(
                    fontSize: 20, fontWeight: FontWeight.bold)),
            GestureDetector(
              onTap: onMore,
              child: const Text('더보기 >',
                  style: TextStyle(color: Colors.grey, fontSize: 12)),
            ),
          ],
        ),
        const SizedBox(height: 8),

        // 카드 섹션 (3개 고정 + 상하 테두리)
        Container(
          decoration: const BoxDecoration(
            border: Border(
              top: BorderSide(color: Colors.black12),
              bottom: BorderSide(color: Colors.black12),
            ),
          ),
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: List.generate(3, (i) {
              if (i < items.length) {
                final perfume = items[i];
                return _buildPerfumeCard(perfume);
              } else {
                return const SizedBox(width: 100); // 빈칸 유지
              }
            }),
          ),
        ),

        if (items.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 20),
            child: Center(
              child: Text(
                '아직 향수가 없습니다.',
                style: TextStyle(color: Colors.black45, fontSize: 13),
              ),
            ),
          ),
      ],
    );
  }

  // 향수 카드 (MyWishlistScreen 스타일)
  Widget _buildPerfumeCard(Map<String, String> perfume) {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => const PerfumeDetailScreen(fromStorage: true),
          ),
        );
      },
      child: SizedBox(
        width: 100,
        height: 160,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            ClipRRect(
              child: Image.asset(
                perfume['image'] ?? 'assets/images/dummy.jpg',
                height: 108,
                width: 90,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              perfume['brand'] ?? '',
              style: const TextStyle(color: Colors.grey, fontSize: 10),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 2),
            Text(
              perfume['name'] ?? '',
              style:
              const TextStyle(fontWeight: FontWeight.bold, fontSize: 11),
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  // 📅 캘린더 프리뷰 (한 달 요약 + 향수 기록 점)
  Widget _buildCalendarPreview(BuildContext context) {
    final calendar = context.watch<CalendarProvider>();
    final now = DateTime.now();

    final firstDay = DateTime(now.year, now.month, 1);
    final daysInMonth = DateTime(now.year, now.month + 1, 0).day;
    final startWeekday = firstDay.weekday % 7;
    final totalCells = startWeekday + daysInMonth;
    final rows = (totalCells / 7).ceil();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('향수 캘린더',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            GestureDetector(
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MyCalendarScreen()),
              ),
              child: const Text('더보기 >',
                  style: TextStyle(color: Colors.grey, fontSize: 13)),
            ),
          ],
        ),
        const SizedBox(height: 8),

        // 캘린더 프리뷰
        Container(
          decoration: const BoxDecoration(
            border: Border(
              top: BorderSide(color: Colors.black12),
              bottom: BorderSide(color: Colors.black12),
            ),
          ),
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
          child: Column(
            children: [
              // 요일 헤더
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: const [
                  Text('일', style: TextStyle(color: Colors.grey, fontSize: 12)),
                  Text('월', style: TextStyle(color: Colors.grey, fontSize: 12)),
                  Text('화', style: TextStyle(color: Colors.grey, fontSize: 12)),
                  Text('수', style: TextStyle(color: Colors.grey, fontSize: 12)),
                  Text('목', style: TextStyle(color: Colors.grey, fontSize: 12)),
                  Text('금', style: TextStyle(color: Colors.grey, fontSize: 12)),
                  Text('토', style: TextStyle(color: Colors.grey, fontSize: 12)),
                ],
              ),
              const SizedBox(height: 6),

              // 날짜 그리드
              Column(
                children: List.generate(rows, (r) {
                  return Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: List.generate(7, (c) {
                      final idx = r * 7 + c;
                      if (idx < startWeekday || idx >= totalCells) {
                        return const SizedBox(width: 28, height: 32);
                      }
                      final dayNum = idx - startWeekday + 1;
                      final has = calendar.hasRecord(
                        DateTime(now.year, now.month, dayNum),
                      );
                      final dotColor = has ? Colors.grey : null;

                      return SizedBox(
                        width: 28,
                        height: 32,
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              '$dayNum',
                              style: const TextStyle(
                                fontSize: 11,
                                color: Colors.black87,
                              ),
                            ),
                            const SizedBox(height: 2),
                            if (dotColor != null)
                              Container(
                                width: 6,
                                height: 6,
                                decoration: BoxDecoration(
                                  color: dotColor,
                                  shape: BoxShape.circle,
                                ),
                              ),
                          ],
                        ),
                      );
                    }),
                  );
                }),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
