# app/scripts/seed_pbti_questions.py
from app.core.db import SessionLocal
from app.models.pbti_question import PBTIQuestion

QUESTIONS = [
    # temperature
    ("레몬·민트·바람 같은 상쾌한 느낌의 향이 특히 끌린다", "temperature", 1),
    ("앰버·우드·레진처럼 따뜻하고 포근한 향이 더 만족스럽다", "temperature", -1),
    ("비나 바다를 떠올리는 물기 있는 향이 좋다", "temperature", 1),
    ("가을·겨울에 어울리는 따뜻한 무드의 향을 더 선호한다", "temperature", -1),
    ("그린·허브의 시원하고 선명한 느낌이 마음에 든다", "temperature", 1),
    ("스모키·스위트한 따뜻함이 느껴지는 향에 더 마음이 간다", "temperature", -1),

    # texture
    ("가까이에서만 은은하게 느껴지는 가벼운 향이 좋다", "texture", 1),
    ("분사 후 존재감이 강하고 밀도 있는 향을 선호한다", "texture", -1),
    ("상쾌한 첫인상이 지속력보다 더 중요하다", "texture", 1),
    ("하루 종일 진한 잔향이 남아야 만족한다", "texture", -1),
    ("적게 뿌려도 부담 없는 가벼운 질감을 선호한다", "texture", 1),
    ("무게감과 깊이가 느껴지는 진한 질감이 매력적이다", "texture", -1),

    # mood
    ("바닐라·카라멜·초콜릿 같은 달콤한 향이 좋다", "mood", 1),
    ("후추·시나몬·카다멈 등 향신료의 톡 쏘는 느낌을 더 좋아한다", "mood", -1),
    ("복숭아·베리·사과 등 과일의 달큰함이 매력적이다", "mood", 1),
    ("달달한 향은 금방 물리는 편이다", "mood", -1),
    ("허브·생강 같은 드라이하고 깔끔한 스파이스 무드가 좋다", "mood", -1),
    ("디저트 숍을 연상시키는 포근한 단향이 편안하다", "mood", 1),

    # nature
    ("숲·풀·흙처럼 자연의 냄새에 끌린다", "nature", 1),
    ("오존·레더·머스크 등 현대적·합성 느낌이 세련되게 느껴진다", "nature", -1),
    ("에센셜 오일 기반의 자연스러운 향을 선호한다", "nature", 1),
    ("세제/샤워젤 같은 깨끗한 합성 향을 특히 좋아한다", "nature", -1),
    ("전통적/자연주의 향취가 실험적 향보다 더 마음에 든다", "nature", 1),
    ("합성적이더라도 창의적이고 니치한 향이면 더 끌린다", "nature", -1),
]

def run():
    db = SessionLocal()
    try:
        for text, axis, direction in QUESTIONS:
            exists = db.query(PBTIQuestion).filter(PBTIQuestion.text == text).first()
            if not exists:
                db.add(PBTIQuestion(text=text, axis=axis, direction=direction))
        db.commit()
        print("seed done")
    finally:
        db.close()

if __name__ == "__main__":
    run()
