// lib/providers/acorrd_provider.dart
import 'dart:convert';
import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../models/perfume_summary.dart';

class AccordProvider extends ChangeNotifier {
  List<PerfumeSummary> perfumes = [];

  bool isLoading = false;

  /// GET /catalog/perfumes?accords=xxx&limit=12
  Future<void> fetchPerfumesByAccord(String accord, {int limit = 50}) async {
    isLoading = true;
    notifyListeners();

    try {
      final res = await ApiClient.I.get(
        "/catalog/perfumes",
        query: {
          "accords": accord,
          "limit": limit.toString(),
        },
      );

      if (res.statusCode == 200) {
        final List<dynamic> list = jsonDecode(res.body);
        perfumes = list.map((e) => PerfumeSummary.fromJson(e)).toList();
      }
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

}
