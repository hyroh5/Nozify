// lib/models/perfume_brief.dart
class PerfumeBrief {
  final String id;
  final String name;
  final String? brandName;
  final String? imageUrl;
  final String? gender;

  PerfumeBrief({
    required this.id,
    required this.name,
    this.brandName,
    this.imageUrl,
    this.gender,
  });

  factory PerfumeBrief.fromJson(Map<String, dynamic> json) {
    return PerfumeBrief(
      id: json['id'] as String,
      name: (json['name'] as String?) ?? '',
      brandName: json['brand_name'] as String?,
      imageUrl: json['image_url'] as String?,
      gender: json['gender'] as String?,
    );
  }
}
