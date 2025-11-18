class RefreshResponse {
  final String accessToken;

  const RefreshResponse({required this.accessToken});

  factory RefreshResponse.fromJson(Map<String, dynamic> json) {
    return RefreshResponse(
      accessToken: json['access_token'] ?? "",
    );
  }
}
