# 화면 이관 2차 기능/회귀 검증표 (고위험)

대상: UI 전환(서버 API 유지)

- `/frontend/research-notes/[noteId]/viewer`
- `/frontend/projects/[projectId]/research-notes`

## 구현 범위
- 연구노트: viewer/파일 다운로드/PDF 내보내기/이미지·PDF 미리보기
- 프로젝트: 연구파일 업로드, 표지 저장/표지 PDF 출력, 연구파일 병합 PDF 출력
- 모든 동작은 기존 백엔드 엔드포인트를 프록시하는 web API route를 통해 수행

## 회귀 결과 표

| 케이스 | 검증 방법 | 결과 | 비고 |
|---|---|---|---|
| PDF 내보내기 성공 | `GET /api/research-notes/{noteId}/export-pdf`, `GET /api/projects/{projectId}/research-notes/export-pdf` 호출 | ✅ 성공 | 응답이 `application/pdf`로 반환됨 |
| 파일 업로드/다운로드 | `POST /api/projects/{projectId}/research-notes/upload` + `GET /api/research-notes/{noteId}/files/{fileId}/content?download=1` | ✅ 성공 | 업로드/다운로드 프록시 동작 확인 |
| 이미지/PDF 미리보기 | viewer 화면에서 파일 확장자에 따라 `iframe(pdf)`/`img(image)` 렌더링 | ✅ 성공 | 동일 파일 content endpoint 사용 |
| 권한별 접근 | 인증 없는 상태에서 관련 API 호출 시 401/403 전달 확인 | ✅ 성공 | 백엔드 권한 정책 유지(프론트는 코드/메시지 표시) |

## 페이지별 기능 parity 체크리스트

### `/frontend/research-notes/[noteId]/viewer`
- [x] 파일 선택
- [x] PDF/이미지 미리보기
- [x] 원본 다운로드
- [x] PDF 내보내기
- [x] 오류 표시(권한/404 포함)

### `/frontend/projects/[projectId]/research-notes`
- [x] 파일 업로드
- [x] 표지 데이터 저장
- [x] 표지 PDF 출력
- [x] 선택/전체 병합 PDF 출력
- [x] 오류 표시(권한/유효성 포함)
