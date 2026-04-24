let discoveredPapers = [];
let selectedPapers = [];

let currentPage = 1;
let currentQuery = "";
let currentProfile = "";
let currentMode = 1;
let currentInputData = "";

document.addEventListener('DOMContentLoaded', () => {
    const btnDiscover = document.getElementById('btn-discover');
    const btnAnalyze = document.getElementById('btn-analyze');
    const btnSearchMore = document.getElementById('btn-search-more');

    btnDiscover.addEventListener('click', handleDiscover);
    btnAnalyze.addEventListener('click', handleDeepAnalyze);
    if (btnSearchMore) btnSearchMore.addEventListener('click', handleSearchMore);
});

async function handleDiscover() {
    const mode = document.getElementById('search-mode').value;
    const inputData = document.getElementById('search-input').value.trim();

    if (!inputData) {
        alert("Please enter a search query.");
        return;
    }

    currentPage = 1;
    currentMode = parseInt(mode);
    currentInputData = inputData;

    const btn = document.getElementById('btn-discover');
    const spinner = btn.querySelector('.spinner');
    const progressContainer = document.getElementById('search-progress-container');
    const progressBar = document.getElementById('search-progress-bar');
    const progressText = document.getElementById('search-progress-text');
    const progressPercent = document.getElementById('search-progress-percent');

    btn.disabled = true;
    spinner.classList.remove('hidden');
    progressContainer.classList.remove('hidden');

    // Simulate Progress
    let progress = 0;
    progressBar.style.width = '0%';
    progressPercent.textContent = '0%';

    const statusMessages = [
        "Connecting to Academic Databases...",
        "Fetching papers from OpenAlex & ArXiv...",
        "Running AI Relevance Profiling...",
        "Generating 3-Sentence Insights...",
        "Finalizing Discovery Gallery..."
    ];
    let messageIndex = 0;
    progressText.textContent = statusMessages[0];

    const progressInterval = setInterval(() => {
        // Slow down as it gets closer to 95% to simulate waiting
        if (progress < 40) progress += 2;
        else if (progress < 70) progress += 1;
        else if (progress < 95) progress += 0.5;

        progressBar.style.width = progress + '%';
        progressPercent.textContent = Math.floor(progress) + '%';

        // Update text based on progress
        if (progress > 20 && messageIndex < 1) { messageIndex = 1; progressText.textContent = statusMessages[1]; }
        if (progress > 45 && messageIndex < 2) { messageIndex = 2; progressText.textContent = statusMessages[2]; }
        if (progress > 70 && messageIndex < 3) { messageIndex = 3; progressText.textContent = statusMessages[3]; }
        if (progress > 85 && messageIndex < 4) { messageIndex = 4; progressText.textContent = statusMessages[4]; }
    }, 200);

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: parseInt(mode), input_data: inputData })
        });

        clearInterval(progressInterval);
        progressBar.style.width = '100%';
        progressPercent.textContent = '100%';
        progressText.textContent = "Complete!";

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "Failed to discover papers.");
        }

        currentQuery = data.query;
        currentProfile = data.profile;

        discoveredPapers = data.papers;
        document.getElementById('profile-display').textContent = data.profile;
        renderDiscoveryGallery(discoveredPapers);

        // Slight delay to show 100% before transitioning
        setTimeout(() => {
            document.getElementById('input-section').classList.replace('section-active', 'section-hidden');
            document.getElementById('gallery-section').classList.replace('section-hidden', 'section-active');

            // Reset for future uses
            btn.disabled = false;
            spinner.classList.add('hidden');
            progressContainer.classList.add('hidden');
        }, 800);

    } catch (error) {
        clearInterval(progressInterval);
        progressText.textContent = "Error Occurred!";
        progressText.style.color = "#ef4444";
        progressBar.style.background = "#ef4444";
        alert("Error: " + error.message);

        btn.disabled = false;
        spinner.classList.add('hidden');
    }
}

