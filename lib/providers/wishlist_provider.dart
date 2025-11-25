// lib/providers/wishlist_provider.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import '../services/api_client.dart';

class WishlistItem {
  final String perfumeId;
  final String name;
  final String brandName;
  final String? imageUrl;
  final String? gender;
  final DateTime? addedAt;

  WishlistItem({
    required this.perfumeId,
    required this.name,
    required this.brandName,
    this.imageUrl,
    this.gender,
    this.addedAt,
  });

  factory WishlistItem.fromJson(Map<String, dynamic> json) {
    final p = json['perfume'] as Map<String, dynamic>;
    return WishlistItem(
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

class WishlistProvider with ChangeNotifier {
  List<WishlistItem> _items = [];
  bool _isLoading = false;

  List<WishlistItem> get items => _items;
  bool get isLoading => _isLoading;

  Future<void> fetchWishlist() async {
    _isLoading = true;
    notifyListeners();

    try {
      final res = await ApiClient.I.get("/user/wishlist", auth: true);
      final List<dynamic> list = jsonDecode(res.body);
      _items = list.map((e) => WishlistItem.fromJson(e)).toList();
    } catch (_) {
      _items = [];
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> add(String perfumeId) async {
    try {
      await ApiClient.I.post(
        "/user/wishlist?perfume_id=$perfumeId",
        auth: true,
      );
      await fetchWishlist();
    } catch (_) {}
  }

  Future<void> remove(String perfumeId) async {
    try {
      await ApiClient.I.delete("/user/wishlist/$perfumeId", auth: true);
      _items.removeWhere((e) => e.perfumeId == perfumeId);
      notifyListeners();
    } catch (_) {}
  }

  bool contains(String perfumeId) {
    return _items.any((e) => e.perfumeId == perfumeId);
  }
}
