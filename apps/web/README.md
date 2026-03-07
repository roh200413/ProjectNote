# apps/web

Next.js web workspace bootstrap for monorepo migration.

## Environment

Set backend API base URL (optional):

```bash
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Install

```bash
cd apps/web
npm install
```

## Run

```bash
npm run dev
```

Then open: `http://127.0.0.1:3000`


## Auth bridge endpoints (web -> backend proxy)

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/health`

## Migrated pages (phase 1, low-risk)

- `GET /frontend/projects`
- `GET /frontend/research-notes`

Parity checklist/table: `apps/web/docs/parity-phase1.md`

## Migrated pages (phase 2, high-risk)

- `GET /frontend/research-notes/[noteId]/viewer`
- `GET /frontend/projects/[projectId]/research-notes`

Regression table: `apps/web/docs/parity-phase2.md`


## Current runtime note

`/frontend/*` pages are currently served by Django templates. `apps/web` routes are available for incremental migration and parity validation.
