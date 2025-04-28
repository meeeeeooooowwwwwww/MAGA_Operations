// Influencer View functionality
// Manages the display and interaction with media influencers

// DOM References (assigned in DOMContentLoaded)
let influencerSearchInput = null;
let influencerSearchIndicator = null;
let influencersList = null;
let influencerView = null;
let influencerDetailView = null;
let influencerTabs = null;
let influencerBackButton = null;

// State management
let currentInfluencer = null;
let debounceTimer;

// Initialize Influencer module on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('[influencer-view.js] DOMContentLoaded event fired');
    // Assign DOM elements
    influencerSearchInput = document.getElementById('influencer-search-input');
    influencerSearchIndicator = document.getElementById('influencer-search-indicator');
    influencersList = document.getElementById('influencers-list');
    influencerView = document.getElementById('influencer-view');
    influencerDetailView = document.getElementById('influencer-detail');
    influencerTabs = document.querySelectorAll('#influencer-detail .tab-button');
    influencerBackButton = document.getElementById('influencer-back-button');

    // Initialize sidebar navigation
    window.appUtils.initializeSidebarNavigation('explore-influencers');

    // Hide initial lists and detail views
    if (influencersList) influencersList.style.display = 'none';
    if (influencerDetailView) influencerDetailView.style.display = 'none';

    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    console.log('Setting up influencer event listeners');
    // Search input - debounce on input
    if (influencerSearchInput) {
        influencerSearchInput.addEventListener('input', () => applySearch());
    } else console.error('influencerSearchInput not found');
    
    // Back button in detail view - return to list
    if (influencerBackButton) {
        influencerBackButton.addEventListener('click', function() {
            // Show influencer search view, hide detail view
            if (influencerView) influencerView.style.display = 'block';
            if (influencerDetailView) influencerDetailView.style.display = 'none';
            
            // Clear current influencer
            currentInfluencer = null;
            
            // If search input has text, make sure the influencer list is visible
            if (influencerSearchInput && influencerSearchInput.value.trim().length > 0) {
                if (influencersList) influencersList.style.display = 'block';
            }
        });
    }

    // Tabs listener for detail view
    if (influencerTabs) {
        influencerTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                showTab(tab.dataset.tab);
            });
        });
    }
    
    // Influencer list click listener
    if (influencersList) {
        influencersList.addEventListener('click', (event) => {
            const listItem = event.target.closest('.influencer-item');
            if (listItem && listItem.dataset.id) {
                getInfluencerDetails(listItem.dataset.id);
            }
        });
    }
}

// Helper to call Python bridge commands
function pythonBridge(command, ...args) {
    return window.electronAPI.invoke('python-bridge', command, ...args);
}

// Handle search
function applySearch() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        if (!influencerSearchInput || !influencersList) return;
        const searchTerm = influencerSearchInput.value.trim();
        if (searchTerm.length === 0) {
            influencersList.style.display = 'none';
            return;
        }
        
        // Show loading indicator
        if (influencerSearchIndicator) {
            influencerSearchIndicator.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
            influencerSearchIndicator.style.display = 'block';
        }
        // Use Python bridge for influencer search
        pythonBridge('search_influencers', searchTerm)
            .then(response => {
                if (influencerSearchIndicator) influencerSearchIndicator.style.display = 'none';
                // Expect response = JSON string or object
                let data = response;
                if (typeof response === 'string') {
                    try { data = JSON.parse(response); } catch { data = { success: false }; }
                }
                const results = data.success && Array.isArray(data.data) ? data.data : [];
                // Prioritize word-start matches then substring
                const termLower = searchTerm.toLowerCase();
                let matches = results.filter(i => i.name && i.name.split(/\s+/).some(part => part.toLowerCase().startsWith(termLower)));
                if (matches.length === 0) matches = results.filter(i => i.name && i.name.toLowerCase().includes(termLower));
                const display = matches.slice(0, 50);
                renderInfluencersList(display);
                influencersList.style.display = 'block';
            })
            .catch(error => {
                console.error('Error searching influencers:', error);
                if (influencerSearchIndicator) influencerSearchIndicator.style.display = 'none';
                influencersList.innerHTML = `<li class="influencer-item error"><i class="fas fa-exclamation-triangle"></i> Error searching media targets: ${error.message}</li>`;
                influencersList.style.display = 'block';
            });
    }, 300); // 300ms debounce
}

// Render influencers list based on search
function renderInfluencersList(influencers) {
    console.log(`renderInfluencersList called with ${influencers ? influencers.length : 0} targets.`);
    // Clear the current list
    influencersList.innerHTML = '';
    
    if (!influencers || influencers.length === 0) {
        const noResults = document.createElement('li');
        noResults.classList.add('influencer-item', 'no-results');
        noResults.innerHTML = '<i class="fas fa-search"></i> No media targets found matching your search.';
        influencersList.appendChild(noResults);
        return;
    }
    
    // Create a list item for each influencer
    influencers.forEach(influencer => {
        const li = document.createElement('li');
        li.classList.add('influencer-item');
        li.setAttribute('data-id', influencer.id || '');
        
        // Create type indicator based on influencer type
        let typeClass = 'social';
        let typeIcon = 'fa-hashtag';
        
        if (influencer.type === 'journalist') {
            typeClass = 'journalist';
            typeIcon = 'fa-newspaper';
        } else if (influencer.type === 'television') {
            typeClass = 'television';
            typeIcon = 'fa-tv';
        }
        
        // Build the HTML content
        let html = `
            <div class="influencer-info">
                <div class="influencer-name">${influencer.name || 'Unknown'}</div>
                <div class="influencer-details">
                    <span class="influencer-title">${influencer.platform || 'Media Target'}</span>
                    <span class="influencer-location">${influencer.outlet || ''}</span>
                </div>
            </div>
            <div class="influencer-type ${typeClass}" data-tooltip="${influencer.type || 'Social Media'}">
                <i class="fas ${typeIcon}"></i>
            </div>
        `;
        
        li.innerHTML = html;
        
        influencersList.appendChild(li);
    });
}

