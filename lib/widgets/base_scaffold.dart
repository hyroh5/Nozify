import 'package:flutter/material.dart';
import 'custom_drawer.dart';

class BaseScaffold extends StatelessWidget {
  final PreferredSizeWidget appBar;
  final Widget body;
  final Widget? bottomNav;

  const BaseScaffold({
    super.key,
    required this.appBar,
    required this.body,
    this.bottomNav,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar,
      drawer: const CustomDrawer(),
      body: body,
      bottomNavigationBar: bottomNav,
    );
  }
}
