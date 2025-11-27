// lib/models/search_suggestion.dart
class SearchSuggestion {
  final String name;
  final String type;
  final double score;

  SearchSuggestion({
    required this.name,
    required this.type,
    required this.score,
  });

  factory SearchSuggestion.fromJson(Map<String, dynamic> json) {
    return SearchSuggestion(
      name: json['name'] ?? '',
      type: json['type'] ?? '',
      score: (json['score'] as num).toDouble(),
    );
  }
}
