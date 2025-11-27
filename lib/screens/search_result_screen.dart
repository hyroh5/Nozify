import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/search_provider.dart';
import '../../widgets/topbar/appbar_ver2.dart';
import 'perfume_detail_screen.dart';

class SearchResultScreen extends StatefulWidget {
  final String query;

  const SearchResultScreen({super.key, required this.query});

  @override
  State<SearchResultScreen> createState() => _SearchResultScreenState();
}

class _SearchResultScreenState extends State<SearchResultScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      context.read<SearchProvider>().search(widget.query);
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<SearchProvider>();
    final perfumes = provider.results;

    final valid = perfumes.where((p) =>
    p.imageUrl != null &&
        p.imageUrl!.isNotEmpty &&
        p.imageUrl!.startsWith("http")).toList();

    return Scaffold(
      appBar: const AppBarVer2(),
      body: provider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : valid.isEmpty
          ? const Center(child: Text("검색 결과가 없습니다."))
          : GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate:
        const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 3,
          childAspectRatio: 0.56,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
        ),
        itemCount: valid.length,
        itemBuilder: (_, i) {
          final perfume = valid[i];

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
                    errorBuilder: (_, __, ___) => Image.asset(
                      'assets/images/dummy.jpg',
                      fit: BoxFit.cover,
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  perfume.brandName,
                  style: const TextStyle(
                    fontSize: 10,
                    color: Colors.grey,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  perfume.name,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
