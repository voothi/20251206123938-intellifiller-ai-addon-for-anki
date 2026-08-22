import json
import urllib.request
import urllib.error


class OllamaClient:
    def __init__(self, api_url="http://localhost:11434/api/generate", api_key=None, model="llama3", temperature=None):
        self.api_url = api_url.strip()
        if not self.api_url:
            self.api_url = "http://localhost:11434/api/generate"

        # Force Ollama Cloud to use OpenAI-compatible chat completions
        if "ollama.com" in self.api_url:
            self.is_chat = True
            self.api_url = "https://ollama.com/v1/chat/completions"
        else:
            # Check if it's an OpenAI-compatible endpoint
            self.is_chat = ("/v1" in self.api_url or "/chat" in self.api_url)

            if self.is_chat:
                # If it's a base v1 or chat URL, append /chat/completions
                if not (self.api_url.endswith("/chat/completions") or self.api_url.endswith("/completions")):
                    self.api_url = self.api_url.rstrip("/") + "/chat/completions"
            else:
                # Native Ollama endpoint
                if "/" not in self.api_url.replace("http://", "").replace("https://", ""):
                    # No path components, append default endpoint
                    self.api_url = self.api_url.rstrip("/") + "/api/generate"
                elif not self.api_url.endswith("/generate"):
                    self.api_url = self.api_url.rstrip("/") + "/generate"

        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    def generate_content(self, prompt, timeout=60.0, temperature=None):
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        effective_temp = temperature if temperature is not None else self.temperature
        payload = {
            "model": self.model,
            "stream": False
        }
        if effective_temp is not None:
            try:
                temp_val = float(effective_temp)
                if self.is_chat:
                    payload["temperature"] = temp_val
                else:
                    payload["options"] = {"temperature": temp_val}
            except (ValueError, TypeError):
                pass

        if self.is_chat:
            payload["messages"] = [{"role": "user", "content": prompt}]
        else:
            payload["prompt"] = prompt

        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))

            if self.is_chat:
                choices = result.get("choices", [])
                if choices and choices[0].get("message"):
                    return choices[0]["message"].get("content", "").strip()
                else:
                    raise ValueError(f"Unexpected OpenAI-compatible response structure: {result}")
            else:
                if "response" in result:
                    return result["response"].strip()
                elif "message" in result and "content" in result["message"]:
                    return result["message"]["content"].strip()
                else:
                    raise ValueError(f"Unexpected Ollama response structure: {result}")
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                error_body = str(e)
            raise Exception(f"Error calling Ollama API: HTTP {e.code} {e.reason} - {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"Error calling Ollama API: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling Ollama API: {str(e)}")
