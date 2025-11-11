import 'package:flutter/material.dart';
import '../widgets/topbar/appbar_ver2.dart';

class DummyCategoryScreen extends StatelessWidget {
  final String categoryName;
  const DummyCategoryScreen({super.key, required this.categoryName});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const AppBarVer2(),
      body: Center(
        child: Text(
          '$categoryName 계열 페이지 (구현 예정)',
          style: const TextStyle(fontSize: 18, color: Colors.grey),
        ),
      ),
    );
  }
}
