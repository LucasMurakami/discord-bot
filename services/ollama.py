import os
import aiohttp

class OllamaService:
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_URL')
        self.default_model = os.getenv('OLLAMA_MODEL')
        self.session = aiohttp.ClientSession()

    """Generate text using Ollama's API with test limits"""
    async def generate_text_response(self, prompt: str, model: str = None) -> str:
        model = model or self.default_model
        url = f"{self.base_url}/api/generate"
        system_instruction = os.getenv('PROMPT_TEXT')

        payload = {
            "model": model,
            "prompt": f"{system_instruction}\n\nUser: {prompt}\nAssistant:",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 900
            }
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['response'][:2000]  # Maximum Discord Limit
                else:
                    error = await response.text()
                    return f"Error: {response.status} - {error[:150]}..."
        except aiohttp.ClientError as e:
            return f"Connection error: {str(e)[:200]}"
        except Exception as e:
            return f"Unexpected error: {str(e)[:200]}"
        

    """Generate text for voice response using Ollama's API with test limits"""
    async def generate_text_voice_response(self, prompt: str, model: str = None) -> str:        
        model = model or self.default_model
        url = f"{self.base_url}/api/generate"
        system_instruction = os.getenv('PROMPT_VOICE')

        payload = {
          "model": self.default_model,
          "prompt": f"{system_instruction}\n\nUser: {prompt}\nAssistant:",
          "stream": False,
          "options": {
              "temperature": 0.7,
              "max_tokens": 200 
          }
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['response'][:200]
                else:
                    error = await response.text()
                    return f"Error: {response.status} - {error[:150]}..."
        except aiohttp.ClientError as e:
            return f"Connection error: {str(e)[:200]}"
        except Exception as e:
            return f"Unexpected error: {str(e)[:200]}"

    async def close(self):
        await self.session.close()