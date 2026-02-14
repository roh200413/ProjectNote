# ProjectNote Backend (FastAPI)

연구노트 통합 플랫폼을 위한 백엔드 API 서버입니다.

## Repository 전략
- `ProjectNote-Back`: API / DB / 인증 / 비즈니스 로직
- `ProjectNote-Front`: 웹 UI
- 백/프를 분리하면 배포/스케일/릴리즈를 독립적으로 운영하기 좋습니다.

## 포함 내용
- 제시한 DB 스키마를 반영한 SQLAlchemy 모델 (`app/db/models.py`)
- FastAPI 기반 API
  - `GET /api/v1/health`
  - `GET /api/v1/frontend/bootstrap` (프론트 초기 연결 확인)
  - `GET /api/v1/dashboard/summary` (대시보드 집계)
  - `POST /api/v1/users`
  - `POST /api/v1/organizations`
  - `GET /api/v1/organizations`
  - `POST /api/v1/projects`
  - `GET /api/v1/projects?org_id=<org_uuid>`
  - `POST /api/v1/notes` (초기 리비전 + 해시 생성)
  - `GET /api/v1/notes/{note_id}`
  - `GET /api/v1/notes/{note_id}/revisions`
  - `POST /api/v1/notes/{note_id}/revisions` (체인 해시 기반 후속 리비전)

## DB / CORS 설정
기본값은 SQLite이며 `.env`로 변경할 수 있습니다.

```env
DATABASE_URL=sqlite:///./projectnote.db
# 예시(PostgreSQL)
# DATABASE_URL=postgresql+psycopg://projectnote:projectnote@localhost:5432/projectnote

# 프론트(예: Next.js) 로컬 주소 허용
CORS_ALLOW_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

> 운영 환경에서는 `.env` 대신 GitHub Secrets / 클라우드 시크릿 매니저 사용을 권장합니다.

## 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

## 프론트와 함께 실행
1. 백엔드 실행 (`http://localhost:8000`)
2. 프론트(`ProjectNote-Front`)에서 API base URL을 `http://localhost:8000/api/v1`로 설정
3. 브라우저에서 프론트 실행 (보통 `http://localhost:3000`)
