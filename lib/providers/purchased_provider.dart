// lib/providers/purchased_provider.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/api_client.dart';

class PurchasedItem {
  final String perfumeId;
  final String name;
  final String brandName;
  final String? imageUrl;
  final String? gender;
  final DateTime? addedAt;

  PurchasedItem({
    required this.perfumeId,
    required this.name,
    required this.brandName,
    this.imageUrl,
    this.gender,
    this.addedAt,
  });

  factory PurchasedItem.fromJson(Map<String, dynamic> json) {
    final p = json['perfume'] as Map<String, dynamic>;
    return PurchasedItem(
      perfumeId: p['id'],
      name: p['name'] ?? '',
      brandName: p['brand_name'] ?? '',
      imageUrl: p['image_url'],
      gender: p['gender'],
      addedAt: json['added_at'] != null
          ? DateTime.tryParse(json['added_at'])
          : null,
    );
  }
}

class PurchasedProvider with ChangeNotifier {
  List<PurchasedItem> _items = [];
  bool _isLoading = false;

  List<PurchasedItem> get items => _items;
  bool get isLoading => _isLoading;

  Future<void> fetchPurchased({int limit = 20, int offset = 0}) async {
    _isLoading = true;
    notifyListeners();

    try {
      final res = await ApiClient.I.get(
        "/user/purchase-history",
        auth: true,
        query: {
          "limit": "$limit",
          "offset": "$offset",
        },
      );

      final List<dynamic> list = jsonDecode(res.body);
      _items = list.map((e) => PurchasedItem.fromJson(e)).toList();
    } catch (_) {
      _items = [];
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> add(String perfumeId) async {
    try {
      await ApiClient.I.post(
        "/user/purchase-history?perfume_id=$perfumeId",
        auth: true,
      );
      await fetchPurchased();
    } catch (_) {}
  }

  Future<void> remove(String perfumeId) async {
    try {
      await ApiClient.I.delete("/user/purchase-history/$perfumeId", auth: true);
      _items.removeWhere((e) => e.perfumeId == perfumeId);
      notifyListeners();
    } catch (_) {}
  }

  bool contains(String perfumeId) {
    return _items.any((e) => e.perfumeId == perfumeId);
  }
}
