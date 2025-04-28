// Main UI controller

// DOM References
const views = {
    home: document.getElementById('home-view'),
    setup: document.getElementById('setup-view'),
    politician: document.getElementById('politician-view'),
    influencer: document.getElementById('influencer-view'),
    claims: document.getElementById('claims-view'),
    warroom: document.getElementById('warroom-view')
};

// Button references
const navButtons = {
    politiciansBtn: document.getElementById('explore-politicians-btn'),
    influencersBtn: document.getElementById('explore-influencers-btn'),
    claimsBtn: document.getElementById('evaluate-claims-btn'),
    warroomBtn: document.getElementById('check-warroom-action-btn')
};

// Initialize app
function init() {
    console.log('Initializing MAGA_Ops application...');
    
    // Initialize modules
    if (window.politicianView) {
        window.politicianView.init();
    }
    
    if (window.influencerView) {
        window.influencerView.init();
    }
    
    setupEventListeners();
    showView('home');
}

// Setup event listeners
function setupEventListeners() {
    // Navigation buttons
    if (navButtons.politiciansBtn) {
        navButtons.politiciansBtn.addEventListener('click', () => showView('politician'));
    }
    
    if (navButtons.influencersBtn) {
        navButtons.influencersBtn.addEventListener('click', () => showView('influencer'));
    }
    
    if (navButtons.claimsBtn) {
        navButtons.claimsBtn.addEventListener('click', () => showView('claims'));
    }
    
    if (navButtons.warroomBtn) {
        navButtons.warroomBtn.addEventListener('click', () => showView('warroom'));
    }
}

// Show specific view and hide others
function showView(viewName) {
    console.log(`Showing view: ${viewName}`);
    
    // Hide all views
    Object.values(views).forEach(view => {
        if (view) view.style.display = 'none';
    });
    
    // Show requested view
    if (views[viewName]) {
        views[viewName].style.display = 'block';
        
        // Call show method if available
        if (window[`${viewName}View`] && typeof window[`${viewName}View`].show === 'function') {
            window[`${viewName}View`].show();
        }
    }
} 