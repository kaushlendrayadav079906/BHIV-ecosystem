// State management
let selectedFile = null;
let lastResult = null;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const fileName = document.getElementById('fileName');
const analyzeBtn = document.getElementById('analyzeBtn');
const identifyBtn = document.getElementById('identifyBtn');
const clearBtn = document.getElementById('clearBtn');
const copyBtn = document.getElementById('copyBtn');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const jsonOutput = document.getElementById('jsonOutput');
const quickInfo = document.getElementById('quickInfo');
const observationsSection = document.getElementById('observationsSection');
const observationsList = document.getElementById('observationsList');
const spinner = document.getElementById('spinner');
const errorMessage = document.getElementById('errorMessage');

// Event Listeners
uploadArea.addEventListener('click', () => imageInput.click());
uploadArea.addEventListener('dragover', handleDragOver);
uploadArea.addEventListener('dragleave', handleDragLeave);
uploadArea.addEventListener('drop', handleDrop);
imageInput.addEventListener('change', handleFileSelect);
analyzeBtn.addEventListener('click', () => analyzeImage('analyze'));
identifyBtn.addEventListener('click', () => analyzeImage('identify'));
clearBtn.addEventListener('click', clearUI);
copyBtn.addEventListener('click', copyJsonToClipboard);

// File Upload Handlers
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        selectedFile = files[0];
        showPreview();
        enableButtons();
    }
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        selectedFile = e.target.files[0];
        showPreview();
        enableButtons();
    }
}

function showPreview() {
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        fileName.textContent = `Selected: ${selectedFile.name}`;
        imagePreview.style.display = 'block';
    };
    reader.readAsDataURL(selectedFile);
}

function enableButtons() {
    analyzeBtn.disabled = false;
    identifyBtn.disabled = false;
}

function clearUI() {
    selectedFile = null;
    imageInput.value = '';
    imagePreview.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    analyzeBtn.disabled = true;
    identifyBtn.disabled = true;
    uploadArea.classList.remove('drag-over');
    lastResult = null;
}

// API Analysis
async function analyzeImage(mode) {
    if (!selectedFile) {
        showError('Please select an image first');
        return;
    }

    // Show loading state
    spinner.style.display = 'inline-block';
    const btnText = analyzeBtn.querySelector('.btn-text') || analyzeBtn;
    const originalText = btnText.textContent;
    btnText.textContent = mode === 'analyze' ? '🔍 Analyzing...' : '🔍 Identifying...';
    analyzeBtn.disabled = true;
    identifyBtn.disabled = true;

    // Log to terminal
    console.log(`\n${'='.repeat(80)}`);
    console.log(`[${new Date().toLocaleTimeString()}] Starting ${mode.toUpperCase()} analysis...`);
    console.log(`File: ${selectedFile.name}`);
    console.log(`Size: ${(selectedFile.size / 1024).toFixed(2)} KB`);
    console.log(`${'='.repeat(80)}\n`);

    try {
        const formData = new FormData();
        formData.append('image', selectedFile);

        const endpoint = mode === 'analyze' ? '/analyze' : '/identify';
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`HTTP ${response.status}: ${JSON.stringify(errorData)}`);
        }

        const result = await response.json();
        lastResult = result;

        // Log to terminal
        console.log(`✅ Analysis completed successfully!`);
        console.log(`Response Status: ${response.status} OK`);
        console.log(`\n${'='.repeat(80)}`);
        console.log('ANALYSIS RESULTS:');
        console.log(`${'='.repeat(80)}`);
        console.log(JSON.stringify(result, null, 2));
        console.log(`${'='.repeat(80)}\n`);

        // Display results
        displayResults(result, mode);
        resultsSection.style.display = 'block';
        errorSection.style.display = 'none';
    } catch (error) {
        console.error(`❌ Error during ${mode}:`, error);
        showError(`Error during ${mode}: ${error.message}`);
    } finally {
        spinner.style.display = 'none';
        btnText.textContent = originalText;
        analyzeBtn.disabled = false;
        identifyBtn.disabled = false;
    }
}

function displayResults(result, mode) {
    // Display JSON
    jsonOutput.textContent = JSON.stringify(result, null, 2);

    // Clear previous results
    quickInfo.innerHTML = '';
    observationsList.innerHTML = '';

    if (mode === 'identify') {
        // Quick Identify results
        displayQuickInfo(result);
    } else {
        // Full Analyze results
        displayQuickInfo(result);
        displayObservations(result);
    }
}

