from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

SecurityLevel = Literal["safe", "warn", "danger"]


class SecurityIssue(BaseModel):
    type: SecurityLevel = "safe"
    title: str = ""
    desc: str = ""


class SecurityInfo(BaseModel):
    level: SecurityLevel = "safe"
    issues: list[SecurityIssue] = []


class DarkDataItem(BaseModel):
    label: str = ""
    reason: str = ""


class CalendarEvent(BaseModel):
    title: str = ""
    date: str = ""
    time: Optional[str] = None
    location: Optional[str] = None


class AnalysisResult(BaseModel):
    subject: str = "메일 분석"
    summary: str = "요약을 생성하지 못했습니다."
    security: SecurityInfo = SecurityInfo()
    darkdata: list[DarkDataItem] = []
    calendar: list[CalendarEvent] = []


class MailRecord(BaseModel):
    id: int
    subject: Optional[str] = None
    content: str
    is_dark: bool
    dark_reason: Optional[str] = None
    security_level: SecurityLevel
    user_id: Optional[int] = None
    created_at: datetime


class SpamKeyword(BaseModel):
    id: int
    keyword: str
    is_active: bool
    created_at: datetime


class AnalyzeRequest(BaseModel):
    content: str
    keywords: list[str] = []


class MailSaveRequest(BaseModel):
    content: str
    subject: Optional[str] = None
    is_dark: bool
    dark_reason: Optional[str] = None
    security_level: SecurityLevel


class KeywordCreateRequest(BaseModel):
    keyword: str


class KeywordToggleRequest(BaseModel):
    is_active: bool
