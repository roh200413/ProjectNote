# ProjectNote Monorepo

ProjectNote를 **모노레포 구조**로 정리했습니다.

- `server/`: 기존 Django 백엔드
- `apps/web`: 기존 `client/*.html` 화면들을 React 라우트 기반으로 옮긴 프론트엔드

## Workspace 구조

```text
.
├─ apps/
│  └─ web/          # React + Vite
├─ client/          # 기존 HTML 템플릿(참고/점진적 이전용)
└─ server/          # Django 백엔드
```

## 실행 방법

### 1) React 프론트엔드

```bash
npm install
npm run dev:web
```

- 기본 주소: `http://localhost:5173`
- React 앱은 Django 페이지를 프록시(`/__django/*`)로 보여주므로 백엔드 서버도 함께 실행해야 로그인/페이지 기능이 동작합니다.
- CSRF 오류가 나면 `.env`에 `DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`를 확인하세요(기본값에 포함됨).

### 2) Django 백엔드

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
touch .env
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## React 전환 범위

`apps/web/src/pages/routeCatalog.js`에 기존 HTML 경로를 기준으로 React 라우트를 구성했습니다.

- 인증: 로그인/회원가입/관리자 로그인
- 워크플로우: 홈, 프로젝트 목록/생성/상세, 연구자/마이페이지/서명/다운로드
- 연구노트: 목록/상세/뷰어/커버/출력
- 관리자: 대시보드/팀/유저/테이블

기존 HTML은 삭제하지 않고 `client/`에 유지해 점진적 마이그레이션이 가능하도록 했습니다.
