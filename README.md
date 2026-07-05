
# 메일트랙 (MailTrack) Backend

AI 기반 이메일 보안 분석 서비스의 FastAPI 백엔드입니다. Google OAuth 2.0, Gmail API, Gemini API, Supabase를 연동해 실제 메일 데이터를 수집하고 보안 등급, 개인정보·다크데이터, 일정 정보를 분석합니다.

- 프론트엔드 배포 링크: https://illustrious-cupcake-8c5538.netlify.app
- 백엔드 API: [https://mailtrack-backend.onrender.com](https://mailtrack-backend.onrender.com/docs)
- 프론트엔드 저장소: https://github.com/jinyoung929/mailtrack-frontend


<img width="1431" height="771" alt="스크린샷 2026-06-30 오전 6 12 02" src="https://github.com/user-attachments/assets/1d9bdab8-9a52-4e64-ba83-bb54f2a5c765" />

<img width="1440" height="738" alt="스크린샷 2026-06-30 오전 6 42 03" src="https://github.com/user-attachments/assets/94374ec6-97c3-461f-bf05-7c0841475f68" />

<img width="1440" height="792" alt="스크린샷 2026-06-30 오전 6 42 14" src="https://github.com/user-attachments/assets/88051aa9-01e4-44b6-8d6f-f1b6169ebc9b" />


## Project Context

본 저장소는 2023년 팀 프로젝트를 바탕으로, 2026년 포트폴리오 공개를 위해 개인적으로 재구현한 백엔드입니다. 원본 프로젝트에서 유실되었거나 구현되지 않았던 인증, 메일 수집, 분석, 키워드 관리 라우터를 직접 설계·구현했습니다.

## My Role

- Google OAuth 2.0 인증 흐름 구현
- Gmail API 기반 메일 조회 라우터 구현
- Gemini 기반 메일 요약, 보안 등급 분류, 다크데이터 탐지 로직 구현
- 개인정보, 민감정보, 광고성 메일, 의심 첨부파일 등 탐지 기준 설계
- 사용자 키워드 기반 스마트 필터 API 구현
- Supabase 기반 사용자/키워드 데이터 저장 구조 연동
- API 쿼터 초과 및 외부 API 실패 상황 fallback 처리

## Why This Project Matters

업무 메일은 비정형 데이터이지만 개인정보, 일정, 보안 위험, 불필요 데이터가 함께 존재합니다. 이 백엔드는 Gmail API에서 가져온 메일을 AI가 바로 판단하게 두지 않고, 명시적 탐지 기준과 사용자 키워드를 함께 반영해 사용자가 검토 가능한 분석 결과를 제공하는 데 초점을 두었습니다.

## 주요 기능

| 기능 | 설명 |
| --- | --- |
| OAuth 인증 | Google OAuth 2.0 로그인 및 토큰 처리 |
| Gmail 연동 | 실제 받은 메일함 데이터 조회 |
| AI 분석 | Gemini API 기반 메일 요약, 보안 등급, 다크데이터 탐지 |
| 키워드 관리 | 사용자 정의 스팸/위험 키워드 저장 및 분석 기준 반영 |
| 예외 처리 | API 쿼터 초과 등 외부 API 오류 시 graceful fallback |

## 다크 데이터 탐지 기준

1. 광고성 메일: 제목에 (광고) 표시 또는 명백한 마케팅 목적
2. 발신자 회신 불가 주소: no-reply, noreply 등
3. 개인정보 포함: 주민번호, 계좌번호, 카드번호, 전화번호, 주소 패턴
4. 민감 의료정보: 진단명, 처방전, 검사결과 등
5. 첨부파일 언급: 압축파일(.zip .rar), 매크로 문서(.xlsm .docm) 등 의심 확장자
6. 중복/불필요 데이터: 동일 내용 반복, 만료된 이벤트/공지

## 기술 스택

- Backend: FastAPI, Python
- AI: Gemini API
- External API: Google OAuth 2.0, Gmail API
- DB: Supabase(PostgreSQL)
- 배포: Render
