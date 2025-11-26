// lib/models/recent_view.dart
class RecentViewItem {
  final String perfumeId;
  final String name;
  final String brandName;
  final String? imageUrl;
  final DateTime viewedAt;

  RecentViewItem({
    required this.perfumeId,
    required this.name,
    required this.brandName,
    required this.imageUrl,
    required this.viewedAt,
  });

  factory RecentViewItem.fromJson(Map<String, dynamic> json) {
    return RecentViewItem(
      perfumeId: json["perfume_id"],
      name: json["name"],
      brandName: json["brand_name"],
      imageUrl: json["image_url"],
      viewedAt: DateTime.parse(json["viewed_at"]),
    );
  }
}
