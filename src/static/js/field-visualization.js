/**
 * Field Extraction Visualization JavaScript
 * Handles UI interactions and visualization of field extraction results
 */

// Configuration
const CONFIG = {
    colorMap: {
        text: 'field-text',
        number: 'field-number',
        date: 'field-date',
        checkbox: 'field-checkbox',
        signature: 'field-signature',
        other: 'field-other'
    },
    defaultType: 'other',
    zoomLevels: [0.5, 0.75, 1, 1.25, 1.5, 2, 3],
    defaultZoomLevel: 2, // Index in the zoomLevels array
    debugMode: false,  // Enable to show more debug information
    keyboardShortcuts: {
        // Navigation
        'ArrowLeft': 'previousPage',
        'ArrowRight': 'nextPage',
        
        // Display
        'o': 'toggleOverlay',
        'l': 'toggleLabels',
        'd': 'toggleDebug',
        
        // Selection
        'a': 'selectAll',
        'Escape': 'deselectAll',
        'Delete': 'deleteSelected',
        
        // Zoom
        '+': 'zoomIn',
        '=': 'zoomIn',
        '-': 'zoomOut',
        
        // Saving
        's': 'save'
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
    allFields: [],
    currentPageFields: [],
    showOverlay: true,
    showLabels: true,
    showDebug: false,
    fieldTypeFilters: new Set(),  // Empty means show all
    activeDrag: null,             // For drag operations
    dragStartPos: { x: 0, y: 0 }, // Starting position for drag
    resizeHandle: null,           // Current resize handle
    isModified: false,            // Track if any fields have been modified
    selectedFields: new Set(),    // Set of selected field IDs
    isMultiSelect: false,         // Flag for multi-selection (Shift key)
    currentZoomLevel: CONFIG.defaultZoomLevel, // Current zoom level index
    zoomFactor: CONFIG.zoomLevels[CONFIG.defaultZoomLevel] // Current zoom factor
};

// DOM Elements
const elements = {
    documentName: document.getElementById('documentName'),
    documentDate: document.getElementById('documentDate'),
    totalFields: document.getElementById('totalFields'),
    fieldTypeCounts: document.getElementById('fieldTypeCounts'),
    fieldTypeFilters: document.getElementById('fieldTypeFilters'),
    toggleFieldOverlay: document.getElementById('toggleFieldOverlay'),
    toggleFieldLabels: document.getElementById('toggleFieldLabels'),
    prevPage: document.getElementById('prevPage'),
    nextPage: document.getElementById('nextPage'),
    pageInfo: document.getElementById('pageInfo'),
    documentImage: document.getElementById('documentImage'),
    fieldOverlay: document.getElementById('fieldOverlay'),
    fieldTableBody: document.getElementById('fieldTableBody'),
    exportJsonBtn: document.getElementById('exportJsonBtn'),
    zoomIn: document.getElementById('zoomIn'),
    zoomOut: document.getElementById('zoomOut'),
    zoomLevel: document.getElementById('zoomLevel'),
    zoomReset: document.getElementById('zoomReset'),
    selectAll: document.getElementById('selectAll'),
    deselectAll: document.getElementById('deselectAll'),
    deleteSelected: document.getElementById('deleteSelected'),
    saveChanges: document.getElementById('saveChanges'),
    documentContainer: document.getElementById('documentContainer'),
    // Field detail modal elements
    detailFieldName: document.getElementById('detailFieldName'),
    detailFieldType: document.getElementById('detailFieldType'),
    detailFieldValue: document.getElementById('detailFieldValue'),
    detailFieldCoordinates: document.getElementById('detailFieldCoordinates')
};

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    // Get document ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const documentId = urlParams.get('id') || window.location.pathname.split('/').pop();
    
    if (documentId) {
        state.documentId = documentId;
        await loadDocumentData(documentId);
        setupEventListeners();
    } else {
        showError('No document ID provided');
    }
});

