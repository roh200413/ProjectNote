from __future__ import annotations

from django.http import JsonResponse



_METHOD_OVERRIDES: dict[str, list[str]] = {
    "api/v1/health": ["get"],
    "api/v1/frontend/bootstrap": ["get"],
    "api/v1/auth/signup": ["post"],
    "api/v1/auth/login": ["post"],
    "api/v1/auth/logout": ["post"],
    "api/v1/auth/me": ["get"],
}


_COMPONENT_SCHEMAS = {
    "HealthResponse": {
        "type": "object",
        "properties": {"status": {"type": "string", "example": "ok"}},
        "required": ["status"],
    },
    "FrontendBootstrapResponse": {
        "type": "object",
        "properties": {
            "api_name": {"type": "string"},
            "api_version": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
        },
        "required": ["api_name", "api_version", "timestamp"],
    },
    "AuthMeResponse": {
        "type": "object",
        "properties": {
            "user": {"type": "object", "additionalProperties": True},
            "detail": {"type": "string"},
        },
    },
    "AuthLoginResponse": {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "user": {"type": "object", "additionalProperties": True},
            "detail": {"type": "string"},
        },
    },
}


_RESPONSE_OVERRIDES = {
    "api/v1/health": {
        "200": {
            "description": "OK",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/HealthResponse"}
                }
            },
        }
    },
    "api/v1/frontend/bootstrap": {
        "200": {
            "description": "Frontend bootstrap info",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/FrontendBootstrapResponse"}
                }
            },
        }
    },
    "api/v1/auth/login": {
        "200": {
            "description": "Login success",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/AuthLoginResponse"}
                }
            },
        },
        "401": {"description": "Invalid credentials"},
        "403": {"description": "Not approved or unauthorized"},
    },
    "api/v1/auth/me": {
        "200": {
            "description": "Current session profile",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/AuthMeResponse"}
                }
            },
        },
        "401": {"description": "Authentication required"},
    },
    "api/v1/auth/logout": {
        "200": {"description": "Logged out"},
    },
}


def _normalize_path(route: str) -> str:
    cleaned = route.strip("^").strip("$")
    cleaned = cleaned.replace("<str:", "{").replace("<int:", "{").replace(">", "}")
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    return cleaned


def build_openapi_spec() -> dict:
    paths: dict[str, dict] = {}

    from server.config.urls import urlpatterns

    for url in urlpatterns:
        route = getattr(url.pattern, "_route", "")
        if not route.startswith("api/v1/"):
            continue

        normalized = _normalize_path(route)
        methods = _METHOD_OVERRIDES.get(route, ["get", "post"])

        operations: dict[str, dict] = {}
        for method in methods:
            responses = _RESPONSE_OVERRIDES.get(route, {
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "additionalProperties": True}
                        }
                    },
                }
            })
            operations[method] = {
                "operationId": f"{method}_{route.replace('/', '_').replace('-', '_')}",
                "responses": responses,
            }

        paths[normalized] = operations

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "ProjectNote API",
            "version": "v1",
        },
        "paths": paths,
        "components": {"schemas": _COMPONENT_SCHEMAS},
    }


def openapi_json_api(_request):
    return JsonResponse(build_openapi_spec())
