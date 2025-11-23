import json
from typing import List, Dict, Any

# =========================================================================
# 1. 데이터 기반 PBTI 매핑 가중치 정의
# =========================================================================

PBTI_MAPPING_WEIGHTS = {
    # F (Warm, 따뜻함) vs W (Cool, 시원함)
    "F_POSITIVE": {
        "woody": 0.5, "warm spicy": 1.0, "amber": 1.0, "vanilla": 0.9, "balsamic": 0.8,
        "tobacco": 0.7, "honey": 0.6, "caramel": 0.7, "cacao": 0.6, "chocolate": 0.6,
        "coffee": 0.5, "tonka bean": 0.7, "benzoin": 0.7, "patchouli": 0.6, "rum": 0.5 
    },
    "W_POSITIVE": {
        "citrus": 1.0, "fresh": 0.8, "aquatic": 0.9, "ozonic": 0.8, "green": 0.7,
        "mint": 0.6, "aldehydic": 0.5, "sea notes": 0.6, "calone": 0.5, "ginger": 0.4,
        "bergamot": 0.8, "lemon": 0.7, "grapefruit": 0.7
    },
    
    # L (Soft, 부드러움) vs H (Intense, 강렬함)
    "L_POSITIVE": {
        "powdery": 1.0, "musky": 0.8, "iris": 0.9, "violet": 0.7, "almond": 0.6,
        "soft spicy": 0.7, "rose": 0.6, "yellow floral": 0.5, "lactonic": 0.5,
        "heliotrope": 0.7, "tea": 0.5, "white musk": 0.6, "orris": 0.8
    },
    "H_POSITIVE": {
        "leather": 1.0, "animalic": 0.9, "smoky": 1.0, "oud": 0.9, "earthy": 0.8,
        "incense": 0.8, "oakmoss": 0.7, "labdanum": 0.7, "castoreum": 0.6, "civet": 0.6,
        "saffron": 0.5, "myrrh": 0.5, "tuberose": 0.6, "black pepper": 0.5
    },

    # S (Calm, 차분함) vs P (Active, 활발함)
    "S_POSITIVE": {
        "aromatic": 1.0, "lavender": 1.0, "herbal": 0.8, "mossy": 0.7, "green": 0.6,
        "tea": 0.5, "sage": 0.6, "rosemary": 0.6, "coriander": 0.5, "chamomile": 0.4
    },
    "P_POSITIVE": {
        "sweet": 1.0, "fruity": 1.0, "tropical": 0.8, "cinnamon": 0.7, "nutty": 0.7,
        "pear": 0.6, "peach": 0.6, "raspberry": 0.6, "plum": 0.5, "cherry": 0.5,
        "red berries": 0.5, "pineapple": 0.5, "caramel": 0.7, "sweet pea": 0.5, "gourmand": 0.8
    },

    # N (Natural, 자연) vs M (Structure, 구조)
    "N_POSITIVE": {
        "green": 1.0, "earthy": 1.0, "mossy": 0.9, "herbal": 0.8, "woody": 0.7,
        "floral": 0.6, "rose": 0.5, "vetiver": 0.7, "cedar": 0.6, "sandalwood": 0.5,
        "oakmoss": 0.7, "grass": 0.6, "fig": 0.5, "hay": 0.4
    },
    "M_POSITIVE": {
        "aldehydic": 1.0, "powdery": 0.9, "musky": 0.8, "ozonic": 0.7, "metallic": 0.6,
        "soapy": 0.5, "clean": 0.5, "white musk": 0.6, "ambergris": 0.4, "iris": 0.5
    },
}

# 강도 및 단계별 가중치 계수
ACCORD_STRENGTH_MULTIPLIER = {
    "Prominent": 3.0,
    "Moderate": 2.0,
    "Subtle": 1.0,
}

