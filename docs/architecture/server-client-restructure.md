# ProjectNote 구조 재설계안 (server/client + 핵심 기능 분리)

요청하신 대로 루트 기준으로 `server/`와 `client/`를 분리한다.
(`projectnote/projectnote/...`처럼 중첩되어 보이는 구조는 사용하지 않음)

## 1) 최상위 분리 원칙

```text
ProjectNote/
  projectnote/  # Django settings/urls/wsgi/asgi
  server/       # JSON API, 인증/권한 공통, 도메인 기능 분리
  client/       # 템플릿 렌더링(Web pages)
  templates/
```

- `projectnote/`: 프레임워크 부트스트랩(설정/URL 엔트리)만.
- `server/`: API 및 서버 코어 로직.
- `client/`: 페이지 렌더링 핸들러.

## 2) 실제 반영된 서버 구조

```text
server/
  core/
    dependencies.py    # repository/service, 인증 계정 동기화/인증 함수
    http.py            # auth decorator, session 저장, UUID 검증 유틸

  interfaces/http/
    api/
      system.py        # health/bootstrap/dashboard/final-download
      auth.py          # signup API
      projects.py
      researchers.py
      research_notes.py
      signatures.py
      data_updates.py
      admin.py
      __init__.py
    router.py
```

## 3) 실제 반영된 클라이언트 구조

```text
client/
  interfaces/
    common.py          # 템플릿 공통 context
    web.py             # 로그인/관리자/워크플로우/연구노트 페이지 렌더링
```

## 4) 라우팅/호환성

- `projectnote/urls.py`는 `server.interfaces.http.router.urlpatterns`를 사용.
- `projectnote/views.py`는 하위 호환 import를 위한 re-export 레이어 유지.

## 5) 다음 단계 (DDD 고도화)

1. `server/application/<domain>/usecases` 신설
2. `server/domains/<domain>/repository_port` 도입
3. `server/infrastructure/persistence`로 ORM/repository 구현 이관
4. `client/templates` 도입 또는 기존 `templates/`와 명시적 매핑
