import hashlib
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class DBManager:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            print("WARNING: Supabase credentials not found in .env. Initialization will fail if called.")
            self.supabase = None
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)

    def _insert_paper_sync(self, paper_id, title, abstract, score, url, local_path):
        data = {
            "id": paper_id,
            "title": title,
            "abstract": abstract,
            "score": score,
            "url": url,
            "local_path": local_path
        }
        if self.supabase:
            self.supabase.table("papers").upsert(data).execute()

    async def save_paper(self, paper_id, title, abstract, score, url, local_path=None):
        """Asynchronously save paper metadata without blocking the event loop."""
        await asyncio.to_thread(self._insert_paper_sync, paper_id, title, abstract, score, url, local_path)

    def _get_cached_analysis_sync(self, chunk_text):
        chunk_hash = hashlib.sha256(chunk_text.encode('utf-8')).hexdigest()
        if self.supabase:
            response = self.supabase.table("chunk_cache").select("analysis_result").eq("chunk_hash", chunk_hash).execute()
            data = response.data
            if data and len(data) > 0:
                return data[0]["analysis_result"]
        return None

    async def get_cached_analysis(self, chunk_text):
        """Asynchronously fetch cached analysis from Supabase."""
        return await asyncio.to_thread(self._get_cached_analysis_sync, chunk_text)

    def _cache_analysis_sync(self, chunk_text, analysis_result):
        chunk_hash = hashlib.sha256(chunk_text.encode('utf-8')).hexdigest()
        data = {
            "chunk_hash": chunk_hash,
            "analysis_result": analysis_result
        }
        if self.supabase:
            self.supabase.table("chunk_cache").upsert(data).execute()

    async def cache_analysis(self, chunk_text, analysis_result):
        """Asynchronously insert analysis result into Supabase."""
        await asyncio.to_thread(self._cache_analysis_sync, chunk_text, analysis_result)

    def _get_all_cached_analyses_sync(self):
        if self.supabase:
            response = self.supabase.table("chunk_cache").select("analysis_result").execute()
            data = response.data
            return [row["analysis_result"] for row in data]
        return []

    async def get_all_cached_analyses(self):
        return await asyncio.to_thread(self._get_all_cached_analyses_sync)

    async def clear_session_cache(self):
        # We don't generally clear the remote database cache in production
        pass