// Set up event listeners
function setupEventListeners() {
    // Page navigation
    elements.prevPage.addEventListener('click', () => navigateToPage(state.currentPage - 1));
    elements.nextPage.addEventListener('click', () => navigateToPage(state.currentPage + 1));
    
    // Display controls
    elements.toggleFieldOverlay.addEventListener('change', () => {
        state.showOverlay = elements.toggleFieldOverlay.checked;
        renderFieldOverlay();
    });
    
    elements.toggleFieldLabels.addEventListener('change', () => {
        state.showLabels = elements.toggleFieldLabels.checked;
        renderFieldOverlay();
    });
    
    // Add debug mode toggle to UI
    const debugToggle = document.createElement('div');
    debugToggle.className = 'form-check form-switch mb-2';
    debugToggle.innerHTML = `
        <input class="form-check-input" type="checkbox" id="toggleDebugMode">
        <label class="form-check-label" for="toggleDebugMode">Debug Mode</label>
    `;
    elements.fieldTypeFilters.parentNode.insertBefore(debugToggle, elements.fieldTypeFilters);
    
    // Debug mode toggle
    const toggleDebugMode = document.getElementById('toggleDebugMode');
    toggleDebugMode.addEventListener('change', () => {
        state.showDebug = toggleDebugMode.checked;
        CONFIG.debugMode = toggleDebugMode.checked;
        renderFieldOverlay();
    });
    
    // Export button
    elements.exportJsonBtn.addEventListener('click', exportJsonData);
    
    // Zoom controls
    elements.zoomIn.addEventListener('click', zoomIn);
    elements.zoomOut.addEventListener('click', zoomOut);
    elements.zoomReset.addEventListener('click', resetZoom);
    
    // Selection controls
    elements.selectAll.addEventListener('click', selectAllFields);
    elements.deselectAll.addEventListener('click', deselectAllFields);
    elements.deleteSelected.addEventListener('click', deleteSelectedFields);
    
    // Save changes
    elements.saveChanges.addEventListener('click', saveFieldChanges);
    
    // Keyboard events
    document.addEventListener('keydown', handleKeyboardShortcut);
    document.addEventListener('keydown', (e) => {
        // Set multi-select flag when Shift key is pressed
        if (e.key === 'Shift') {
            state.isMultiSelect = true;
        }
    });
    
    document.addEventListener('keyup', (e) => {
        // Clear multi-select flag when Shift key is released
        if (e.key === 'Shift') {
            state.isMultiSelect = false;
        }
    });
    
    // Document display interactions
    elements.documentContainer.addEventListener('mousemove', handleMouseMove);
    elements.documentContainer.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mouseup', handleMouseUp); // Catch mouseup outside the document
    
    // Load first page image
    if (state.pageData.length > 0) {
        loadPageImage(state.currentPage);
    }
}

