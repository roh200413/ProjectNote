.PHONY: run-backend run-web check-ui check-types generate-api-types lint-repo

run-backend:
	./tooling/scripts/run_backend.sh

run-web:
	./tooling/scripts/run_web.sh

check-ui:
	./tooling/scripts/check_ui.sh

check-types:
	./tooling/scripts/check_types.sh

generate-api-types:
	./tooling/scripts/generate_api_types.sh

lint-repo:
	./tooling/scripts/lint_repo.sh
