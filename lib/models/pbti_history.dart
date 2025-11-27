class PbtiHistoryItem {
  final int id;
  final String finalType;

  PbtiHistoryItem({
    required this.id,
    required this.finalType,
  });

  factory PbtiHistoryItem.fromJson(Map<String, dynamic> json) {
    return PbtiHistoryItem(
      id: json["id"] as int,
      finalType: json["final_type"] ?? "----",
    );
  }
}