// Load document and field data
async function loadDocumentData(documentId) {
    try {
        console.log(`Loading document data for ID: ${documentId}`);
        const response = await fetch(`/api/field-visualization/${documentId}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load document data: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log("Received document data:", data);
        
        // Check if there are fields in the response
        if (!data.fields || data.fields.length === 0) {
            console.warn("No fields found in document data");
            const noFieldsAlert = document.createElement('div');
            noFieldsAlert.className = 'alert alert-warning';
            noFieldsAlert.textContent = 'No fields found in this document. Try enabling Debug Mode to see more information.';
            document.querySelector('.main-content').prepend(noFieldsAlert);
        } else {
            console.log(`Loaded ${data.fields.length} fields`);
        }
        
        // Update document info
        state.documentName = data.document_name || 'Unknown Document';
        state.processingDate = data.processing_date || 'Unknown Date';
        state.pageData = data.pages || [];
        state.allFields = data.fields || [];
        state.totalPages = state.pageData.length;
        
        console.log(`Document has ${state.totalPages} pages and ${state.allFields.length} fields`);
        
        // Initialize field type filters to include all types
        const fieldTypes = new Set(state.allFields.map(field => field.type || CONFIG.defaultType));
        state.fieldTypeFilters = new Set(fieldTypes);
        
        console.log("Field types found:", Array.from(fieldTypes));
        
        // Update UI elements
        elements.documentName.textContent = `Document: ${state.documentName}`;
        elements.documentDate.textContent = `Processed: ${state.processingDate}`;
        
        // Create field type filter UI
        createFieldTypeFilters(fieldTypes);
        
        // Update metrics
        updateMetrics();
        
        // Navigate to first page
        navigateToPage(1);
    } catch (error) {
        console.error('Error loading document data:', error);
        showError('Failed to load document data');
    }
}

// Create field type filter checkboxes
function createFieldTypeFilters(fieldTypes) {
    elements.fieldTypeFilters.innerHTML = '';
    
    fieldTypes.forEach(type => {
        const filterContainer = document.createElement('div');
        filterContainer.classList.add('field-type-filter');
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `filter-${type}`;
        checkbox.checked = true;
        checkbox.classList.add('form-check-input');
        
        checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
                state.fieldTypeFilters.add(type);
            } else {
                state.fieldTypeFilters.delete(type);
            }
            updateCurrentPageFields();
        });
        
        const label = document.createElement('label');
        label.htmlFor = `filter-${type}`;
        label.classList.add('form-check-label', 'ms-2');
        
        const indicator = document.createElement('span');
        indicator.classList.add('field-type-indicator');
        indicator.style.backgroundColor = getColorForType(type);
        
        label.appendChild(indicator);
        label.appendChild(document.createTextNode(capitalizeFirstLetter(type)));
        
        filterContainer.appendChild(checkbox);
        filterContainer.appendChild(label);
        elements.fieldTypeFilters.appendChild(filterContainer);
    });
}

// Navigate to specific page
function navigateToPage(pageNumber) {
    if (pageNumber < 1 || pageNumber > state.totalPages) return;
    
    console.log(`Navigating to page ${pageNumber} of ${state.totalPages}`);
    state.currentPage = pageNumber;
    
    // Update buttons state
    elements.prevPage.disabled = pageNumber === 1;
    elements.nextPage.disabled = pageNumber === state.totalPages;
    elements.pageInfo.textContent = `Page ${pageNumber} of ${state.totalPages}`;
    
    // Get page data
    const page = state.pageData[pageNumber - 1];
    console.log("Page data:", page);
    
    // Load page image
    elements.documentImage.src = page.image_url;
    console.log("Loading image from:", page.image_url);
    elements.documentImage.onload = () => {
        console.log(`Image loaded with dimensions: ${elements.documentImage.width}x${elements.documentImage.height}`);
        updateCurrentPageFields();
    };
}

// Update fields for current page
function updateCurrentPageFields() {
    state.currentPageFields = state.allFields.filter(field => 
        field.page === state.currentPage && 
        (state.fieldTypeFilters.size === 0 || state.fieldTypeFilters.has(field.type || CONFIG.defaultType))
    );
    
    console.log(`Found ${state.currentPageFields.length} fields for page ${state.currentPage}`);
    if (state.currentPageFields.length > 0) {
        console.log("First field on page:", state.currentPageFields[0]);
    }
    
    renderFieldOverlay();
    renderFieldTable();
}

// Render field overlay on the document image
function renderFieldOverlay() {
    const overlay = elements.fieldOverlay;
    overlay.innerHTML = '';
    
    if (!state.showOverlay) {
        return;
    }
    
    // Get the document image dimensions
    const docImage = elements.documentImage;
    const docWidth = docImage.width;
    const docHeight = docImage.height;
    
    console.log(`Rendering overlay with image dimensions: ${docWidth}x${docHeight}`);
    
    // Apply zoom to container
    elements.documentContainer.style.transform = `scale(${state.zoomFactor})`;
    elements.documentContainer.style.transformOrigin = 'top left';
    
    // Update zoom level indicator
    elements.zoomLevel.textContent = `${Math.round(state.zoomFactor * 100)}%`;
    
    // Create field markers for the current page
    state.currentPageFields.forEach((field, index) => {
        const bbox = field.bbox || {};
        
        // Skip if no bounding box information
        if (!bbox) {
            console.warn(`Field ${field.id} has no bbox data`);
            
            // In debug mode, create a marker at the top left with warning style
            if (CONFIG.debugMode) {
                createDebugFieldMarker(field, overlay, 0, 0, 100, 30);
            }
            return;
        }
        
        // Handle different bbox formats - some have left/top/right/bottom, others have left/top/width/height
        let left, top, width, height;
        
        // Calculate absolute positions
        if (bbox.hasOwnProperty('width') && bbox.hasOwnProperty('height')) {
            // Format: left, top, width, height
            left = bbox.left * docWidth;
            top = bbox.top * docHeight;
            width = bbox.width * docWidth;
            height = bbox.height * docHeight;
        } else if (bbox.hasOwnProperty('right') && bbox.hasOwnProperty('bottom')) {
            // Format: left, top, right, bottom
            left = bbox.left * docWidth;
            top = bbox.top * docHeight;
            width = (bbox.right - bbox.left) * docWidth;
            height = (bbox.bottom - bbox.top) * docHeight;
        } else {
            console.warn(`Field ${field.id} has invalid bbox format:`, bbox);
            
            // In debug mode, create a marker at the top left with warning style
            if (CONFIG.debugMode) {
                createDebugFieldMarker(field, overlay, 20, 0, 100, 30);
            }
            return;
        }
        
        // Apply a size multiplier for checkboxes and small fields to make them more visible
        // This is especially important for checkbox fields which are often very small
        const sizeMultiplier = (field.type === 'checkbox' || (width < 20 && height < 20)) ? 2.5 : 1.0;
        
        // Ensure minimum dimensions for visibility
        width = Math.max(width * sizeMultiplier, 16);
        height = Math.max(height * sizeMultiplier, 16);
        
        // Adjust position to compensate for increased size to maintain center alignment
        if (sizeMultiplier > 1.0) {
            left -= (width - (bbox.width * docWidth)) / 2;
            top -= (height - (bbox.height * docHeight)) / 2;
        }
        
        // Create field marker
        const marker = document.createElement('div');
        marker.classList.add('field-marker');
        marker.classList.add(getColorForType(field.type));
        marker.dataset.fieldId = field.id;
        marker.dataset.fieldIndex = index;
        
        // Add selected state if applicable
        if (state.selectedFields.has(field.id)) {
            marker.classList.add('selected');
        }
        
        // Set position and size
        marker.style.left = `${left}px`;
        marker.style.top = `${top}px`;
        marker.style.width = `${width}px`;
        marker.style.height = `${height}px`;
        
        // Add label if enabled
        if (state.showLabels) {
            const label = document.createElement('div');
            label.classList.add('field-label');
            label.textContent = field.name || field.id;
            marker.appendChild(label);
        }
        
        // Add debug info if enabled
        if (CONFIG.debugMode) {
            const debugInfo = document.createElement('div');
            debugInfo.classList.add('debug-info');
            debugInfo.textContent = `${Math.round(left)},${Math.round(top)} ${Math.round(width)}x${Math.round(height)}`;
            marker.appendChild(debugInfo);
            marker.title = JSON.stringify(field.bbox, null, 2);
        }
        
        // Add resize handles
        const handles = ['tl', 'tr', 'bl', 'br'];
        handles.forEach(pos => {
            const handle = document.createElement('div');
            handle.classList.add('resize-handle', `handle-${pos}`);
            handle.dataset.handle = pos;
            handle.dataset.fieldId = field.id;
            marker.appendChild(handle);
            
            // Add event listeners for resize
            handle.addEventListener('mousedown', handleResizeMouseDown);
        });
        
        // Add event listeners for field selection and dragging
        marker.addEventListener('mousedown', handleFieldMarkerMouseDown);
        marker.addEventListener('click', (e) => {
            handleFieldSelection(field.id, e);
        });
        
        overlay.appendChild(marker);
        
        // Debug output to verify field positioning
        if (CONFIG.debugMode) {
            console.debug(`Rendered field ${field.id} at (${left}, ${top}) with size ${width}x${height}`);
        }
    });
}

// Helper function to create a debug marker for fields with issues
function createDebugFieldMarker(field, overlay, offsetX, offsetY, width, height) {
    const marker = document.createElement('div');
    marker.classList.add('field-marker', 'field-debug');
    marker.dataset.fieldId = field.id;
    
    // Set position and size
    marker.style.left = `${offsetX}px`;
    marker.style.top = `${offsetY}px`;
    marker.style.width = `${width}px`;
    marker.style.height = `${height}px`;
    marker.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
    marker.style.borderColor = 'red';
    
    // Add label
    const label = document.createElement('div');
    label.classList.add('field-label');
    label.textContent = `Missing: ${field.name || field.id}`;
    marker.appendChild(label);
    
    overlay.appendChild(marker);
    
    console.debug(`Added debug marker for field ${field.id} with invalid bbox`);
}

// Handle field marker mouse down for dragging
function handleFieldMarkerMouseDown(event) {
    // Ignore if it's from a resize handle
    if (event.target.classList.contains('resize-handle')) {
        return;
    }
    
    // Prevent default to avoid text selection
    event.preventDefault();
    
    const marker = event.currentTarget;
    const fieldId = marker.dataset.fieldId;
    
    // If clicking on a non-selected field without multi-select, clear selection
    if (!state.selectedFields.has(fieldId) && !state.isMultiSelect) {
        deselectAllFields();
    }
    
    // Start dragging logic (only if field is selected)
    if (state.selectedFields.has(fieldId)) {
        state.activeDrag = {
            element: marker,
            fieldId: fieldId,
            initialPos: {
                x: event.clientX,
                y: event.clientY
            },
            initialOffset: {
                left: parseFloat(marker.style.left),
                top: parseFloat(marker.style.top)
            }
        };
        
        // Add event listeners for dragging
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }
}

// Handle field selection
function handleFieldSelection(fieldId, event) {
    // Don't trigger selection during drag or resize operations
    if (state.activeDrag || state.resizeHandle) {
        return;
    }
    
    // Toggle selection based on multi-select mode
    if (state.isMultiSelect) {
        // Toggle this field's selection
        if (state.selectedFields.has(fieldId)) {
            state.selectedFields.delete(fieldId);
        } else {
            state.selectedFields.add(fieldId);
        }
    } else {
        // Select only this field
        state.selectedFields.clear();
        state.selectedFields.add(fieldId);
    }
    
    // Update UI to reflect selection
    renderFieldOverlay();
    highlightSelectedFieldsInTable();
}

// Highlight selected fields in the table
function highlightSelectedFieldsInTable() {
    // Clear all highlighting
    const rows = elements.fieldTableBody.querySelectorAll('tr');
    rows.forEach(row => {
        row.classList.remove('selected');
    });
    
    // Highlight selected fields
    state.selectedFields.forEach(fieldId => {
        const row = elements.fieldTableBody.querySelector(`tr[data-field-id="${fieldId}"]`);
        if (row) {
            row.classList.add('selected');
        }
    });
}

// Handle mousedown on resize handle
function handleResizeMouseDown(event) {
    // Only respond to left mouse button
    if (event.button !== 0) return;
    
    const handle = event.target;
    const fieldMarker = handle.parentElement;
    const fieldId = handle.dataset.fieldId;
    const fieldIndex = parseInt(handle.dataset.index);
    const handlePosition = handle.dataset.handle;
    
    // Set resize state
    state.resizeHandle = {
        handle: handlePosition,
        element: fieldMarker,
        fieldId: fieldId,
        fieldIndex: fieldIndex
    };
    
    // Store starting position and dimensions
    state.dragStartPos = {
        x: event.clientX,
        y: event.clientY,
        left: parseFloat(fieldMarker.style.left),
        top: parseFloat(fieldMarker.style.top),
        width: parseFloat(fieldMarker.style.width),
        height: parseFloat(fieldMarker.style.height)
    };
    
    // Add global event listeners for resize
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    event.preventDefault();
    event.stopPropagation();
}

// Handle mouse move for drag or resize
function handleMouseMove(event) {
    // Handle field marker dragging
    if (state.activeDrag) {
        const dx = event.clientX - state.dragStartPos.x;
        const dy = event.clientY - state.dragStartPos.y;
        
        const newLeft = state.dragStartPos.left + dx;
        const newTop = state.dragStartPos.top + dy;
        
        // Update element position
        state.activeDrag.element.style.left = `${newLeft}px`;
        state.activeDrag.element.style.top = `${newTop}px`;
        
        // Update field label position if visible
        if (state.showLabels) {
            const labels = elements.fieldOverlay.querySelectorAll('.field-label');
            const label = labels[state.activeDrag.fieldIndex];
            if (label) {
                label.style.left = `${newLeft}px`;
                label.style.top = `${newTop - 20}px`;
            }
        }
        
        state.isModified = true;
    }
    
    // Handle resize operation
    if (state.resizeHandle) {
        const dx = event.clientX - state.dragStartPos.x;
        const dy = event.clientY - state.dragStartPos.y;
        const handle = state.resizeHandle.handle;
        const element = state.resizeHandle.element;
        
        let newLeft = state.dragStartPos.left;
        let newTop = state.dragStartPos.top;
        let newWidth = state.dragStartPos.width;
        let newHeight = state.dragStartPos.height;
        
        // Adjust dimensions based on handle position
        switch (handle) {
            case 'tl': // Top-left
                newLeft = state.dragStartPos.left + dx;
                newTop = state.dragStartPos.top + dy;
                newWidth = state.dragStartPos.width - dx;
                newHeight = state.dragStartPos.height - dy;
                break;
            case 'tr': // Top-right
                newTop = state.dragStartPos.top + dy;
                newWidth = state.dragStartPos.width + dx;
                newHeight = state.dragStartPos.height - dy;
                break;
            case 'bl': // Bottom-left
                newLeft = state.dragStartPos.left + dx;
                newWidth = state.dragStartPos.width - dx;
                newHeight = state.dragStartPos.height + dy;
                break;
            case 'br': // Bottom-right
                newWidth = state.dragStartPos.width + dx;
                newHeight = state.dragStartPos.height + dy;
                break;
        }
        
        // Enforce minimum dimensions
        if (newWidth < 10) newWidth = 10;
        if (newHeight < 10) newHeight = 10;
        
        // Update element dimensions
        element.style.left = `${newLeft}px`;
        element.style.top = `${newTop}px`;
        element.style.width = `${newWidth}px`;
        element.style.height = `${newHeight}px`;
        
        // Update field label position if visible
        if (state.showLabels) {
            const labels = elements.fieldOverlay.querySelectorAll('.field-label');
            const label = labels[state.resizeHandle.fieldIndex];
            if (label) {
                label.style.left = `${newLeft}px`;
                label.style.top = `${newTop - 20}px`;
            }
        }
        
        state.isModified = true;
    }
}

// Handle mouse up to end drag or resize
function handleMouseUp() {
    if (state.activeDrag || state.resizeHandle) {
        // Get the field being modified
        const fieldIndex = state.activeDrag 
            ? state.activeDrag.fieldIndex 
            : state.resizeHandle.fieldIndex;
        
        const field = state.currentPageFields[fieldIndex];
        const element = state.activeDrag 
            ? state.activeDrag.element 
            : state.resizeHandle.element;
        
        // Get image dimensions for normalization
        const image = elements.documentImage;
        const rect = image.getBoundingClientRect();
        const { width, height } = rect;
        
        // Update field bbox with normalized coordinates
        field.bbox = {
            left: parseFloat(element.style.left) / width,
            top: parseFloat(element.style.top) / height,
            width: parseFloat(element.style.width) / width,
            height: parseFloat(element.style.height) / height
        };
        
        // Update field right and bottom properties if they exist
        if (field.bbox.right !== undefined) {
            field.bbox.right = field.bbox.left + field.bbox.width;
        }
        if (field.bbox.bottom !== undefined) {
            field.bbox.bottom = field.bbox.top + field.bbox.height;
        }
        
        // Update state
        if (state.isModified) {
            // Show save changes button
            if (!document.getElementById('saveChangesBtn')) {
                const saveBtn = document.createElement('button');
                saveBtn.id = 'saveChangesBtn';
                saveBtn.className = 'btn btn-success w-100 mb-2';
                saveBtn.textContent = 'Save Field Changes';
                saveBtn.addEventListener('click', saveFieldChanges);
                
                // Insert before export button
                const exportControls = document.querySelector('.export-controls');
                exportControls.insertBefore(saveBtn, elements.exportJsonBtn);
            }
        }
    }
    
    // Reset drag/resize state
    state.activeDrag = null;
    state.resizeHandle = null;
    
    // Remove global event listeners
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
}

// Save field changes to server
async function saveFieldChanges() {
    try {
        // Prepare data for saving
        const saveData = {
            document_id: state.documentId,
            fields: state.allFields
        };
        
        // Send to server
        const response = await fetch('/api/field-visualization/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(saveData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to save changes: ${response.statusText}`);
        }
        
        state.isModified = false;
        showSuccess('Field changes saved successfully');
        
        // Remove save button
        const saveBtn = document.getElementById('saveChangesBtn');
        if (saveBtn) saveBtn.remove();
        
    } catch (error) {
        console.error('Error saving field changes:', error);
        showError('Failed to save field changes');
    }
}

