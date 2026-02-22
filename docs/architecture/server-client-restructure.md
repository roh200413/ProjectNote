# ProjectNote 구조 재설계안 (server/client + 핵심 기능 분리)

이 문서는 `projectnote/views.py` 단일 책임 집중 구조를
`server`(API/도메인 기능)와 `client`(템플릿 렌더링)로 분리한 실제 적용 구조를 정리한다.

## 1) 최상위 분리 원칙

```text
projectnote/
  server/   # JSON API, 인증/권한 공통, 도메인 기능 분리
  client/   # 템플릿 렌더링(Web pages)
```

- `server`: 비즈니스/데이터 접근을 사용하는 API 엔드포인트 중심.
- `client`: 화면 렌더링, 페이지 라우트, 세션 기반 UX 흐름.

## 2) 실제 반영된 서버 구조

```text
projectnote/server/
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
      __init__.py      # API export
    router.py          # 전체 URL 매핑
```

### 핵심 기능 구분 기준

- `system`: 헬스체크/부트스트랩/요약 메타 API
- `auth`: 가입 등 인증 관련 API
- `projects / researchers / research_notes / signatures / data_updates / admin`: 도메인별 API

## 3) 실제 반영된 클라이언트 구조

```text
projectnote/client/
  interfaces/
    common.py          # 템플릿 공통 context
    web.py             # 로그인/관리자/워크플로우/연구노트 페이지 렌더링
```

- 템플릿 렌더링 핸들러는 `client.interfaces.web`로 이동.
- 즉, **API(server)** 와 **템플릿 페이지(client)** 를 코드 레벨에서 분리.

## 4) 라우팅/호환성

- `projectnote/urls.py` → `server.interfaces.http.router.urlpatterns` 단일 진입.
- `projectnote/views.py`는 하위 호환 import를 위한 re-export 레이어 유지.

## 5) 다음 단계 (DDD 고도화)

1. `server/application/<domain>/usecases` 신설 (현재 API에서 직접 repository 접근 제거)
2. `server/domains/<domain>/repository_port` 도입 (포트/어댑터)
3. `server/infrastructure/persistence`로 ORM/repository 구현 이관
4. `client/templates` 디렉터리 명시 도입(현재는 기존 `templates/` 유지)

이 문서는 “server/client 분리 + 핵심 기능별 구분”의 최소 실구현 기준이다.
