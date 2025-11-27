import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/search_provider.dart';
import '../../screens/search_result_screen.dart';

class AppBarVer1 extends StatefulWidget implements PreferredSizeWidget {
  const AppBarVer1({super.key});

  @override
  Size get preferredSize => const Size.fromHeight(130);

  @override
  State<AppBarVer1> createState() => _AppBarVer1State();
}

class _AppBarVer1State extends State<AppBarVer1> {
  final TextEditingController controller = TextEditingController();
  final FocusNode _focusNode = FocusNode();

  final LayerLink _layerLink = LayerLink();
  OverlayEntry? _overlayEntry;

  @override
  void initState() {
    super.initState();

    _focusNode.addListener(() {
      if (_focusNode.hasFocus) {
        _insertOverlay();
      } else {
        _removeOverlay();
      }
      setState(() {});
    });
  }

  @override
  void dispose() {
    _removeOverlay();
    super.dispose();
  }

  void _insertOverlay() {
    if (_overlayEntry != null) return;

    _overlayEntry = OverlayEntry(
      builder: (context) {
        final suggestions =
            context.watch<SearchProvider>().suggestions;

        if (suggestions.isEmpty) return const SizedBox.shrink();

        return Positioned(
          width: MediaQuery.of(context).size.width - 32,
          child: CompositedTransformFollower(
            link: _layerLink,
            offset: const Offset(0, 56),
            showWhenUnlinked: false,
            child: Material(
              color: Colors.white,
              elevation: 4,
              borderRadius: BorderRadius.circular(10),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxHeight: 240),
                child: ListView.builder(
                  padding: EdgeInsets.zero,
                  itemCount: suggestions.length,
                  itemBuilder: (_, i) {
                    final s = suggestions[i];
                    return ListTile(
                      title: Text(s.name, style: const TextStyle(fontSize: 14)),
                      subtitle: Text(
                        s.type,
                        style: const TextStyle(fontSize: 11, color: Colors.grey),
                      ),
                      onTap: () {
                        controller.text = s.name;
                        _goSearch(context, s.name);
                      },
                    );
                  },
                ),
              ),
            ),
          ),
        );
      },
    );

    Overlay.of(context).insert(_overlayEntry!);
    print("✨ Overlay inserted");
  }

  void _removeOverlay() {
    if (_overlayEntry != null) {
      _overlayEntry!.remove();
      _overlayEntry = null;
      print("🗑 Overlay removed");
    }
  }

  void _goSearch(BuildContext context, String q) {
    final query = q.trim();
    if (query.isEmpty) return;

    FocusScope.of(context).unfocus();
    context.read<SearchProvider>().clearSuggestions();

    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => SearchResultScreen(query: query)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(height: 12),
          // 로고 + 메뉴
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Image.asset('assets/images/appbar_logo.png',
                  height: 26, fit: BoxFit.contain),
              Builder(
                builder: (inner) => IconButton(
                  icon: const Icon(Icons.menu, color: Colors.black),
                  onPressed: () => Scaffold.of(inner).openEndDrawer(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 0),

          // 검색창 (Overlay anchor)
          CompositedTransformTarget(
            link: _layerLink,
            child: TextField(
              controller: controller,
              focusNode: _focusNode,
              onChanged: (q) =>
                  context.read<SearchProvider>().fetchSuggest(q),
              onSubmitted: (q) => _goSearch(context, q),
              decoration: InputDecoration(
                prefixIcon: const Icon(Icons.search, color: Colors.grey),
                hintText: "향수 이름, 브랜드 검색",
                filled: true,
                fillColor: Colors.grey[100],
                contentPadding: const EdgeInsets.symmetric(horizontal: 12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
