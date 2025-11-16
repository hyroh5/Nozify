// lib/config/env.dart
// 목적: 앱이 FastAPI 서버에 연결할 때 사용할 기본 주소와 공통 경로를
// 한 파일에 모아 하드코딩하지 않고 구조적으로 관리
// ${Env.baseUrl}${Env.apiPrefix}/나머지 상세 주소..

class Env {
  // 에뮬레이터에서 PC 로컬 FastAPI로 접근할 때:
  // Android emulator: 10.0.2.2, iOS simulator: 127.0.0.1
  static const String baseUrl = "http://10.0.2.2:8000"; // 배포 시 교체
  static const String apiPrefix = "/api/v1";
}