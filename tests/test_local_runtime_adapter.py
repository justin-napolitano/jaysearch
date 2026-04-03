from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.local_runtime.ollama_adapter import OllamaAdapter


def test_ollama_adapter_runtime_probe_reports_missing_models() -> None:
    def requester(url: str, method: str, payload: dict | None) -> dict:
        assert url.endswith("/api/tags")
        assert method == "GET"
        assert payload is None
        return {"models": [{"name": "router"}]}

    adapter = OllamaAdapter(base_url="http://127.0.0.1:11434", requester=requester)
    report = adapter.runtime_probe(required_models=["router", "planner"])

    assert report["backend"] == "ollama"
    assert report["reachable"] is True
    assert report["models_checked"] == ["router", "planner"]
    assert report["missing_models"] == ["planner"]


def test_ollama_adapter_generate_json_parses_response_object() -> None:
    def requester(url: str, method: str, payload: dict | None) -> dict:
        assert url.endswith("/api/generate")
        assert method == "POST"
        assert payload is not None
        return {"response": '{"route_target":"local_planner","reason_codes":["task_is_local_planning"]}'}

    adapter = OllamaAdapter(base_url="http://127.0.0.1:11434", requester=requester)
    payload = adapter.generate_json(model="router", prompt="test")

    assert payload["route_target"] == "local_planner"
    assert payload["reason_codes"] == ["task_is_local_planning"]
