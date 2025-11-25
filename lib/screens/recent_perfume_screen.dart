// lib/screens/recent_perfume_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/recent_perfume_provider.dart';
import '../widgets/topbar/appbar_ver2.dart';
import '../widgets/bottom_navbar.dart';
import '../widgets/custom_drawer.dart';
import 'home_screen.dart';
import 'perfume_detail_screen.dart';

class RecentPerfumeScreen extends StatefulWidget {
  const RecentPerfumeScreen({super.key});

  @override
  State<RecentPerfumeScreen> createState() => _RecentPerfumeScreenState();
}

class _RecentPerfumeScreenState extends State<RecentPerfumeScreen> {
  int _selectedIndex = 3;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<RecentPerfumeProvider>().fetchRecent();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<RecentPerfumeProvider>();
    final recent = provider.items;

    // ✅ 3개씩 묶어서 행 단위로 구성 (원래 로직 그대로)
    final List<List<RecentPerfume>> rows = [];
    for (int i = 0; i < recent.length; i += 3) {
      rows.add(
        recent.sublist(i, (i + 3 > recent.length) ? recent.length : i + 3),
      );
    }

    return Scaffold(
      appBar: const AppBarVer2(),
      endDrawer: const CustomDrawer(),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '최근 본 제품',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: recent.isEmpty
                  ? const Center(
                child: Text(
                  '아직 본 향수가 없습니다.',
                  style: TextStyle(color: Colors.black54),
                ),
              )
                  : ListView.builder(
                itemCount: rows.length,
                itemBuilder: (context, rowIndex) {
                  final rowItems = rows[rowIndex];
                  return Container(
                    decoration: const BoxDecoration(
                      border: Border(
                        top: BorderSide(color: Colors.black12),
                      ),
                    ),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: List.generate(3, (i) {
                        if (i < rowItems.length) {
                          return _buildPerfumeCard(rowItems[i]);
                        } else {
                          return const SizedBox(width: 100);
                        }
                      }),
                    ),
                  );
                },
              ),
            ),
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

  Widget _buildPerfumeCard(RecentPerfume perfume) {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => PerfumeDetailScreen(
              perfumeId: perfume.id,
              fromStorage: true,
            ),
          ),
        );
      },
      child: SizedBox(
        width: 100,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            ClipRRect(
              child: perfume.imageUrl != null && perfume.imageUrl!.isNotEmpty
                  ? Image.network(
                perfume.imageUrl!,
                height: 108,
                width: 90,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) {
                  return Image.asset(
                    'assets/images/dummy.jpg',
                    fit: BoxFit.fitHeight,
                  );
                },
              )
                  : Image.asset(
                'assets/images/dummy.jpg',
                height: 108,
                width: 90,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              perfume.brandName,
              style: const TextStyle(color: Colors.grey, fontSize: 10),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 2),
            Text(
              perfume.name,
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
}
