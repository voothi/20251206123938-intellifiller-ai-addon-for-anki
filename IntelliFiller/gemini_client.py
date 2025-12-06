import httpx

class GeminiClient:
    def __init__(self, api_key, model="gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generate_content(self, prompt):
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        try:
            response = httpx.post(
                self.base_url,
                headers=headers,
                params={"key": self.api_key},
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            # Extract text from the response structure
            # Response format: { "candidates": [ { "content": { "parts": [ { "text": "..." } ] } } ] }
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            raise Exception(f"Error calling Gemini API: {str(e)}")
