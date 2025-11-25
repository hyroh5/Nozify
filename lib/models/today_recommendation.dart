// lib/models/today_recommendation_item.dart
class TodayRecommendationItem {
  final String id;
  final String name;
  final String brandName;
  final String imageUrl;
  final String gender;
  final double score;

  TodayRecommendationItem({
    required this.id,
    required this.name,
    required this.brandName,
    required this.imageUrl,
    required this.gender,
    required this.score,
  });

  factory TodayRecommendationItem.fromJson(Map<String, dynamic> json) {
    return TodayRecommendationItem(
      id: json['id'] as String,
      name: json['name'] as String,
      brandName: json['brand_name'] as String,
      imageUrl: json['image_url'] as String,
      gender: json['gender'] as String,
      score: (json['score'] as num).toDouble(),
    );
  }
}
