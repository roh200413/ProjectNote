# apps/backend

Django backend workspace for monorepo migration.

## Run (from repo root)

```bash
python apps/backend/manage.py migrate --noinput
python apps/backend/manage.py runserver 127.0.0.1:8000
```

## Smoke check

```bash
python apps/backend/manage.py check
```


> 참고: `runserver` 실행 시 `manage.py`가 기본적으로 `migrate --noinput`를 먼저 수행합니다. 필요하면 `--skip-migrate` 옵션으로 생략할 수 있습니다.
