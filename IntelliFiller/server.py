import os
import sys
import json
import time
import socket
import logging
import threading
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any, List

# Add parent directory of IntelliFiller to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from IntelliFiller.config_manager import ConfigManager
from IntelliFiller.data_request import create_prompt, send_prompt_to_llm, test_connection
from IntelliFiller.headless_entrypoint import parse_llm_json, classify_error, resolve_prompt_config

logger = logging.getLogger("IntelliFiller.server")


def generate_server_zid(server) -> str:
    """
    Generates a unique server-side ZID per state-mutating request.
    Uses thread-safe monotonic incrementing to prevent collision within the same second.
    """
    now = datetime.now()
    with server.seq_lock:
        server.seq_counter = (server.seq_counter + 1) % 10000
        seq = server.seq_counter
    return f"{now:%Y%m%d%H%M%S}-{seq:04d}"


def warmup_llm_backend():
    """
    Pre-initialize network connections / sockets to local Ollama (127.0.0.1:11434) or cloud backend.
    """
    try:
        settings = ConfigManager.load_settings()
        selected = settings.get("selectedApi", "openai")
        logger.info(f"Warming up LLM connection for provider: {selected}")
        if selected == "ollama":
            url = settings.get("ollamaUrl") or "http://127.0.0.1:11434/api/generate"
            base_url = url.split("/api/")[0] if "/api/" in url else "http://127.0.0.1:11434"
            try:
                import urllib.request
                req = urllib.request.Request(base_url, method="GET")
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    pass
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"LLM backend warmup notice: {e}")


class IntelliFillerRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP REST handler for IntelliFiller vocabulary enrichment service.
    """

    def setup(self):
        super().setup()
        # Enforce strict 5-second socket timeout to prevent Slowloris-style worker thread hangs
        self.connection.settimeout(5.0)

    def address_string(self):
        # Override to bypass Windows reverse DNS lookup delays (<1ms vs 2s-5s latency)
        return self.client_address[0]

    def log_message(self, format_str, *args):
        if self.path and ('/health' in self.path or '/healthz' in self.path):
            return
        logger.info("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format_str % args))

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-ZID, X-Trace-ID')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, status_code: int, data_obj: dict):
        body = json.dumps(data_obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status_code: int, code: str, message: str, zid: Optional[str] = None, trace_id: Optional[str] = None, row_id: Optional[int] = None, retryable: bool = False, details: Optional[dict] = None):
        payload = {
            "status": "error",
            "zid": zid or "",
            "trace_id": trace_id or "",
            "code": code,
            "message": message,
            "row_id": row_id,
            "retryable": retryable,
            "details": details if details is not None else {}
        }
        self._send_json(status_code, payload)

    def _read_json_body(self) -> dict:
        content_length = self.headers.get('Content-Length')
        if not content_length:
            raise ValueError("Missing Content-Length header")
        try:
            length = int(content_length)
        except ValueError:
            raise ValueError("Invalid Content-Length header")
        raw_body = self.rfile.read(length)
        try:
            return json.loads(raw_body.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"Malformed JSON body: {e}")

    def do_GET(self):
        path = self.path.split('?')[0].rstrip('/')
        if path in ('/health', '/api/v1/health', '/healthz', ''):
            settings = ConfigManager.load_settings()
            prompts = [p.get("promptName") for p in ConfigManager.list_prompts() if p.get("promptName")]
            uptime = round(time.time() - getattr(self.server, 'start_time', time.time()), 2)
            backend = settings.get("selectedApi", "openai")
            model = settings.get(f"{backend}Model", "") or settings.get("openaiModel", "")
            data = {
                "status": "ok",
                "backend": backend,
                "model": model,
                "prompts": prompts,
                "uptime_seconds": uptime,
                "server_time": datetime.now().isoformat(),
                "zid": generate_server_zid(self.server)
            }
            self._send_json(200, data)
            return

        self._send_error(404, "ERR_NOT_FOUND", f"Endpoint '{self.path}' not found")

    def do_POST(self):
        path = self.path.split('?')[0].rstrip('/')
        if path in ('/shutdown', '/api/v1/shutdown'):
            req_zid = generate_server_zid(self.server)
            self._send_json(200, {"status": "success", "message": "Server shutting down", "zid": req_zid})
            def shutdown_server():
                time.sleep(0.1)
                try:
                    self.server.shutdown()
                    self.server.server_close()
                except Exception as e:
                    logger.error(f"Error during server shutdown: {e}")
            threading.Thread(target=shutdown_server, daemon=True).start()
            return

        if path in ('/enrich', '/api/v1/enrich'):
            start_time = time.perf_counter()
            try:
                body = self._read_json_body()
            except ValueError as e:
                self._send_error(400, "ERR_INVALID_PAYLOAD", str(e))
                return

            if not isinstance(body, dict):
                self._send_error(400, "ERR_INVALID_PAYLOAD", "Request body must be a JSON object")
                return

            prompt_name = body.get("prompt")
            if not prompt_name:
                self._send_error(400, "ERR_MISSING_PROMPT", "Field 'prompt' is required in payload", zid=body.get("zid"), trace_id=body.get("trace_id"))
                return

            rows = body.get("rows")
            if rows is None or not isinstance(rows, list):
                self._send_error(400, "ERR_MISSING_ROWS", "Field 'rows' must be a list of row objects", zid=body.get("zid"), trace_id=body.get("trace_id"))
                return

            zid = body.get("zid") or generate_server_zid(self.server)
            trace_id = body.get("trace_id") or f"{zid}:enrich"
            language = body.get("language", "")

            # Resolve prompt configuration (Anki prompts + built-in fallback)
            prompt_config = resolve_prompt_config(
                prompt_name=prompt_name,
                prompt_template_arg=body.get("prompt_template"),
                field_mapping_arg=body.get("field_mapping")
            )

            if not prompt_config:
                self._send_error(400, "ERR_PROMPT_NOT_FOUND", f"Prompt '{prompt_name}' not found", zid=zid, trace_id=trace_id)
                return

            mapping = dict(prompt_config.get("fieldMapping", {}))
            if body.get("field_mapping") and isinstance(body.get("field_mapping"), dict):
                mapping.update(body.get("field_mapping"))

            fmt = prompt_config.get("responseFormat", "text")
            settings = ConfigManager.load_settings()
            overwrite_global = settings.get("overwriteField", False)
            overwrite = prompt_config.get("overwriteField", overwrite_global)

            # Support request-level LLM overrides
            req_config = None
            if body.get("model") or body.get("base_url") or body.get("temperature") is not None or body.get("api_key") is not None:
                req_config = {}
                if body.get("base_url"):
                    req_config["selectedApi"] = "custom"
                    b_url = str(body["base_url"]).strip()
                    if not (b_url.endswith("/chat/completions") or b_url.endswith("/generate")):
                        if b_url.endswith("/v1"):
                            b_url = b_url + "/chat/completions"
                        elif "/v1" not in b_url and not b_url.endswith("/generate"):
                            b_url = b_url.rstrip("/") + "/v1/chat/completions"
                    req_config["customUrl"] = b_url
                    req_config["customModel"] = body.get("model") or "qwen2.5:3b"
                    req_config["customKey"] = body.get("api_key") or ""
                elif body.get("model"):
                    selected = settings.get("selectedApi", "openai")
                    req_config["selectedApi"] = selected
                    req_config[f"{selected}Model"] = body["model"]
                    if body.get("api_key") is not None:
                        req_config[f"{selected}Key"] = body["api_key"]
                        req_config["apiKey"] = body["api_key"]
                if body.get("temperature") is not None:
                    req_config["temperature"] = body["temperature"]

            enriched_rows = []
            for idx, row in enumerate(rows):
                if not isinstance(row, dict):
                    self._send_error(400, "ERR_INVALID_ROW", f"Row at index {idx} must be a dictionary", zid=zid, trace_id=trace_id, row_id=idx)
                    return

                row_id = row.get("row_id", idx)
                # Map fields if user passed 'word' instead of 'WordSource' or 'sentence' instead of 'SentenceSource' / 'Quotation'
                row_dict = dict(row)
                if "word" in row_dict and "WordSource" not in row_dict:
                    row_dict["WordSource"] = row_dict["word"]
                if "sentence" in row_dict:
                    if "Quotation" not in row_dict:
                        row_dict["Quotation"] = row_dict["sentence"]
                    if "SentenceSource" not in row_dict:
                        row_dict["SentenceSource"] = row_dict["sentence"]

                response = None
                try:
                    prompt_str = create_prompt(row_dict, prompt_config)
                    logger.info(f"[{zid}][{trace_id}] Processing row {idx+1}/{len(rows)}: {row_dict.get('WordSource', '')}")
                    try:
                        response = send_prompt_to_llm(prompt_str, config=req_config)
                    except TypeError:
                        response = send_prompt_to_llm(prompt_str)

                    enriched_item = {"row_id": row_id}
                    if fmt == "json":
                        data = parse_llm_json(response)
                        if not data:
                            raise ValueError(f"Failed to parse JSON response from LLM: {response[:100] if response else ''}")
                        
                        for k, v in data.items():
                            enriched_item[k] = v
                        for json_key, target_field in mapping.items():
                            if json_key in data:
                                enriched_item[target_field] = data[json_key]
                    else:
                        target_field = prompt_config.get("targetField", "translation")
                        enriched_item[target_field] = response.replace("\n", "<br>")
                        enriched_item["text"] = response

                    enriched_rows.append(enriched_item)
                except Exception as e:
                    err_info = classify_error(e, response_text=response)
                    logger.error(f"[{zid}][{trace_id}] Enrichment error at row {row_id}: {err_info['code']} - {err_info['message']}")
                    status_code = 500
                    if err_info["code"] == "ERR_LLM_RATE_LIMIT":
                        status_code = 429
                    elif err_info["code"] == "ERR_LLM_AUTH":
                        status_code = 401
                    elif err_info["code"] == "ERR_LLM_TIMEOUT":
                        status_code = 504
                    elif err_info["code"] == "ERR_LLM_NETWORK":
                        status_code = 503
                    elif err_info["code"] == "ERR_LLM_PARSE":
                        status_code = 422

                    self._send_error(
                        status_code=status_code,
                        code=err_info["code"],
                        message=err_info["message"],
                        zid=zid,
                        trace_id=trace_id,
                        row_id=row_id,
                        retryable=err_info["retryable"],
                        details=err_info["details"]
                    )
                    return

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._send_json(200, {
                "status": "success",
                "zid": zid,
                "trace_id": trace_id,
                "enriched_rows": enriched_rows,
                "duration_ms": duration_ms
            })
            return

        self._send_error(404, "ERR_NOT_FOUND", f"Endpoint '{self.path}' not found")


def start_server(host: str = "127.0.0.1", port: int = 8083):
    """
    Starts the IntelliFiller HTTP service.
    """
    server = ThreadingHTTPServer((host, port), IntelliFillerRequestHandler)
    server.allow_reuse_address = False
    server.daemon_threads = True
    server.disable_nagle_algorithm = True
    server.start_time = time.time()
    server.seq_counter = 0
    server.seq_lock = threading.Lock()

    warmup_llm_backend()

    logger.info(f"IntelliFiller HTTP Service running at http://{host}:{port}")
    print(f"IntelliFiller HTTP Service running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("IntelliFiller HTTP Service stopped by KeyboardInterrupt")
    finally:
        try:
            server.server_close()
        except Exception:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    port = 8083
    host = "127.0.0.1"
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    start_server(host=host, port=port)
