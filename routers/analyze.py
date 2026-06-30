from fastapi import APIRouter, HTTPException
from schemas import AnalyzeRequest, AnalysisResult
from gemini import analyze_mail

router = APIRouter(tags=["분석"])


@router.post("/analyze", response_model=AnalysisResult)
async def analyze(body: AnalyzeRequest):
    if not body.content.strip():
        raise HTTPException(status_code=422, detail="메일 내용이 비어 있습니다.")

    try:
        result = analyze_mail(body.content, body.keywords)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류: {e}")
