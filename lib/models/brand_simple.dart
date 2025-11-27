class BrandSimple {
  final String id;
  final String name;
  final String? logoUrl;
  final double score;

  BrandSimple({
    required this.id,
    required this.name,
    required this.logoUrl,
    required this.score,
  });

  factory BrandSimple.fromJson(Map<String, dynamic> json) {
    return BrandSimple(
      id: json["brand_id"],
      name: json["brand_name"],
      logoUrl: json["logo_url"], // null이어도 OK
      score: (json["score"] as num).toDouble(),
    );
  }
}
