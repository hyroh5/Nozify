class PbtiRecommendationItem {
  final String perfumeId;
  final String name;
  final String brandName;
  final String imageUrl;
  final double score;

  PbtiRecommendationItem({
    required this.perfumeId,
    required this.name,
    required this.brandName,
    required this.imageUrl,
    required this.score,
  });

  factory PbtiRecommendationItem.fromJson(Map<String, dynamic> json) {
    return PbtiRecommendationItem(
      perfumeId: json['perfume_id'] ?? '',
      name: json['name'] ?? '',
      brandName: json['brand_name'] ?? '',
      imageUrl: json['image_url'] ?? '',
      score: (json['score'] as num).toDouble(),
    );
  }
}
