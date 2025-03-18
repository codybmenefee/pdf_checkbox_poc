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
    },
    metrics: {
        enabled: true,           // Enable/disable metrics collection
        logToConsole: true,      // Log metrics to console
        sendToServer: true       // Send metrics to server
    },
    fieldVisuals: {
        activeClass: 'active-drag',
        resizeClass: 'active-resize',
        selectedClass: 'selected',
        overlapWarningClass: 'overlap-warning',
        animateChanges: true     // Enable animations for field changes
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
    isRectangleSelect: false,     // Flag for rectangle selection mode (Ctrl key)
    rectangleSelect: {            // State for rectangle selection
        startX: 0,
        startY: 0,
        endX: 0,
        endY: 0,
        active: false
    },
    currentZoomLevel: CONFIG.defaultZoomLevel, // Current zoom level index
    zoomFactor: CONFIG.zoomLevels[CONFIG.defaultZoomLevel], // Current zoom factor
    preloadedImages: new Map(),   // Cache for preloaded images
    preloadInProgress: false,     // Flag to track ongoing preloads
    batchOperationActive: false,  // Flag for batch operations
    lastSelectedFieldId: null     // Last selected field for range selection
};

// Metrics tracking
const metrics = {
    sessionId: generateSessionId(),
    imageLoads: {
        total: 0,
        success: 0,
        failure: 0,
        fallbackSuccess: 0,
        timings: []
    },
    navigation: {
        pageChanges: 0,
        averageLoadTime: 0
    },
    errors: [],
    timestamps: {
        sessionStart: Date.now(),
        lastPageChange: 0
    }
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
    // Get document ID or form ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const documentId = urlParams.get('id');
    const formId = urlParams.get('form_id');
    
    if (documentId) {
        state.documentId = documentId;
        await loadDocumentData(documentId);
        setupEventListeners();
    } else if (formId) {
        state.documentId = formId; // Store the form ID as the document ID
        await loadFormData(formId);
        setupEventListeners();
    } else {
        showError('No document ID or form ID provided');
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
    
    // Debug mode toggle
    const toggleDebugMode = document.getElementById('toggleDebugMode');
    if (toggleDebugMode) {
        toggleDebugMode.addEventListener('change', () => {
            state.showDebug = toggleDebugMode.checked;
            CONFIG.debugMode = toggleDebugMode.checked;
            
            // Toggle debug areas
            const debugArea = document.getElementById('debugArea');
            const debugOverlay = document.getElementById('debugOverlay');
            
            if (debugArea) {
                debugArea.style.display = state.showDebug ? 'block' : 'none';
            }
            
            if (debugOverlay) {
                debugOverlay.style.display = state.showDebug ? 'block' : 'none';
            }
            
            renderFieldOverlay();
        });
    }
    
    // Mouse position tracking on document image
    elements.documentImage.addEventListener('mousemove', (e) => {
        if (!state.showDebug) return;
        
        const rect = elements.documentImage.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        if (x >= 0 && y >= 0 && x <= rect.width && y <= rect.height) {
            // Get both pixel and normalized coordinates
            const normalizedX = (x / rect.width).toFixed(3);
            const normalizedY = (y / rect.height).toFixed(3);
            
            // Update cursor position displays
            const cursorPos = document.getElementById('cursorPos');
            const docCursorPos = document.getElementById('docCursorPos');
            
            if (cursorPos) {
                cursorPos.textContent = `${Math.round(x)},${Math.round(y)} (${normalizedX},${normalizedY})`;
            }
            
            if (docCursorPos) {
                docCursorPos.textContent = `${Math.round(x)},${Math.round(y)} (${normalizedX},${normalizedY})`;
            }
        }
    });
    
    // Update image dimensions on load
    elements.documentImage.addEventListener('load', () => {
        if (state.showDebug) {
            const imageSize = document.getElementById('imageSize');
            if (imageSize) {
                imageSize.textContent = `${elements.documentImage.width}x${elements.documentImage.height}`;
            }
        }
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
    
    // Rectangle selection
    elements.documentContainer.addEventListener('mousedown', handleDocumentMouseDown);
    elements.documentContainer.addEventListener('mousemove', handleDocumentMouseMove);
    elements.documentContainer.addEventListener('mouseup', handleDocumentMouseUp);
    
    // Batch operation buttons 
    const batchAlignLeftBtn = document.getElementById('batchAlignLeft');
    if (batchAlignLeftBtn) {
        batchAlignLeftBtn.addEventListener('click', () => batchAlign('left'));
    }
    
    const batchAlignRightBtn = document.getElementById('batchAlignRight');
    if (batchAlignRightBtn) {
        batchAlignRightBtn.addEventListener('click', () => batchAlign('right'));
    }
    
    const batchAlignTopBtn = document.getElementById('batchAlignTop');
    if (batchAlignTopBtn) {
        batchAlignTopBtn.addEventListener('click', () => batchAlign('top'));
    }
    
    const batchAlignBottomBtn = document.getElementById('batchAlignBottom');
    if (batchAlignBottomBtn) {
        batchAlignBottomBtn.addEventListener('click', () => batchAlign('bottom'));
    }
    
    const batchDistributeHorizontalBtn = document.getElementById('batchDistributeHorizontal');
    if (batchDistributeHorizontalBtn) {
        batchDistributeHorizontalBtn.addEventListener('click', () => batchDistribute('horizontal'));
    }
    
    const batchDistributeVerticalBtn = document.getElementById('batchDistributeVertical');
    if (batchDistributeVerticalBtn) {
        batchDistributeVerticalBtn.addEventListener('click', () => batchDistribute('vertical'));
    }
    
    const batchSameWidthBtn = document.getElementById('batchSameWidth');
    if (batchSameWidthBtn) {
        batchSameWidthBtn.addEventListener('click', () => batchSetSameSize('width'));
    }
    
    const batchSameHeightBtn = document.getElementById('batchSameHeight');
    if (batchSameHeightBtn) {
        batchSameHeightBtn.addEventListener('click', () => batchSetSameSize('height'));
    }

    // Add Ctrl key handling for rectangle selection
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Control') {
            state.isRectangleSelect = true;
            
            // Add visual indicator that rectangle select mode is active
            const docContainer = elements.documentContainer;
            if (docContainer) {
                docContainer.classList.add('rectangle-select-mode');
            }
        }
    });
    
    document.addEventListener('keyup', (e) => {
        if (e.key === 'Control') {
            state.isRectangleSelect = false;
            state.rectangleSelect.active = false;
            
            // Remove visual indicator
            const docContainer = elements.documentContainer;
            if (docContainer) {
                docContainer.classList.remove('rectangle-select-mode');
            }
            
            // Remove selection rectangle
            const selectionRect = document.getElementById('selectionRectangle');
            if (selectionRect) {
                selectionRect.remove();
            }
        }
    });
    
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

// Load form field data
async function loadFormData(formId) {
    try {
        console.log("Form ID being requested:", formId);
        console.log(`Loading form data for ID: ${formId}`);
        const response = await fetch(`/api/field-visualization/form/${formId}`);
        
        if (!response.ok) {
            console.error(`Server responded with status: ${response.status} ${response.statusText}`);
            throw new Error(`Failed to load form data: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log("Full form data received:", data);
        
        // Process the data (same as document data but with form-specific fields)
        if (!data.fields || data.fields.length === 0) {
            console.error("No fields found in the form data");
            showError('No fields found in the document');
            return;
        }
        
        // Check if fields are being processed
        console.log("Field count:", data.fields ? data.fields.length : 0);
        
        // Update state with document data
        state.documentName = data.document_name || 'Form PDF';
        state.processingDate = data.processing_date || new Date().toISOString();
        state.totalPages = data.total_pages || 1;
        state.pageData = data.pages || [];
        state.allFields = data.fields || [];
        
        // Update UI with document info
        updateDocumentInfo();
        
        // Initialize field type filters
        initFieldTypeFilters();
        
        // Set navigation button states
        updatePageNavigation();
        
        // Load first page
        navigateToPage(1);
        
    } catch (error) {
        console.error('Error loading form data:', error);
        showError(`Failed to load form data: ${error.message}`);
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
    
    // Track the page navigation
    const previousPage = state.currentPage;
    
    console.log(`Navigating to page ${pageNumber} of ${state.totalPages}`);
    state.currentPage = pageNumber;
    
    // Update buttons state
    elements.prevPage.disabled = pageNumber === 1;
    elements.nextPage.disabled = pageNumber === state.totalPages;
    elements.pageInfo.textContent = `Page ${pageNumber} of ${state.totalPages}`;
    
    // Get page data
    const pageData = state.pageData.find(p => p.page_number === pageNumber);
    
    if (!pageData) {
        console.error(`Page data not found for page ${pageNumber}`);
        return;
    }
    
    // Track page navigation metrics
    trackPageNavigation(previousPage, pageNumber);
    
    // Load the image (fast if preloaded)
    loadPageImage(pageData);
    
    // Update fields display
    updateCurrentPageFields();
    
    // Preload adjacent pages
    preloadAdjacentPages(pageNumber);
}

// Load page image
function loadPageImage(pageData) {
    console.log(`Loading image for page ${pageData.page_number}`);
    
    // Check if we have this image preloaded
    if (state.preloadedImages.has(pageData.page_number)) {
        console.log(`Using preloaded image for page ${pageData.page_number}`);
        
        // Use the preloaded image
        const imageUrl = state.preloadedImages.get(pageData.page_number);
        setDocumentImage(imageUrl, pageData);
        return;
    }
    
    // Not preloaded, load normally with multiple fallback sources
    const imageUrl = getImageUrl(pageData.image_url);
    
    // Load the image 
    loadImageWithFallbacks(imageUrl, (successUrl) => {
        setDocumentImage(successUrl, pageData);
        state.preloadedImages.set(pageData.page_number, successUrl); // Cache for future
    });
}

// Set document image
function setDocumentImage(imageUrl, pageData) {
    // Update the image source
    elements.documentImage.src = imageUrl;
    
    // Set the image dimensions
    elements.documentImage.style.width = `${pageData.width * state.zoomFactor}px`;
    elements.documentImage.style.height = `${pageData.height * state.zoomFactor}px`;
    
    // Update field overlay dimensions
    elements.fieldOverlay.style.width = `${pageData.width * state.zoomFactor}px`;
    elements.fieldOverlay.style.height = `${pageData.height * state.zoomFactor}px`;
    
    // Render the field overlay
    renderFieldOverlay();
}

// Preload adjacent pages
function preloadAdjacentPages(currentPage) {
    // Don't preload if already in progress
    if (state.preloadInProgress) return;
    
    state.preloadInProgress = true;
    console.log("Preloading adjacent pages");
    
    // Define which pages to preload
    const pagesToPreload = [];
    
    // Always preload next page if available
    if (currentPage < state.totalPages) {
        pagesToPreload.push(currentPage + 1);
    }
    
    // Then preload previous page if available
    if (currentPage > 1) {
        pagesToPreload.push(currentPage - 1);
    }
    
    // Preload in sequence
    preloadNextPageInQueue(pagesToPreload, 0, () => {
        console.log("Preloading complete");
        state.preloadInProgress = false;
    });
}

// Process the preload queue sequentially
function preloadNextPageInQueue(pages, index, onComplete) {
    if (index >= pages.length) {
        onComplete();
        return;
    }
    
    const pageNumber = pages[index];
    
    // Skip if already preloaded
    if (state.preloadedImages.has(pageNumber)) {
        console.log(`Page ${pageNumber} already preloaded, skipping`);
        preloadNextPageInQueue(pages, index + 1, onComplete);
        return;
    }
    
    // Get page data
    const pageData = state.pageData.find(p => p.page_number === pageNumber);
    if (!pageData) {
        console.error(`Page data not found for preloading page ${pageNumber}`);
        preloadNextPageInQueue(pages, index + 1, onComplete);
        return;
    }
    
    console.log(`Preloading page ${pageNumber}`);
    
    // Get the image URL with possible variations
    const imageUrl = getImageUrl(pageData.image_url);
    
    // Attempt to load with fallbacks
    loadImageWithFallbacks(imageUrl, (successUrl) => {
        // Cache the successfully loaded URL
        state.preloadedImages.set(pageNumber, successUrl);
        console.log(`Successfully preloaded page ${pageNumber}`);
        
        // Load the next page in queue
        preloadNextPageInQueue(pages, index + 1, onComplete);
    });
}

// Get possible image URLs with document ID
function getImageUrl(originalUrl) {
    // Remove leading slash if present
    const cleanUrl = originalUrl.startsWith('/') ? originalUrl.substring(1) : originalUrl;
    
    // Determine the visualization ID (which could be form ID or document ID)
    const visId = state.documentId;
    
    return `/static/visualizations/${visId}/${cleanUrl}`;
}

// Load image with multiple fallback sources
function loadImageWithFallbacks(primaryUrl, onSuccess) {
    console.log(`Attempting to load image: ${primaryUrl}`);
    
    // Metrics - start timing
    const startTime = Date.now();
    
    // Create a test image to try loading
    const testImg = new Image();
    
    // Track if any source succeeded
    let succeeded = false;
    let fallbackUsed = false;
    
    // List of alternative URL formats to try
    const altUrls = [
        primaryUrl,                                           // Primary URL
        primaryUrl.replace('/static/visualizations/', '/'),   // Direct file
        primaryUrl.replace('/static/visualizations/', '/api/visualizations/') // API path
    ];
    
    // Try next alternative URL
    let currentAltIndex = 0;
    
    // Set up error handler to try next alternative
    testImg.onerror = function() {
        currentAltIndex++;
        
        if (currentAltIndex < altUrls.length) {
            console.log(`Primary image load failed, trying alternative URL: ${altUrls[currentAltIndex]}`);
            fallbackUsed = true;
            testImg.src = altUrls[currentAltIndex];
        } else {
            console.error("All image loading attempts failed");
            
            // Track the failed load
            trackImageLoad(primaryUrl, startTime, false, fallbackUsed);
            
            // Log the error
            logErrorMetric('image-load', 'All image loading attempts failed', {
                primaryUrl,
                altUrls,
                page: state.currentPage
            });
            
            // Use a placeholder or default image
            onSuccess('/static/img/page_not_found.png');
        }
    };
    
    // Set up success handler
    testImg.onload = function() {
        succeeded = true;
        console.log(`Successfully loaded image from: ${testImg.src}`);
        
        // Track the successful load
        trackImageLoad(testImg.src, startTime, true, fallbackUsed);
        
        onSuccess(testImg.src);
    };
    
    // Start loading first URL
    testImg.src = altUrls[0];
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
        
        // Add visual indicator for active dragging
        marker.classList.add(CONFIG.fieldVisuals.activeClass);
        
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
    
    // Update debug display if in debug mode
    if (CONFIG.debugMode) {
        updateDebugDisplay(fieldId);
    }
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
    
    // Add visual indicator for active resizing
    fieldMarker.classList.add(CONFIG.fieldVisuals.resizeClass);
    
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
    
    // Update debug display if in debug mode
    if (CONFIG.debugMode) {
        updateDebugDisplay(fieldId);
    }
    
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
        const element = state.activeDrag 
            ? state.activeDrag.element 
            : state.resizeHandle.element;
            
        // Remove visual indicators
        element.classList.remove(CONFIG.fieldVisuals.activeClass);
        element.classList.remove(CONFIG.fieldVisuals.resizeClass);
        
        // Get the field being modified
        const fieldIndex = state.activeDrag 
            ? state.activeDrag.fieldIndex 
            : state.resizeHandle.fieldIndex;
        
        const field = state.currentPageFields[fieldIndex];
        
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
        
        // Check for field overlaps after repositioning
        checkFieldOverlaps(field.id, element);
        
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
        
        // Update debug display if in debug mode
        if (CONFIG.debugMode) {
            updateDebugDisplay(field.id);
        }
    }
    
    // Reset drag/resize state
    state.activeDrag = null;
    state.resizeHandle = null;
    
    // Remove global event listeners
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
}

// Check if a field overlaps with any other fields
function checkFieldOverlaps(fieldId, element) {
    // Skip if element is null
    if (!element) return false;
    
    // Get the current field's rectangle
    const rect1 = element.getBoundingClientRect();
    let hasOverlap = false;
    
    // Remove any existing overlap warnings
    document.querySelectorAll(`.${CONFIG.fieldVisuals.overlapWarningClass}`).forEach(el => {
        el.classList.remove(CONFIG.fieldVisuals.overlapWarningClass);
    });
    
    // Check against all other fields on the current page
    const otherFields = document.querySelectorAll(`.field-marker:not([data-field-id="${fieldId}"])`);
    
    otherFields.forEach(otherField => {
        const rect2 = otherField.getBoundingClientRect();
        
        // Check for rectangle overlap
        if (!(rect1.right < rect2.left || 
              rect1.left > rect2.right || 
              rect1.bottom < rect2.top || 
              rect1.top > rect2.bottom)) {
            
            // Overlap detected
            hasOverlap = true;
            
            // Add warning class to both fields
            element.classList.add(CONFIG.fieldVisuals.overlapWarningClass);
            otherField.classList.add(CONFIG.fieldVisuals.overlapWarningClass);
            
            // Log warning if debug mode is enabled
            if (CONFIG.debugMode) {
                console.log(`Field overlap detected: ${fieldId} with ${otherField.dataset.fieldId}`);
            }
        }
    });
    
    return hasOverlap;
}

// Update debug display with detailed information
function updateDebugDisplay(fieldId) {
    if (!CONFIG.debugMode) return;
    
    // Make sure debug area is visible
    const debugInfo = document.getElementById('debugInfo');
    debugInfo.style.display = 'block';
    
    // Update selection info
    const selectionInfo = document.getElementById('selectionInfo');
    if (selectionInfo) {
        if (state.selectedFields.size === 0) {
            selectionInfo.textContent = "No fields selected";
        } else {
            selectionInfo.textContent = `${state.selectedFields.size} field(s) selected: ${Array.from(state.selectedFields).join(', ')}`;
        }
    }
    
    // Update field details if a field ID is provided
    if (fieldId) {
        const field = state.allFields.find(f => f.id === fieldId);
        if (field) {
            const selectedFieldDetails = document.getElementById('selectedFieldDetails');
            if (selectedFieldDetails) {
                selectedFieldDetails.textContent = JSON.stringify(field, null, 2);
            }
        }
    }
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

// Generate a unique session ID
function generateSessionId() {
    return 'vis_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
}

// Log a metric event
function logMetric(category, action, label, value) {
    if (!CONFIG.metrics.enabled) return;
    
    const event = {
        timestamp: Date.now(),
        category,
        action,
        label,
        value
    };
    
    // Log to console if enabled
    if (CONFIG.metrics.logToConsole) {
        console.log(`METRIC: [${category}] ${action} - ${label}: ${value}`);
    }
    
    // Send to server if enabled
    if (CONFIG.metrics.sendToServer) {
        // Queue the event for batch sending
        sendMetricToServer(event);
    }
    
    return event;
}

// Send metrics to server
function sendMetricToServer(event) {
    // Add form/document ID to the event
    event.documentId = state.documentId;
    event.sessionId = metrics.sessionId;
    
    // Use fetch to send the metric to a server endpoint
    fetch('/api/metrics/log', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(event),
        // Use keepalive to ensure the request completes even if page is unloading
        keepalive: true
    }).catch(error => {
        console.error('Error sending metric to server:', error);
    });
}

// Track image load performance
function trackImageLoad(url, startTime, success, fallbackUsed) {
    // Calculate timing
    const endTime = Date.now();
    const loadTime = endTime - startTime;
    
    // Update metrics
    metrics.imageLoads.total++;
    
    if (success) {
        metrics.imageLoads.success++;
        if (fallbackUsed) {
            metrics.imageLoads.fallbackSuccess++;
        }
    } else {
        metrics.imageLoads.failure++;
    }
    
    // Store timing data
    metrics.imageLoads.timings.push({
        url,
        loadTime,
        success,
        fallbackUsed,
        timestamp: endTime
    });
    
    // Log the metric
    logMetric('image', success ? 'load-success' : 'load-failure', 
             url, {
                 loadTime, 
                 fallbackUsed,
                 page: state.currentPage
             });
    
    return loadTime;
}

// Track page navigation performance
function trackPageNavigation(fromPage, toPage) {
    const navigationTime = Date.now();
    const timeFromLastChange = metrics.timestamps.lastPageChange > 0 ? 
                            navigationTime - metrics.timestamps.lastPageChange : 0;
    
    metrics.timestamps.lastPageChange = navigationTime;
    metrics.navigation.pageChanges++;
    
    // Log the metric
    logMetric('navigation', 'page-change', 
             `${fromPage}->${toPage}`, {
                 timeFromLastChange,
                 cumulativePageChanges: metrics.navigation.pageChanges
             });
}

// Log an error
function logErrorMetric(category, message, details) {
    const errorEvent = {
        timestamp: Date.now(),
        category, 
        message,
        details
    };
    
    metrics.errors.push(errorEvent);
    
    // Log the metric
    logMetric('error', category, message, details);
    
    return errorEvent;
}

// Generate performance report
function generatePerformanceReport() {
    // Calculate statistics
    const totalLoads = metrics.imageLoads.total;
    const successRate = totalLoads > 0 ? 
                       (metrics.imageLoads.success / totalLoads) * 100 : 0;
    const fallbackRate = metrics.imageLoads.success > 0 ? 
                        (metrics.imageLoads.fallbackSuccess / metrics.imageLoads.success) * 100 : 0;
    
    // Calculate average load time
    let totalLoadTime = 0;
    let successLoadTime = 0;
    let successCount = 0;
    
    metrics.imageLoads.timings.forEach(timing => {
        totalLoadTime += timing.loadTime;
        if (timing.success) {
            successLoadTime += timing.loadTime;
            successCount++;
        }
    });
    
    const avgLoadTime = totalLoads > 0 ? totalLoadTime / totalLoads : 0;
    const avgSuccessLoadTime = successCount > 0 ? successLoadTime / successCount : 0;
    
    // Create report
    const report = {
        sessionId: metrics.sessionId,
        documentId: state.documentId,
        sessionDuration: Date.now() - metrics.timestamps.sessionStart,
        imageLoads: {
            total: totalLoads,
            success: metrics.imageLoads.success,
            failure: metrics.imageLoads.failure,
            successRate: successRate.toFixed(2) + '%',
            fallbackSuccessRate: fallbackRate.toFixed(2) + '%',
            averageLoadTime: avgLoadTime + 'ms',
            averageSuccessLoadTime: avgSuccessLoadTime + 'ms'
        },
        navigation: {
            pageChanges: metrics.navigation.pageChanges
        },
        errorCount: metrics.errors.length
    };
    
    console.log('Performance Report:', report);
    
    // Send to server
    if (CONFIG.metrics.sendToServer) {
        fetch('/api/metrics/report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(report)
        }).catch(error => {
            console.error('Error sending performance report:', error);
        });
    }
    
    return report;
}

// Handle mousedown on document for rectangle selection
function handleDocumentMouseDown(event) {
    // Only start rectangle selection if rectangle select mode is active
    if (!state.isRectangleSelect) return;
    
    // Don't trigger if clicking on a field marker or handle
    if (event.target.classList.contains('field-marker') || 
        event.target.classList.contains('resize-handle')) {
        return;
    }
    
    // Get position relative to the document container
    const rect = elements.documentContainer.getBoundingClientRect();
    const startX = event.clientX - rect.left;
    const startY = event.clientY - rect.top;
    
    // Initialize rectangle selection state
    state.rectangleSelect = {
        startX,
        startY,
        endX: startX,
        endY: startY,
        active: true
    };
    
    // Create visual selection rectangle
    let selectionRect = document.getElementById('selectionRectangle');
    if (selectionRect) {
        selectionRect.remove();
    }
    
    selectionRect = document.createElement('div');
    selectionRect.id = 'selectionRectangle';
    selectionRect.style.position = 'absolute';
    selectionRect.style.border = '1px dashed #007bff';
    selectionRect.style.backgroundColor = 'rgba(0, 123, 255, 0.1)';
    selectionRect.style.zIndex = '5';
    selectionRect.style.pointerEvents = 'none';
    
    elements.documentContainer.appendChild(selectionRect);
    
    // Update the rectangle
    updateSelectionRectangle();
}

// Handle mousemove during rectangle selection
function handleDocumentMouseMove(event) {
    if (!state.rectangleSelect.active) return;
    
    // Update end position
    const rect = elements.documentContainer.getBoundingClientRect();
    state.rectangleSelect.endX = event.clientX - rect.left;
    state.rectangleSelect.endY = event.clientY - rect.top;
    
    // Update visual rectangle
    updateSelectionRectangle();
}

// Handle mouseup after rectangle selection
function handleDocumentMouseUp(event) {
    if (!state.rectangleSelect.active) return;
    
    // Final update to end position
    const rect = elements.documentContainer.getBoundingClientRect();
    state.rectangleSelect.endX = event.clientX - rect.left;
    state.rectangleSelect.endY = event.clientY - rect.top;
    
    // Select fields that intersect with the selection rectangle
    selectFieldsInRectangle();
    
    // Clean up
    state.rectangleSelect.active = false;
    
    // Remove selection rectangle
    const selectionRect = document.getElementById('selectionRectangle');
    if (selectionRect) {
        selectionRect.remove();
    }
}

// Update the selection rectangle visualization
function updateSelectionRectangle() {
    const selectionRect = document.getElementById('selectionRectangle');
    if (!selectionRect) return;
    
    const { startX, startY, endX, endY } = state.rectangleSelect;
    
    // Calculate rectangle dimensions
    const left = Math.min(startX, endX);
    const top = Math.min(startY, endY);
    const width = Math.abs(endX - startX);
    const height = Math.abs(endY - startY);
    
    // Update visual rectangle
    selectionRect.style.left = `${left}px`;
    selectionRect.style.top = `${top}px`;
    selectionRect.style.width = `${width}px`;
    selectionRect.style.height = `${height}px`;
}

// Select fields that intersect with the selection rectangle
function selectFieldsInRectangle() {
    // Get selection rectangle coordinates
    const { startX, startY, endX, endY } = state.rectangleSelect;
    const selRect = {
        left: Math.min(startX, endX),
        top: Math.min(startY, endY),
        right: Math.max(startX, endX),
        bottom: Math.max(startY, endY)
    };
    
    // Get all field markers
    const fieldMarkers = document.querySelectorAll('.field-marker');
    
    // If not in multi-select mode, clear current selection
    if (!state.isMultiSelect) {
        state.selectedFields.clear();
    }
    
    // Check each field marker for intersection with selection rectangle
    fieldMarkers.forEach(marker => {
        const fieldRect = marker.getBoundingClientRect();
        const containerRect = elements.documentContainer.getBoundingClientRect();
        
        // Convert field rect to container coordinates
        const fieldInContainer = {
            left: fieldRect.left - containerRect.left,
            top: fieldRect.top - containerRect.top,
            right: fieldRect.right - containerRect.left,
            bottom: fieldRect.bottom - containerRect.top
        };
        
        // Check for intersection
        if (!(fieldInContainer.right < selRect.left || 
              fieldInContainer.left > selRect.right || 
              fieldInContainer.bottom < selRect.top || 
              fieldInContainer.top > selRect.bottom)) {
            
            // Add to selection
            const fieldId = marker.dataset.fieldId;
            state.selectedFields.add(fieldId);
        }
    });
    
    // Update UI to reflect new selection
    renderFieldOverlay();
    highlightSelectedFieldsInTable();
    
    // Update debug display
    if (CONFIG.debugMode) {
        updateDebugDisplay();
    }
}

// Batch align the selected fields
function batchAlign(alignType) {
    if (state.selectedFields.size < 2) {
        alert('Select at least two fields to align');
        return;
    }
    
    state.batchOperationActive = true;
    
    // Get selected field markers
    const selectedMarkers = [];
    state.selectedFields.forEach(fieldId => {
        const marker = document.querySelector(`.field-marker[data-field-id="${fieldId}"]`);
        if (marker) {
            selectedMarkers.push(marker);
        }
    });
    
    // No valid markers found
    if (selectedMarkers.length < 2) {
        state.batchOperationActive = false;
        return;
    }
    
    // Determine target value for alignment
    let targetValue;
    switch (alignType) {
        case 'left':
            // Find leftmost value
            targetValue = Math.min(...selectedMarkers.map(marker => parseFloat(marker.style.left)));
            // Apply to all markers
            selectedMarkers.forEach(marker => {
                marker.style.left = `${targetValue}px`;
            });
            break;
        case 'right':
            // Find rightmost value
            targetValue = Math.max(...selectedMarkers.map(marker => 
                parseFloat(marker.style.left) + parseFloat(marker.style.width)
            ));
            // Apply to all markers
            selectedMarkers.forEach(marker => {
                const width = parseFloat(marker.style.width);
                marker.style.left = `${targetValue - width}px`;
            });
            break;
        case 'top':
            // Find topmost value
            targetValue = Math.min(...selectedMarkers.map(marker => parseFloat(marker.style.top)));
            // Apply to all markers
            selectedMarkers.forEach(marker => {
                marker.style.top = `${targetValue}px`;
            });
            break;
        case 'bottom':
            // Find bottommost value
            targetValue = Math.max(...selectedMarkers.map(marker => 
                parseFloat(marker.style.top) + parseFloat(marker.style.height)
            ));
            // Apply to all markers
            selectedMarkers.forEach(marker => {
                const height = parseFloat(marker.style.height);
                marker.style.top = `${targetValue - height}px`;
            });
            break;
    }
    
    // Update field data with new positions
    updateFieldPositionsFromMarkers(selectedMarkers);
    
    state.batchOperationActive = false;
    state.isModified = true;
    
    // Check for overlaps
    selectedMarkers.forEach(marker => {
        checkFieldOverlaps(marker.dataset.fieldId, marker);
    });
    
    // Update debug display
    if (CONFIG.debugMode) {
        updateDebugDisplay();
    }
}

// Distribute fields evenly
function batchDistribute(direction) {
    if (state.selectedFields.size < 3) {
        alert('Select at least three fields to distribute');
        return;
    }
    
    state.batchOperationActive = true;
    
    // Get selected field markers
    const selectedMarkers = [];
    state.selectedFields.forEach(fieldId => {
        const marker = document.querySelector(`.field-marker[data-field-id="${fieldId}"]`);
        if (marker) {
            selectedMarkers.push(marker);
        }
    });
    
    // No valid markers found
    if (selectedMarkers.length < 3) {
        state.batchOperationActive = false;
        return;
    }
    
    if (direction === 'horizontal') {
        // Sort by left position
        selectedMarkers.sort((a, b) => parseFloat(a.style.left) - parseFloat(b.style.left));
        
        // Find leftmost and rightmost markers
        const firstMarker = selectedMarkers[0];
        const lastMarker = selectedMarkers[selectedMarkers.length - 1];
        
        // Calculate total distributable space
        const startPos = parseFloat(firstMarker.style.left);
        const endPos = parseFloat(lastMarker.style.left);
        const totalSpace = endPos - startPos;
        
        // Calculate even spacing
        const spacing = totalSpace / (selectedMarkers.length - 1);
        
        // Distribute markers
        for (let i = 1; i < selectedMarkers.length - 1; i++) {
            const marker = selectedMarkers[i];
            const newLeft = startPos + (spacing * i);
            marker.style.left = `${newLeft}px`;
        }
    } else if (direction === 'vertical') {
        // Sort by top position
        selectedMarkers.sort((a, b) => parseFloat(a.style.top) - parseFloat(b.style.top));
        
        // Find topmost and bottommost markers
        const firstMarker = selectedMarkers[0];
        const lastMarker = selectedMarkers[selectedMarkers.length - 1];
        
        // Calculate total distributable space
        const startPos = parseFloat(firstMarker.style.top);
        const endPos = parseFloat(lastMarker.style.top);
        const totalSpace = endPos - startPos;
        
        // Calculate even spacing
        const spacing = totalSpace / (selectedMarkers.length - 1);
        
        // Distribute markers
        for (let i = 1; i < selectedMarkers.length - 1; i++) {
            const marker = selectedMarkers[i];
            const newTop = startPos + (spacing * i);
            marker.style.top = `${newTop}px`;
        }
    }
    
    // Update field data with new positions
    updateFieldPositionsFromMarkers(selectedMarkers);
    
    state.batchOperationActive = false;
    state.isModified = true;
    
    // Check for overlaps
    selectedMarkers.forEach(marker => {
        checkFieldOverlaps(marker.dataset.fieldId, marker);
    });
    
    // Update debug display
    if (CONFIG.debugMode) {
        updateDebugDisplay();
    }
}

// Set same size for all selected fields
function batchSetSameSize(dimension) {
    if (state.selectedFields.size < 2) {
        alert('Select at least two fields to set the same size');
        return;
    }
    
    state.batchOperationActive = true;
    
    // Get selected field markers
    const selectedMarkers = [];
    state.selectedFields.forEach(fieldId => {
        const marker = document.querySelector(`.field-marker[data-field-id="${fieldId}"]`);
        if (marker) {
            selectedMarkers.push(marker);
        }
    });
    
    // No valid markers found
    if (selectedMarkers.length < 2) {
        state.batchOperationActive = false;
        return;
    }
    
    // Use the first selected marker's size as the reference
    const referenceMarker = selectedMarkers[0];
    
    if (dimension === 'width') {
        const referenceWidth = parseFloat(referenceMarker.style.width);
        selectedMarkers.forEach(marker => {
            marker.style.width = `${referenceWidth}px`;
        });
    } else if (dimension === 'height') {
        const referenceHeight = parseFloat(referenceMarker.style.height);
        selectedMarkers.forEach(marker => {
            marker.style.height = `${referenceHeight}px`;
        });
    }
    
    // Update field data with new sizes
    updateFieldPositionsFromMarkers(selectedMarkers);
    
    state.batchOperationActive = false;
    state.isModified = true;
    
    // Check for overlaps
    selectedMarkers.forEach(marker => {
        checkFieldOverlaps(marker.dataset.fieldId, marker);
    });
    
    // Update debug display
    if (CONFIG.debugMode) {
        updateDebugDisplay();
    }
}

// Update field positions from markers
function updateFieldPositionsFromMarkers(markers) {
    // Get image dimensions for normalization
    const image = elements.documentImage;
    const rect = image.getBoundingClientRect();
    const { width, height } = rect;
    
    // Update each field
    markers.forEach(marker => {
        const fieldId = marker.dataset.fieldId;
        const field = state.allFields.find(f => f.id === fieldId);
        
        if (field) {
            // Update bbox with normalized coordinates
            field.bbox = {
                left: parseFloat(marker.style.left) / width,
                top: parseFloat(marker.style.top) / height,
                width: parseFloat(marker.style.width) / width,
                height: parseFloat(marker.style.height) / height
            };
            
            // Update right and bottom properties if they exist
            if (field.bbox.right !== undefined) {
                field.bbox.right = field.bbox.left + field.bbox.width;
            }
            if (field.bbox.bottom !== undefined) {
                field.bbox.bottom = field.bbox.top + field.bbox.height;
            }
        }
    });
}

// Update debug display with detailed information
function updateDebugDisplay() {
    if (!CONFIG.debugMode) return;
    
    // Make sure debug area is visible
    const debugInfo = document.getElementById('debugInfo');
    debugInfo.style.display = 'block';
    
    // Update selection info
    const selectionInfo = document.getElementById('selectionInfo');
    if (selectionInfo) {
        if (state.selectedFields.size === 0) {
            selectionInfo.textContent = "No fields selected";
        } else {
            selectionInfo.textContent = `${state.selectedFields.size} field(s) selected: ${Array.from(state.selectedFields).join(', ')}`;
        }
    }
    
    // Update field details if a specific field ID is provided
    if (state.selectedFields.size > 0) {
        const firstFieldId = Array.from(state.selectedFields)[0];
        const field = state.allFields.find(f => f.id === firstFieldId);
        
        if (field) {
            const selectedFieldDetails = document.getElementById('selectedFieldDetails');
            if (selectedFieldDetails) {
                if (state.selectedFields.size === 1) {
                    selectedFieldDetails.textContent = JSON.stringify(field, null, 2);
                } else {
                    // For multiple selection, show a summary
                    const summary = {
                        selectionCount: state.selectedFields.size,
                        selectedFields: Array.from(state.selectedFields),
                        batchOperationsAvailable: {
                            align: state.selectedFields.size >= 2,
                            distribute: state.selectedFields.size >= 3,
                            sameSize: state.selectedFields.size >= 2
                        }
                    };
                    selectedFieldDetails.textContent = JSON.stringify(summary, null, 2);
                }
            }
        }
    }
} 