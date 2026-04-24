import os
import aiohttp
import json
import sys
import asyncio
import re
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

class LLMManager:
    def __init__(self, api_url="https://api.ilmu.ai/anthropic/v1/messages", model="ilmu-glm-5.1"):
        self.api_url = api_url
        self.model = model
        self.conversation_history = []
        
        api_key = os.getenv("LLM_API_KEY", "")
        if not api_key:
            print("WARNING: LLM_API_KEY not found in .env. API calls will fail.")
            
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self._session = None

    async def get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _clean_output(self, raw_text: str) -> str:
        """
        Sanitize the LLM output by removing unwanted JSON tags, 
        internal symbols, and markdown code block wrappers.
        """
        if not isinstance(raw_text, str):
            return str(raw_text)
            
        # Remove ```json or ``` blocks
        cleaned = re.sub(r'```[a-zA-Z]*\n', '', raw_text)
        cleaned = re.sub(r'```', '', cleaned)
        
        # Remove internal thinking/chunk tags if present (e.g., <chunk>...</chunk>)
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # Strip leading/trailing whitespaces
        return cleaned.strip()

    async def _call_api(self, messages):
        payload = {
            "model": self.model,
            "messages": messages
        }
        max_retries = 3  # Increased retries for stability
        retry_delay = 3
        session = await self.get_session()

        for attempt in range(max_retries):
            try:
                # Use a longer timeout (300s) because the final synthesis report takes a long time to generate
                async with session.post(self.api_url, headers=self.headers, json=payload, timeout=300) as response:
                    if response.status == 504:
                        if attempt < max_retries - 1:
                            tqdm.write(f"API 504 Gateway Timeout. Retrying in {retry_delay}s...")
                            await asyncio.sleep(retry_delay)
                            continue
                        return "Error: API Gateway Timeout (504)", []
                    
                    if response.status != 200:
                        text = await response.text()
                        tqdm.write(f"API Error {response.status}: {text[:100]}...")
                    
                    response.raise_for_status()
                    data = await response.json()
                    assistant_content = data.get("content", [])
                    reply_text = "\n".join([item.get("text", "") for item in assistant_content if item.get("type") == "text"])
                    return reply_text, assistant_content
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return f"Error: {str(e)}", []
        return "Error: Max retries exceeded", []

    async def chat(self, message, clear_history=False):
        if clear_history:
            self.conversation_history = []
        
        self.conversation_history.append({"role": "user", "content": [{"type": "text", "text": message}]})
        reply_text, assistant_content = await self._call_api(self.conversation_history)
        
        if assistant_content:
            self.conversation_history.append({"role": "assistant", "content": assistant_content})
        
        return self._clean_output(reply_text)

    async def analyze_chunk(self, chunk_text, prompt):
        messages = [
            {"role": "user", "content": [{"type": "text", "text": f"{prompt}\n\nChunk:\n{chunk_text}"}]}
        ]
        reply_text, _ = await self._call_api(messages)
        return self._clean_output(reply_text)

    async def synthesize(self, summarized_results, final_prompt):
        messages = [
            {"role": "user", "content": [{"type": "text", "text": f"{final_prompt}\n\nSummarized Results:\n{summarized_results}"}]}
        ]
        reply_text, _ = await self._call_api(messages)
        return self._clean_output(reply_text)
