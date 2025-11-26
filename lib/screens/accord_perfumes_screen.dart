// lib/screens/catalog/accord_perfumes_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/accord_provider.dart';
import 'perfume_detail_screen.dart';
import '../services/api_client.dart';
import '../widgets/topbar/appbar_ver2.dart';

class AccordPerfumesScreen extends StatefulWidget {
  final String accordName;

  const AccordPerfumesScreen({
    super.key,
    required this.accordName
  });

  @override
  State<AccordPerfumesScreen> createState() => _AccordPerfumesScreenState();
}

class _AccordPerfumesScreenState extends State<AccordPerfumesScreen> {
  @override
  void initState() {
    super.initState();
    print(ApiClient.I.buildUri("/catalog/perfumes", {"accords": "floral"}).toString());
    Future.microtask(() {
      context
          .read<AccordProvider>()
          .fetchPerfumesByAccord(widget.accordName, limit: 50);
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AccordProvider>();
    final perfumes = provider.perfumes;

    // 🔥 이미지 URL 있는 애들만 filtering
    final validPerfumes = perfumes.where((p) {
      return p.imageUrl != null &&
          p.imageUrl!.isNotEmpty &&
          p.imageUrl!.startsWith("http");
    }).toList();

    return Scaffold(
      appBar: AppBarVer2(),
      body: provider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : validPerfumes.isEmpty
          ? const Center(child: Text("향수를 찾을 수 없습니다."))
          : GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 3,
          childAspectRatio: 0.56,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
        ),
        itemCount: validPerfumes.length,
        itemBuilder: (context, index) {
          final perfume = validPerfumes[index];

          return GestureDetector(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => PerfumeDetailScreen(
                    perfumeId: perfume.id,
                  ),
                ),
              );
            },
            child: Column(
              children: [
                Container(
                  width: 100,
                  height: 120,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(8),
                    color: Colors.grey[200],
                  ),
                  clipBehavior: Clip.hardEdge,
                  child: Image.network(
                    perfume.imageUrl!,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) {
                      // ❌ 에러면 그냥 빈 이미지 → 카드 삭제됨
                      return Image.asset(
                        'assets/images/dummy.jpg',
                        fit: BoxFit.cover,
                      );
                    },
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  perfume.brandName,
                  style: const TextStyle(
                      fontSize: 10, color: Colors.grey),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  perfume.name,
                  style: const TextStyle(
                      fontSize: 11, fontWeight: FontWeight.bold),
                  maxLines: 1,
                  textAlign: TextAlign.center,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
