# ProjectNote Backend (FastAPI)

연구노트 통합 플랫폼을 위한 초기 백엔드입니다.

## 포함 내용
- 제시한 DB 스키마를 반영한 SQLAlchemy 모델 (`app/db/models.py`)
- FastAPI 기반 기본 API
  - `GET /api/v1/health`
  - `POST /api/v1/users`
  - `POST /api/v1/organizations`
  - `GET /api/v1/organizations`
  - `POST /api/v1/projects`
  - `GET /api/v1/projects?org_id=<org_uuid>`
  - `POST /api/v1/notes` (초기 리비전 + 해시 생성)
  - `POST /api/v1/notes/{note_id}/revisions` (체인 해시 기반 후속 리비전)
  - `GET /api/v1/notes/{note_id}`

## 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

기본 DB는 `sqlite:///./projectnote.db`이며, `.env`에 `DATABASE_URL` 설정 시 변경 가능합니다.
