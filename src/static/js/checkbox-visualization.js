/**
 * Checkbox Visualization JavaScript
 * Handles UI interactions and visualization of checkbox detection results
 */

// Configuration
const CONFIG = {
    highConfidenceThreshold: 0.9,
    mediumConfidenceThreshold: 0.7,
    colorMap: {
        highConfidence: '#198754',
        mediumConfidence: '#fd7e14',
        lowConfidence: '#dc3545',
        manuallyCorrection: '#0d6efd'
    }
};

// Global state
let state = {
    documentId: null,
    documentName: '',
    processingDate: '',
    currentPage: 1,
    totalPages: 1,
    pageData: [],
    allCheckboxes: [],
    currentPageCheckboxes: [],
    manualCorrections: [],
    highConfidenceThreshold: CONFIG.highConfidenceThreshold,
    mediumConfidenceThreshold: CONFIG.mediumConfidenceThreshold
};

// DOM Elements
const elements = {
    documentName: document.getElementById('documentName'),
    documentDate: document.getElementById('documentDate'),
    totalCheckboxes: document.getElementById('totalCheckboxes'),
    highConfidence: document.getElementById('highConfidence'),
    mediumConfidence: document.getElementById('mediumConfidence'),
    lowConfidence: document.getElementById('lowConfidence'),
    manualCorrections: document.getElementById('manualCorrections'),
    highConfidenceThreshold: document.getElementById('highConfidenceThreshold'),
    highThresholdValue: document.getElementById('highThresholdValue'),
    mediumConfidenceThreshold: document.getElementById('mediumConfidenceThreshold'),
    mediumThresholdValue: document.getElementById('mediumThresholdValue'),
    prevPage: document.getElementById('prevPage'),
    nextPage: document.getElementById('nextPage'),
    pageInfo: document.getElementById('pageInfo'),
    documentImage: document.getElementById('documentImage'),
    checkboxOverlay: document.getElementById('checkboxOverlay'),
    checkboxTableBody: document.getElementById('checkboxTableBody'),
    exportJsonBtn: document.getElementById('exportJsonBtn'),
    saveCorrectionsBtn: document.getElementById('saveCorrectionsBtn'),
    editCheckboxModal: new bootstrap.Modal(document.getElementById('editCheckboxModal')),
    editCheckboxId: document.getElementById('editCheckboxId'),
    editCheckboxLabel: document.getElementById('editCheckboxLabel'),
    editCheckboxState: document.getElementById('editCheckboxState'),
    editCheckboxConfidence: document.getElementById('editCheckboxConfidence'),
    markAsManualCorrection: document.getElementById('markAsManualCorrection'),
    saveCheckboxEdit: document.getElementById('saveCheckboxEdit')
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    // Extract document ID from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    state.documentId = urlParams.get('id');
    
    if (!state.documentId) {
        showError('No document ID provided');
        return;
    }
    
    // Set up event listeners
    setupEventListeners();
    
    // Load document data
    loadDocumentData(state.documentId);
});

// Setup event listeners
function setupEventListeners() {
    // Threshold sliders
    elements.highConfidenceThreshold.addEventListener('input', (e) => {
        state.highConfidenceThreshold = parseFloat(e.target.value);
        elements.highThresholdValue.textContent = state.highConfidenceThreshold.toFixed(2);
        updateConfidenceCategories();
        renderCheckboxOverlay();
        updateMetrics();
    });
    
    elements.mediumConfidenceThreshold.addEventListener('input', (e) => {
        state.mediumConfidenceThreshold = parseFloat(e.target.value);
        elements.mediumThresholdValue.textContent = state.mediumConfidenceThreshold.toFixed(2);
        updateConfidenceCategories();
        renderCheckboxOverlay();
        updateMetrics();
    });
    
    // Page navigation
    elements.prevPage.addEventListener('click', () => {
        if (state.currentPage > 1) {
            navigateToPage(state.currentPage - 1);
        }
    });
    
    elements.nextPage.addEventListener('click', () => {
        if (state.currentPage < state.totalPages) {
            navigateToPage(state.currentPage + 1);
        }
    });
    
    // Export and save buttons
    elements.exportJsonBtn.addEventListener('click', exportJsonData);
    elements.saveCorrectionsBtn.addEventListener('click', saveCorrections);
    
    // Edit modal save button
    elements.saveCheckboxEdit.addEventListener('click', saveCheckboxEdits);
}

