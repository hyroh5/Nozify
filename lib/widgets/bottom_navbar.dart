// lib/widgets/bottom_navbar.dart
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sw_showcase/screens/home_screen.dart';
import 'package:sw_showcase/screens/camera/camera_screen.dart';
import 'package:sw_showcase/screens/storage/my_storage_main_screen.dart';
import 'package:sw_showcase/screens/pbti/pbti_intro_screen.dart';
import 'package:sw_showcase/screens/pbti/pbti_main_screen.dart';

class BottomNavBar extends StatelessWidget {
  final int currentIndex;
  final Function(int) onTap;

  const BottomNavBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return BottomNavigationBar(
      currentIndex: currentIndex,
      type: BottomNavigationBarType.fixed,
      backgroundColor: Colors.white,
      selectedItemColor: Colors.black,
      unselectedItemColor: Colors.grey,
      showSelectedLabels: true,
      showUnselectedLabels: true,

      onTap: (index) async {
        if (index == 0) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const HomeScreen()),
          );
          return;
        }

        if (index == 1) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => CameraScreen()), // ❗ const 금지
          );
          return;
        }

        if (index == 2) {
          final prefs = await SharedPreferences.getInstance();
          final hasPbti = prefs.getStringList('pbtiResults')?.isNotEmpty ?? false;

          if (hasPbti) {
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (_) => const PbtiMainScreen()),
            );
          } else {
            Navigator.pushReplacement(
              context,
              // ❗ 클래스명 정확히: PBTIIntro1Screen (대문자 BTI)
              MaterialPageRoute(builder: (_) => PBTIIntroScreen()),
            );
          }
          return;
        }

        if (index == 3) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const MyStorageMainScreen()),
          );
          return;
        }

        onTap(index);
      },

      items: const [
        BottomNavigationBarItem(icon: Icon(Icons.home_outlined), label: '홈'),
        BottomNavigationBarItem(icon: Icon(Icons.center_focus_weak), label: '렌즈'),
        BottomNavigationBarItem(icon: Icon(Icons.person_search_outlined), label: '맞춤 추천'),
        BottomNavigationBarItem(icon: Icon(Icons.favorite_border), label: '내 저장소'),
      ],
    );
  }
}
