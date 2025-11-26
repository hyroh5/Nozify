// lib/models/pbti_result.dart
class PbtiAnswerModel {
  final int questionId;
  final int choice;
  final int score;

  PbtiAnswerModel({
    required this.questionId,
    required this.choice,
    required this.score,
  });

  factory PbtiAnswerModel.fromJson(Map<String, dynamic> json) {
    return PbtiAnswerModel(
      questionId: json['question_id'] as int? ?? 0,
      choice: json['choice'] as int? ?? 0,
      score: (json['score'] is double)
          ? (json['score'] as double).toInt()
          : (json['score'] as int? ?? 0),
    );
  }
}

class PbtiResultModel {
  final int temperatureScore;
  final int textureScore;
  final int moodScore;
  final int natureScore;
  final String finalType;
  final String typeName;
  final double confidence;

  /// 서버가 보내는 answers (optional)
  final List<PbtiAnswerModel> answers;

  PbtiResultModel({
    required this.temperatureScore,
    required this.textureScore,
    required this.moodScore,
    required this.natureScore,
    required this.finalType,
    required this.typeName,
    required this.confidence,
    required this.answers,
  });

  factory PbtiResultModel.fromJson(Map<String, dynamic> json) {
    int _safeInt(dynamic v) {
      if (v is int) return v;
      if (v is double) return v.toInt();
      return int.tryParse(v.toString()) ?? 0;
    }

    double _safeDouble(dynamic v) {
      if (v is double) return v;
      if (v is int) return v.toDouble();
      return double.tryParse(v.toString()) ?? 0.0;
    }

    List<PbtiAnswerModel> parsedAnswers = [];
    if (json['answers'] is List) {
      parsedAnswers = (json['answers'] as List)
          .map((e) => PbtiAnswerModel.fromJson(e))
          .toList();
    }

    return PbtiResultModel(
      temperatureScore: _safeInt(json['temperature_score']),
      textureScore: _safeInt(json['texture_score']),
      moodScore: _safeInt(json['mood_score']),
      natureScore: _safeInt(json['nature_score']),
      finalType: json['final_type'] as String? ?? '----',
      typeName: json['type_name'] as String? ?? '',
      confidence: _safeDouble(json['confidence']),
      answers: parsedAnswers,
    );
  }
}
