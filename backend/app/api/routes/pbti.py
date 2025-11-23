import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple

from app.core.db import get_db
from app.api.deps import get_current_user_id
from app.models.pbti_question import PBTIQuestion
from app.models.pbti_result import PBTIResult
from app.models.user import User

from app.models.perfume import Perfume
from app.models.brand import Brand

# FIX: 함수 이름을 'get_pbti_recommendations_by_type'으로 변경하고 임포트 이름 통일
from app.services.recommendation_service import get_pbti_recommendations_by_type

from app.schemas.pbti import (
    PBTISubmitRequest,
    PBTISubmitResponse,
    PBTIResultResponse,
    PBTIRecommendationsResponse,
    PBTIRecommendationItem,
)
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pbti", tags=["pbti"])

# ==================================================
# 질문 메타 (dim, reverse)
# ==================================================
QUESTION_META: Dict[int, Tuple[int, bool]] = {
    1: (1, False), 2: (1, True), 3: (1, False), 4: (1, True), 5: (1, False), 6: (1, True),
    7: (2, False), 8: (2, True), 9: (2, False), 10: (2, True), 11: (2, False), 12: (2, True),
    13: (3, False), 14: (3, True), 15: (3, False), 16: (3, True), 17: (3, True), 18: (3, False),
    19: (4, False), 20: (4, True), 21: (4, False), 22: (4, True), 23: (4, False), 24: (4, True),
}

DIMENSION_LETTERS = {
    1: ("F", "W"),
    2: ("L", "H"),
    3: ("S", "P"),
    4: ("N", "M"),
}

TYPE_NAMES = {}


# ==================================================
# 유틸 함수 (calculate_match_score 추가)
# ==================================================
def choice_to_score(choice: int) -> int:
    return choice - 3

def normalize_score(raw_sum: int, n_items: int) -> int:
    min_sum = -2 * n_items
    max_sum = 2 * n_items
    norm = (raw_sum - min_sum) / (max_sum - min_sum) * 100
    return int(round(norm))

def calc_confidence(raw_sum: int, n_items: int) -> float:
    return abs(raw_sum) / (2 * n_items)

def _format_result_response(r: PBTIResult) -> PBTIResultResponse:
    # (기존 코드 유지)
    raw_sum = {1: 0, 2: 0, 3: 0, 4: 0}
    cnt = {1: 0, 2: 0, 3: 0, 4: 0}

    for a in (r.answers or []):
        qid = a.get("question_id")
        score = a.get("score")
        if qid in QUESTION_META and isinstance(score, int):
            dim, _ = QUESTION_META[qid]
            raw_sum[dim] += score
            cnt[dim] += 1

    confs = [
        calc_confidence(raw_sum[d], cnt[d]) if cnt[d] > 0 else 0.0
        for d in [1, 2, 3, 4]
    ]
    confidence = float(round(sum(confs) / 4.0, 3))

    return PBTIResultResponse(
        temperature_score=r.temperature_score or 0,
        texture_score=r.texture_score or 0,
        mood_score=r.mood_score or 0,
        nature_score=r.nature_score or 0,
        final_type=r.final_type or "",
        type_name=r.type_name or (r.final_type or ""),
        confidence=confidence,
        answers=r.answers or [],
        is_active=r.is_active,
        created_at=r.created_at,
    )

def calculate_match_score(user_scores: Dict[str, int], perfume_scores: Dict[str, float]) -> float:
    """
    사용자의 0-100점 상세 점수와 향수의 -100~100점 PBTI 프로파일 점수를 비교하여 매칭 점수를 계산합니다.
    매칭 점수는 0.0 (최악) ~ 1.0 (최고) 사이의 값입니다.
    """
    # 1. 사용자 점수를 -100 ~ 100 범위로 변환 (0점 = -100점, 50점 = 0점, 100점 = 100점)
    # user_score (0~100) -> user_centered_score (-100 ~ 100)
    user_centered = {
        'F_W_Score': user_scores['temperature_score'] * 2 - 100, # F/W (1)
        'L_H_Score': user_scores['texture_score'] * 2 - 100,      # L/H (2)
        'S_P_Score': user_scores['mood_score'] * 2 - 100,        # S/P (3)
        'N_M_Score': user_scores['nature_score'] * 2 - 100,      # N/M (4)
    }

    # 2. 각 축별 거리 (절대값 차이) 계산
    diff_sum = 0
    
    perfume_keys = ['F_W_Score', 'L_H_Score', 'S_P_Score', 'N_M_Score']
    user_keys = list(user_centered.keys())

    for u_key, p_key in zip(user_keys, perfume_keys):
        # 거리: |사용자 점수 - 향수 점수|
        diff = abs(user_centered[u_key] - perfume_scores[p_key])
        diff_sum += diff
    
    # 3. 매칭 점수 정규화
    # 최대 거리: 200 (예: 사용자 100, 향수 -100) * 4축 = 800
    MAX_DIFF_SUM = 800 
    
    # 매칭 점수: 1.0 - (실제 거리 / 최대 거리)
    match_score = 1.0 - (diff_sum / MAX_DIFF_SUM)
    
    return max(0.0, min(1.0, float(round(match_score, 3))))


