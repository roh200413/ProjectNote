# ProjectNote Backend (Django)

연구노트 통합 플랫폼을 위한 Django 기반 백엔드/프론트 프로토타입입니다.
모든 화면은 `templates/base.html` 디자인 시스템(공통 네비게이션/토큰/컴포넌트)을 기반으로 동작합니다.

## 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## DB 적용 및 직접 확인

### 1) DB 파일 위치
이 프로젝트는 Django + SQLite를 사용하며 DB 파일은 아래 경로입니다.

- `/workspace/ProjectNote/projectnote.db`

`projectnote/settings.py`의 `DATABASES` 설정에서 확인할 수 있습니다.

### 2) 테이블 생성(마이그레이션)
```bash
python manage.py migrate
```

### 3) 데모 데이터 생성(옵션)
```bash
python manage.py seed_demo --reset
python manage.py shell -c "from projectnote.workflow_app.infrastructure.sqlalchemy_session import sqlalchemy_table_names; print(sqlalchemy_table_names())"
```

### 4) SQLite CLI로 직접 확인
```bash
sqlite3 projectnote.db ".tables"
sqlite3 projectnote.db "SELECT id, name, status FROM workflow_app_project;"
sqlite3 projectnote.db "SELECT id, email, organization FROM workflow_app_researcher;"
```

### 5) JetBrains DB Navigator / Database Tool 설정
- Database Type: `SQLite`
- Config Type: `File`
- Database file: `/workspace/ProjectNote/projectnote.db`
- Schema: `main`
- SSH Tunnel: 사용 안 함


## 아키텍처(DDD + ORM)
- `projectnote/workflow_app/domain`: 도메인 커맨드/엔티티
- `projectnote/workflow_app/application`: Pydantic 입력 스키마, 유스케이스 서비스
- `projectnote/workflow_app/infrastructure`: Django ORM Repository, SQLAlchemy 세션/모델

SQLAlchemy는 DB 직접 점검/외부 도구 연동 시 사용할 수 있고, 애플리케이션 기본 데이터 접근은 Django ORM Repository가 담당합니다.

## 주요 API
- `GET /api/v1/health`
- `GET /api/v1/frontend/bootstrap`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/projects?org_id=<uuid>`
- `GET/POST /api/v1/project-management`
- `GET/POST /api/v1/researchers`
- `GET/POST /api/v1/data-updates`
- `GET /api/v1/final-download`
- `GET/POST /api/v1/signatures`
- `GET /api/v1/research-notes`
- `GET /api/v1/research-notes/<id>`

## 프론트엔드 페이지
- `GET/POST /login`
- `GET /logout`
- `GET /frontend/workflows`
- `GET /frontend/admin`
- `GET /frontend/projects`
- `GET /frontend/projects/create`
- `GET /frontend/projects/<id>`
- `GET /frontend/researchers` (연구자 전용 정보 관리)
- `GET /frontend/my-page`
- `POST /frontend/my-page/signature` (data URL 이미지 업로드)
- `GET /frontend/data-updates`
- `GET /frontend/final-download`
- `GET /frontend/signatures`
- `GET /frontend/research-notes`
- `GET /frontend/research-notes/<id>`

## 테스트
```bash
pytest -q
python manage.py check
```

## 환경 변수
`.env.example` 파일을 참고하세요.
