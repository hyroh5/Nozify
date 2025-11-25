// lib/screens/storage/my_purchased_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../widgets/topbar/appbar_ver2.dart';
import '../../widgets/bottom_navbar.dart';
import '../home_screen.dart';
import '../perfume_detail_screen.dart';
import '../../providers/auth_provider.dart';
import '../../providers/purchased_provider.dart';
import '../../widgets/custom_drawer.dart';

class MyPurchasedScreen extends StatefulWidget {
  const MyPurchasedScreen({super.key});

  @override
  State<MyPurchasedScreen> createState() => _MyPurchasedScreenState();
}

class _MyPurchasedScreenState extends State<MyPurchasedScreen> {
  int _selectedIndex = 3;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final auth = context.read<AuthProvider>();

      if (!auth.isLoggedIn) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("로그인 후 이용할 수 있습니다.")),
        );
        return;
      }

      await context.read<PurchasedProvider>().fetchPurchased();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<PurchasedProvider>();
    final perfumes = provider.items;

    final List<List<PurchasedItem>> rows = [];
    for (int i = 0; i < perfumes.length; i += 3) {
      rows.add(
        perfumes.sublist(i, (i + 3 > perfumes.length) ? perfumes.length : i + 3),
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
            const Text('내가 구매한 향수',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Expanded(
              child: perfumes.isEmpty
                  ? const Center(
                child: Text(
                  '아직 구매한 향수가 없습니다.',
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

  Widget _buildPerfumeCard(PurchasedItem perfume) {
    return GestureDetector(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => PerfumeDetailScreen(
              perfumeId: perfume.perfumeId,
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