// Render table of fields on current page
function renderFieldTable() {
    const tableBody = elements.fieldTableBody;
    tableBody.innerHTML = '';
    
    state.currentPageFields.forEach(field => {
        const row = document.createElement('tr');
        row.dataset.fieldId = field.id;
        
        // Add selected state if applicable
        if (state.selectedFields.has(field.id)) {
            row.classList.add('selected');
        }
        
        // Add columns
        const nameCell = document.createElement('td');
        nameCell.textContent = field.name || '(unnamed)';
        
        const typeCell = document.createElement('td');
        typeCell.textContent = capitalizeFirstLetter(field.type || CONFIG.defaultType);
        
        const valueCell = document.createElement('td');
        valueCell.textContent = field.value || '';
        
        const actionsCell = document.createElement('td');
        
        // Add edit button
        const editBtn = document.createElement('button');
        editBtn.classList.add('btn', 'btn-sm', 'btn-outline-primary', 'me-1');
        editBtn.innerHTML = '<i class="bi bi-pencil"></i>';
        editBtn.addEventListener('click', () => openFieldDetailModal(field));
        
        // Add select button
        const selectBtn = document.createElement('button');
        selectBtn.classList.add('btn', 'btn-sm', 'btn-outline-secondary');
        selectBtn.innerHTML = '<i class="bi bi-check2-square"></i>';
        selectBtn.addEventListener('click', () => {
            handleFieldSelection(field.id, { shiftKey: false });
        });
        
        actionsCell.appendChild(editBtn);
        actionsCell.appendChild(selectBtn);
        
        // Add cells to row
        row.appendChild(nameCell);
        row.appendChild(typeCell);
        row.appendChild(valueCell);
        row.appendChild(actionsCell);
        
        // Add row to table
        tableBody.appendChild(row);
        
        // Add click listener for row selection
        row.addEventListener('click', (e) => {
            // Don't trigger if clicking on a button
            if (e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
                handleFieldSelection(field.id, e);
            }
        });
    });
}

