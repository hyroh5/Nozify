import 'package:flutter/material.dart';

class AppColors {

  // background
  static const background01 = Color(0xFFB0B59E);
  static const LinearGradient background02 = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color(0xFFFFFFFF),
      Color(0xFFD5D0BA),
    ],
    stops: [0.25, 1.0],
  );
  static LinearGradient background03 = LinearGradient(
    begin: Alignment.bottomCenter,
    end: Alignment.topCenter,
    colors: [
      const Color(0xFF909880).withOpacity(0.7),
      const Color(0xFFFFFFFF).withOpacity(0.7),
    ],
    stops: [0.36, 1.0]
  );

  // button
  static const button = Color(0xFF3A4932);
}