// Get influencer details and show profile
function getInfluencerDetails(influencerId) {
    if (!influencerId) {
        console.error('No influencer ID provided');
        return;
    }
    
    console.log(`Target clicked with ID: ${influencerId}`);
    
    // In a real app, this would fetch data from your backend
    // For now, we'll use mock data
    setTimeout(() => {
        // Mock influencer data
        const mockInfluencer = {
            id: influencerId,
            name: influencerId === 'inf1' ? 'Alex Media' : 
                  influencerId === 'inf2' ? 'Sarah Broadcast' : 
                  influencerId === 'inf3' ? 'Mike Reporter' :
                  influencerId === 'inf4' ? 'Taylor Influencer' : 'Unknown Influencer',
            platform: influencerId === 'inf1' ? 'Twitter' : 
                      influencerId === 'inf2' ? 'CNN' :
                      influencerId === 'inf3' ? 'Fox News' :
                      influencerId === 'inf4' ? 'Instagram' : 'Other',
            outlet: influencerId === 'inf1' ? 'Independent' : 
                    influencerId === 'inf2' ? 'CNN' :
                    influencerId === 'inf3' ? 'Fox News' :
                    influencerId === 'inf4' ? 'Independent' : 'Unknown',
            followers: influencerId === 'inf1' ? '1.2M' : 
                       influencerId === 'inf2' ? '800K' :
                       influencerId === 'inf3' ? '1.5M' :
                       influencerId === 'inf4' ? '5.2M' : '0',
            type: influencerId === 'inf1' ? 'journalist' : 
                  influencerId === 'inf2' ? 'television' :
                  influencerId === 'inf3' ? 'television' :
                  influencerId === 'inf4' ? 'social' : 'other',
            bio: `This is a mock biography for the media target. In a real application, this would contain actual information about the influencer's background, focus areas, and relevance.`,
            recentPosts: [
                { date: '2023-10-15', content: 'Sample post content about politics.' },
                { date: '2023-10-12', content: 'Another sample post discussing current events.' }
            ],
            contacts: {
                email: `${influencerId}@example.com`,
                twitter: influencerId === 'inf1' ? '@alexmedia' : 
                         influencerId === 'inf2' ? '@sarahbroadcast' :
                         influencerId === 'inf3' ? '@mikereporter' :
                         influencerId === 'inf4' ? '@taylorinf' : '@unknown',
                phone: '555-123-4567'
            }
        };
        
        showInfluencerProfile(mockInfluencer);
    }, 300);
}

// Show detailed influencer profile
function showInfluencerProfile(influencer) {
    // Store current
    currentInfluencer = influencer;
    // Hide search view, show detail view
    if (influencerView) influencerView.style.display = 'none';
    if (influencerDetailView) influencerDetailView.style.display = 'flex';
    // Reset to profile tab
    showTab('profile');
    // Populate profile tab
    const detailContent = document.getElementById('influencer-detail-content');
    if (detailContent) {
        detailContent.innerHTML = `
            <h2>${influencer.name}</h2>
            <p>Platform: ${influencer.platform}</p>
            <p>Outlet: ${influencer.outlet}</p>
            <p>Followers: ${influencer.followers}</p>
            <p>${influencer.bio}</p>
        `;
    }
    // Populate contacts tab
    populateContactTab(influencer);
}

// Populate Contacts Tab
function populateContactTab(influencer) {
    const contactDetails = document.getElementById('influencer-contact-details');
    if (!contactDetails) return;
    let html = '';
    if (influencer.contacts.email) html += `<p>Email: ${influencer.contacts.email}</p>`;
    if (influencer.contacts.twitter) html += `<p>Twitter: ${influencer.contacts.twitter}</p>`;
    if (influencer.contacts.phone) html += `<p>Phone: ${influencer.contacts.phone}</p>`;
    contactDetails.innerHTML = html;
}

// Show specific tab
function showTab(tabName) {
    document.querySelectorAll('#influencer-detail .tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('#influencer-detail .tab-content').forEach(c => c.classList.remove('active'));
    document.querySelector(`#influencer-detail .tab-button[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Hide the detail view
function hideDetail() {
    document.getElementById('influencers-container').style.display = 'block';
    influencerDetailView.style.display = 'none';
}

// Export the module for main.js to use
window.influencerView = {
    init,
    show: function() {
        influencerView.style.display = 'block';
    },
    hide: function() {
        influencerView.style.display = 'none';
    }
}; 