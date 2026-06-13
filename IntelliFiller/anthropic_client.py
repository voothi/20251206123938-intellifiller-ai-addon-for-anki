import json
import urllib.request
import urllib.error


class SimpleAnthropicClient:
    def __init__(self, api_key, model="claude-haiku-4-5"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"

    def create_message(self, prompt, max_tokens=2000, timeout=60.0):
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        data = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            req = urllib.request.Request(
                self.base_url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload['content'][0]['text']
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                error_body = str(e)
            raise Exception(f"Error calling Anthropic API: HTTP {e.code} {e.reason} - {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"Error calling Anthropic API: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling Anthropic API: {str(e)}")
