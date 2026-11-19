import ast
import inspect
from pathlib import Path
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_curriculum_service, get_teacher_service, get_generation_service

client = TestClient(app)


class TestAsyncApiAndTryCatchStandard:
    """TDD Test Suite for Sprint 07: Verifies 100% of API endpoints use `async def` and `try-except` error handling."""

    def test_all_registered_api_endpoints_are_async_coroutines(self):
        """1. Ensures every custom APIRoute registered in FastAPI (including nested routers) is declared with `async def`."""
        def collect_api_routes(routes_list):
            collected = []
            for r in routes_list:
                if isinstance(r, APIRoute):
                    if not r.path.startswith("/openapi") and not r.path.startswith("/docs") and not r.path.startswith("/redoc"):
                        collected.append(r)
                elif hasattr(r, "original_router") and hasattr(r.original_router, "routes"):
                    collected.extend(collect_api_routes(r.original_router.routes))
                elif hasattr(r, "included_router") and hasattr(r.included_router, "routes"):
                    collected.extend(collect_api_routes(r.included_router.routes))
                elif hasattr(r, "routes"):
                    collected.extend(collect_api_routes(r.routes))
            return collected

        custom_routes = collect_api_routes(app.routes)
        assert len(custom_routes) >= 11

        non_async_routes = []
        for route in custom_routes:
            if not inspect.iscoroutinefunction(route.endpoint):
                non_async_routes.append(f"{route.methods} {route.path} -> {route.endpoint.__name__}")

        assert not non_async_routes, f"Found synchronous API endpoints (must be async def): {non_async_routes}"

    def test_all_endpoint_modules_contain_try_except_blocks(self):
        """2. Parses AST of all endpoint files to verify every route function wraps logic in a `try ... except` block."""
        endpoints_dir = Path(__file__).resolve().parent.parent / "app" / "api" / "v1" / "endpoints"
        endpoint_files = sorted(p for p in endpoints_dir.glob("*.py") if p.name != "__init__.py")
        assert len(endpoint_files) >= 5

        missing_try_except = []
        sync_functions = []

        for py_file in endpoint_files:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    sync_functions.append(f"{py_file.name}:{node.name}")
                elif isinstance(node, ast.AsyncFunctionDef):
                    has_try = any(isinstance(child, ast.Try) for child in ast.walk(node))
                    if not has_try:
                        missing_try_except.append(f"{py_file.name}:{node.name}")

        assert not sync_functions, f"Found sync `def` functions in endpoints (must be `async def`): {sync_functions}"
        assert not missing_try_except, f"Found `async def` endpoints missing `try ... except` block: {missing_try_except}"

    def test_endpoint_try_except_catches_unexpected_runtime_errors_gracefully(self):
        """3. Simulates unexpected runtime crash inside a service and verifies the endpoint's try-except returns safe HTTP 500 JSON."""
        class CrashingCurriculumService:
            def get_subjects(self, jenjang=None, kelas=None):
                raise RuntimeError("Simulated unexpected database cursor crash")

        app.dependency_overrides[get_curriculum_service] = lambda: CrashingCurriculumService()
        try:
            resp = client.get("/api/v1/curriculum/subjects?jenjang=SMP&kelas=7")
            assert resp.status_code == 500
            body = resp.json()
            assert body["success"] is False
            assert body["error_code"] == "INTERNAL_SERVER_ERROR"
            assert "Simulated unexpected database cursor crash" in body["message"]
        finally:
            app.dependency_overrides.clear()
