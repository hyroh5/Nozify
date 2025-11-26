class PerfumeSimple {
  final String id;
  final String name;
  final String brandName;
  final String? imageUrl;

  PerfumeSimple({
    required this.id,
    required this.name,
    required this.brandName,
    this.imageUrl,
  });

  factory PerfumeSimple.fromJson(Map<String, dynamic> json) {
    return PerfumeSimple(
      id: json['id'] ?? json['perfume_id'],  // 두 API 모두 호환
      name: json['name'] ?? '',
      brandName: json['brand_name'] ?? '',
      imageUrl: json['image_url'],
    );
  }
}
