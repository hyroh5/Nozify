// lib/config/env.dart
// 목적: 앱이 FastAPI 서버에 연결할 때 사용할 기본 주소와 공통 경로를
// 한 파일에 모아 하드코딩하지 않고 구조적으로 관리
// ${Env.baseUrl}${Env.apiPrefix}/나머지 상세 주소..

class Env {
  static const String baseUrl = "https://nozify-production.up.railway.app";
  static const String apiPrefix = "/api/v1";
}