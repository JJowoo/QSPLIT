// main.dart
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import './screens/home_screen.dart'; // 경로 중요

// 클래스 멤버로 선언
WebSocketChannel? _logChannel;

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final baseTheme = ThemeData.light(useMaterial3: true);

    return MaterialApp(
      title: 'Quantum Split Learning UI',
      theme: baseTheme.copyWith(
        scaffoldBackgroundColor: Colors.white,
        textTheme: GoogleFonts.notoSansTextTheme(baseTheme.textTheme),
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueGrey),
        cardTheme: CardThemeData(
          elevation: 2,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: Colors.grey.shade300, width: 1),
          ),
          clipBehavior: Clip.antiAlias,
          margin: const EdgeInsets.symmetric(vertical: 8.0),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black87,
          elevation: 1,
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          ),
        ),
      ),
      home: const QuantumHomePage(), // 홈 화면으로 연결
      debugShowCheckedModeBanner: false,
    );
  }
}