function renderDiscoveryGallery(papers) {
    const grid = document.getElementById('gallery-grid');
    grid.innerHTML = '';

    papers.forEach(paper => {
        const card = document.createElement('div');
        card.className = 'glass-card paper-card';
        card.id = `card-${paper.external_id}`;

        card.innerHTML = `
            <div class="card-header">
                <h3 class="paper-title">${paper.title}</h3>
                <span class="relevance-badge">${paper.relevance_score}%</span>
            </div>
            <div class="paper-meta">${paper.authors} • ${paper.publication_year}</div>
            <div class="paper-insight">${paper.insight}</div>
            <div class="card-footer">
                <a href="${paper.url}" target="_blank" style="color: var(--primary);">View Source</a>
                <label class="checkbox-container">
                    <input type="checkbox" value="${paper.external_id}" onchange="handleSelectionChange()">
                    <span>Select for Analysis</span>
                </label>
            </div>
        `;
        grid.appendChild(card);
    });
}

function handleSelectionChange() {
    const checkboxes = document.querySelectorAll('#gallery-grid input[type="checkbox"]:checked');
    selectedPapers = Array.from(checkboxes).map(cb => {
        return discoveredPapers.find(p => p.external_id === cb.value);
    });

    const btnAnalyze = document.getElementById('btn-analyze');
    btnAnalyze.disabled = selectedPapers.length === 0;
}

async function handleSearchMore() {
    const btn = document.getElementById('btn-search-more');
    const spinner = btn.querySelector('.spinner');

    btn.disabled = true;
    spinner.classList.remove('hidden');

    currentPage++;

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mode: currentMode,
                input_data: currentInputData,
                page: currentPage,
                existing_query: currentQuery,
                existing_profile: currentProfile
            })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "Failed to fetch more papers.");
        }

        // Append to existing array
        discoveredPapers = discoveredPapers.concat(data.papers);

        // Append to UI without clearing
        appendDiscoveryGallery(data.papers);

    } catch (error) {
        alert("Error: " + error.message);
        currentPage--; // Revert page count on error
    } finally {
        btn.disabled = false;
        spinner.classList.add('hidden');
    }
}

function appendDiscoveryGallery(papers) {
    const grid = document.getElementById('gallery-grid');

    papers.forEach(paper => {
        const card = document.createElement('div');
        card.className = 'glass-card paper-card';
        card.id = `card-${paper.external_id}`;

        card.innerHTML = `
            <div class="card-header">
                <h3 class="paper-title">${paper.title}</h3>
                <span class="relevance-badge">${paper.relevance_score}%</span>
            </div>
            <div class="paper-meta">${paper.authors} • ${paper.publication_year}</div>
            <div class="paper-insight">${paper.insight}</div>
            <div class="card-footer">
                <a href="${paper.url}" target="_blank" style="color: var(--primary);">View Source</a>
                <label class="checkbox-container">
                    <input type="checkbox" value="${paper.external_id}" onchange="handleSelectionChange()">
                    <span>Select for Analysis</span>
                </label>
            </div>
        `;
        grid.appendChild(card);
    });
}

async function handleDeepAnalyze() {
    if (selectedPapers.length === 0) return;

    const btn = document.getElementById('btn-analyze');
    const spinner = btn.querySelector('.spinner');

    btn.disabled = true;
    spinner.classList.remove('hidden');

    // Move selected cards to Analysis Tray
    setupAnalysisTray();

    // Transition to Stage 3
    document.getElementById('gallery-section').classList.replace('section-active', 'section-hidden');
    document.getElementById('analysis-section').classList.replace('section-hidden', 'section-active');

    try {
        const profile = document.getElementById('profile-display').textContent;

        // Step 1: POST to start analysis and get task_id
        const response = await fetch('/api/start_analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ selected_papers: selectedPapers, profile: profile })
        });

        const data = await response.json();
        if (!response.ok || data.error) throw new Error(data.error);

        const taskId = data.task_id;

        // Step 2: GET SSE using task_id
        startSSEStream(taskId);

    } catch (error) {
        alert("Error starting analysis: " + error.message);
        btn.disabled = false;
        spinner.classList.add('hidden');
    }
}

function setupAnalysisTray() {
    const tray = document.getElementById('analysis-tray');
    tray.innerHTML = '';

    selectedPapers.forEach(paper => {
        const card = document.createElement('div');
        card.className = 'glass-card paper-card';
        card.id = `tray-${paper.external_id}`;

        card.innerHTML = `
            <div class="card-header">
                <h3 class="paper-title">${paper.title}</h3>
            </div>
            <div class="progress-container">
                <div class="progress-bar" id="prog-${paper.external_id}" style="width: 5%"></div>
            </div>
            <span class="status-label" id="status-${paper.external_id}">Waiting to start...</span>
        `;
        tray.appendChild(card);
    });
}

