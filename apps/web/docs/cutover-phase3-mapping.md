# Django 템플릿 컷오버(Phase 3) 매핑표

목표: Django의 `/frontend/*` 템플릿 렌더 라우트를 제거하고, web 앱 라우팅으로 전환.

- 유지 범위: `/api/v1/*`, `login/signup/logout`, `admin/login` 백엔드 인증/관리 API
- 예외 유지(템플릿 아님):
  - `POST /frontend/my-page/signature`
  - `POST /frontend/my-page/research-note/upload`
  - `GET /frontend/research-notes/{note_id}/files/{file_id}/content`

## 1:1 대체 경로 매핑

| 제거된 Django 템플릿 라우트 | 대체 web 경로 | 전환 방식 |
|---|---|---|
| `/frontend/admin` | `/frontend/admin` | 302 redirect to web app |
| `/frontend/admin/dashboard` | `/frontend/admin/dashboard` | 302 redirect to web app |
| `/frontend/admin/teams` | `/frontend/admin/teams` | 302 redirect to web app |
| `/frontend/admin/users` | `/frontend/admin/users` | 302 redirect to web app |
| `/frontend/admin/tables` | `/frontend/admin/tables` | 302 redirect to web app |
| `/frontend/workflows` | `/frontend/workflows` | 302 redirect to web app |
| `/frontend/projects` | `/frontend/projects` | 302 redirect to web app |
| `/frontend/projects/create` | `/frontend/projects/create` | 302 redirect to web app |
| `/frontend/projects/{project_id}` | `/frontend/projects/{project_id}` | 302 redirect to web app |
| `/frontend/projects/{project_id}/researchers` | `/frontend/projects/{project_id}/researchers` | 302 redirect to web app |
| `/frontend/projects/{project_id}/research-notes` | `/frontend/projects/{project_id}/research-notes` | 302 redirect to web app |
| `/frontend/projects/{project_id}/research-notes/print` | `/frontend/projects/{project_id}/research-notes/print` | 302 redirect to web app |
| `/frontend/my-page` | `/frontend/my-page` | 302 redirect to web app |
| `/frontend/researchers` | `/frontend/researchers` | 302 redirect to web app |
| `/frontend/integrations/github` | `/frontend/integrations/github` | 302 redirect to web app |
| `/frontend/integrations/collaboration` | `/frontend/integrations/collaboration` | 302 redirect to web app |
| `/frontend/data-updates` | `/frontend/data-updates` | 302 redirect to web app |
| `/frontend/final-download` | `/frontend/final-download` | 302 redirect to web app |
| `/frontend/signatures` | `/frontend/signatures` | 302 redirect to web app |
| `/frontend/research-notes` | `/frontend/research-notes` | 302 redirect to web app |
| `/frontend/research-notes/{note_id}` | `/frontend/research-notes/{note_id}` | 302 redirect to web app |
| `/frontend/research-notes/{note_id}/viewer` | `/frontend/research-notes/{note_id}/viewer` | 302 redirect to web app |
| `/frontend/research-notes/{note_id}/cover` | `/frontend/research-notes/{note_id}/cover` | 302 redirect to web app |
| `/frontend/research-notes/{note_id}/printable` | `/frontend/research-notes/{note_id}/printable` | 302 redirect to web app |

## 404 / 리다이렉트 정책

- 정책 1: Django는 `/frontend/*`를 템플릿 렌더링하지 않고 `WEB_APP_ORIGIN`(기본 `http://127.0.0.1:3000`)의 동일 경로로 **302 리다이렉트**한다.
- 정책 2: 쿼리스트링은 그대로 보존한다. (`/frontend/projects?q=a` -> `${WEB_APP_ORIGIN}/frontend/projects?q=a`)
- 정책 3: web 앱에 해당 경로가 없으면 최종 404는 web 앱에서 처리한다.
- 정책 4: 위 “예외 유지” 경로는 기존 백엔드 동작을 유지하며 redirect 대상에서 제외한다.
