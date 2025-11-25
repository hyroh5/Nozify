import 'perfume_simple.dart';

/// ------------------------------------------------------------
/// PBTI 축별 추천 전체 응답 모델 (forward / reverse로 통합)
/// ------------------------------------------------------------
class PbtiByTypeRecommendation {
  final String finalType;

  /// Forward = perfect + axis1 + axis2
  final List<PerfumeSimple> forward;

  /// Reverse = axis3 + axis4
  final List<PerfumeSimple> reverse;

  PbtiByTypeRecommendation({
    required this.finalType,
    required this.forward,
    required this.reverse,
  });

  factory PbtiByTypeRecommendation.fromJson(Map<String, dynamic> json) {
    final data = json['recommendations_by_type'] ?? {};

    /// raw list → PerfumeSimple 변환 함수
    List<PerfumeSimple> _parse(List? raw) {
      if (raw == null) return [];
      return raw
          .map((e) => PerfumeSimple(
        id: e["perfume_id"],
        name: e["name"],
        brandName: e["brand_name"],
        imageUrl: e["image_url"],
      ))
          .toList();
    }

    // 정방향
    final perfect = _parse(data['perfect_match']);
    final axis1 = _parse(data['axis_1_match']);
    final axis2 = _parse(data['axis_2_match']);

    // 역방향
    final axis3 = _parse(data['axis_3_match']);
    final axis4 = _parse(data['axis_4_match']);

    return PbtiByTypeRecommendation(
      finalType: json['final_type'] ?? '----',
      forward: [...perfect, ...axis1, ...axis2],
      reverse: [...axis3, ...axis4],
    );
  }
}
