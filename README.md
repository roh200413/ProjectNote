# ProjectNote Backend (Django)

연구노트 통합 플랫폼을 위한 Django 기반 백엔드 작업 환경입니다.

## 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python manage.py runserver 0.0.0.0:8000
```

## 기본 API
- `GET /api/v1/health`
- `GET /api/v1/frontend/bootstrap`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/projects?org_id=<uuid>`

## 테스트
```bash
pytest
```

## 환경 변수
`.env.example` 파일을 참고하세요.
