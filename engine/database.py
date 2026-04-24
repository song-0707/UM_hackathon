import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class DatabaseManager:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            print("WARNING: Supabase credentials not found in .env. Initialization will fail if called.")
            self.supabase = None
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)

    def _upsert_discovery_sync(self, paper_dict):
        """Phase 1: Upsert discovery data synchronously."""
        if not self.supabase:
            return None
        
        # We assume paper_dict contains: external_id, title, authors, abstract, url, publication_year, relevance_score, insight
        # We use upsert with on_conflict="external_id" to prevent duplicates
        response = self.supabase.table("papers").upsert(paper_dict, on_conflict="external_id").execute()
        return response.data

    async def upsert_discovery_data(self, paper_dict):
        """Asynchronously save Phase 1 results without blocking the event loop."""
        return await asyncio.to_thread(self._upsert_discovery_sync, paper_dict)

    def _update_deep_analysis_sync(self, external_id, markdown_report):
        """Phase 2: Update with Markdown report synchronously."""
        if not self.supabase:
            return None
            
        data = {
            "markdown_report": markdown_report,
            "analysis_status": "completed"
        }
        response = self.supabase.table("papers").update(data).eq("external_id", external_id).execute()
        return response.data

    async def update_deep_analysis(self, external_id, markdown_report):
        """Asynchronously save Phase 2 results without blocking event loop."""
        return await asyncio.to_thread(self._update_deep_analysis_sync, external_id, markdown_report)

    # For retrieving previous analysis state if needed
    def _get_paper_sync(self, external_id):
        if not self.supabase:
            return None
        response = self.supabase.table("papers").select("*").eq("external_id", external_id).execute()
        data = response.data
        if data and len(data) > 0:
            return data[0]
        return None

    async def get_paper(self, external_id):
        return await asyncio.to_thread(self._get_paper_sync, external_id)
        
db = DatabaseManager()
