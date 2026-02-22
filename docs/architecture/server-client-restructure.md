# ProjectNote 구조 재설계안 (server/client 기준)

이 문서는 현재 `projectnote/views.py` 중심 구조를 **server/client** 중심으로 재편하기 위한 목표 구조와 파일 매핑을 정의한다.

## 1. 최상위 디렉터리 제안

```text
projectnote/
  server/
  client/
  shared/
  docs/
```

- `server/`: 비즈니스 규칙, 유스케이스, API/웹 인터페이스, DB 연동.
- `client/`: 템플릿/정적 파일/클라이언트 스크립트.
- `shared/`: 정말 공통인 상수, 에러코드, 공통 타입만 허용.

## 2. server 내부 표준 구조

```text
server/
  core/
    config/
    exceptions/
    logging/
    security/
    utils/

  domains/
    auth/
    admin/
    projects/
    researchers/
    research_notes/
    signatures/
    data_updates/
    dashboard/

  application/
    auth/
    admin/
    projects/
    researchers/
    research_notes/
    signatures/
    data_updates/
    dashboard/

  interfaces/
    http/
      api/v1/
      web/
      schemas/

  infrastructure/
    persistence/
      django_models/
      repositories/
      migrations/
    sessions/
    files/
    external/
```

### 계층 규칙

- `domain`: 엔티티/값객체/도메인 규칙/리포지토리 포트.
- `application`: 유스케이스(트랜잭션 경계, 권한/정책 orchestration).
- `interfaces`: HTTP 입출력(요청 검증, 응답 직렬화, 라우팅).
- `infrastructure`: ORM, DB repository 구현, 외부 시스템 연동.
- `core`: 프레임워크 독립 공통 유틸/예외/보안 도우미.

## 3. 도메인 템플릿 (예: projects)

```text
server/domains/projects/
  domain/
    entities.py
    value_objects.py
    policies.py
    repository_port.py

  application/
    usecases/
      create_project.py
      get_project_detail.py
      add_project_member.py
    schemas/
      commands.py
      queries.py
      dto.py

  interfaces/
    api.py
    web.py
    schema.py

  infrastructure/
    models.py
    repository.py
    mappers.py
```

## 4. client 내부 표준 구조

```text
client/
  templates/
    auth/
    admin/
    projects/
    researchers/
    research_notes/
    shared/

  static/
    js/
      auth/
      admin/
      projects/
      researchers/
      research_notes/
      shared/
    css/
      shared/
      admin/
      projects/
      researchers/
      research_notes/
```

## 5. 현재 파일 → 목표 구조 매핑

### 서버 진입/설정

- `projectnote/settings.py` → `server/core/config/settings.py`
- `projectnote/urls.py` → `server/interfaces/http/router.py`
- `projectnote/views.py` → 도메인별 `server/interfaces/http/{api,web}` 모듈로 분해

### 도메인/유스케이스

- `projectnote/workflow_app/domains/projects/*` → `server/domains/projects/*`
- `projectnote/workflow_app/domains/researchers/*` → `server/domains/researchers/*`
- `projectnote/workflow_app/domains/research_notes/*` → `server/domains/research_notes/*`
- `projectnote/workflow_app/domains/signatures/*` → `server/domains/signatures/*`
- `projectnote/workflow_app/domains/data_updates/*` → `server/domains/data_updates/*`
- `projectnote/workflow_app/domains/admin/*` → `server/domains/admin/*`
- `projectnote/workflow_app/domains/dashboard/*` → `server/domains/dashboard/*`
- `projectnote/workflow_app/application/services.py` → 도메인별 `server/application/*/usecases/`
- `projectnote/workflow_app/application/schemas.py` → 도메인별 `server/application/*/schemas/`

### 인프라

- `projectnote/workflow_app/models.py` → `server/infrastructure/persistence/django_models/`
- `projectnote/workflow_app/repositories.py` → 도메인별 `server/infrastructure/persistence/repositories/`
- `projectnote/workflow_app/infrastructure/*` → `server/infrastructure/*`
- `projectnote/workflow_app/migrations/*` → `server/infrastructure/persistence/migrations/`

### 클라이언트

- `templates/auth/*` → `client/templates/auth/*`
- `templates/admin/*` → `client/templates/admin/*`
- `templates/workflow/projects*.html` 및 `project_detail.html` → `client/templates/projects/*`
- `templates/workflow/researchers.html` → `client/templates/researchers/list.html`
- `templates/research_notes/*` → `client/templates/research_notes/*`
- `templates/base.html`, `templates/base_admin.html` → `client/templates/shared/*`

## 6. 단계별 이행 계획

1. **인터페이스 분리 1차**: `views.py`를 도메인별 모듈로 먼저 쪼개고 기존 URL 유지.
2. **유스케이스 고정**: 서비스 로직을 `application/usecases`로 이동, view는 orchestration만 수행.
3. **인프라 분리**: ORM 및 repository 구현을 `infrastructure`로 고정.
4. **클라이언트 정리**: `templates/workflow`를 도메인 폴더로 분해.
5. **최종 네이밍 변경**: `projectnote/workflow_app`를 `server/` 패키지로 치환.

## 7. 설계 가드레일

- 도메인 규칙은 `core`에 넣지 않는다.
- API schema(HTTP)와 domain entity를 분리한다.
- repository interface(포트)와 구현체(adapter)를 분리한다.
- 새 기능은 반드시 `usecase` 단위로 추가한다.

## 8. 이번 변경으로 실제 적용된 최소 구조

아래 구조는 코드에 실제로 반영되었다.

- `projectnote/server/interfaces/http/common.py`
- `projectnote/server/interfaces/http/auth.py`
- `projectnote/server/interfaces/http/api.py`
- `projectnote/server/interfaces/http/web.py`
- `projectnote/server/interfaces/http/router.py`

또한 `projectnote/urls.py`는 라우팅 단일 진입점을 `server.interfaces.http.router`로 변경했고,
기존 `projectnote/views.py`는 하위 호환을 위한 re-export 모듈로 축소했다.