// Open field detail modal
function openFieldDetailModal(field) {
    elements.detailFieldName.value = field.name;
    elements.detailFieldType.value = capitalizeFirstLetter(field.type || CONFIG.defaultType);
    elements.detailFieldValue.value = field.value || '';
    elements.detailFieldCoordinates.value = JSON.stringify({
        page: field.page,
        bbox: field.bbox
    }, null, 2);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('fieldDetailModal'));
    modal.show();
}

// Update metrics display
function updateMetrics() {
    // Total fields
    elements.totalFields.textContent = state.allFields.length;
    
    // Fields by type
    elements.fieldTypeCounts.innerHTML = '';
    
    // Count fields by type
    const fieldTypeCounts = {};
    state.allFields.forEach(field => {
        const type = field.type || CONFIG.defaultType;
        fieldTypeCounts[type] = (fieldTypeCounts[type] || 0) + 1;
    });
    
    // Display counts
    Object.entries(fieldTypeCounts).forEach(([type, count]) => {
        const countItem = document.createElement('div');
        countItem.classList.add('field-type-count');
        
        const typeLabel = document.createElement('span');
        const indicator = document.createElement('span');
        indicator.classList.add('field-type-indicator');
        indicator.style.backgroundColor = getColorForType(type);
        
        typeLabel.appendChild(indicator);
        typeLabel.appendChild(document.createTextNode(capitalizeFirstLetter(type)));
        
        const countValue = document.createElement('span');
        countValue.textContent = count;
        
        countItem.appendChild(typeLabel);
        countItem.appendChild(countValue);
        
        elements.fieldTypeCounts.appendChild(countItem);
    });
}

