# packages/types

OpenAPI contract + generated reusable TypeScript types.

## Generate contract and types

```bash
python packages/types/scripts/generate_api_contract.py
python packages/types/scripts/generate_api_types.py
```

or

```bash
./tooling/scripts/generate_api_types.sh
```

## Verify artifacts are up-to-date (CI-safe)

```bash
python packages/types/check_types.py
```

If API contracts change but generated types are stale, `check_types.py` fails.
