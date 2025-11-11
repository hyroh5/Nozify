// main。dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:sw_showcase/screens/loading_screen.dart';
import 'providers/calendar_provider.dart';
import 'providers/auth_provider.dart';
import 'providers/recent_perfume_provider.dart';
import 'providers/pbti_provider.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Provider 초기화 + 데이터 로드
  final calendarProvider = CalendarProvider();
  await calendarProvider.loadFromStorage();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: calendarProvider),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => RecentPerfumeProvider()),
        ChangeNotifierProvider(create: (_) => PbtiProvider()),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Nozify',
      theme: ThemeData(
        scaffoldBackgroundColor: Colors.white,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.white),
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          surfaceTintColor: Colors.transparent, // 스크롤 했을때 상단 바 색깔
        )
      ),
      home: const LoadingScreen(), // 시작화면
      scrollBehavior: const MaterialScrollBehavior().copyWith(
        overscroll: false, // 글로우 효과 제거
      ),
    );
  }
}