// Export data as JSON
async function exportJsonData() {
    try {
        const response = await fetch('/api/field-visualization/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                document_id: state.documentId
            }),
        });
        
        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Download as file
        const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `field_extraction_${state.documentId}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showSuccess('Data exported successfully');
    } catch (error) {
        console.error('Error exporting data:', error);
        showError('Failed to export data');
    }
}

// Utility functions
function getColorForType(type) {
    const colorClass = CONFIG.colorMap[type] || CONFIG.colorMap.other;
    switch (colorClass) {
        case 'field-text': return '#0d6efd';
        case 'field-number': return '#198754';
        case 'field-date': return '#dc3545';
        case 'field-checkbox': return '#fd7e14';
        case 'field-signature': return '#6610f2';
        case 'field-other': return '#6c757d';
        default: return '#6c757d';
    }
}

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function showError(message) {
    // Implementation depends on your preferred notification system
    alert(`Error: ${message}`);
}

function showSuccess(message) {
    // Implementation depends on your preferred notification system
    alert(`Success: ${message}`);
}

// Add these CSS styles into the style tag
document.head.insertAdjacentHTML('beforeend', `
    <style>
    .resize-handle {
        position: absolute;
        width: 8px;
        height: 8px;
        background-color: white;
        border: 1px solid #333;
        border-radius: 50%;
    }
    .resize-nw {
        left: -4px;
        top: -4px;
        cursor: nw-resize;
    }
    .resize-ne {
        right: -4px;
        top: -4px;
        cursor: ne-resize;
    }
    .resize-sw {
        left: -4px;
        bottom: -4px;
        cursor: sw-resize;
    }
    .resize-se {
        right: -4px;
        bottom: -4px;
        cursor: se-resize;
    }
    </style>
