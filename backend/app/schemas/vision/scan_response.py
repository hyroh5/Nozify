# =============================================================================
# scan_response.py — Vision Scan 응답 스키마 명세(주석 전용, 코드 없음)
# =============================================================================
#
# C. 성공 응답(HTTP 200)
#
# | 필드                       | 타입             | 설명                                  |
# | ------------------------ | -------------- | ----------------------------------- |
# | bottle                  | object         | 병 탐지/세그멘테이션 결과                    |
# | bottle.present          | boolean        | 병 존재 여부 최종 판정                       |
# | bottle.score            | number         | 신뢰도(0~1). 세그멘테이션/탐지 점수              |
# | bottle.mask_polygon     | array[[x,y]]   | 정규화 다각형(윤곽선). 없으면 null              |
# | bottle.bbox             | object         | 외접 사각형(정규화)                           |
# | bottle.bbox.x,y,w,h     | number         | 정규화 사각형                               |
# | bottle.area_ratio       | number         | 병 마스크 면적 ÷ 프레임(또는 가이드) 면적           |
# | bottle.inside_ratio     | number         | 병 마스크가 가이드 박스 안에 포함된 비율             |
# | texts                   | array<object>  | OCR 결과 배열(감지된 순으로 정렬)                |
# | texts[i].text           | string         | 인식 문자열(정규화·클린업 이후)                  |
# | texts[i].confidence     | number         | 0~1 신뢰도                                 |
# | texts[i].box            | object         | 텍스트 박스 정규화 사각형                       |
# | texts[i].box.x,y,w,h    | number         | 정규화 사각형                               |
# | match                   | object         | 브랜드/제품 매칭 결과                          |
# | match.final             | object or null | 최종 후보. 없으면 null                        |
# | match.final.brand       | string         | 표준화 브랜드명                               |
# | match.final.product     | string         | 표준화 제품명                                |
# | match.final.product_id  | string         | 내부 제품 ID                                |
# | match.final.score       | number         | 0~1 매칭 점수                                |
# | match.candidates        | array<object>  | 상위 N개 후보(점수 내림차순, 동점은 사전순)         |
# | quality                 | object         | 품질 지표                                   |
# | quality.blur            | number         | 라플라시안 분산 등 상대값                        |
# | quality.brightness      | number         | 0~1 정규화 평균 조도                          |
# | quality.glare_ratio     | number         | 반사(하이라이트) 비율 추정(0~1)                 |
# | action                  | enum           | stay 또는 auto_advance                    |
# | timing                  | object         | 처리 시간(ms) 분해                            |
# | timing.detect_ms        | int            | 병 탐지/세그멘테이션                            |
# | timing.ocr_ms           | int            | OCR                                       |
# | timing.match_ms         | int            | 매칭                                        |
# | timing.total_ms         | int            | 총 소요                                      |
# | request_id              | string         | 요청과 동일 ID 에코                            |
# | debug                   | object or null | 디버그 경로(디버그 모드일 때만)                  |
# | debug.overlay_path      | string         | 디버그 합성 이미지 저장 경로(선택)                |
#
# [판정 규칙(서버 내 기준값)]
# - bottle.score ≥ THRESH_BOTTLE_SCORE
# - bottle.inside_ratio ≥ 0.80
# - 0.50 ≤ bottle.area_ratio ≤ 0.90  (과대/과소 방지)
# - OCR 평균 신뢰도(예: 0.50) 미만 텍스트는 폐기
# - 매칭 최종 점수 ≥ THRESH_TEXT_MATCH 일 때만 match.final 채움
# - action 결정: 병/텍스트/매칭/품질 조건 모두 충족 시 auto_advance, 아니면 stay
#   (연속 프레임 안정성 판단은 클라이언트에서 수행: 예, N프레임 연속)
#
# D. 에러 응답(HTTP 4xx/5xx)
#
# | 필드           | 타입     | 설명                                                              |
# | ------------- | ------ | ----------------------------------------------------------------- |
# | error.code    | string | 예: INVALID_FILE_TYPE, FILE_TOO_LARGE, DETECTION_FAIL, OCR_FAIL, TIMEOUT |
# | error.message | string | 사용자/개발자 메시지(간결)                                                 |
# | request_id    | string | 문제 추적용                                                           |
#
# 추가 규칙
# - 파일 오류: 400, 내부 추론 예외: 500, 타임아웃: 504 권장
# - 에러에도 request_id는 반드시 반환
#
# E. Health 체크(참고)
# - GET /api/v1/vision/health
# - 반환: status(ok|warming_up), device(cpu|cuda), model_loaded(bool), ocr_ready(bool)
#
# F. 매칭 규약(사전)
# - 사전(브랜드/제품)은 대문자 정규화 및 별칭(aliases) 포함
# - 퍼지 매칭: 토큰 기반(공백 구분) + 부분 일치 허용
# - 동점 처리: 점수 동일 시 사전순
#
# G. 보안/성능 규정
# - 허용 MIME: image/jpeg, image/png
# - 최대 바이트: MAX_IMAGE_BYTES
# - 클라이언트 RPS 가이드: 최대 5 RPS 권장
# - 서버 타임아웃(내부 처리): 2초 권장
#
# H. 완료 체크리스트
# - 위 스키마 명세를 두 파일에 주석으로 기록
# - 프런트와 필드/좌표계/판정 규칙 합의
# - 에러 코드 문자열 목록 합의
# - health 응답 필드 합의
# - README에 “스키마 합의 완료” 메모 추가
#
# =============================================================================
# 이 파일은 ‘명세’만 담습니다. 후속 단계에서 Pydantic 모델로 구현합니다.
# =============================================================================
