import json
import urllib.request
import urllib.parse
import urllib.error


class GeminiClient:
    def __init__(self, api_key, model="gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generate_content(self, prompt, timeout=60.0):
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        url = self.base_url + "?" + urllib.parse.urlencode({"key": self.api_key})

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result['candidates'][0]['content']['parts'][0]['text']
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                error_body = str(e)
            raise Exception(f"Error calling Gemini API: HTTP {e.code} {e.reason} - {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"Error calling Gemini API: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling Gemini API: {str(e)}")
