import 'package:flutter/material.dart';

class AppBarVer2 extends StatelessWidget implements PreferredSizeWidget {
  final Color backgroundColor; // 외부에서 배경색 파라미터 받기 가능
  final Color iconColor;       // 외부에서 아이콘 색상 파라미터 받기 가능
  final VoidCallback? onBack;  // 뒤로가기 동작을 외부에서 정의 가능

  const AppBarVer2({
    super.key,
    this.onBack,
    this.backgroundColor = Colors.white,
    this.iconColor = Colors.black,
  });

  @override
  Size get preferredSize => const Size.fromHeight(56);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      backgroundColor: backgroundColor,
      elevation: 0,
      leading: IconButton(
        icon: Icon(Icons.arrow_back, color: iconColor),
        onPressed: onBack ?? () => Navigator.pop(context),
      ),
      actions: [
        // ✅ Builder로 감싸야 Scaffold context를 찾을 수 있음
        Builder(
          builder: (context) => IconButton(
            icon: Icon(Icons.menu, color: iconColor),
            onPressed: () => Scaffold.of(context).openEndDrawer(),
          ),
        ),
      ],
    );
  }
}
