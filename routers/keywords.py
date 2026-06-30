"""
GET    /api/keywords      — 키워드 목록
POST   /api/keywords      — 키워드 추가
PATCH  /api/keywords/{id} — 활성/비활성 토글
DELETE /api/keywords/{id} — 키워드 삭제

면접 포인트:
- PATCH vs PUT: PATCH는 일부 필드만 수정, PUT은 리소스 전체 교체.
  is_active 하나만 바꾸므로 PATCH가 의미상 정확합니다.
- 낙관적 업데이트(Optimistic Update): 프론트엔드 SmartFilterPage에서
  API 응답을 기다리지 않고 UI를 먼저 업데이트한 뒤, 실패 시 롤백합니다.
  이 방식으로 체감 성능을 높입니다.
- 중복 방지는 DB unique 제약이 아닌 앱 레벨에서 처리 (프론트에서 1차 검증)
"""
from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
from schemas import SpamKeyword, KeywordCreateRequest, KeywordToggleRequest
from supabase_client import get_supabase

router = APIRouter(tags=["키워드"])

TABLE = "tb_spam_keywords"


@router.get("/keywords", response_model=list[SpamKeyword])
async def get_keywords(db: Client = Depends(get_supabase)):
    """스팸 키워드 목록을 등록 최신순으로 반환합니다."""
    try:
        res = db.table(TABLE).select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keywords", response_model=SpamKeyword, status_code=201)
async def create_keyword(body: KeywordCreateRequest, db: Client = Depends(get_supabase)):
    """새 스팸 키워드를 추가합니다. 기본 활성 상태로 생성됩니다."""
    keyword = body.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=422, detail="키워드가 비어 있습니다.")

    try:
        res = db.table(TABLE).insert({"keyword": keyword, "is_active": True}).execute()
        if not res.data:
            raise HTTPException(status_code=500, detail="추가 실패")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/keywords/{keyword_id}", response_model=SpamKeyword)
async def toggle_keyword(
    keyword_id: int,
    body: KeywordToggleRequest,
    db: Client = Depends(get_supabase),
):
    """키워드의 활성 상태를 변경합니다."""
    try:
        res = (
            db.table(TABLE)
            .update({"is_active": body.is_active})
            .eq("id", keyword_id)
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/keywords/{keyword_id}")
async def delete_keyword(keyword_id: int, db: Client = Depends(get_supabase)):
    """키워드를 삭제합니다."""
    try:
        res = db.table(TABLE).delete().eq("id", keyword_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
        return {"message": "삭제 완료"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