NOTE_ROLE_MULTIPLIER = {
    "top_notes": 1.0,
    "middle_notes": 2.0,
    "base_notes": 3.0, # 베이스 노트에 가장 높은 가중치를 부여합니다.
}

def parse_data(data: Any) -> Any:
    """JSON 문자열을 파싱하거나, 이미 파싱된 객체를 반환합니다."""
    if isinstance(data, str):
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return {}
    return data if data is not None else {}

def calculate_pbti_affinity(perfume_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    하나의 향수 데이터에 대해 PBTI 4개 축의 친화도 점수를 계산하고 최종 PBTI 유형을 결정합니다.
    """
    
    # 0. 점수 초기화
    scores = {"F": 0.0, "W": 0.0, "L": 0.0, "H": 0.0, "S": 0.0, "P": 0.0, "N": 0.0, "M": 0.0}
    max_possible_score = 0.0

    # !!! 수정된 부분: main_accords 키를 사용합니다. !!!
    accords_percent = parse_data(perfume_data.get('main_accords')) 

    # 1. 메인 어코드(계열) 기반 점수 계산
    if accords_percent and isinstance(accords_percent, dict):
        for accord_name_raw, strength_raw in accords_percent.items():
            accord_name = accord_name_raw.strip().lower()
            
            # 강도 파싱 및 승수 적용
            strength = str(strength_raw).strip().capitalize() if strength_raw else "Subtle"
            multiplier = ACCORD_STRENGTH_MULTIPLIER.get(strength, 1.0)
            
            for axis_type, weights in PBTI_MAPPING_WEIGHTS.items():
                score_key = axis_type[0] 
                if accord_name in weights:
                    # 계열은 노트보다 영향력을 높이기 위해 1.5배 가중
                    weight = weights[accord_name]
                    score_increase = weight * multiplier * 1.5 
                    scores[score_key] += score_increase
                    max_possible_score += abs(score_increase) 

    # 2. 상세 노트(Top/Middle/Base) 기반 점수 계산
    for role, role_multiplier in NOTE_ROLE_MULTIPLIER.items():
        notes_list = parse_data(perfume_data.get(role))
        
        if not isinstance(notes_list, list): continue

        note_names = []
        for note in notes_list:
            if isinstance(note, dict) and 'name' in note:
                note_names.append(note['name'].strip().lower())
            elif isinstance(note, str):
                note_names.append(note.strip().lower())
        
        for note_name in note_names:
            if not note_name: continue

            for axis_type, weights in PBTI_MAPPING_WEIGHTS.items():
                score_key = axis_type[0]
                
                if note_name in weights:
                    weight = weights[note_name]
                    score_increase = weight * role_multiplier
                    scores[score_key] += score_increase
                    max_possible_score += abs(score_increase)

    # 3. 최종 PBTI 축 점수 계산 및 정규화
    final_scores = {}
    
    max_score_norm = max_possible_score if max_possible_score > 0 else 1.0

    def calculate_axis_score(pos_key, neg_key):
        """두 극단 점수를 빼고 정규화하여 -100 ~ 100 범위의 축 점수를 계산"""
        raw_score = (scores[pos_key] - scores[neg_key]) / max_score_norm
        return round(raw_score * 100, 2)

    final_scores["F_W_Score"] = calculate_axis_score("F", "W")
    final_scores["L_H_Score"] = calculate_axis_score("L", "H")
    final_scores["S_P_Score"] = calculate_axis_score("S", "P")
    final_scores["N_M_Score"] = calculate_axis_score("N", "M")

    # 4. PBTI 유형 결정
    pbti_type = ""
    pbti_type += "F" if final_scores["F_W_Score"] >= 0 else "W"
    pbti_type += "L" if final_scores["L_H_Score"] >= 0 else "H"
    pbti_type += "S" if final_scores["S_P_Score"] >= 0 else "P"
    pbti_type += "N" if final_scores["N_M_Score"] >= 0 else "M"
    
    final_scores["pbti_type"] = pbti_type

    return final_scores