`);

// Zoom in
function zoomIn() {
    if (state.currentZoomLevel < CONFIG.zoomLevels.length - 1) {
        state.currentZoomLevel++;
        state.zoomFactor = CONFIG.zoomLevels[state.currentZoomLevel];
        renderFieldOverlay();
    }
}

// Zoom out
function zoomOut() {
    if (state.currentZoomLevel > 0) {
        state.currentZoomLevel--;
        state.zoomFactor = CONFIG.zoomLevels[state.currentZoomLevel];
        renderFieldOverlay();
    }
}

// Reset zoom
function resetZoom() {
    state.currentZoomLevel = CONFIG.defaultZoomLevel;
    state.zoomFactor = CONFIG.zoomLevels[state.currentZoomLevel];
    renderFieldOverlay();
}

// Select all fields on current page
function selectAllFields() {
    state.currentPageFields.forEach(field => {
        state.selectedFields.add(field.id);
    });
    renderFieldOverlay();
    highlightSelectedFieldsInTable();
}

// Deselect all fields
function deselectAllFields() {
    state.selectedFields.clear();
    renderFieldOverlay();
    highlightSelectedFieldsInTable();
}

// Delete selected fields
function deleteSelectedFields() {
    if (state.selectedFields.size === 0) {
        return;
    }
    
    // Filter out selected fields
    state.allFields = state.allFields.filter(field => !state.selectedFields.has(field.id));
    
    // Update current page fields
    updateCurrentPageFields();
    
    // Clear selection
    state.selectedFields.clear();
    
    // Mark as modified
    state.isModified = true;
    
    // Update metrics
    updateMetrics();
}

// Handle keyboard shortcuts
function handleKeyboardShortcut(event) {
    // Skip if in input elements
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
    }
    
    const key = event.key.toLowerCase();
    
    // Check if key is a command or if it's a Ctrl+key combination
    let command = CONFIG.keyboardShortcuts[key];
    if (!command && event.ctrlKey) {
        command = CONFIG.keyboardShortcuts[key];
    }
    
    if (!command) {
        return;
    }
    
    switch (command) {
        case 'previousPage':
            navigateToPage(state.currentPage - 1);
            break;
        case 'nextPage':
            navigateToPage(state.currentPage + 1);
            break;
        case 'toggleOverlay':
            elements.toggleFieldOverlay.checked = !elements.toggleFieldOverlay.checked;
            state.showOverlay = elements.toggleFieldOverlay.checked;
            renderFieldOverlay();
            break;
        case 'toggleLabels':
            elements.toggleFieldLabels.checked = !elements.toggleFieldLabels.checked;
            state.showLabels = elements.toggleFieldLabels.checked;
            renderFieldOverlay();
            break;
        case 'toggleDebug':
            const toggleDebugMode = document.getElementById('toggleDebugMode');
            toggleDebugMode.checked = !toggleDebugMode.checked;
            state.showDebug = toggleDebugMode.checked;
            CONFIG.debugMode = toggleDebugMode.checked;
            renderFieldOverlay();
            break;
        case 'selectAll':
            selectAllFields();
            break;
        case 'deselectAll':
            deselectAllFields();
            break;
        case 'deleteSelected':
            deleteSelectedFields();
            break;
        case 'zoomIn':
            zoomIn();
            break;
        case 'zoomOut':
            zoomOut();
            break;
        case 'save':
            if (event.ctrlKey) {
                event.preventDefault();
                saveFieldChanges();
            }
            break;
    }
} 