function displayQuickInfo(result) {
    const isUnknown = result.status === 'Unknown Plant';
    
    if (isUnknown) {
        quickInfo.innerHTML = `
            <div class="info-item unknown">
                <div class="info-label">Status</div>
                <div class="info-value unknown">${result.status}</div>
            </div>
            <div class="info-item unknown">
                <div class="info-label">Confidence</div>
                <div class="info-value unknown">${(result.confidence * 100).toFixed(1)}%</div>
            </div>
            ${result.reason ? `<div class="info-item unknown">
                <div class="info-label">Reason</div>
                <div class="info-value unknown">${result.reason}</div>
            </div>` : ''}
        `;
    } else {
        quickInfo.innerHTML = `
            ${result.plant_species ? `<div class="info-item">
                <div class="info-label">🌿 Plant Species</div>
                <div class="info-value">${result.plant_species}</div>
            </div>` : ''}
            ${result.confidence !== undefined ? `<div class="info-item">
                <div class="info-label">Species Confidence</div>
                <div class="info-value">${(result.confidence * 100).toFixed(1)}%</div>
            </div>` : ''}
            ${result.plant_part ? `<div class="info-item">
                <div class="info-label">🍃 Plant Part</div>
                <div class="info-value">${result.plant_part}</div>
            </div>` : ''}
            ${result.plant_part_confidence !== undefined ? `<div class="info-item">
                <div class="info-label">Part Confidence</div>
                <div class="info-value">${(result.plant_part_confidence * 100).toFixed(1)}%</div>
            </div>` : ''}
            ${result.growth_stage ? `<div class="info-item">
                <div class="info-label">🌱 Growth Stage</div>
                <div class="info-value">${result.growth_stage}</div>
            </div>` : ''}
            ${result.growth_confidence !== undefined ? `<div class="info-item">
                <div class="info-label">Growth Confidence</div>
                <div class="info-value">${(result.growth_confidence * 100).toFixed(1)}%</div>
            </div>` : ''}
            ${result.inference_time ? `<div class="info-item">
                <div class="info-label">⏱ Processing Time</div>
                <div class="info-value">${result.inference_time}</div>
            </div>` : ''}
            ${result.model_version ? `<div class="info-item">
                <div class="info-label">Model Version</div>
                <div class="info-value">${result.model_version}</div>
            </div>` : ''}
        `;

        // Show alternatives if present
        const alts = result.alternatives || [];
        if (alts.length > 0) {
            const altHTML = alts.map(a =>
                `<span style="margin-right:12px">🔸 ${a.species} (${(a.confidence*100).toFixed(1)}%)</span>`
            ).join('');
            quickInfo.innerHTML += `
                <div class="info-item" style="grid-column: 1 / -1">
                    <div class="info-label">Alternatives</div>
                    <div class="detail-value" style="font-size:0.9rem">${altHTML}</div>
                </div>`;
        }

        // Show explanation if present
        const exp = result.explanation;
        if (exp) {
            quickInfo.innerHTML += `
                <div class="info-item" style="grid-column: 1 / -1; border-left: 4px solid #ff9800">
                    <div class="info-label">💡 Explanation</div>
                    <div class="detail-value">${exp.summary}</div>
                </div>`;
        }
    }
}

function displayObservations(result) {
    const observations = result.observations || [];
    
    if (observations.length === 0) {
        observationsSection.style.display = 'none';
        return;
    }

    observationsSection.style.display = 'block';
    
    observations.forEach((obs, index) => {
        const confidencePercent = (obs.confidence * 100).toFixed(1);
        const features = Array.isArray(obs.supporting_features) 
            ? obs.supporting_features.join(', ')
            : obs.supporting_features || 'N/A';

        const obsItem = document.createElement('div');
        obsItem.className = 'observation-item';
        obsItem.innerHTML = `
            <div class="observation-type">${index + 1}. ${obs.type}</div>
            <div class="observation-details">
                <div class="detail">
                    <div class="detail-label">Observation ID</div>
                    <div class="detail-value">${obs.observation_id}</div>
                </div>
                <div class="detail">
                    <div class="detail-label">Value</div>
                    <div class="detail-value">${obs.value}</div>
                </div>
                <div class="detail">
                    <div class="detail-label">Confidence</div>
                    <div class="detail-value">${confidencePercent}%</div>
                </div>
                <div class="detail">
                    <div class="detail-label">Evidence Source</div>
                    <div class="detail-value">${obs.evidence_source}</div>
                </div>
                <div class="detail" style="grid-column: 1 / -1;">
                    <div class="detail-label">Supporting Features</div>
                    <div class="detail-value">${features}</div>
                </div>
            </div>
        `;
        observationsList.appendChild(obsItem);
    });
}

function showError(message) {
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    resultsSection.style.display = 'none';
    
    console.error(`❌ ERROR: ${message}`);
    console.log(`Timestamp: ${new Date().toLocaleString()}\n`);
}

function copyJsonToClipboard() {
    if (!lastResult) return;

    const jsonStr = JSON.stringify(lastResult, null, 2);
    navigator.clipboard.writeText(jsonStr).then(() => {
        const originalText = copyBtn.textContent;
        copyBtn.textContent = '✅ Copied!';
        
        console.log('📋 JSON copied to clipboard');
        
        setTimeout(() => {
            copyBtn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        showError('Failed to copy JSON to clipboard');
    });
}

// Log initial state
console.log(`
╔═══════════════════════════════════════════════════════════════╗
║          🌿 Plant Intelligence Capability v1.0.0            ║
║                  Terminal Output Monitor                      ║
╚═══════════════════════════════════════════════════════════════╝

[${new Date().toLocaleTimeString()}] UI Ready - Waiting for image upload...
API Endpoints:
  - POST /identify - Quick species identification
  - POST /analyze  - Full analysis with evidence generation
`);
