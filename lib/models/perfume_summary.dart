class PerfumeSummary {
  final String id;
  final String name;
  final String brandName;
  final String? imageUrl;
  final String? gender;
  final int viewCount;
  final int wishCount;

  PerfumeSummary({
    required this.id,
    required this.name,
    required this.brandName,
    this.imageUrl,
    this.gender,
    required this.viewCount,
    required this.wishCount,
  });

  factory PerfumeSummary.fromJson(Map<String, dynamic> json) {
    return PerfumeSummary(
      id: json["id"] as String,
      name: json["name"],
      brandName: json["brand_name"],
      imageUrl: json["image_url"],
      gender: json["gender"],
      viewCount: json["view_count"] ?? 0,
      wishCount: json["wish_count"] ?? 0,
    );
  }
}
