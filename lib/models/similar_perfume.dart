// lib/models/similar_perfume_item.dart
import 'package:sw_showcase/models/perfume_simple.dart';

class SimilarPerfumeItem {
  final String id;
  final String name;
  final String brandName;
  final String? imageUrl;

  SimilarPerfumeItem({
    required this.id,
    required this.name,
    required this.brandName,
    required this.imageUrl,
  });

  factory SimilarPerfumeItem.fromJson(Map<String, dynamic> json) {
    return SimilarPerfumeItem(
      id: json["id"],
      name: json["name"],
      brandName: json["brand_name"],
      imageUrl: json["image_url"],
    );
  }

  /// PerfumeSimple로 변환 → 공용 카드 사용 가능
  PerfumeSimple toSimple() {
    return PerfumeSimple(
      id: id,
      name: name,
      brandName: brandName,
      imageUrl: imageUrl,
    );
  }
}
