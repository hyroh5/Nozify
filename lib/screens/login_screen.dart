// login、dart
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:provider/provider.dart';
import 'package:flutter/gestures.dart';
import '../screens/signup_screen.dart';
import '../screens/home_screen.dart';
import '../widgets/custom_text_field.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController emailController = TextEditingController();
  final TextEditingController pwController = TextEditingController();
  bool saveLogin = false;

  @override
  void initState() {
    super.initState();
    _loadLoginInfo();
  }

  Future<void> _loadLoginInfo() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      saveLogin = prefs.getBool('saveLogin') ?? false;
      if (saveLogin) {
        emailController.text = prefs.getString('email') ?? '';
        pwController.text = prefs.getString('password') ?? '';
      }
    });
  }

  Future<void> _saveLoginInfo() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    if (saveLogin) {
      await prefs.setBool('saveLogin', true);
      await prefs.setString('email', emailController.text);
      await prefs.setString('password', pwController.text);
    } else {
      await prefs.setBool('saveLogin', false);
      await prefs.remove('email');
      await prefs.remove('password');
    }
  }

  // 변경 포인트만 발췌
  void _login() async {
    final email = emailController.text.trim();
    final password = pwController.text.trim();

    if (email.isEmpty || password.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('이메일과 비밀번호를 모두 입력하세요.')),
      );
      return;
    }
    try {
      await context.read<AuthProvider>().signIn(email, password);

      // 이메일만 저장(옵션)
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('saveLogin', saveLogin);
      if (saveLogin) {
        await prefs.setString('email', email);
      } else {
        await prefs.remove('email');
      }

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const HomeScreen()),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('로그인 실패: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: true, // 키보드 대응
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.only(
            left: 32,
            right: 32,
            top: 160,
            bottom: MediaQuery.of(context).viewInsets.bottom, // 키보드 높이만큼 공간 확보
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                '로그인',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 72),

              // 네 컨트롤러 그대로 사용
              CustomTextField(
                controller: emailController,
                hintText: '이메일',
              ),

              const SizedBox(height: 24),

              CustomTextField(
                controller: pwController,
                hintText: '비밀번호',
                obscureText: true,
              ),

              const SizedBox(height: 4),

              Row(
                children: [
                  Checkbox(
                    value: saveLogin,
                    onChanged: (value) => setState(() => saveLogin = value!),
                    activeColor: const Color(0xFF3C463A),
                  ),
                  const Text('로그인 정보 저장'),
                ],
              ),

              const SizedBox(height: 60),

              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF3C463A),
                  minimumSize: const Size(double.infinity, 48),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                ),
                onPressed: _login,
                child: const Text(
                  '로그인',
                  style: TextStyle(color: Colors.white, fontSize: 16),
                ),
              ),

              const SizedBox(height: 16),

              Center(
                child: GestureDetector(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const SignUpScreen()),
                    );
                  },
                  child: RichText(
                    text: TextSpan(
                      style: const TextStyle(
                        color: Colors.black87,
                        fontSize: 12,
                      ),
                      children: const [
                        TextSpan(text: '아직 계정이 없으신가요? '),
                        TextSpan(
                          text: '회원가입',
                          style: TextStyle(
                            decoration: TextDecoration.underline,
                            color: Colors.black,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}