// Load document data
async function loadDocumentData(documentId) {
    try {
        const response = await fetch(`/api/visualization/${documentId}`);
        if (!response.ok) throw new Error(`Failed to load document data: ${response.statusText}`);
        
        const data = await response.json();
        
        // Update state with document data
        state.documentName = data.document_name;
        state.processingDate = new Date(data.processing_date).toLocaleString();
        state.totalPages = data.total_pages;
        state.pageData = data.pages;
        state.allCheckboxes = data.checkboxes;
        
        // Update UI elements
        elements.documentName.textContent = `Document: ${state.documentName}`;
        elements.documentDate.textContent = `Processed: ${state.processingDate}`;
        
        // Update confidence categories
        updateConfidenceCategories();
        
        // Navigate to first page
        navigateToPage(1);
        
        // Update metrics
        updateMetrics();
    } catch (error) {
        showError(`Error loading document: ${error.message}`);
    }
}

// Navigate to a specific page
function navigateToPage(pageNumber) {
    state.currentPage = pageNumber;
    
    // Update page navigation controls
    elements.prevPage.disabled = state.currentPage <= 1;
    elements.nextPage.disabled = state.currentPage >= state.totalPages;
    elements.pageInfo.textContent = `Page ${state.currentPage} of ${state.totalPages}`;
    
    // Get page data
    const page = state.pageData.find(p => p.page_number === state.currentPage);
    if (!page) {
        showError(`Page ${state.currentPage} not found`);
        return;
    }
    
    // Load page image
    elements.documentImage.src = page.image_url;
    
    // Get checkboxes for this page
    state.currentPageCheckboxes = state.allCheckboxes.filter(cb => cb.page === state.currentPage);
    
    // Render checkbox overlay
    renderCheckboxOverlay();
    
    // Populate checkbox table
    renderCheckboxTable();
}

// Update confidence categories based on thresholds
function updateConfidenceCategories() {
    state.allCheckboxes.forEach(checkbox => {
        if (checkbox.confidence >= state.highConfidenceThreshold) {
            checkbox.confidenceCategory = 'high';
        } else if (checkbox.confidence >= state.mediumConfidenceThreshold) {
            checkbox.confidenceCategory = 'medium';
        } else {
            checkbox.confidenceCategory = 'low';
        }
    });
}

// Render checkbox overlay on the document
function renderCheckboxOverlay() {
    // Clear existing overlay
    elements.checkboxOverlay.innerHTML = '';
    
    // Get image dimensions
    const imageWidth = elements.documentImage.offsetWidth;
    const imageHeight = elements.documentImage.offsetHeight;
    
    // Create checkbox markers
    state.currentPageCheckboxes.forEach(checkbox => {
        const marker = document.createElement('div');
        marker.classList.add('checkbox-marker');
        
        // Set position and size
        const left = checkbox.bbox.left * imageWidth;
        const top = checkbox.bbox.top * imageHeight;
        const width = (checkbox.bbox.right - checkbox.bbox.left) * imageWidth;
        const height = (checkbox.bbox.bottom - checkbox.bbox.top) * imageHeight;
        
        marker.style.left = `${left}px`;
        marker.style.top = `${top}px`;
        marker.style.width = `${width}px`;
        marker.style.height = `${height}px`;
        
        // Set color based on confidence category or manual correction
        if (checkbox.manuallyCorrect) {
            marker.classList.add('manually-corrected');
        } else {
            marker.classList.add(`${checkbox.confidenceCategory}-confidence`);
        }
        
        // Add tooltip
        marker.title = `${checkbox.label} (${(checkbox.confidence * 100).toFixed(1)}%)`;
        
        // Add click event to open edit modal
        marker.addEventListener('click', () => openEditModal(checkbox.id));
        
        // Add to overlay
        elements.checkboxOverlay.appendChild(marker);
    });
}

// Render checkbox table for current page
function renderCheckboxTable() {
    // Clear existing table
    elements.checkboxTableBody.innerHTML = '';
    
    // Add rows for each checkbox
    state.currentPageCheckboxes.forEach(checkbox => {
        const row = document.createElement('tr');
        row.classList.add('checkbox-row');
        row.dataset.checkboxId = checkbox.id;
        
        // Set row color based on confidence or manual correction
        if (checkbox.manuallyCorrect) {
            row.classList.add('table-primary');
        } else if (checkbox.confidenceCategory === 'low') {
            row.classList.add('table-danger');
        } else if (checkbox.confidenceCategory === 'medium') {
            row.classList.add('table-warning');
        }
        
        // Create row cells
        row.innerHTML = `
            <td>${checkbox.id}</td>
            <td>${checkbox.label}</td>
            <td>
                <div class="state-indicator ${checkbox.value ? 'checked' : ''}"></div>
            </td>
            <td class="confidence-cell ${checkbox.confidenceCategory}-confidence">
                ${(checkbox.confidence * 100).toFixed(1)}%
                ${checkbox.manuallyCorrect ? ' <span class="badge bg-primary">Manual</span>' : ''}
            </td>
            <td class="actions-cell">
                <button class="btn btn-sm btn-outline-primary edit-btn">Edit</button>
            </td>
        `;
        
        // Add to table
        elements.checkboxTableBody.appendChild(row);
    });
    
    // Add click handlers to edit buttons
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const row = e.target.closest('tr');
            openEditModal(row.dataset.checkboxId);
        });
    });
}

