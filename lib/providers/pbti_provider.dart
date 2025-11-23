import 'dart:convert';
import 'package:flutter/material.dart';

import '../services/api_client.dart';
import 'auth_provider.dart';

/// 서버에서 내려오는 PBTI 결과 한 건
class PbtiResultModel {
  final int temperatureScore; // 0~100
  final int textureScore;     // 0~100
  final int moodScore;        // 0~100
  final int natureScore;      // 0~100
  final String finalType;     // 예: FLSN
  final String typeName;      // 타입 이름 (없으면 finalType과 동일)
  final double confidence;    // 0.0 ~ 1.0

  PbtiResultModel({
    required this.temperatureScore,
    required this.textureScore,
    required this.moodScore,
    required this.natureScore,
    required this.finalType,
    required this.typeName,
    required this.confidence,
  });

  factory PbtiResultModel.fromJson(Map<String, dynamic> json) {
    return PbtiResultModel(
      temperatureScore: json['temperature_score'] as int? ?? 0,
      textureScore: json['texture_score'] as int? ?? 0,
      moodScore: json['mood_score'] as int? ?? 0,
      natureScore: json['nature_score'] as int? ?? 0,
      finalType: json['final_type'] as String? ?? '----',
      typeName: json['type_name'] as String? ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

/// PBTI 히스토리/상태 관리
class PbtiProvider with ChangeNotifier {
  /// 서버에서 가져온 PBTI 코드 리스트 (최신순)
  /// 예: ["FLSN", "WLPM", ...]
  List<String> _results = [];

  List<String> get results => _results;
  bool get hasResult => _results.isNotEmpty;

  /// 가장 최근 코드
  String? get latestCode => hasResult ? _results.first : null;

  /// 로그인된 유저의 PBTI 히스토리를 서버에서 로드
  Future<void> loadResults(AuthProvider auth) async {
    if (!auth.isLoggedIn) {
      _results = [];
      notifyListeners();
      return;
    }

    try {
      final res = await ApiClient.I.get(
        "/pbti/history",
        auth: true, // access_token 포함
      );

      if (res.statusCode != 200) {
        // 히스토리 없거나 에러 나면 일단 비우고 조용히 넘어감
        _results = [];
        notifyListeners();
        return;
      }

      final List<dynamic> jsonList = jsonDecode(res.body) as List<dynamic>;
      // 최신순으로 온다고 가정 (백엔드에서 created_at desc)
      _results = jsonList
          .map<String>((e) => (e as Map<String, dynamic>)['final_type'] as String? ?? '----')
          .toList();

      notifyListeners();
    } catch (e) {
      // 네트워크 에러 등
      _results = [];
      notifyListeners();
    }
  }

  /// 설문 답안을 서버에 제출
  /// answers: [{ "question_id": 1, "choice": 5 }, ...]
  Future<PbtiResultModel> submitPbti(
      AuthProvider auth,
      List<Map<String, int>> answers,
      ) async {
    if (!auth.isLoggedIn) {
      throw Exception("로그인 후 이용 가능합니다.");
    }

    final body = jsonEncode({
      "answers": answers,
    });

    final res = await ApiClient.I.post(
      "/pbti/submit",
      auth: true,
      body: body,
    );

    if (res.statusCode != 201 && res.statusCode != 200) {
      throw Exception("PBTI 제출 실패 (status: ${res.statusCode})");
    }

    final Map<String, dynamic> json = jsonDecode(res.body);
    final result = PbtiResultModel.fromJson(json);

    // 서버에 이미 저장되었으므로, 히스토리 갱신
    await loadResults(auth);

    return result;
  }

  /// 로그아웃 시 초기화
  void clear() {
    _results = [];
    notifyListeners();
  }
}
