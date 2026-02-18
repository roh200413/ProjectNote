# ProjectNote Backend (Django)

연구노트 통합 플랫폼을 위한 Django 기반 백엔드/프론트 프로토타입입니다.
모든 화면은 `templates/base.html` 디자인 시스템(공통 네비게이션/토큰/컴포넌트)을 기반으로 동작합니다.

## 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python manage.py runserver 0.0.0.0:8000
```

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
- `GET /frontend/my-page`
- `GET /frontend/researchers`
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
