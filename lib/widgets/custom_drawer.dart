import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/auth_provider.dart';
import '../screens/login_screen.dart';
import '../screens/my_info_screen.dart';
import '../screens/recent_perfume_screen.dart';
import '../screens/home_screen.dart';

class CustomDrawer extends StatelessWidget {
  const CustomDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final isLoggedIn = auth.isLoggedIn;
    final user = auth.user;

    return Drawer(
      backgroundColor: Colors.white,
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ===========================
              // 상단 사용자 정보
              // ===========================
              Row(
                children: [
                  const SizedBox(height: 40, width: 20),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          isLoggedIn
                              ? '${user?.name ?? '사용자'}님'
                              : '비회원으로 이용 중',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          isLoggedIn
                              ? user?.email ?? ''
                              : '로그인 시 더 많은 기능을 이용할 수 있습니다.',
                          style: const TextStyle(
                            fontSize: 11,
                            color: Colors.grey,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 24),
              const Divider(thickness: 1),

              // ===========================
              // 로그인 상태별 메뉴
              // ===========================
              Expanded(
                child: ListView(
                  children: [
                    if (isLoggedIn) ...[
                      ListTile(
                        leading: const Icon(Icons.person_outline),
                        title: const Text('내 정보'),
                        onTap: () {
                          Navigator.pop(context);
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const MyInfoScreen(),
                            ),
                          );
                        },
                      ),
                      ListTile(
                        leading: const Icon(Icons.history),
                        title: const Text('최근 본 제품'),
                        onTap: () {
                          Navigator.pop(context);
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const RecentPerfumeScreen(),
                            ),
                          );
                        },
                      ),
                      ListTile(
                        leading: const Icon(Icons.logout),
                        title: const Text('로그아웃'),
                        onTap: () async {
                          // 로그아웃 처리
                          await context.read<AuthProvider>().signOut();

                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('로그아웃 되었습니다.'),
                            ),
                          );

                          // Drawer 닫기 전에 전체 앱 초기화
                          Navigator.pushAndRemoveUntil(
                            context,
                            MaterialPageRoute(
                                builder: (_) => const HomeScreen()),
                                (route) => false,
                          );
                        },
                      ),
                    ],

                    if (!isLoggedIn)
                      ListTile(
                        leading: const Icon(Icons.login),
                        title: const Text('로그인하기'),
                        onTap: () {
                          Navigator.pop(context);
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const LoginScreen(),
                            ),
                          );
                        },
                      ),
                  ],
                ),
              ),

              const Divider(thickness: 1),
              const SizedBox(height: 8),
              const Text(
                '© 2025 Nozify',
                style: TextStyle(color: Colors.grey, fontSize: 11),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
