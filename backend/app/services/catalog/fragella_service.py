from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from requests import Response
from dotenv import load_dotenv, find_dotenv

# .env 로드
load_dotenv(find_dotenv(), override=False)

__all__ = ["FragellaClient", "FragellaError"]

class FragellaError(Exception):
    """Fragella API 호출 중 발생한 HTTP/네트워크 에러 래퍼"""
    def __init__(self, message: str, status: Optional[int] = None, url: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.url = url


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

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            resp: Response = self.session.get(url, params=params, timeout=30)
        except requests.RequestException as e:
            raise FragellaError(f"네트워크 오류: {e}", url=url) from e

        if not resp.ok:
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
    # 공개 메서드 (문서 기반, 결과는 모두 '배열')
    # ─────────────────────────────
    def get_usage(self) -> Any:
        return self._get("/usage")

    def search_fragrances(self, term: str, limit: int = 10) -> List[Dict[str, Any]]:
        # GET /fragrances?search=term&limit=10
        out = self._get("/fragrances", {"search": term, "limit": limit})
        return out if isinstance(out, list) else []

    def list_fragrances_by_brand(self, brand_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        # GET /brands/:brandName?limit=N  → 배열 반환
        out = self._get(f"/brands/{brand_name}", {"limit": limit})
        return out if isinstance(out, list) else []

    def search_notes(self, term: str, limit: int = 10) -> List[Dict[str, Any]]:
        out = self._get("/notes", {"search": term, "limit": limit})
        return out if isinstance(out, list) else []

    def search_accords(self, term: str, limit: int = 10) -> List[Dict[str, Any]]:
        out = self._get("/accords", {"search": term, "limit": limit})
        return out if isinstance(out, list) else []
