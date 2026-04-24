# System Analysis Document (SAD) - ScholarFlow AI

## 1. High-Level Architecture
ScholarFlow operates on an asynchronous, cloud-ready architecture:
- **Client Tier:** Vanilla HTML/CSS/JS frontend utilizing modern `EventSource` (Server-Sent Events) for live data streaming.
- **Application Tier:** Python FastAPI backend executing asynchronous non-blocking I/O tasks (`asyncio`).
- **Data Tier:** Supabase (PostgreSQL) hosted in the cloud, utilizing Row Level Security (RLS) policies.
- **External Services:** Z AI GLM API (Reasoning), OpenAlex API (Metadata), ArXiv API (Fallback Open Access).

## 2. GLM as Service Layer
The Z AI GLM model serves as the central orchestration and reasoning engine. 
- **Prompt Construction:** The `LLMManager` injects dynamic context (e.g., Target Profiles, Abstracts, PDF Chunks) into strict prompt templates.
- **Context Window Management:** To bypass context limits on 30+ page PDFs, the `PaperHandler` uses `PyMuPDF` to extract text and slice it into 2000-token chunks. The GLM analyzes these chunks in parallel via `asyncio.gather` with a `Semaphore(5)` to prevent 429 Rate Limits.
- **Parsing:** Responses are sanitized using RegEx to strip unwanted markdown wrappers (e.g., ````json`) and internal thinking tags before database insertion.

## 3. Sequence Diagram (User Journey: Submit Request to Resolution)
1. **User Input:** User enters research query in UI.
2. **Discovery (Stage 1):** FastAPI receives `POST /api/search`. Engine queries OpenAlex/ArXiv. GLM generates insights/scores. FastAPI returns JSON. UI renders Gallery.
3. **Approval:** User checks desired papers and clicks "Deep Analyze".
4. **Task Initialization:** `POST /api/start_analysis` generates a unique `task_id`.
5. **Deep Analysis (Stage 2):** UI opens SSE connection to `GET /api/analyze/{task_id}`.
6. **Processing:** Engine downloads PDFs. If 403 Forbidden (paywall), falls back to ArXiv. PDFs are chunked. GLM analyzes chunks. Progress is streamed via SSE.
7. **Synthesis & Storage:** GLM synthesizes all chunk data. Final Markdown report is upserted to Supabase. SSE connection closes. UI renders report.

## 4. Technological Stack
- **Frontend:** HTML5, Vanilla CSS (Glassmorphism), JavaScript, `marked.js` (Markdown parsing).
- **Backend Core:** Python 3.10+, FastAPI, Uvicorn, `sse-starlette` (Streaming).
- **Data & APIs:** `supabase-py` (Database), `aiohttp` (Async HTTP client), `fitz` / PyMuPDF (PDF processing).
- **AI Integration:** Z AI GLM API (`ilmu-glm-5.1`).

## 5. Data Flow Diagram (DFD)
- **Input:** Unstructured User Problem Statement -> [GLM Boolean Expander].
- **Fetch:** Boolean String -> [OpenAlex API] -> JSON Metadata.
- **Enrich:** JSON Metadata -> [GLM Insight Generator] -> Enriched Metadata (Phase 1 DB Upsert).
- **Extract:** PDF URL -> [PyMuPDF] -> Raw Text -> [Chunker] -> Array of Text Chunks.
- **Analyze:** Text Chunks -> [GLM Analyzer] -> Array of Key Findings (Saved to `chunk_cache` DB).
- **Output:** Array of Key Findings -> [GLM Synthesizer] -> Structured Markdown Report (Phase 2 DB Update).