function startSSEStream(taskId) {
    const eventSource = new EventSource(`/api/analyze/${taskId}`);

    eventSource.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.type === "progress") {
            updateProgressUI(data.message);
        } else if (data.type === "paper_complete") {
            renderPaperReport(data.external_id, data.report);
        } else if (data.type === "all_complete") {
            eventSource.close();
            selectedPapers.forEach(p => {
                const pb = document.getElementById(`prog-${p.external_id}`);
                if (pb) pb.style.width = '100%';
            });

            // Hide the analysis section so we ONLY show the reports
            document.getElementById('analysis-section').classList.replace('section-active', 'section-hidden');

            // Add a UI indicator that the program is completely finished
            const reportH2 = document.querySelector('#report-section h2');
            if (reportH2 && !reportH2.innerHTML.includes('Analysis Complete')) {
                reportH2.innerHTML = `4. Final Synthesis Reports <span class="relevance-badge" style="background: var(--success, #10b981); color: white; margin-left: 1rem; border: none; padding: 0.3rem 0.8rem;">✓ Analysis Complete</span>`;
            }
        } else if (data.type === "error") {
            alert("Analysis Error: " + data.message);
            eventSource.close();
        }
    };

    eventSource.onerror = function () {
        // SSE sometimes closes naturally, but if error we can close
        eventSource.close();
    };
}

function updateProgressUI(message) {
    // For simplicity, we broadcast the message to the first processing card, 
    // or all of them depending on how the backend formats messages.
    // The backend sends f"[CHUNKING] Extracting text from {title}"
    // We can parse the tag to style it.

    let tag = "info";
    let text = message;

    const match = message.match(/^\[(.*?)\] (.*)/);
    if (match) {
        tag = match[1].toLowerCase();
        text = match[2];
    }

    let tagHtml = `<span class="status-tag ${tag}">[${tag.toUpperCase()}]</span>`;

    selectedPapers.forEach(p => {
        if (text.includes(p.title) || text.includes(p.title.substring(0, 20))) {
            const statusLabel = document.getElementById(`status-${p.external_id}`);
            const progressBar = document.getElementById(`prog-${p.external_id}`);

            if (statusLabel) {
                // Remove the paper title and trailing " of " from the label for cleaner UI
                let cleanText = text.replace(p.title, '').replace(/ of\s*$/, '').trim();
                statusLabel.innerHTML = `${tagHtml} ${cleanText}`;
            }
            if (progressBar) {
                if (text.includes("Finished chunk")) {
                    if (!p.chunksFinished) p.chunksFinished = 0;
                    p.chunksFinished += 1;

                    const progressMatch = text.match(/(\d+)\/(\d+)/);
                    if (progressMatch) {
                        const total = parseInt(progressMatch[2]);
                        const percent = Math.min(95, Math.max(5, (p.chunksFinished / total) * 100));
                        progressBar.style.width = percent + '%';
                    }
                } else if (text.includes("Analyzing chunk")) {
                    // Just slightly bump progress to show activity if it's stuck waiting
                    let currentW = parseInt(progressBar.style.width) || 5;
                    if (currentW < 15) progressBar.style.width = '15%';
                }
            }
        }
    });
}

function renderPaperReport(external_id, markdownText) {
    // Stage 4 transition if not already transitioned
    const reportSection = document.getElementById('report-section');
    if (reportSection.classList.contains('section-hidden')) {
        // DO NOT hide the analysis section! Keep it visible so users see parallel progress.
        reportSection.classList.replace('section-hidden', 'section-active');
    }

    // Make this specific paper's progress bar 100%
    const pb = document.getElementById(`prog-${external_id}`);
    if (pb) pb.style.width = '100%';

    const reportList = document.getElementById('report-list');

    const reportCard = document.createElement('div');
    reportCard.className = 'glass-card markdown-body';
    // Append the Markdown parsed HTML
    reportCard.innerHTML = marked.parse(markdownText);

    reportList.appendChild(reportCard);
}
