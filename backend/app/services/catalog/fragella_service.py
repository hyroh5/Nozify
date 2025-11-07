from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from requests import Response
from dotenv import load_dotenv, find_dotenv

# .env 로드
load_dotenv(find_dotenv(), override=False)

__all__ = ["FragellaClient", "FragellaError", "TOP_BRANDS"]


class FragellaError(Exception):
    """Fragella API 호출 중 발생한 HTTP/네트워크 에러 래퍼"""
    def __init__(self, message: str, status: Optional[int] = None, url: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.url = url


TOP_BRANDS: List[str] = [
    "Chanel", "Dior", "Jo Malone London", "Diptyque", "Byredo",
    "Tom Ford", "Yves Saint Laurent", "Gucci", "Hermes", "Creed",
    "Maison Francis Kurkdjian", "Montblanc", "Versace", "Giorgio Armani",
    "Lancome", "Mugler", "Calvin Klein", "Burberry", "Givenchy", "Guerlain",
]


class FragellaClient:
    """
    Fragella REST API 래퍼.

    필요 ENV:
      - FRAGELLA_BASE_URL (예: https://api.fragella.com/api/v1)
      - FRAGELLA_API_KEY
      - FRAGELLA_AUTH_HEADER (기본값: x-api-key)
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.base_url = (base_url or os.getenv("FRAGELLA_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("FRAGELLA_API_KEY", "")
        self.auth_header = os.getenv("FRAGELLA_AUTH_HEADER", "x-api-key")

        if not self.base_url:
            raise RuntimeError("FRAGELLA_BASE_URL 가 설정되어 있지 않습니다. .env 를 확인하세요.")
        if not self.api_key:
            raise RuntimeError("FRAGELLA_API_KEY 가 설정되어 있지 않습니다. .env 를 확인하세요.")

        self.session = requests.Session()
        self.session.headers.update({self.auth_header: self.api_key})

    # ─────────────────────────────
    # 내부 GET 헬퍼
    # ─────────────────────────────
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            resp: Response = self.session.get(url, params=params, timeout=30)
        except requests.RequestException as e:
            raise FragellaError(f"네트워크 오류: {e}", url=url) from e

        if not resp.ok:
            # 디버그에 도움 되도록 최소한의 본문 포함
            snippet = ""
            try:
                snippet = resp.text[:200]
            except Exception:
                pass
            raise FragellaError(
                f"HTTP {resp.status_code} {resp.reason}: {snippet}",
                status=resp.status_code,
                url=str(resp.url),
            )
        try:
            return resp.json()
        except ValueError as e:
            raise FragellaError("JSON 파싱 실패", status=resp.status_code, url=str(resp.url)) from e

    # ─────────────────────────────
    # 공개 메서드 (문서에 맞춰 구성)
    # ─────────────────────────────
    def list_brands(self, page: int = 1, size: int = 100) -> Any:
        # 필요 시 페이징 지원되는 엔드포인트로 교체
        return self._get("/brands", {"page": page, "size": size})

    def list_perfumes(self, page: int = 1, size: int = 100) -> Any:
        # 전체 향수 목록 엔드포인트가 있는 경우 사용
        return self._get("/perfumes", {"page": page, "size": size})

    def list_fragrances_by_brand(self, brand_name: str, limit: int = 50) -> Any:
        # 문서 기준: GET /brands/{brand}?limit=N  (brand는 URL path segment)
        # 브랜드명에 공백이 있을 수 있으므로 requests가 알아서 인코딩
        return self._get(f"/brands/{brand_name}", {"limit": limit})

    def get_perfume_detail(self, perfume_id: int | str) -> Any:
        return self._get(f"/perfumes/{perfume_id}")

    def get_usage(self) -> Any:
        # 문서 기준 사용량 엔드포인트. 프로젝트에 맞게 조정 가능.
        return self._get("/usage")
      