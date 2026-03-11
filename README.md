# ProjectNote Monorepo

ProjectNote를 **모노레포 구조**로 정리했습니다.

- `server/`: 기존 Django 백엔드
- `apps/web`: 기존 `client/*.html` 화면들을 React 라우트 기반으로 옮긴 프론트엔드
  - React 전환 이후 레거시 HTML 소스는 `apps/web`에서 제거됨

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
- React 앱은 Django API를 Vite 프록시로 연결하므로 백엔드 서버도 함께 실행해야 합니다.
- 기본 프록시 대상은 `http://127.0.0.1:8000`이며, 필요하면 `apps/web/.env.local`에 `VITE_BACKEND_ORIGIN=http://<host>:<port>`를 설정하세요.
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

기존 HTML 경로 기준으로 React 라우트를 구성했습니다.

- 인증: 로그인/회원가입/관리자 로그인
- 워크플로우: 홈, 프로젝트 목록/생성/상세, 연구자/마이페이지/서명/다운로드
- 연구노트: 목록/상세/뷰어/커버/출력
- 관리자: 대시보드/팀/유저/테이블
- 관리자(`\/auth\/admin-login`, `\/admin\/*`)는 React 네이티브 화면으로 동작하며 Django API와 세션 인증으로 통신합니다.

레거시 Django 템플릿 렌더링은 제거되었고, 화면 라우팅은 React 앱 경로를 사용합니다.

### 레거시 Django HTML fallback on/off

기본값은 **OFF** 입니다. (React 구현 페이지가 아니면 안내 화면 표시)

- 설정 위치: `apps/web/.env.local`
- 임시 활성화 값:

```bash
echo "VITE_ENABLE_LEGACY_PAGES=true" > apps/web/.env.local
```

- dev 서버 재시작 후 반영됩니다.

### 자주 발생하는 오류

- `http proxy error ... ECONNREFUSED 127.0.0.1:8000`
  - 원인: Django 서버 미실행 또는 포트 불일치
  - 조치: `python manage.py runserver 0.0.0.0:8000` 실행 또는 `VITE_BACKEND_ORIGIN` 수정
