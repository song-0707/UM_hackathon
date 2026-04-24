let discoveredPapers = [];
let selectedPapers = [];

document.addEventListener('DOMContentLoaded', () => {
    const btnDiscover = document.getElementById('btn-discover');
    const btnAnalyze = document.getElementById('btn-analyze');
    
    btnDiscover.addEventListener('click', handleDiscover);
    btnAnalyze.addEventListener('click', handleDeepAnalyze);
});

async function handleDiscover() {
    const mode = document.getElementById('search-mode').value;
    const inputData = document.getElementById('search-input').value.trim();
    
    if (!inputData) {
        alert("Please enter a search query.");
        return;
    }

    const btn = document.getElementById('btn-discover');
    const spinner = btn.querySelector('.spinner');
    
    btn.disabled = true;
    spinner.classList.remove('hidden');

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: parseInt(mode), input_data: inputData })
        });

        const data = await response.json();
        
        if (!response.ok || data.error) {
            throw new Error(data.error || "Failed to discover papers.");
        }

        discoveredPapers = data.papers;
        document.getElementById('profile-display').textContent = data.profile;
        renderDiscoveryGallery(discoveredPapers);

        // Transition to Stage 2
        document.getElementById('input-section').classList.replace('section-active', 'section-hidden');
        document.getElementById('gallery-section').classList.replace('section-hidden', 'section-active');

    } catch (error) {
        alert("Error: " + error.message);
    } finally {
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

    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);

        if (data.type === "progress") {
            updateProgressUI(data.message);
        } else if (data.type === "complete") {
            renderFinalReport(data.report);
            eventSource.close();
        } else if (data.type === "error") {
            alert("Analysis Error: " + data.message);
            eventSource.close();
        }
    };

    eventSource.onerror = function() {
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

function renderFinalReport(markdownText) {
    // Stage 4 transition
    document.getElementById('analysis-section').classList.replace('section-active', 'section-hidden');
    document.getElementById('report-section').classList.replace('section-hidden', 'section-active');

    // Make all progress bars 100%
    selectedPapers.forEach(p => {
        const pb = document.getElementById(`prog-${p.external_id}`);
        if(pb) pb.style.width = '100%';
    });

    const reportContent = document.getElementById('report-content');
    reportContent.innerHTML = marked.parse(markdownText);
}
