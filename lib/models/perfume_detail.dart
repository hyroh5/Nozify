// lib/models/perfume_detail.dart
class PerfumeDetailModel {
  final String id;
  final String name;
  final String brandId;
  final String? brandName;
  final String? imageUrl;
  final String? gender;
  final double? price;
  final String? currency;
  final double? longevity; // 0~100 가정
  final double? sillage;   // 0~100 가정

  final List<String>? mainAccords;
  final Map<String, dynamic>? mainAccordsPercentage;

  final List<dynamic>? topNotes;
  final List<dynamic>? middleNotes;
  final List<dynamic>? baseNotes;
  final List<dynamic>? generalNotes;

  final Map<String, dynamic>? seasonRanking;
  final Map<String, dynamic>? occasionRanking;
  final String? purchaseUrl;
  final String? fragellaId;
  final int? viewCount;
  final int? wishCount;
  final int? purchaseCount;

  PerfumeDetailModel({
    required this.id,
    required this.name,
    required this.brandId,
    this.brandName,
    this.imageUrl,
    this.gender,
    this.price,
    this.currency,
    this.longevity,
    this.sillage,
    this.mainAccords,
    this.mainAccordsPercentage,
    this.topNotes,
    this.middleNotes,
    this.baseNotes,
    this.generalNotes,
    this.seasonRanking,
    this.occasionRanking,
    this.purchaseUrl,
    this.fragellaId,
    this.viewCount,
    this.wishCount,
    this.purchaseCount,
  });

  factory PerfumeDetailModel.fromJson(Map<String, dynamic> json) {
    return PerfumeDetailModel(
      id: json['id'] as String,
      name: json['name'] as String? ?? '',
      brandId: json['brand_id'] as String? ?? '',
      brandName: json['brand_name'] as String?,
      imageUrl: json['image_url'] as String?,
      gender: json['gender'] as String?,
      price: (json['price'] as num?)?.toDouble(),
      currency: json['currency'] as String?,
      longevity: (json['longevity'] as num?)?.toDouble(),
      sillage: (json['sillage'] as num?)?.toDouble(),
      mainAccords: (json['main_accords'] as List?)
          ?.map((e) => e.toString())
          .toList(),
      mainAccordsPercentage:
      json['main_accords_percentage'] as Map<String, dynamic>?,
      topNotes: json['top_notes'] as List?,
      middleNotes: json['middle_notes'] as List?,
      baseNotes: json['base_notes'] as List?,
      generalNotes: json['general_notes'] as List?,
      seasonRanking: json['season_ranking'] as Map<String, dynamic>?,
      occasionRanking: json['occasion_ranking'] as Map<String, dynamic>?,
      purchaseUrl: json['purchase_url'] as String?,
      fragellaId: json['fragella_id'] as String?,
      viewCount: (json['view_count'] as num?)?.toInt(),
      wishCount: (json['wish_count'] as num?)?.toInt(),
      purchaseCount: (json['purchase_count'] as num?)?.toInt(),
    );
  }
}