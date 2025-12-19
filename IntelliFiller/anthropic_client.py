import json
import httpx

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
            response = httpx.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()['content'][0]['text']
        except Exception as e:
            raise Exception(f"Error calling Anthropic API: {str(e)}")