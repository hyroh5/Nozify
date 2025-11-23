from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.models.perfume import Perfume


def perfume_to_dict(perfume: Perfume) -> Dict[str, Any]:
    """Perfume ORM 객체를 추천 응답용 dict로 변환"""
    return {
        "id": perfume.id,
        "name": perfume.name,
        "brand": perfume.brand_name,
        "pbti_type": perfume.pbti_type,
        "F_W_Score": perfume.F_W_Score,
        "L_H_Score": perfume.L_H_Score,
        "S_P_Score": perfume.S_P_Score,
        "N_M_Score": perfume.N_M_Score,
    }


def get_pbti_recommendations_by_type(
    db: Session,
    user_pbti_type: str,
    limit: int = 10
) -> Dict[str, List[Dict[str, Any]]]:
    """
    사용자 PBTI 유형 기반 5종 추천 제공
    perfect_match, axis_1_match, axis_2_match, axis_3_match, axis_4_match
    """

    if not user_pbti_type or len(user_pbti_type) != 4:
        raise ValueError("PBTI 유형은 4글자여야 합니다 예 FWSP")

    recommendations: Dict[str, List[Dict[str, Any]]] = {}

    axis_1 = user_pbti_type[0]
    axis_2 = user_pbti_type[1]
    axis_3 = user_pbti_type[2]
    axis_4 = user_pbti_type[3]

    # 1 완벽 일치
    perfect_match_results = (
        db.query(Perfume)
        .filter(Perfume.pbti_type == user_pbti_type)
        .limit(limit)
        .all()
    )
    recommendations["perfect_match"] = [perfume_to_dict(p) for p in perfect_match_results]

    # 2 첫 번째 축 일치
    axis1_match_results = (
        db.query(Perfume)
        .filter(Perfume.pbti_type.like(f"{axis_1}___"))
        .filter(Perfume.pbti_type != user_pbti_type)
        .limit(limit)
        .all()
    )
    recommendations["axis_1_match"] = [perfume_to_dict(p) for p in axis1_match_results]

    # 3 두 번째 축 일치
    axis2_match_results = (
        db.query(Perfume)
        .filter(Perfume.pbti_type.like(f"_{axis_2}__"))
        .filter(Perfume.pbti_type != user_pbti_type)
        .limit(limit)
        .all()
    )
    recommendations["axis_2_match"] = [perfume_to_dict(p) for p in axis2_match_results]

    # 4 세 번째 축 일치
    axis3_match_results = (
        db.query(Perfume)
        .filter(Perfume.pbti_type.like(f"__{axis_3}_"))
        .filter(Perfume.pbti_type != user_pbti_type)
        .limit(limit)
        .all()
    )
    recommendations["axis_3_match"] = [perfume_to_dict(p) for p in axis3_match_results]

    # 5 네 번째 축 일치
    axis4_match_results = (
        db.query(Perfume)
        .filter(Perfume.pbti_type.like(f"___{axis_4}"))
        .filter(Perfume.pbti_type != user_pbti_type)
        .limit(limit)
        .all()
    )
    recommendations["axis_4_match"] = [perfume_to_dict(p) for p in axis4_match_results]

    return recommendations
