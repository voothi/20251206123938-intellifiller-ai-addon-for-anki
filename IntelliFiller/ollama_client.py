import httpx

class OllamaClient:
    def __init__(self, api_url="http://localhost:11434/api/generate", api_key=None, model="llama3"):
        self.api_url = api_url.strip()
        # If the user put just a base domain/port, append /api/generate
        if not self.api_url:
            self.api_url = "http://localhost:11434/api/generate"
        elif "/" not in self.api_url.replace("http://", "").replace("https://", ""):
            # No path components, append default endpoint
            self.api_url = self.api_url.rstrip("/") + "/api/generate"
            
        self.api_key = api_key
        self.model = model

    def generate_content(self, prompt, timeout=60.0):
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        is_chat = ("/v1/chat/completions" in self.api_url or "/chat" in self.api_url)
        
        payload = {
            "model": self.model,
            "stream": False
        }
        if is_chat:
            payload["messages"] = [{"role": "user", "content": prompt}]
        else:
            payload["prompt"] = prompt

        try:
            response = httpx.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()
            
            if is_chat:
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
        except Exception as e:
            raise Exception(f"Error calling Ollama API: {str(e)}")
