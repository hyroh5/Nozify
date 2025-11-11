// signup。dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../screens/home_screen.dart';
import '../widgets/custom_text_field.dart';
import '../providers/auth_provider.dart';


class SignUpScreen extends StatelessWidget {
  const SignUpScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final TextEditingController nameController = TextEditingController();
    final TextEditingController emailController = TextEditingController();
    final TextEditingController pwController = TextEditingController();
    final TextEditingController pwCheckController = TextEditingController();

    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 160),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('회원가입', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
            const SizedBox(height: 60),
            CustomTextField(controller: nameController, hintText: '이름'),
            const SizedBox(height: 24),
            CustomTextField(controller: emailController, hintText: '이메일'),
            const SizedBox(height: 24),
            CustomTextField(controller: pwController, hintText: '비밀번호', obscureText: true),
            const SizedBox(height: 24),
            CustomTextField(controller: pwCheckController, hintText: '비밀번호 확인', obscureText: true),
            const SizedBox(height: 72),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF3C463A),
                minimumSize: const Size(double.infinity, 48),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(30),
                ),
              ),
              onPressed: () async {
                if (pwController.text != pwCheckController.text) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('비밀번호가 일치하지 않습니다.')),
                  );
                  return;
                }
                await context.read<AuthProvider>().signUp(
                  nameController.text.trim(),
                  emailController.text.trim(),
                  pwController.text,
                );

                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => const HomeScreen()),
                );
                },
              child: const Text('가입하기', style: TextStyle(color: Colors.white, fontSize: 16)),
            ),
          ],
        ),
      ),
    );
  }
}




