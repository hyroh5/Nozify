class PerfumeDetailModel {
  final String id;
  final String name;
  final String brandId;
  final String? brandName;
  final String? imageUrl;
  final String? gender;
  final double? price;
  final String? currency;
  final double? longevity;
  final double? sillage;

  final List<String>? mainAccords;
  final Map<String, dynamic>? mainAccordsPercentage;

  final List<Map<String, dynamic>>? topNotes;
  final List<Map<String, dynamic>>? middleNotes;
  final List<Map<String, dynamic>>? baseNotes;
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
    List<dynamic>? safeList(dynamic data) {
      if (data is List) return data;
      return null;
    }

    List<Map<String, dynamic>>? safeMapList(dynamic data) {
      if (data is List) {
        return data.whereType<Map<String, dynamic>>().toList();
      }
      return null;
    }

    Map<String, dynamic>? safeRanking(dynamic data) {
      if (data is List) {
        return {
          for (final e in data)
            if (e is Map && e['name'] != null) e['name']: e['score']
        };
      }
      return null;
    }

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

      mainAccords: safeList(json['main_accords'])
          ?.map((e) => e.toString())
          .toList(),

      mainAccordsPercentage:
      json['main_accords_percentage'] is Map<String, dynamic>
          ? json['main_accords_percentage']
          : null,

      topNotes: safeMapList(json['top_notes']),
      middleNotes: safeMapList(json['middle_notes']),
      baseNotes: safeMapList(json['base_notes']),
      generalNotes: safeList(json['general_notes']),

      seasonRanking: safeRanking(json['season_ranking']),
      occasionRanking: safeRanking(json['occasion_ranking']),

      purchaseUrl: json['purchase_url'] as String?,
      fragellaId: json['fragella_id'] as String?,
      viewCount: (json['view_count'] as num?)?.toInt(),
      wishCount: (json['wish_count'] as num?)?.toInt(),
      purchaseCount: (json['purchase_count'] as num?)?.toInt(),
    );
  }
}