# ==================================================
# GET /pbti/questions
# (기존 코드 유지)
# ==================================================
@router.get("/questions")
def get_questions(db: Session = Depends(get_db)):
    qs = (
        db.query(PBTIQuestion)
        .filter(PBTIQuestion.active == True)
        .order_by(PBTIQuestion.id.asc())
        .all()
    )
    return [
        {
            "id": q.id,
            "axis": q.axis,
            "direction": q.direction,
            "text": q.text,
            "active": q.active,
        }
        for q in qs
    ]


# ==================================================
# POST /pbti/submit
# (기존 코드 유지)
# ==================================================
@router.post("/submit", response_model=PBTISubmitResponse, status_code=status.HTTP_201_CREATED)
def submit_pbti(
    body: PBTISubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    current_user_id_bytes = current_user.id

    if not body.answers:
        raise HTTPException(status_code=400, detail="answers가 비어있습니다")

    # dim 별 점수
    raw_sum = {1: 0, 2: 0, 3: 0, 4: 0}
    cnt = {1: 0, 2: 0, 3: 0, 4: 0}
    packed_answers: List[dict] = []

    for a in body.answers:
        if a.question_id not in QUESTION_META:
            raise HTTPException(status_code=400, detail=f"unknown question_id {a.question_id}")

        dim, is_reverse = QUESTION_META[a.question_id]
        s = choice_to_score(a.choice)
        if is_reverse:
            s = -s

        raw_sum[dim] += s
        cnt[dim] += 1
        packed_answers.append({"question_id": a.question_id, "choice": a.choice, "score": s})

    # dim별 정규화
    dim_scores = {}
    dim_conf = {}
    for d in [1, 2, 3, 4]:
        if cnt[d] == 0:
            raise HTTPException(status_code=400, detail=f"dimension {d} answers missing")
        dim_scores[d] = normalize_score(raw_sum[d], cnt[d])
        dim_conf[d] = calc_confidence(raw_sum[d], cnt[d])

    # PBTI type
    letters = []
    for d in [1, 2, 3, 4]:
        left, right = DIMENSION_LETTERS[d]
        letters.append(left if dim_scores[d] >= 50 else right)

    final_type = "".join(letters)
    type_name = TYPE_NAMES.get(final_type, final_type)
    confidence = float(round(sum(dim_conf.values()) / 4.0, 3))

    db.query(PBTIResult).filter(
        PBTIResult.user_id == current_user_id_bytes,
        PBTIResult.is_active == True,
    ).update({"is_active": False}, synchronize_session='fetch')

    new_result = PBTIResult(
        user_id=current_user_id_bytes,
        temperature_score=dim_scores[1],
        texture_score=dim_scores[2],
        mood_score=dim_scores[3],
        nature_score=dim_scores[4],
        final_type=final_type,
        type_name=type_name,
        answers=packed_answers,
        is_active=True,
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    return PBTISubmitResponse(
        temperature_score=dim_scores[1],
        texture_score=dim_scores[2],
        mood_score=dim_scores[3],
        nature_score=dim_scores[4],
        final_type=final_type,
        type_name=type_name,
        confidence=confidence,
        answers=packed_answers,
    )


# ==================================================
# GET /pbti/result
# ==================================================
@router.get("/result", response_model=PBTIResultResponse)
def get_my_pbti_result(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    current_user_id_bytes = current_user.id


    r = (
        db.query(PBTIResult)
        .filter(PBTIResult.user_id == current_user_id_bytes, PBTIResult.is_active == True)
        .order_by(PBTIResult.created_at.desc())
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="active pbti result not found")

    return _format_result_response(r)


# ==================================================
# GET /pbti/history (모든 결과 리스트)
# ==================================================
@router.get("/history", response_model=List[PBTIResultResponse])
def get_all_pbti_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
):
    current_user_id_bytes = current_user.id

    # is_active 필터 없이, 해당 유저의 모든 결과를 최신순으로 가져옵니다.
    results = (
        db.query(PBTIResult)
        .filter(PBTIResult.user_id == current_user_id_bytes)
        .order_by(PBTIResult.created_at.desc())
        .all()
    )
    
    if not results:
        # 히스토리가 없는 경우 빈 리스트 반환 (404 대신 200 [] 반환이 일반적)
        return []

    # 각 결과 레코드를 PBTIResultResponse 스키마에 맞게 변환하여 리스트로 반환
    return [_format_result_response(r) for r in results]

# ==================================================
# GET /pbti/recommendations
# --------------------------------------------------
# 사용자의 상세 PBTI 점수와 향수의 PBTI 프로파일 점수를 동적으로 비교하여
# 매칭 점수가 높은 향수 목록을 반환합니다. (기존 로직 유지)
# ==================================================
@router.get("/recommendations", response_model=PBTIRecommendationsResponse)
def recommend_by_pbti(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
    limit: int = 10,
):
    current_user_id_bytes = current_user.id

    # 1. 사용자의 최신 상세 PBTI 점수 가져오기
    user_result = (
        db.query(PBTIResult)
        .filter(PBTIResult.user_id == current_user_id_bytes, PBTIResult.is_active == True)
        .order_by(PBTIResult.created_at.desc())
        .first()
    )
    if not user_result:
        raise HTTPException(status_code=404, detail="active pbti result not found for user")

    final_type = user_result.final_type or ""

    # 사용자의 0-100점 상세 점수 딕셔너리
    user_pbti_scores = {
        'temperature_score': user_result.temperature_score or 50,
        'texture_score': user_result.texture_score or 50,
        'mood_score': user_result.mood_score or 50,
        'nature_score': user_result.nature_score or 50,
    }

    # 2. 모든 향수와 그 PBTI 프로파일 점수 가져오기
    try:
        # Perfume.brand_id는 Perfume 모델 정의에 없지만, 여기서는 있다고 가정하고 Brand 테이블과 JOIN
        perfume_rows = (
            db.query(
                Perfume.id, Perfume.name, Perfume.F_W_Score, Perfume.L_H_Score, 
                Perfume.S_P_Score, Perfume.N_M_Score, Brand.name.label("brand_name")
            )
            .join(Brand, Perfume.brand_id == Brand.id)
            .all()
        )
    except Exception as e:
        logger.error(f"Database Query Error on Perfume Profile: {e}")
        raise HTTPException(status_code=500, detail="향수 프로파일 데이터를 가져오는 중 오류가 발생했습니다. (DB 스키마 확인 필요)")

    if not perfume_rows:
        logger.warning("No perfume data found in the database.")
        return PBTIRecommendationsResponse(
            final_type=final_type, 
            items=[],
            message="데이터베이스에서 추천할 향수 목록을 찾을 수 없습니다.",
        )

    # 3. 각 향수와 사용자 점수를 비교하여 매칭 점수 계산
    scored_perfumes: List[Dict[str, Any]] = []
    skipped_count = 0
    
    for row in perfume_rows:
        # 향수 PBTI 점수 딕셔너리 (-100 ~ 100)
        perfume_pbti_scores = {
            'F_W_Score': row.F_W_Score or 0.0,
            'L_H_Score': row.L_H_Score or 0.0,
            'S_P_Score': row.S_P_Score or 0.0,
            'N_M_Score': row.N_M_Score or 0.0,
        }
        
        # 매칭 점수 계산
        match_score = calculate_match_score(user_pbti_scores, perfume_pbti_scores)
        
        # ----------------------------------------------------------------------
        # FIX: UUID 이진 데이터를 UUID 문자열로 변환
        raw_perfume_id = row.id
        perfume_id_safe = None
        
        try:
            if isinstance(raw_perfume_id, bytes) and len(raw_perfume_id) == 16:
                # 16바이트 이진 데이터를 UUID 문자열로 변환
                perfume_id_safe = str(uuid.UUID(bytes=raw_perfume_id))
            elif isinstance(raw_perfume_id, str):
                   # 이미 문자열인 경우
                perfume_id_safe = raw_perfume_id
            else:
                # 예상치 못한 다른 타입인 경우
                perfume_id_safe = str(raw_perfume_id)
        except Exception as e:
            # 변환 실패 시 로그 기록 후 건너뛰기
            logger.error(f"Perfume ID conversion failed for ID: {raw_perfume_id!r} (Type: {type(raw_perfume_id)}). Error: {e}. Skipping item.")
            skipped_count += 1
            continue
        # ----------------------------------------------------------------------

        scored_perfumes.append({
            "perfume_id": perfume_id_safe, # 이제 문자열 UUID입니다.
            "name": row.name,
            "brand_name": row.brand_name,
            "score": match_score,
            "final_type": final_type, 
        })
    
    # 디버깅 포인트 2: 건너뛴 항목 수 확인
    if skipped_count > 0:
        logger.warning(f"Total {skipped_count} out of {len(perfume_rows)} perfumes were skipped due to ID conversion errors.")
        
    # 4. 매칭 점수가 높은 순으로 정렬 및 제한
    scored_perfumes.sort(key=lambda x: x['score'], reverse=True)
    top_recommendations = scored_perfumes[:limit]

    # 5. 최종 응답 스키마로 변환
    items: List[PBTIRecommendationItem] = [
        PBTIRecommendationItem(
            perfume_id=p["perfume_id"], # 이제 str 타입입니다.
            name=p["name"],
            brand_name=p["brand_name"],
            score=p["score"], 
        ) for p in top_recommendations
    ]
    
    return PBTIRecommendationsResponse(
        final_type=final_type, 
        items=items,
        message=f"PBTI 타입 '{final_type}' 및 상세 점수를 기반으로 한 맞춤 추천 향수 {len(items)}개입니다.",
    )


# ==================================================
# GET /pbti/recommendations/by_type
# --------------------------------------------------
# FIX: 서비스 함수 이름 호출을 'get_pbti_recommendations_by_type'로 수정
# ==================================================
@router.get("/recommendations/by_type")
def recommend_by_pbti_type(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id),
    limit: int = 10,
):
    current_user_id_bytes = current_user.id

    # 1. 사용자의 최신 PBTI 유형 가져오기
    user_result = (
        db.query(PBTIResult)
        .filter(PBTIResult.user_id == current_user_id_bytes, PBTIResult.is_active == True)
        .order_by(PBTIResult.created_at.desc())
        .first()
    )
    if not user_result:
        raise HTTPException(status_code=404, detail="active pbti result not found for user")

    final_type = user_result.final_type
    if not final_type or len(final_type) != 4:
          raise HTTPException(status_code=400, detail="Invalid or missing final_type in user result")

    # 2. 추천 서비스 함수 호출 (get_pbti_recommendations_by_type로 수정)
    try:
        recommendations = get_pbti_recommendations_by_type(db, final_type, limit=limit)
    except Exception as e:
        # DB 연결 또는 서비스 로직 오류 처리
        logger.error(f"Recommendation Service Error: {e}")
        raise HTTPException(status_code=500, detail="PBTI 유형 기반 추천 데이터를 가져오는 중 오류가 발생했습니다.")


    # 3. 최종 응답 형식 구성 및 반환
    formatted_recommendations: Dict[str, List[PBTIRecommendationItem]] = {}
    
    for category, perfumes in recommendations.items():
        formatted_list = []
        for p in perfumes:
            
            raw_id = p["id"]
            safe_id = None
            try:
                if isinstance(raw_id, bytes) and len(raw_id) == 16:
                    safe_id = str(uuid.UUID(bytes=raw_id))
                elif isinstance(raw_id, str):
                    safe_id = raw_id
                else:
                    safe_id = str(raw_id)
            except Exception as e:
                logger.error(f"Error converting type-based perfume ID: {raw_id!r}. Skipping item. Error: {e}")
                continue

            formatted_list.append(PBTIRecommendationItem(
                perfume_id=safe_id,
                name=p["name"],
                # recommendation_service.py에서 'brand' 컬럼을 가져오므로 p.get("brand") 사용
                brand_name=p.get("brand"), 
                score=1.0, 
            ))
        formatted_recommendations[category] = formatted_list


    # 클라이언트에서 탭을 구분할 수 있도록 딕셔너리 형태로 반환
    return {
        "final_type": final_type,
        "recommendations_by_type": formatted_recommendations,
        "message": f"PBTI 타입 '{final_type}'에 대한 5가지 카테고리별 추천 결과입니다.",
    }