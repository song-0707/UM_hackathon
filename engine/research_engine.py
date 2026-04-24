import asyncio
from .llm_manager import LLMManager
from .database import db
from .paper_handler import PaperHandler
from .db_manager import DBManager # We might still need chunk_cache table which was in DBManager, but we can migrate it if needed. For now, keep it for chunk cache.
import re

class ResearchEngine:
    def __init__(self):
        self.llm = LLMManager()
        self.paper_handler = PaperHandler()
        self.cache_db = DBManager() # Keep DBManager for chunk cache for now, or use Supabase chunk_cache
        # self.db = db # imported from database.py for phase 1 and 2

    async def shutdown(self):
        await self.llm.close()
        await self.paper_handler.close()

    async def get_boolean_query(self, keyword):
        prompt = f"Expand the following keyword into a professional Boolean search string (using AND, OR, NOT) optimized for OpenAlex: {keyword}. Return only the Boolean string."
        return await self.llm.ask(prompt)

    async def create_relevance_profile(self, description):
        prompt = f"Analyze the following complex problem and create a 'Target Relevance Profile' for scoring academic papers. Profile should include key themes, required methodologies, and specific exclusion criteria: {description}"
        return await self.llm.ask(prompt)

    async def discover(self, mode, input_data):
        """Stage 1: Discover papers and get predicted relevance and insight.
        Implements rate limiting via Semaphore(5) and top_k slice."""
        if mode == 1:
            query = await self.get_boolean_query(input_data)
            if query.startswith("Error:"): return {"error": query}
            profile = f"Search Query: {query}"
        else:
            profile = await self.create_relevance_profile(input_data)
            if profile.startswith("Error:"): return {"error": profile}
            query = input_data

        # Fetch articles
        results = await self.paper_handler.search_openalex(query)
        if not results:
            results = await self.paper_handler.search_arxiv(query)

        if not results:
            return {"error": "No papers found on both OpenAlex and ArXiv."}

        # Rate Limiting: Top 10 papers
        top_results = results[:10]
        
        # Rate Limiting: Semaphore for concurrent LLM calls
        semaphore = asyncio.Semaphore(5)
        
        discovered_papers = []

        async def process_insight(paper):
            async with semaphore:
                title = paper.get("title", "")
                abstract = paper.get("abstract", "")
                external_id = paper.get("id", "")
                authors = ", ".join(paper.get("authors", [])) if "authors" in paper else ""
                if not authors and "author" in paper:
                    authors = ", ".join([a.get("name", "") for a in paper.get("author", [])])
                year = str(paper.get("publication_year") or paper.get("year") or "Unknown")
                url = paper.get("open_access", {}).get("oa_url", "") or paper.get("id", "")
                
                # Get Relevance Score
                prompt_score = f"Target Profile: {profile}\nAnalyze relevance (0-100) based on Objective Alignment and Methodological Suitability.\nReturn ONLY a numeric score.\nTitle: {title}\nAbstract: {abstract}"
                score_str = await self.llm.ask(prompt_score)
                try:
                    score = int(re.search(r'\d+', score_str).group())
                except:
                    score = 0
                
                # Get 3-Sentence Insight
                prompt_insight = f"Based on the following abstract, provide a concise 3-sentence insight highlighting the main contribution and potential relevance to the profile: {profile}\n\nAbstract: {abstract}"
                insight = await self.llm.ask(prompt_insight)
                
                paper_dict = {
                    "external_id": external_id,
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "url": url,
                    "publication_year": year,
                    "relevance_score": score,
                    "insight": insight
                }
                
                # Insert into Supabase
                await db.upsert_discovery_data(paper_dict)
                
                return paper_dict

        tasks = [process_insight(paper) for paper in top_results]
        processed_results = await asyncio.gather(*tasks)
        
        return {"profile": profile, "papers": processed_results}

    async def deep_analyze_paper(self, paper_id, title, url, year, profile, yield_callback=None):
        """Perform chunking and analysis for a single paper, yielding progress."""
        if yield_callback: await yield_callback(f"[API CALL] Starting analysis for {title}")
        
        pdf_path = await self.paper_handler.download_pdf(url, paper_id, title, year)
        if not pdf_path:
            # Fallback ArXiv
            arxiv_results = await self.paper_handler.search_arxiv(title)
            if arxiv_results:
                fallback_paper = arxiv_results[0]
                fallback_url = fallback_paper.get("open_access", {}).get("oa_url", "")
                fallback_id = fallback_paper.get("id", "")
                fallback_year = fallback_paper.get("year", "Unknown")
                pdf_path = await self.paper_handler.download_pdf(fallback_url, fallback_id, title, fallback_year)

        if not pdf_path:
            if yield_callback: await yield_callback(f"[FAILED] Could not download PDF for {title}")
            return None

        if yield_callback: await yield_callback(f"[CHUNKING] Extracting text from {title}")
        chunks = self.paper_handler.extract_text_and_chunk(pdf_path)
        
        # Parallelize chunk analysis with a Semaphore to prevent 429 Too Many Requests
        semaphore = asyncio.Semaphore(5)
        
        async def process_chunk(i, chunk):
            async with semaphore:
                cached = await self.cache_db.get_cached_analysis(chunk)
                if cached:
                    if yield_callback: await yield_callback(f"[CACHE HIT] Finished chunk {i+1}/{len(chunks)} of {title}")
                    return (i, cached)
                else:
                    if yield_callback: await yield_callback(f"[API CALL] Analyzing chunk {i+1}/{len(chunks)} of {title}")
                    prompt = f"Analyze this chunk in the context of: {profile}. Extract key findings."
                    analysis = await self.llm.analyze_chunk(chunk, prompt)
                    await self.cache_db.cache_analysis(chunk, analysis)
                    if yield_callback: await yield_callback(f"[SUCCESS] Finished chunk {i+1}/{len(chunks)} of {title}")
                    return (i, analysis)

        tasks = [process_chunk(i, chunk) for i, chunk in enumerate(chunks)]
        results = await asyncio.gather(*tasks)
        
        # Reconstruct the paper analysis in the correct order
        results.sort(key=lambda x: x[0])
        paper_analysis = [res[1] for res in results]
            
        return f"Paper: {title}\n" + "\n".join(paper_analysis)

    async def synthesize_all(self, all_analyses, profile, yield_callback=None):
        if yield_callback: await yield_callback(f"[API CALL] Synthesizing final report...")
        summarized_results = "\n\n---\n\n".join(all_analyses)
        final_report = await self.llm.synthesize(summarized_results, f"Provide a comprehensive research synthesis report in Markdown. Profile: {profile}. Max 4000 tokens.")
        return final_report
