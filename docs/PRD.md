# Product Requirement Document (PRD) - ScholarFlow AI

## 1. Project Overview
**Problem Statement:** 
Academic and R&D researchers face a highly fragmented and manual workflow when conducting literature reviews. Currently, researchers must manually search multiple databases, download PDFs (often hitting paywalls), read full abstracts to determine relevance, and manually synthesize findings. This process is incredibly time-consuming and prone to information overload.

**Solution:** 
ScholarFlow AI is a production-ready, cloud-based research engine that automates the literature review process via a "Two-Step Approval" workflow. It autonomously queries major databases (OpenAlex, ArXiv), uses AI to generate instant 3-sentence insights and relevance scores (Phase 1), and upon user approval, bypasses paywalls to download, chunk, and deeply analyze the PDFs to generate a comprehensive Markdown synthesis report (Phase 2).

## 2. Target Audience
- **Academic Researchers & University Students:** Needing to rapidly write literature reviews.
- **R&D Engineers & Data Scientists:** Looking to quickly discover state-of-the-art methodologies.
- **Corporate Analysts:** Requiring summarized insights from complex whitepapers without reading hundreds of pages.

## 3. AI Model & Prompt Design
- **Model Selection:** The core reasoning engine is powered by **Z AI GLM** (`ilmu-glm-5.1` via the ILMU API). It is utilized for both rapid insight generation and heavy text synthesis.
- **Prompting Strategy:** 
  - *Zero-Shot Prompting:* Used during the Discovery Phase to instantly score objective alignment (0-100) and generate a 3-sentence insight from abstracts.
  - *Multi-Step Agentic Chunking:* Used during Deep Analysis. Because full PDFs exceed standard context windows, the system autonomously chunks the PDF, prompts the GLM model sequentially to extract key findings from each chunk, and finally uses a distinct synthesis prompt to merge all chunk summaries into a final cohesive report.

## 4. System Functionalities
- **Automated Discovery:** Translates user queries into Boolean logic to query OpenAlex and ArXiv.
- **Manual AI Gatekeeper (Phase 1):** Presents an interactive gallery where users review AI-generated relevance scores before committing to deep analysis.
- **Context-Aware PDF Chunking (Phase 2):** Downloads open-access PDFs (with automatic ArXiv fallback for paywalls) and splits them into token-safe chunks.
- **Real-Time Streaming Interface:** Uses Server-Sent Events (SSE) to push live progress bars to the frontend without page reloads.
- **Dynamic Caching:** Implements a `chunk_cache` in PostgreSQL to avoid redundant API calls for previously analyzed text chunks.

## 5. Scope Control
- **In-Scope for MVP (Hackathon):** OpenAlex/ArXiv integrations, Two-Step AI workflow, SSE streaming UI, Supabase integration, automated paywall fallback, Markdown report generation.
- **Out of Scope:** User authentication/login systems, exporting reports to DOCX/PDF, integrating with paid proprietary databases (e.g., IEEE Xplore, Elsevier).
