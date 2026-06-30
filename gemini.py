from google import genai
from datetime import date
import json
import os
from schemas import AnalysisResult, SecurityInfo, SecurityIssue

PROMPT_TEMPLATE = """오늘 날짜는 {today}입니다. 아래 이메일을 분석해서 반드시 JSON만 반환하세요. 다른 텍스트나 마크다운 없이 JSON만.

{{
  "subject": "메일 핵심을 담은 짧은 제목 (15자 이내)",
  "summary": "메일 전체 내용을 2-3문장으로 요약",
  "security": {{
    "level": "safe 또는 warn 또는 danger 중 하나",
    "issues": [
      {{ "type": "warn 또는 danger 또는 safe 중 하나", "title": "항목명", "desc": "왜 수상한지 구체적 이유" }}
    ]
  }},
  "darkdata": [
    {{ "label": "발견된 항목 이름", "reason": "이 항목이 다크 데이터로 분류된 구체적 이유" }}
  ],
  "calendar": [
    {{ "title": "일정 제목", "date": "YYYY-MM-DD", "time": "HH:MM 또는 null", "location": "장소 또는 null" }}
  ]
}}

보안 등급 기준:
danger (위험) — 아래 중 하나라도 해당하면 danger:
1. 피싱 URL 또는 링크 클릭 유도
2. 계좌번호 송금 또는 계좌 변경 요청
3. 본인인증 / 개인정보 / 비밀번호 입력 요구
4. 금융기관 / 공공기관 / 임원 사칭
5. 긴급성 압박 ("즉시", "오늘까지") + 행동 요구

warn (주의) — 아래 중 하나라도 해당하면 warn:
1. 광고 / 스팸 의심 메일
2. 출처 불명확한 링크 포함
3. 과장된 혜택 ("80% 할인", "당첨", "무료 지급" 등)
4. no-reply / noreply 발신자 주소
5. 수신자를 특정하지 않은 대량 발송 형태
{keyword_section}
safe (안전) — 위 항목에 해당하지 않는 일반 메일

다크 데이터는 아래 기준으로만 탐지하세요:
1. 광고성 메일: 제목에 (광고) 표시 또는 명백한 마케팅 목적
2. 발신자 회신 불가 주소: no-reply, noreply 등
3. 개인정보 포함: 주민번호, 계좌번호, 카드번호, 전화번호, 주소 패턴
4. 민감 의료정보: 진단명, 처방전, 검사결과 등
5. 첨부파일 언급: 압축파일(.zip .rar), 매크로 문서(.xlsm .docm) 등 의심 확장자
6. 중복/불필요 데이터: 동일 내용 반복, 만료된 이벤트/공지

calendar는 메일에 날짜/시간이 명시된 일정이 있을 때만 추출하세요.
일정이 없으면 빈 배열 []을 반환하세요.

이메일:
{text}"""


def analyze_mail(text: str, keywords: list[str] = []) -> AnalysisResult:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    if keywords:
        keyword_list = ", ".join(f'"{k}"' for k in keywords)
        keyword_section = f"""
사용자 정의 스팸 키워드 — 아래 키워드가 메일에 포함되면 warn 이상으로 분류하세요:
키워드 목록: {keyword_list}
"""
    else:
        keyword_section = ""

    prompt = PROMPT_TEMPLATE.format(
        today=date.today(),
        text=text,
        keyword_section=keyword_section,
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        data["darkdata"] = data.get("darkdata") or []
        data["calendar"] = data.get("calendar") or []
        return AnalysisResult(**data)

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            return AnalysisResult(
                subject="API 한도 초과",
                summary="Gemini API 무료 사용량을 초과했습니다. 잠시 후 다시 시도해주세요. (무료 플랜: 하루 20회 제한)",
                security=SecurityInfo(
                    level="warn",
                    issues=[SecurityIssue(
                        type="warn",
                        title="API 쿼터 초과",
                        desc="Gemini API 무료 플랜 한도에 도달했습니다. 잠시 후 다시 시도해주세요.",
                    )]
                ),
                darkdata=[],
                calendar=[],
            )
        raise
