// lib/screens/storage/my_storage_main_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../widgets/topbar/appbar_ver2.dart';
import '../../widgets/bottom_navbar.dart';
import '../../widgets/custom_drawer.dart';
import '../home_screen.dart';

import 'my_wishlist_screen.dart';
import 'my_purchased_screen.dart';
import 'my_calendar_screen.dart';

import '../../providers/wishlist_provider.dart';
import '../../providers/purchased_provider.dart';
import '../../providers/calendar_provider.dart';
import '../perfume_detail_screen.dart';

class MyStorageMainScreen extends StatefulWidget {
  const MyStorageMainScreen({super.key});

  @override
  State<MyStorageMainScreen> createState() => _MyStorageMainScreenState();
}

class _MyStorageMainScreenState extends State<MyStorageMainScreen> {
  int _bottomIndex = 3;

  List<Map<String, String>> previewWish = [];
  List<Map<String, String>> previewPurchased = [];

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final wishlistProvider = context.read<WishlistProvider>();
      final purchasedProvider = context.read<PurchasedProvider>();
      final calendarProvider = context.read<CalendarProvider>();

      await wishlistProvider.fetchWishlist();
      await purchasedProvider.fetchPurchased();
      calendarProvider.loadFromStorage();

      // ⭐ provider.items 로부터 미리보기 3개 추출
      final wish = wishlistProvider.items.take(3).map((p) {
        return {
          "image": p.imageUrl ?? "assets/images/dummy.jpg",
          "brand": p.brandName,
          "name": p.name,
          "id": p.perfumeId,
        };
      }).toList();

      final bought = purchasedProvider.items.take(3).map((p) {
        return {
          "image": p.imageUrl ?? "assets/images/dummy.jpg",
          "brand": p.brandName,
          "name": p.name,
          "id": p.perfumeId,
        };
      }).toList();

      setState(() {
        previewWish = wish;
        previewPurchased = bought;
      });
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
              items: previewWish,
              onMore: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MyWishlistScreen()),
              ),
            ),
            const SizedBox(height: 20),
            _buildSection(
              title: '내가 구매한 향수',
              items: previewPurchased,
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
        currentIndex: _bottomIndex,
        onTap: (index) {
          setState(() => _bottomIndex = index);
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

  // 📦 공통 섹션
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

        // 카드 3개 프리뷰
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
                return _buildPerfumeCard(items[i]);
              } else {
                return const SizedBox(width: 100);
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

  // 📷 향수 미리보기 카드
  Widget _buildPerfumeCard(Map<String, String> perfume) {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => PerfumeDetailScreen(
              perfumeId: perfume["id"]!,
              fromStorage: true,
            ),
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
              child: perfume['image']!.startsWith('http')
                  ? Image.network(
                perfume['image']!,
                height: 108,
                width: 90,
                fit: BoxFit.cover,
              )
                  : Image.asset(
                perfume['image']!,
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
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 11,
              ),
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  // 📅 캘린더 프리뷰 (그대로)
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
        // 제목
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

        // 캘린더 박스
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
              // 요일
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

                      final hasRecord = calendar.hasRecord(
                        DateTime(now.year, now.month, dayNum),
                      );

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
                            if (hasRecord)
                              Container(
                                width: 6,
                                height: 6,
                                decoration: const BoxDecoration(
                                  color: Colors.grey,
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
