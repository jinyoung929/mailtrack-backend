from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import base64
import re
import html
import requests as http_requests

router = APIRouter(tags=["인증"])

SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly "
    "https://www.googleapis.com/auth/userinfo.email "
    "openid"
)

token_store: dict = {}

CLIENT_ID = lambda: os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = lambda: os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = lambda: os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")
FRONTEND_URL = lambda: os.getenv("FRONTEND_URL", "http://localhost:5173")


def decode_base64url(data: str) -> str:
    try:
        padded = data + "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(padded).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = html.unescape(text)

    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)

    text = re.sub(r"</(tr|p|div|li|table|br|h[1-6])>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)

    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_body(payload: dict) -> str:
    plain_texts = []
    html_texts = []

    def walk(part: dict):
        mime_type = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data")

        if body_data:
            decoded = decode_base64url(body_data)

            if mime_type == "text/plain":
                plain_texts.append(decoded)
            elif mime_type == "text/html":
                html_texts.append(decoded)

        for sub_part in part.get("parts", []):
            walk(sub_part)

    walk(payload)

    if plain_texts:
        return clean_text("\n".join(plain_texts))

    if html_texts:
        return clean_text("\n".join(html_texts))

    return ""


def make_analysis_text(subject: str, sender: str, date: str, body: str, snippet: str) -> str:
    text = body or snippet or ""

    text = clean_text(text)

    # 너무 긴 주문/결제/광고 메일은 분석 API에서 자주 터지므로 핵심만 제한
    text = text[:1800]

    return f"""
메일 제목: {subject}
보낸 사람: {sender}
날짜: {date}

메일 내용:
{text}
""".strip()


def get_header(headers: list, name: str, default: str = "") -> str:
    return next(
        (h.get("value", default) for h in headers if h.get("name", "").lower() == name.lower()),
        default,
    )


def get_credentials() -> Credentials:
    if "default" not in token_store:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    td = token_store["default"]

    return Credentials(
        token=td.get("access_token"),
        refresh_token=td.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID(),
        client_secret=CLIENT_SECRET(),
        scopes=SCOPES.split(),
    )


@router.get("/auth/login")
async def login():
    if not CLIENT_ID():
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID가 설정되지 않았습니다.")

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={CLIENT_ID()}"
        f"&redirect_uri={REDIRECT_URI()}"
        "&response_type=code"
        f"&scope={SCOPES.replace(' ', '%20')}"
        "&access_type=offline"
        "&prompt=consent"
    )

    return {"auth_url": auth_url}


@router.get("/auth/callback")
async def callback(code: str, state: str = None):
    if not CLIENT_ID() or not CLIENT_SECRET():
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID 또는 GOOGLE_CLIENT_SECRET이 설정되지 않았습니다.",
        )

    try:
        token_res = http_requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": CLIENT_ID(),
                "client_secret": CLIENT_SECRET(),
                "redirect_uri": REDIRECT_URI(),
                "grant_type": "authorization_code",
            },
            timeout=10,
        )

        token_data = token_res.json()

        if token_res.status_code >= 400 or "error" in token_data:
            raise HTTPException(
                status_code=400,
                detail=token_data.get("error_description")
                or token_data.get("error")
                or "토큰 발급 실패",
            )

        token_store["default"] = token_data

        return RedirectResponse(url=f"{FRONTEND_URL()}?auth=success")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/gmail")
async def get_gmail_messages(max_results: int = 10):
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)

        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_results,
        ).execute()

        messages = results.get("messages", [])
        mail_list = []

        for msg in messages:
            msg_detail = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full",
            ).execute()

            payload = msg_detail.get("payload", {})
            headers = payload.get("headers", [])

            subject = get_header(headers, "Subject", "제목 없음")
            sender = get_header(headers, "From", "발신자 없음")
            date = get_header(headers, "Date", "")
            snippet = msg_detail.get("snippet", "")

            body = extract_body(payload)

            if not body:
                body = snippet

            if not body:
                body = "본문을 가져올 수 없습니다."

            analysis_text = make_analysis_text(subject, sender, date, body, snippet)

            mail_list.append({
                "id": msg["id"],
                "threadId": msg_detail.get("threadId"),
                "subject": subject,
                "sender": sender,
                "from": sender,
                "date": date,
                "body": body[:2000],
                "content": analysis_text,
                "analysis_text": analysis_text,
                "snippet": snippet,
            })

        return mail_list

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gmail 메일 조회 실패: {str(e)}")


@router.get("/auth/me")
async def get_me():
    if "default" not in token_store:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    td = token_store["default"]
    res = http_requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {td.get('access_token')}"},
    )
    return res.json()
