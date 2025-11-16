import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../widgets/topbar/appbar_ver2.dart';
import '../widgets/custom_drawer.dart';
import 'home_screen.dart';

class MyInfoScreen extends StatefulWidget {
  const MyInfoScreen({super.key});

  @override
  State<MyInfoScreen> createState() => _MyInfoScreenState();
}

class _MyInfoScreenState extends State<MyInfoScreen> {
  late TextEditingController nameController;
  late TextEditingController emailController;
  late TextEditingController pwController;

  bool _loading = false; // 로딩 상태 추가

  @override
  void initState() {
    super.initState();

    final user = context.read<AuthProvider>().user;
    nameController = TextEditingController(text: user?.name ?? '');
    emailController = TextEditingController(text: user?.email ?? '');
    pwController = TextEditingController();
  }

  Future<void> _saveInfo() async {
    final name = nameController.text.trim();
    final email = emailController.text.trim();
    final password = pwController.text.trim();

    if (name.isEmpty || email.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('이름과 이메일은 필수입니다.')),
      );
      return;
    }

    setState(() => _loading = true);

    try {
      await context.read<AuthProvider>().updateUser(
        name: name,
        email: email,
        password: password,
      );

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('정보가 수정되었습니다.')),
      );

      pwController.clear(); // 비밀번호 입력칸 초기화
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('수정 실패: $e')),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBarVer2(
        onBack: () {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const HomeScreen()),
          );
        },
      ),
      endDrawer: const CustomDrawer(),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 60),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('내 정보',
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
            const SizedBox(height: 60),

            // 이름
            TextField(
              controller: nameController,
              decoration: const InputDecoration(labelText: '이름'),
            ),
            const SizedBox(height: 20),

            // 이메일
            TextField(
              controller: emailController,
              decoration: const InputDecoration(labelText: '이메일'),
            ),
            const SizedBox(height: 20),

            // 비밀번호
            TextField(
              controller: pwController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: '비밀번호(변경 시에만 입력)',
              ),
            ),
            const SizedBox(height: 40),

            _loading
                ? const Center(
              child: CircularProgressIndicator(
                  color: Color(0xFF3C463A)),
            )
                : ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF3C463A),
                minimumSize: const Size(double.infinity, 48),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(30),
                ),
              ),
              onPressed: _saveInfo,
              child: const Text('저장',
                  style: TextStyle(color: Colors.white, fontSize: 16)),
            ),
          ],
        ),
      ),
    );
  }
}
