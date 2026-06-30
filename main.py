import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import analyze, mails, keywords, auth

load_dotenv()

app = FastAPI(
    title="메일트랙 API",
    description="AI 기반 이메일 보안 분석 서비스 메일트랙의 백엔드입니다.",
    version="1.0.0",
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/api")
app.include_router(mails.router, prefix="/api")
app.include_router(keywords.router, prefix="/api")
app.include_router(auth.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
