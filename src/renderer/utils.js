console.log('[utils.js] Loaded');

/**
 * Navigates the window to the specified URL.
 * @param {string} url - The target URL.
 */
function navigateTo(url) {
    console.log(`[utils.js] Navigating to: ${url}`);
    window.location.href = url;
}

/**
 * Checks if the IPC API is available and properly initialized
 * @returns {boolean} - True if the IPC API is available
 */
function isIpcApiAvailable() {
    if (!window.electronAPI) {
        console.error('[utils.js] window.electronAPI is not defined. preload.js might not be properly set up.');
        return false;
    }
    
    if (typeof window.electronAPI.invoke !== 'function') {
        console.error('[utils.js] window.electronAPI.invoke is not a function. preload.js might be misconfigured.');
        return false;
    }
    
    return true;
}

/**
 * Safely executes an IPC call and handles errors
 * @param {string} channel - The IPC channel to invoke
 * @param {any} args - Arguments to pass to the IPC channel
 * @param {function} onSuccess - Callback function for successful response
 * @param {function} onError - Callback function for error handling
 */
function safeIpcCall(channel, args, onSuccess, onError) {
    if (!isIpcApiAvailable()) {
        const error = new Error('IPC API not available');
        if (onError) {
            onError(error);
        } else {
            console.error(`[utils.js] IPC call to ${channel} failed:`, error);
        }
        return;
    }
    
    console.log(`[utils.js] Invoking IPC channel: ${channel}`, args);
    window.electronAPI.invoke(channel, args)
        .then(result => {
            console.log(`[utils.js] IPC ${channel} result:`, result);
            if (onSuccess) {
                onSuccess(result);
            }
        })
        .catch(error => {
            console.error(`[utils.js] IPC ${channel} error:`, error);
            if (onError) {
                onError(error);
            }
        });
}

/**
 * Initializes event listeners for the standard sidebar navigation buttons.
 * Sets the active state based on the current page.
 * @param {string} currentPage - Identifier for the current page ('home', 'explore-politicians', 'explore-influencers', 'generate', 'settings').
 */
function initializeSidebarNavigation(currentPage) {
    console.log(`[utils.js] Initializing sidebar for page: ${currentPage}`);

    const homeBtn = document.getElementById('nav-home');
    const exploreBtn = document.getElementById('nav-explore');
    const generateBtn = document.getElementById('nav-generate');
    const settingsBtn = document.getElementById('nav-settings-sidebar');

    // Remove active class from all first
    [homeBtn, exploreBtn, generateBtn, settingsBtn].forEach(btn => btn?.classList.remove('active'));

    // Add listeners and set active class
    if (homeBtn) {
        homeBtn.addEventListener('click', () => navigateTo('landing.html'));
        if (currentPage === 'home') homeBtn.classList.add('active');
    }

    if (exploreBtn) {
        // Determine where explore links based on context? For now, default to politicians
        exploreBtn.addEventListener('click', () => navigateTo('politician-view.html')); 
        if (currentPage === 'explore-politicians' || currentPage === 'explore-influencers') {
             exploreBtn.classList.add('active');
        }
    }

    if (generateBtn) {
        generateBtn.addEventListener('click', () => navigateTo('generate-intel.html'));
        if (currentPage === 'generate') generateBtn.classList.add('active');
    }

    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            console.log('[utils.js] Settings button clicked (Placeholder)');
            alert('Settings page not implemented yet.');
        });
         if (currentPage === 'settings') settingsBtn.classList.add('active');
    }
}

/**
 * Adds a placeholder click listener to a button that shows an alert.
 * @param {HTMLElement} button - The button element.
 * @param {string} actionName - The name of the action for the alert message.
 */
function addPlaceholderListener(button, actionName) {
    if (button) {
        button.addEventListener('click', () => {
            console.log(`[utils.js] Placeholder action button clicked: ${actionName}`);
            alert(`Action triggered: ${actionName} (Placeholder - Not Implemented Yet)`);
        });
    } else {
         console.warn(`[utils.js] Could not find placeholder button for: ${actionName}`);
    }
}

/**
 * Runs a diagnostic check of IPC and database connectivity
 * @returns {Promise} - A promise that resolves with the diagnostic info
 */
function runDiagnostics() {
    return new Promise((resolve, reject) => {
        if (!isIpcApiAvailable()) {
            reject(new Error('IPC API not available'));
            return;
        }
        
        window.electronAPI.invoke('app:diagnostics', { testDb: true })
            .then(diagnosticInfo => {
                console.log('[utils.js] Diagnostics results:', diagnosticInfo);
                resolve(diagnosticInfo);
            })
            .catch(error => {
                console.error('[utils.js] Diagnostics failed:', error);
                reject(error);
            });
    });
}

// Make functions globally accessible (or use modules if build process allows)
window.appUtils = {
    navigateTo,
    initializeSidebarNavigation,
    addPlaceholderListener,
    isIpcApiAvailable,
    safeIpcCall,
    runDiagnostics
}; 