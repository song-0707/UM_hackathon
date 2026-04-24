# 🎓 ScholarFlow AI

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
![Render](https://img.shields.io/badge/Render-Deployed-46E3B7?logo=render&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?logo=supabase&logoColor=white)
![GLM-5.1](https://img.shields.io/badge/Z_AI-GLM--5.1-blueviolet)

> **Live Demo:** [https://scholarflow-gpzh.onrender.com/](https://scholarflow-gpzh.onrender.com/)  
> **Project Board:** [View our Agile Roadmap & Issues](https://github.com/users/song-0707/projects/2/views/1)

## 📖 Introduction
**ScholarFlow AI** is a high-performance, cloud-ready research engine designed to automate the academic literature review process. Powered by the cutting-edge **Z AI GLM** model, it seamlessly integrates with major academic databases like OpenAlex and ArXiv to find relevant papers, generate instant insights, bypass paywalls, and deeply analyze entire research papers using a multi-step agentic chunking process.

## 🎯 The Objective
The primary objective of ScholarFlow is to eliminate the fragmented, manual workflow researchers face when sifting through academic literature. By introducing a **"Two-Step AI Workflow"**, researchers can:
1. Rapidly discover and filter high-relevance papers in seconds.
2. Offload the heavy lifting of reading and synthesizing 30+ page PDFs to the AI, receiving a fully formatted Markdown synthesis report.

## ✨ Core Features
- **🔍 Intelligent Discovery:** Translates complex problem statements into optimized Boolean search strings.
- **⚡ Instant Insights:** Generates 3-sentence summaries and predictive relevance scores (0-100) instantly to act as a "Gatekeeper".
- **🔓 Automated Paywall Evasion:** Attempts to download PDFs natively, automatically falling back to ArXiv open-access preprints if a paper returns a `403 Forbidden`.
- **🧠 Deep Analysis Pipeline:** Downloads and chunks large PDFs to safely bypass LLM context window limits, processing text chunks concurrently.
- **🌊 Real-Time UI:** Modern glassmorphism frontend using Server-Sent Events (SSE) to stream progress dynamically without page reloads.

---

## 🚀 Getting Started (Local Setup)

### Prerequisites
- Python 3.10+
- A [Supabase](https://supabase.com/) account and project
- An ILMU API Key (Z AI GLM)

### Installation Steps
1. **Clone & Navigate to the project directory:**
   ```bash
   git clone [https://github.com/song-0707/UM_hackathon.git](https://github.com/song-0707/UM_hackathon.git)
   cd UM_hackathon
   ```
2. **Install Python Dependencies:**
   Install all required backend modules via pip:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables:**
   Create a `.env` file in the root directory (if not already present) and populate it with your specific API keys:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   LLM_API_KEY=your_ilmu_api_key
   ```
4. **Database Setup:**
   Copy the SQL commands found in the `schema.sql` file and execute them inside your Supabase SQL Editor. This will generate the necessary `papers` and `chunk_cache` tables for the application to function.

## How to Use Locally
1. **Start the FastAPI Server:**
   Run the following command in your terminal to boot up the application:
   ```bash
   uvicorn app:app --host 127.0.0.1 --port 8000 --reload
   ```
2. **Access the Web Interface:**
   Open your preferred web browser and navigate to:
   ```text
   http://127.0.0.1:8000/
   ```
3. **Conduct Research:**
   - **Step 1:** Type your research topic or problem statement in the search field.
   - **Step 2:** Click "Discover Papers" and wait for the AI to fetch, score, and summarize the papers.
   - **Step 3:** Review the interactive gallery and select the specific papers you want to investigate further.
   - **Step 4:** Click "Deep Analyze" and monitor the real-time progress bars as the AI downloads, reads, and synthesizes your final Markdown report!
