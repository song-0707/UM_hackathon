# Quality Assurance Testing Document (QATD) - ScholarFlow AI

## 1. Risk Assessment (5x5 Matrix Focus)
| Risk | Likelihood | Severity | Mitigation Strategy |
| :--- | :---: | :---: | :--- |
| **LLM 429 Rate Limiting** | High | High | Implemented `asyncio.Semaphore(5)` to throttle concurrent GLM requests during parallel chunk analysis. |
| **API 504 Gateway Timeout** | Medium | High | Increased timeout thresholds to 300s for heavy synthesis payloads and implemented a 3-attempt retry loop. |
| **PDF Paywall Blocks (403)** | High | Medium | Engineered an automated fallback sequence that searches ArXiv for open-access preprints if the primary URL fails. |
| **LLM Hallucinations** | Low | Medium | Strict zero-shot prompt framing restricting the model to only use the provided text chunk as ground truth. |
| **Database Connection Loss** | Low | High | Utilized `asyncio.to_thread` for all `supabase-py` calls to prevent blocking the ASGI event loop during DB failures. |

## 2. Test Environment
- **Local Testing:** Uvicorn local server (`localhost:8000`) testing frontend/backend integration.
- **CI/CD Integration:** Ready for automated GitHub Actions workflows running `pytest` for unit testing the `PaperHandler` and `LLMManager` components.
- **Production Staging:** Hosted on Render/Railway for live SSE streaming validation over external networks.

## 3. Test Case Specifications

### A. Happy Case (The "Golden Path")
- **Action:** User searches "Machine Learning in Healthcare", selects 2 papers, and clicks Deep Analyze.
- **Expected Result:** Gallery populates in <15s. Analysis tray shows accurate chunk completion (e.g., 5/5 chunks). Final markdown report renders correctly. Supabase `papers` table reflects `analysis_status: 'completed'`.

### B. Negative Case (Handling Invalid Input/Paywalls)
- **Action:** System attempts to download an ACM Digital Library paper that strictly enforces a paywall (returns 403 Forbidden).
- **Expected Result:** System catches the 403, triggers the ArXiv fallback mechanism, successfully downloads the open-access preprint, and continues the SSE stream without crashing the FastAPI application.

### C. Non-Functional Tests
1. **API Response Times:** Validate that Phase 1 (Discovery) returns enriched insights for 10 papers in under 20 seconds.
2. **Load Handling:** Ensure that analyzing 3 papers simultaneously (approx. 25 chunks) does not trigger GLM rate limits, handled effectively by the `Semaphore` concurrency limit.

## 4. AI-Specific Testing
- **Prompt/Response Pairs:** Validated that prompts requesting "Return ONLY a numeric score" successfully output parseable integers without conversational filler.
- **Boundary Testing:** Sent large 30-page PDFs through the chunker to ensure `fitz` correctly splits tokens below the GLM context limit, preventing `Context Window Exceeded` errors.
- **State Isolation:** Transitioned from a shared `chat()` history to a stateless `ask()` method to ensure concurrent LLM queries do not pollute each other's context windows.
