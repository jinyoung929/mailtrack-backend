"""
GET  /api/mails          — 전체 메일 목록 (최신순)
GET  /api/mails/problems — 위험/주의/다크 메일만
POST /api/mails          — 분석 결과 저장

면접 포인트:
- /problems를 별도 엔드포인트로 분리한 이유: 프론트에서 DarkDataPage와 SecurityPage가
  각각 다른 필터로 메일을 요청하기 때문. 하나의 엔드포인트에 쿼리 파라미터로 처리하는
  방법도 있지만, 의도를 명확히 드러내는 것이 RESTful 설계의 가독성을 높입니다.
- Supabase Python 클라이언트는 SQLAlchemy 없이 HTTP REST API를 직접 호출합니다.
  이 방식의 장점은 ORM 없이 Supabase의 RLS(행 수준 보안)를 그대로 활용할 수 있다는 것입니다.
"""
from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
from schemas import MailRecord, MailSaveRequest
from supabase_client import get_supabase

router = APIRouter(tags=["메일"])

TABLE = "tb_mail"


@router.get("/mails", response_model=list[MailRecord])
async def get_mails(
    limit: int = 50,
    offset: int = 0,
    db: Client = Depends(get_supabase),
):
    """전체 메일 목록을 최신순으로 반환합니다."""
    try:
        res = (
            db.table(TABLE)
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mails/problems", response_model=list[MailRecord])
async def get_problem_mails(db: Client = Depends(get_supabase)):
    """
    문제 메일만 반환합니다.
    조건: security_level이 danger/warn이거나 is_dark가 True인 메일
    """
    try:
        res = (
            db.table(TABLE)
            .select("*")
            .or_("security_level.eq.danger,security_level.eq.warn,is_dark.eq.true")
            .order("created_at", desc=True)
            .execute()
        )
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mails", response_model=MailRecord, status_code=201)
async def save_mail(body: MailSaveRequest, db: Client = Depends(get_supabase)):
    """
    분석된 메일을 DB에 저장합니다.
    프론트에서 분석 후 '저장' 버튼을 누를 때 호출됩니다.
    """
    try:
        payload = {
            "content":        body.content,
            "subject":        body.subject,
            "is_dark":        body.is_dark,
            "dark_reason":    body.dark_reason,
            "security_level": body.security_level,
        }
        res = db.table(TABLE).insert(payload).execute()
        if not res.data:
            raise HTTPException(status_code=500, detail="저장 실패")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
