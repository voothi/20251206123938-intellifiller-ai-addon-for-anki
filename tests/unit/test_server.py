import os
import sys
import json
import time
import socket
import pytest
import threading
import urllib.request
import urllib.error
from unittest.mock import patch, MagicMock

from IntelliFiller.config_manager import ConfigManager
from IntelliFiller.server import IntelliFillerRequestHandler, generate_server_zid, start_server
from http.server import ThreadingHTTPServer


@pytest.fixture
def running_server(monkeypatch):
    """
    Spawns a test IntelliFiller HTTP server on an ephemeral loopback port.
    """
    # Configure test prompt and settings
    ConfigManager.save_settings({"emulate": "yes", "selectedApi": "openai", "openaiModel": "gpt-4o-mini"})
    test_prompt_config = {
        "promptName": "ServerTestPrompt",
        "prompt": "Analyze {{{WordSource}}}. Context: {{{SentenceSource}}}",
        "responseFormat": "json",
        "fieldMapping": {
            "ru": "WordDestination",
            "ipa": "WordSourceIPA",
            "morphology": "MorphologyAI"
        },
        "overwriteField": True
    }
    ConfigManager.save_prompt(test_prompt_config)

    # Find free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]

    server = ThreadingHTTPServer(('127.0.0.1', port), IntelliFillerRequestHandler)
    server.allow_reuse_address = False
    server.daemon_threads = True
    server.disable_nagle_algorithm = True
    server.start_time = time.time()
    server.seq_counter = 0
    server.seq_lock = threading.Lock()

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    yield base_url, server

    try:
        server.shutdown()
        server.server_close()
    except Exception:
        pass


def test_server_health_endpoint(running_server):
    base_url, _ = running_server
    req = urllib.request.Request(f"{base_url}/health", method="GET")
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "ok"
        assert data["backend"] == "openai"
        assert data["model"] == "gpt-4o-mini"
        assert "ServerTestPrompt" in data["prompts"]
        assert "uptime_seconds" in data
        assert "zid" in data


def test_server_enrich_success(running_server, monkeypatch):
    base_url, _ = running_server

    # Mock send_prompt_to_llm
    mock_responses = [
        '{"ru": "яблоко", "ipa": "æpl", "morphology": "Noun|Neut"}',
        '{"ru": "банан", "ipa": "bəˈnɑːnə", "morphology": "Noun|Masc"}'
    ]
    response_idx = 0

    def mock_send(prompt):
        nonlocal response_idx
        res = mock_responses[response_idx]
        response_idx += 1
        return res

    monkeypatch.setattr("IntelliFiller.server.send_prompt_to_llm", mock_send)

    payload = {
        "prompt": "ServerTestPrompt",
        "language": "de",
        "zid": "20260819003000",
        "trace_id": "20260819003000:enrich:test",
        "rows": [
            {"row_id": 1, "WordSource": "Apfel", "SentenceSource": "Ein Apfel."},
            {"row_id": 2, "word": "Banane", "sentence": "Eine Banane."}
        ]
    }

    req = urllib.request.Request(
        f"{base_url}/enrich",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        assert resp.status == 200
        res_data = json.loads(resp.read().decode("utf-8"))
        assert res_data["status"] == "success"
        assert res_data["zid"] == "20260819003000"
        assert res_data["trace_id"] == "20260819003000:enrich:test"
        assert len(res_data["enriched_rows"]) == 2
        assert res_data["enriched_rows"][0]["row_id"] == 1
        assert res_data["enriched_rows"][0]["WordDestination"] == "яблоко"
        assert res_data["enriched_rows"][0]["WordSourceIPA"] == "æpl"
        assert res_data["enriched_rows"][1]["row_id"] == 2
        assert res_data["enriched_rows"][1]["WordDestination"] == "банан"
        assert "duration_ms" in res_data


def test_server_enrich_missing_fields(running_server):
    base_url, _ = running_server

    # Missing prompt
    payload_no_prompt = {"rows": [{"row_id": 1, "word": "test"}]}
    req = urllib.request.Request(
        f"{base_url}/enrich",
        data=json.dumps(payload_no_prompt).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(req, timeout=3.0)
    assert excinfo.value.code == 400
    err_body = json.loads(excinfo.value.read().decode("utf-8"))
    assert err_body["code"] == "ERR_MISSING_PROMPT"

    # Missing rows
    payload_no_rows = {"prompt": "ServerTestPrompt"}
    req2 = urllib.request.Request(
        f"{base_url}/enrich",
        data=json.dumps(payload_no_rows).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with pytest.raises(urllib.error.HTTPError) as excinfo2:
        urllib.request.urlopen(req2, timeout=3.0)
    assert excinfo2.value.code == 400
    err_body2 = json.loads(excinfo2.value.read().decode("utf-8"))
    assert err_body2["code"] == "ERR_MISSING_ROWS"


def test_server_enrich_prompt_not_found(running_server):
    base_url, _ = running_server
    payload = {"prompt": "NonExistentPrompt12345", "rows": [{"row_id": 1, "word": "test"}]}
    req = urllib.request.Request(
        f"{base_url}/enrich",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(req, timeout=3.0)
    assert excinfo.value.code == 400
    err_body = json.loads(excinfo.value.read().decode("utf-8"))
    assert err_body["code"] == "ERR_PROMPT_NOT_FOUND"


def test_server_enrich_rate_limit_error(running_server, monkeypatch):
    base_url, _ = running_server

    def mock_send(prompt):
        raise Exception("HTTP 429 Too Many Requests - Quota exceeded")

    monkeypatch.setattr("IntelliFiller.server.send_prompt_to_llm", mock_send)

    payload = {
        "prompt": "ServerTestPrompt",
        "rows": [{"row_id": 42, "WordSource": "Apfel", "SentenceSource": "Ein Apfel."}],
        "zid": "20260819003000",
        "trace_id": "20260819003000:enrich:ratelimit"
    }

    req = urllib.request.Request(
        f"{base_url}/enrich",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(req, timeout=3.0)
    assert excinfo.value.code == 429
    err_body = json.loads(excinfo.value.read().decode("utf-8"))
    assert err_body["status"] == "error"
    assert err_body["code"] == "ERR_LLM_RATE_LIMIT"
    assert err_body["retryable"] is True
    assert err_body["row_id"] == 42
    assert err_body["zid"] == "20260819003000"
    assert err_body["trace_id"] == "20260819003000:enrich:ratelimit"


def test_server_enrich_parse_error(running_server, monkeypatch):
    base_url, _ = running_server

    def mock_send(prompt):
        return "Invalid json body..."

    monkeypatch.setattr("IntelliFiller.server.send_prompt_to_llm", mock_send)

    payload = {
        "prompt": "ServerTestPrompt",
        "rows": [{"row_id": 10, "WordSource": "Apfel", "SentenceSource": "Ein Apfel."}]
    }

    req = urllib.request.Request(
        f"{base_url}/enrich",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(req, timeout=3.0)
    assert excinfo.value.code == 422
    err_body = json.loads(excinfo.value.read().decode("utf-8"))
    assert err_body["status"] == "error"
    assert err_body["code"] == "ERR_LLM_PARSE"
    assert err_body["retryable"] is False
    assert err_body["row_id"] == 10


def test_server_shutdown_endpoint(running_server):
    base_url, server = running_server
    req = urllib.request.Request(
        f"{base_url}/shutdown",
        data=json.dumps({}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "success"
        assert "Server shutting down" in data["message"]