// Open edit modal for a checkbox
function openEditModal(checkboxId) {
    const checkbox = state.allCheckboxes.find(cb => cb.id === checkboxId);
    if (!checkbox) return;
    
    // Populate modal fields
    elements.editCheckboxId.value = checkbox.id;
    elements.editCheckboxLabel.value = checkbox.label;
    elements.editCheckboxState.value = checkbox.value.toString();
    elements.editCheckboxConfidence.value = `${(checkbox.confidence * 100).toFixed(1)}%`;
    elements.markAsManualCorrection.checked = checkbox.manuallyCorrect || false;
    
    // Show modal
    elements.editCheckboxModal.show();
}

// Save checkbox edits
function saveCheckboxEdits() {
    const checkboxId = elements.editCheckboxId.value;
    const checkbox = state.allCheckboxes.find(cb => cb.id === checkboxId);
    if (!checkbox) return;
    
    // Update checkbox data
    checkbox.label = elements.editCheckboxLabel.value;
    checkbox.value = elements.editCheckboxState.value === 'true';
    checkbox.manuallyCorrect = elements.markAsManualCorrection.checked;
    
    // Add to manual corrections if not already there
    if (checkbox.manuallyCorrect && !state.manualCorrections.includes(checkboxId)) {
        state.manualCorrections.push(checkboxId);
    } else if (!checkbox.manuallyCorrect) {
        // Remove from manual corrections if unchecked
        const index = state.manualCorrections.indexOf(checkboxId);
        if (index !== -1) state.manualCorrections.splice(index, 1);
    }
    
    // Close modal
    elements.editCheckboxModal.hide();
    
    // Update UI
    renderCheckboxOverlay();
    renderCheckboxTable();
    updateMetrics();
}

// Update metrics display
function updateMetrics() {
    const highConfidence = state.allCheckboxes.filter(cb => 
        cb.confidenceCategory === 'high' && !cb.manuallyCorrect).length;
    const mediumConfidence = state.allCheckboxes.filter(cb => 
        cb.confidenceCategory === 'medium' && !cb.manuallyCorrect).length;
    const lowConfidence = state.allCheckboxes.filter(cb => 
        cb.confidenceCategory === 'low' && !cb.manuallyCorrect).length;
    
    elements.totalCheckboxes.textContent = state.allCheckboxes.length;
    elements.highConfidence.textContent = highConfidence;
    elements.mediumConfidence.textContent = mediumConfidence;
    elements.lowConfidence.textContent = lowConfidence;
    elements.manualCorrections.textContent = state.manualCorrections.length;
}

// Export JSON data
async function exportJsonData() {
    // Prepare export data
    const exportData = {
        document_id: state.documentId,
        document_name: state.documentName,
        export_date: new Date().toISOString(),
        checkboxes: state.allCheckboxes.map(cb => ({
            id: cb.id,
            label: cb.label,
            value: cb.value,
            confidence: cb.confidence,
            page: cb.page,
            bbox: cb.bbox,
            manually_corrected: cb.manuallyCorrect || false
        }))
    };
    
    try {
        // Call export API
        const response = await fetch('/api/visualization/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(exportData)
        });
        
        if (!response.ok) throw new Error(`Export failed: ${response.statusText}`);
        
        const result = await response.json();
        
        // Download JSON file
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", `${state.documentName.replace(/\s+/g, '_')}_checkboxes.json`);
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
        
        showSuccess('Data exported successfully');
    } catch (error) {
        showError(`Export failed: ${error.message}`);
    }
}

// Save corrections back to database
async function saveCorrections() {
    try {
        // Prepare corrections data
        const correctionsData = {
            document_id: state.documentId,
            corrections: state.allCheckboxes
                .filter(cb => cb.manuallyCorrect)
                .map(cb => ({
                    id: cb.id,
                    label: cb.label,
                    value: cb.value,
                    manually_corrected: true
                }))
        };
        
        // Call save API
        const response = await fetch('/api/visualization/save-corrections', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(correctionsData)
        });
        
        if (!response.ok) throw new Error(`Save failed: ${response.statusText}`);
        
        showSuccess('Corrections saved successfully');
    } catch (error) {
        showError(`Save failed: ${error.message}`);
    }
}

// Display error message
function showError(message) {
    // Create toast or alert with error message
    alert(`Error: ${message}`);
}

// Display success message
function showSuccess(message) {
    // Create toast or alert with success message
    alert(`Success: ${message}`);
} 