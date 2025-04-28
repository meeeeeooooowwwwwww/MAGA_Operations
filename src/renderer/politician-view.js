// Imports
// const { ipcRenderer } = require('electron');
// These requires aren't available in contextIsolation mode
// const fs = require('fs');
// const path = require('path');

// Declare DOM element variables - will be assigned in DOMContentLoaded
let searchInput = null;
let politiciansList = null;
let welcomeView = null;
let profileView = null;
let claimEvaluationView = null;
let resourcesView = null;
let profileName = null;
let profileMeta = null;
let contactInfo = null;
let bioText = null;
let officesInfo = null;
let socialLinks = null;
let latestTweet = null;
let fetchTweetBtn = null;
let analyzeTweetBtn = null;
let backToSearchBtn = null;
let tweetAnalysisSection = null;
let analysisList = null;
let aiResponse = null;
let cardTabs = null; // Will be assigned NodeList
let tabContents = null; // Will be assigned NodeList
let appTitle = null;
let navHomeBtn = null;
let navResourcesBtn = null;
let articleList = null;
let articleListContainer = null;
let articleContentContainer = null;
let articleTitle = null;
let articleSummary = null;
let backToArticlesBtn = null;
let aiClassification = null;
let aiSummary = null;
let aiEvaluation = null;
let aiFinancialConnection = null;
let aiLegalRelevanceContainer = null;
let aiLegalRelevance = null;
let aiSupportiveResponse = null;
let aiCriticalResponse = null;
let supportiveResponseActions = null;
let criticalResponseActions = null;
let findTargetBtn = null;

// NEW: Report elements
let analysisActions = null;
let reportOutputArea = null;
let reportOutputContent = null;
let closeReportBtn = null;

// NEW: Actions of the Day elements
let navActionsBtn = null;
let actionsView = null;
let commandBriefInput = null;
let processBriefBtn = null;
let actionItemsDisplay = null;

// NEW: Sidebar Message Generator Buttons
let messageGeneratorActions = null; // Container
// Individual buttons (add more as needed)
let generateSocialBtn = null;
let generateEmailBtn = null;
let generateArticleBtn = null;
let generateLetterBtn = null;
let generatePressReleaseBtn = null;
let generateSpeechSnippetBtn = null;

// Global data
let allPoliticians = [];
let currentPolitician = null;
let allArticles = []; // To store scraped article data
let latestCommandBriefContext = { actions: [], themes: [], raw: '' }; // Store parsed brief data
let debounceTimer;

// Paths (using relative path instead of Node.js path module)
// const WARROOM_DATA_PATH = path.join(__dirname, '..', '..', 'data', 'warroom-scraped-content.json');
const WARROOM_DATA_PATH = '../data/warroom-scraped-content.json'; // Relative path - we're not using this anyway

// Load politician data when app starts
document.addEventListener('DOMContentLoaded', () => {
    console.log('[politician-view.js] DOMContentLoaded event fired');
    
    // DEBUG: Check if politician-search-input exists in DOM
    const searchInputDebug = document.getElementById('politician-search-input');
    console.log('DEBUG - Search input exists:', !!searchInputDebug, searchInputDebug);
    
    // Try querying with different methods as well to debug
    const searchInputByQuerySelector = document.querySelector('#politician-search-input');
    console.log('DEBUG - Search input by querySelector:', !!searchInputByQuerySelector);
    
    // Log all inputs in the document for debugging
    const allInputs = document.querySelectorAll('input');
    console.log('DEBUG - All inputs in document:', allInputs.length, allInputs);
    
    // Log the politician-search-container element
    const searchContainer = document.getElementById('politician-search-container');  
    console.log('DEBUG - Search container exists:', !!searchContainer, searchContainer);

    // Assign DOM Elements now that the DOM is loaded
    searchInput = document.getElementById('politician-search-input');
    politiciansList = document.getElementById('politicians-list');
    welcomeView = document.getElementById('welcome-view');
    profileView = document.getElementById('profile-view');
    claimEvaluationView = document.getElementById('claim-evaluation-view');
    resourcesView = document.getElementById('resources-view');
    profileName = document.getElementById('profile-name');
    profileMeta = document.getElementById('profile-meta');
    contactInfo = document.getElementById('contact-info');
    bioText = document.getElementById('bio-text');
    officesInfo = document.getElementById('offices-info');
    socialLinks = document.getElementById('social-links');
    latestTweet = document.getElementById('latest-tweet');
    fetchTweetBtn = document.getElementById('fetch-tweet-btn');
    analyzeTweetBtn = document.getElementById('analyze-tweet-btn');
    backToSearchBtn = document.getElementById('back-to-search-btn');
    tweetAnalysisSection = document.getElementById('tweet-analysis-section');
    analysisList = document.getElementById('analysis-list');
    aiResponse = document.getElementById('ai-response');
    cardTabs = document.querySelectorAll('.card-tab');
    tabContents = document.querySelectorAll('.tab-content');
    appTitle = document.querySelector('.app-title');
    navHomeBtn = document.getElementById('nav-home-btn');
    navResourcesBtn = document.getElementById('nav-resources-btn');
    articleList = document.getElementById('article-list');
    articleListContainer = document.querySelector('.article-list-container');
    articleContentContainer = document.getElementById('article-content-container');
    articleTitle = document.getElementById('article-title');
    articleSummary = document.getElementById('article-summary');
    backToArticlesBtn = document.getElementById('back-to-articles-btn');
    aiClassification = document.getElementById('ai-classification');
    aiSummary = document.getElementById('ai-summary');
    aiEvaluation = document.getElementById('ai-evaluation');
    aiFinancialConnection = document.getElementById('ai-financial-connection');
    aiLegalRelevanceContainer = document.getElementById('ai-legal-relevance-container');
    aiLegalRelevance = document.getElementById('ai-legal-relevance');
    aiSupportiveResponse = document.getElementById('ai-supportive-response');
    aiCriticalResponse = document.getElementById('ai-critical-response');
    supportiveResponseActions = document.getElementById('supportive-response-actions');
    criticalResponseActions = document.getElementById('critical-response-actions');
    findTargetBtn = document.getElementById('find-target-btn');
    analysisActions = document.getElementById('analysis-actions');
    reportOutputArea = document.getElementById('report-output-area');
    reportOutputContent = document.getElementById('report-output-content');
    closeReportBtn = document.getElementById('close-report-btn');
    navActionsBtn = document.getElementById('nav-actions-btn');
    actionsView = document.getElementById('actions-view');
    commandBriefInput = document.getElementById('command-brief-input');
    processBriefBtn = document.getElementById('process-brief-btn');
    actionItemsDisplay = document.getElementById('action-items-display');
    messageGeneratorActions = document.getElementById('message-generator-actions');
    generateSocialBtn = document.getElementById('generate-social-btn');
    generateEmailBtn = document.getElementById('generate-email-btn');
    generateArticleBtn = document.getElementById('generate-article-btn');
    generateLetterBtn = document.getElementById('generate-letter-btn');
    generatePressReleaseBtn = document.getElementById('generate-press-release-btn');
    generateSpeechSnippetBtn = document.getElementById('generate-speech-snippet-btn');
    
    // Debug: Log browserWindow object existence 
    console.log('Window electronAPI available:', !!window.electronAPI);
    if (window.electronAPI) {
        console.log('Available electronAPI methods:', Object.keys(window.electronAPI));
        
        // Run diagnostics to test IPC communication and database connection
        window.appUtils.runDiagnostics()
            .then(diagnosticInfo => {
                console.log('Electron diagnostics:', diagnosticInfo);
                if (diagnosticInfo.dbTest?.success) {
                    console.log(`Database connection test successful. Found ${diagnosticInfo.dbTest.count} politicians.`);
                } else {
                    console.error(`Database connection test failed: ${diagnosticInfo.dbTest?.error || 'Unknown error'}`);
                }
            })
            .catch(error => {
                console.error('Diagnostics failed:', error);
            });
    } else {
        console.error('window.electronAPI is not available. IPC communication will not work.');
    }
    
    // Also check for appUtils availability
    if (!window.appUtils) {
        console.error('window.appUtils is not available. utils.js might not be properly loaded.');
        return; // Stop execution if appUtils is not available
    }
    
    // Initialize standard sidebar navigation
    window.appUtils.initializeSidebarNavigation('explore-politicians'); // Pass current page identifier

    loadPoliticians();
    // loadArticles(); // Comment out or replace if fs/path removed
    setupEventListeners(); // Call AFTER assigning elements
    // Hide politicians list initially
    politiciansList.style.display = 'none';
    // Start on home view
    showView('welcome-view');
    
    // Warroom Action button
    const checkWarroomBtn = document.getElementById('check-warroom-action-btn');
    if (checkWarroomBtn) {
        checkWarroomBtn.addEventListener('click', loadWarRoomCampaigns);
    }
});

// Load politicians from the database
function loadPoliticians() {
    console.log('Attempting to load politicians from database...');
    
    // Show loading indicator or message if available
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) loadingIndicator.style.display = 'flex';
    
    // Use the utility function for safe IPC calls
    window.appUtils.safeIpcCall(
        'get-politicians',
        null,
        (politicians) => {
            console.log(`Received politicians data: ${politicians ? politicians.length : 0} records`);
            
            if (!politicians || politicians.length === 0) {
                console.warn('No politicians data received from database');
                allPoliticians = []; // Ensure it's at least an empty array
                
                // Check if searchInput exists before accessing value
                if (searchInput && searchInput.value.trim() !== '') { 
                    politiciansList.innerHTML = '<li class="politician-item no-results">No politician data available in database.</li>';
                    politiciansList.style.display = 'block';
                }
            } else {
                allPoliticians = politicians;
                console.log(`Successfully loaded ${allPoliticians.length} politicians.`);
                
                // Debug: log the first few politicians to verify structure
                console.log('First few politicians:', allPoliticians.slice(0, 3));
                
                // Check if searchInput exists before accessing value
                if (searchInput && searchInput.value.trim() !== '') { 
                    applySearch();
                }
            }
            
            // Hide loading indicator
            if (loadingIndicator) loadingIndicator.style.display = 'none';
        },
        (error) => {
            console.error('Error loading politicians:', error);
            allPoliticians = []; // Ensure it's at least an empty array
            
            // Check if searchInput exists before accessing value
            if (searchInput && searchInput.value.trim() !== '') { 
                politiciansList.innerHTML = `<li class="politician-item no-results">Error loading politician data: ${error.message || 'Unknown error'}</li>`;
                politiciansList.style.display = 'block';
            }
            
            // Hide loading indicator
            if (loadingIndicator) loadingIndicator.style.display = 'none';
        }
    );
}

// Load articles from scraped JSON file
function loadArticles() {
    console.warn('loadArticles: Direct file system access disabled in contextIsolation mode');
    console.log('To load articles, we need to use IPC to request this data from the main process');
    
    // TODO: Implement proper IPC call to get articles data
    // window.electronAPI.invoke('get-articles').then(articles => {
    //     allArticles = articles || [];
    //     renderArticleList();
    // }).catch(error => {
    //     console.error('Error loading articles:', error);
    //     allArticles = [];
    //     renderArticleList();
    // });
    
    // For now, use empty array
    allArticles = []; 
    renderArticleList();
}

// Function to show a specific view and hide others
function showView(viewId) {
    const views = [welcomeView, /* profileView REMOVED */, claimEvaluationView, resourcesView, actionsView];
    views.forEach(view => {
        if (!view) return;
        if (view.id === viewId) {
            view.style.display = 'flex'; 
        } else {
            view.style.display = 'none';
        }
    });
    
    // Update nav button active states
    [navHomeBtn, navResourcesBtn, navActionsBtn].forEach(btn => btn?.classList.remove('active')); // Add null check
    if (viewId === 'welcome-view' || viewId === 'profile-view' || viewId === 'claim-evaluation-view') {
        navHomeBtn?.classList.add('active');
    } else if (viewId === 'resources-view') {
        navResourcesBtn?.classList.add('active');
    } else if (viewId === 'actions-view') {
        navActionsBtn?.classList.add('active');
    }
    
    // If showing resources view, render the list
    if (viewId === 'resources-view') {
        renderArticleList();
    }
}

// Render politicians list based on search
function renderPoliticiansList(politicians) {
    console.log(`renderPoliticiansList called with ${politicians ? politicians.length : 0} targets.`);
    // Clear the current list
    politiciansList.innerHTML = '';
    
    if (!politicians || politicians.length === 0) {
        const noResults = document.createElement('li');
        noResults.classList.add('politician-item', 'no-results');
        noResults.innerHTML = '<i class="fas fa-search"></i> No targets found matching your search.';
        politiciansList.appendChild(noResults);
        return;
    }
    
    // Create a list item for each politician
    politicians.forEach(politician => {
        const li = document.createElement('li');
        li.classList.add('politician-item');
        li.setAttribute('data-id', politician.id || '');
        
        // Create party indicator based on party affiliation
        let partyClass = 'independent';
        let partyLetter = 'I';
        
        if (politician.party && politician.party.toLowerCase().includes('republican')) {
            partyClass = 'republican';
            partyLetter = 'R';
        } else if (politician.party && politician.party.toLowerCase().includes('democrat')) {
            partyClass = 'democrat';
            partyLetter = 'D';
        }
        
        // Build the HTML content
        let html = `
            <div class="politician-info">
                <div class="politician-name">${politician.name || 'Unknown'}</div>
                <div class="politician-details">
                    <span class="politician-title">${politician.role || 'Target'}</span>
                    <span class="politician-location">${politician.state || ''} ${politician.district || ''}</span>
                </div>
            </div>
            <div class="politician-party ${partyClass}" data-tooltip="${partyClass === 'republican' ? 'Republican' : partyClass === 'democrat' ? 'Democrat' : 'Independent'}">${partyLetter}</div>
        `;
        
        li.innerHTML = html;
        
        // Add click event
        li.addEventListener('click', function() {
            const politicianId = this.dataset.id;
            getPoliticianDetails(politicianId);
        });
        
        politiciansList.appendChild(li);
    });
}

// Get politician details and show profile
function getPoliticianDetails(politicianId) {
    if (!politicianId) {
        console.error('No politician ID provided');
        return;
    }
    
    console.log(`Target clicked with ID: ${politicianId}`);
    
    // Get politician data from DB using the existing IPC handler
    window.appUtils.safeIpcCall(
        'get-politician',
        politicianId,
        (politician) => {
            if (politician) {
                console.log(`Retrieved target data:`, politician);
                showPoliticianProfile(politician);
            } else {
                console.error(`Target with ID ${politicianId} not found`);
                const detailContent = document.getElementById('detail-content');
                if (detailContent) {
                    detailContent.innerHTML = `
                        <div class="error-message">
                            <i class="fas fa-exclamation-circle"></i>
                            Error: Target with ID ${politicianId} not found
                        </div>
                    `;
                }
                
                // Show welcome view again
                if (welcomeView) welcomeView.style.display = 'block';

                // Show list, hide detail view
                const politicianListContainer = document.getElementById('politicians-container');
                const politicianDetailView = document.getElementById('politician-detail');
                
                if (politicianListContainer) politicianListContainer.style.display = 'block';
                if (politicianDetailView) politicianDetailView.style.display = 'none';
            }
        },
        (error) => {
            console.error(`Error retrieving target with ID ${politicianId}:`, error);
            const detailContent = document.getElementById('detail-content');
            if (detailContent) {
                detailContent.innerHTML = `
                    <div class="error-message">
                        <i class="fas fa-exclamation-circle"></i>
                        Error loading target data: ${error.message || 'Unknown error'}
                    </div>
                `;
            }
            
            // Show welcome view again
            if (welcomeView) welcomeView.style.display = 'block';

            // Show list, hide detail view
            const politicianListContainer = document.getElementById('politicians-container');
            const politicianDetailView = document.getElementById('politician-detail');
            
            if (politicianListContainer) politicianListContainer.style.display = 'block';
            if (politicianDetailView) politicianDetailView.style.display = 'none';
        }
    );
}

// Render the list of articles/headings
function renderArticleList() {
    articleList.innerHTML = ''; // Clear existing list
    articleListContainer.style.display = 'block';
    articleContentContainer.style.display = 'none';
    
    if (allArticles.length === 0) {
        const noArticles = document.createElement('li');
        noArticles.classList.add('no-results'); // Reuse style
        noArticles.innerHTML = '<i class="fas fa-info-circle"></i> No articles found';
        articleList.appendChild(noArticles);
        return;
    }
    
    allArticles.forEach((article, index) => {
        const listItem = document.createElement('li');
        listItem.classList.add('article-item');
        listItem.dataset.index = index; // Use index to retrieve later
        
        listItem.innerHTML = `
            <h4>${article.text}</h4>
            <p>Source: warroom.org (${article.tag})</p>
        `;
        
        listItem.addEventListener('click', () => showArticleContent(index));
        articleList.appendChild(listItem);
    });
}

// Show the content/summary for a selected article
function showArticleContent(index) {
    const article = allArticles[index];
    if (!article) return;
    
    articleTitle.textContent = article.text;
    // Placeholder for AI summary - for now, just show a message
    articleSummary.textContent = `AI summary for "${article.text}" will be generated here.`; 
    
    articleListContainer.style.display = 'none';
    articleContentContainer.style.display = 'block';
}

// Show the claim evaluation view when no politician is selected
function showClaimEvaluationPrompt() {
    // This function seems intended for when NO politician is selected.
    // We might need a different function or view for AI analysis of the CURRENT politician.
    // For now, let's adapt the existing profile view's analysis section.
    console.log('showClaimEvaluationPrompt called - intended for no selection scenario.');
    // Let's reuse the main welcome view for now if no politician selected.
    showMainWelcome(); 
}

// Renamed function - initiates the search state
function initiateTargetSearch() {
    console.log('Find Target Politician button clicked - ensuring search is ready.');
    // Ensure welcome view is visible (might be redundant if already there)
    showView('welcome-view'); 
    // Focus the main search input
    searchInput.focus();
    // Make sure the list container is visible (applySearch will handle content)
    // We don't necessarily want to show it empty, applySearch handles visibility based on input
    // politiciansList.style.display = 'block'; 
}

// Show the claim evaluation view when no politician is selected
function showClaimEvaluationPrompt() {
    // This function seems intended for when NO politician is selected.
    // We might need a different function or view for AI analysis of the CURRENT politician.
    // For now, let's adapt the existing profile view's analysis section.
    console.log('showClaimEvaluationPrompt called - intended for no selection scenario.');
    // Let's reuse the main welcome view for now if no politician selected.
    showMainWelcome(); 
}

// Evaluate claim - **NOW TRIGGERS AI ANALYSIS**
function evaluateClaim() {
    if (!currentPolitician) {
        // This button should ideally be disabled if no politician is selected
        // Or we can fetch the tweet first if it hasn't been fetched?
        console.warn('Evaluate Claim button clicked, but no politician selected.');
        showMainWelcome(); // Go back to search
        return;
    }

    // Instead of navigating, trigger the AI analysis function
    console.log('Evaluate Claim button clicked for politician:', currentPolitician.name, '- Triggering AI Analysis.');
    analyzeLatestTweetWithAI();
}

// Show the main welcome/search view
function showMainWelcome() {
    showView('welcome-view'); // Use the new showView function
    // Clear search and hide list
    searchInput.value = '';
    politiciansList.style.display = 'none';
}

// NEW: Request Analysis Report Function
function requestAnalysisReport(reportType) {
    if (!currentPolitician) {
        console.error('Cannot request report: No current politician selected.');
        reportOutputContent.textContent = 'Error: No politician selected.';
        reportOutputArea.style.display = 'block';
        return;
    }

    const bioguideId = currentPolitician.id; // Assuming 'id' holds the bioguide_id
    const politicianName = currentPolitician.name;
    const friendlyReportName = reportType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()); // Format for display

    console.log(`Requesting report type: ${reportType} for politician: ${politicianName} (ID: ${bioguideId})`);

    reportOutputContent.textContent = `Generating ${friendlyReportName} report for ${politicianName}...`;
    reportOutputArea.style.display = 'block';

    // Simulate AI processing delay
    setTimeout(() => {
        // This would need a new IPC handler in main.js 
        // and potentially call a Python script or AI service
        console.warn(`IPC handler for 'generate-report' (type: ${reportType}) not implemented yet.`);
        // const report = await window.electronAPI.invoke('generate-report', currentPolitician.id, reportType);
        // ... Mock response for now ...
        const report = `Mock report for ${currentPolitician.name} - Type: ${reportType}\n\nDetails would go here.`;
        // ...

        reportOutputContent.textContent = report;
        console.log(`Simulated report generated for ${reportType} with updated tone.`);

        // TODO: Replace simulation with actual IPC call to main process
        // Example:
        // window.electronAPI.send('request-analysis-report', { bioguideId, reportType });
        // Then listen for 'analysis-report-result' event

    }, 1500); // Simulate 1.5 seconds processing time
}

// NEW: Parse email content for actions and themes
function parseEmailForActions(emailContent) {
    console.log('Parsing email content...');
    latestCommandBriefContext.raw = emailContent; // Store raw content
    latestCommandBriefContext.actions = [];
    latestCommandBriefContext.themes = [];

    // --- Placeholder Parsing Logic --- 
    // This needs to be significantly more sophisticated based on actual email formats.
    // Example: Look for specific phrases or patterns.
    const potentialActions = [];
    const potentialThemes = [];

    // Simple example: Look for lines mentioning bills (H.R. XXXX, S. XXXX)
    const billRegex = /(H\.R\.|S\.)\s*\d+/gi;
    const billMatches = emailContent.match(billRegex);
    if (billMatches) {
        billMatches.forEach(bill => {
            potentialActions.push({
                type: 'call',
                target: bill.trim(),
                instruction: `Action regarding ${bill.trim()}`, // Placeholder instruction
                points: '[Extract nearby sentences as talking points]' // Placeholder points
            });
            potentialThemes.push(`Bill: ${bill.trim()}`); // Add bill as a theme
        });
    }

    // Simple example: Look for common keywords
    if (emailContent.toLowerCase().includes('border')) potentialThemes.push('Border Security');
    if (emailContent.toLowerCase().includes('vatican')) potentialThemes.push('Vatican Issues');
    if (emailContent.toLowerCase().includes('ccp') || emailContent.toLowerCase().includes('china')) potentialThemes.push('CCP/China Influence');
    if (emailContent.toLowerCase().includes('election')) potentialThemes.push('Election Integrity');
    if (emailContent.toLowerCase().includes('economy')) potentialThemes.push('Economy');
    // Add more keyword checks...
    
    // --- End Placeholder Parsing Logic ---
    
    latestCommandBriefContext.actions = potentialActions;
    // Deduplicate themes
    latestCommandBriefContext.themes = [...new Set(potentialThemes)]; 

    console.log('Parsed Brief Context:', latestCommandBriefContext);
    displayActions(latestCommandBriefContext.actions);
}

// NEW: Display extracted actions
function displayActions(actionsArray) {
    actionItemsDisplay.innerHTML = ''; // Clear previous content

    if (!actionsArray || actionsArray.length === 0) {
        actionItemsDisplay.innerHTML = '<p class="no-actions-message">No specific actions extracted from the provided text.</p>';
        return;
    }

    actionsArray.forEach(action => {
        const actionDiv = document.createElement('div');
        actionDiv.classList.add('action-item');

        let actionHTML = `<h4>${action.instruction || 'Action Item'}</h4>`;
        if (action.target) {
            actionHTML += `<p>Target/Subject: ${action.target}</p>`;
        }
        if (action.points) {
            actionHTML += `<p>Potential Talking Points: ${action.points}</p>`;
        }

        // Add Click-to-Call button if applicable
        if (action.type === 'call') {
            // Basic button - logic for finding rep number needs to be added
            actionHTML += `
                <button class="btn btn-sm btn-secondary click-to-call-btn" data-target="${action.target || 'general'}">
                    <i class="fas fa-phone"></i> Click to Call (Requires Rep Selection)
                </button>`;
        }
        // Add other button types (email, donate link?) later

        actionDiv.innerHTML = actionHTML;
        actionItemsDisplay.appendChild(actionDiv);
    });
    
    // Add listener for click-to-call buttons (using delegation)
    actionItemsDisplay.addEventListener('click', handleActionItemClick);

}

// NEW: Handle clicks within the action items display (e.g., click-to-call)
function handleActionItemClick(event) {
    const callButton = event.target.closest('.click-to-call-btn');
    if (callButton) {
        const targetInfo = callButton.dataset.target;
        console.log(`Click-to-call initiated for target: ${targetInfo}`);
        if (currentPolitician && currentPolitician.phone) {
             const telLink = `tel:${currentPolitician.phone.replace(/\D/g, '')}`; // Basic cleanup for tel link
             console.log(`Attempting to open: ${telLink}`);
             // Update button text temporarily
             callButton.innerHTML = `<i class="fas fa-phone"></i> Calling ${currentPolitician.name}...`;
             callButton.disabled = true;
             window.location.href = telLink; // Attempt to initiate call
             // Reset button after a delay
             setTimeout(() => {
                 callButton.innerHTML = `<i class="fas fa-phone"></i> Click to Call ${currentPolitician.name}`;
                 callButton.disabled = false;
             }, 3000);
        } else {
            console.warn('Cannot initiate call: No current politician selected or no phone number available.');
            // Provide feedback to the user
            callButton.innerHTML = `<i class="fas fa-exclamation-circle"></i> Select Rep First!`;
             setTimeout(() => {
                 callButton.innerHTML = `<i class="fas fa-phone"></i> Click to Call (Requires Rep Selection)`;
             }, 2500);
             // Maybe briefly highlight the search bar or sidebar?
        }
    }
}

// NEW: Generate Campaign Message (Placeholder)
function generateCampaignMessage(messageType) {
    console.log(`Request to generate message type: ${messageType}`);

    if (!currentPolitician) {
        console.warn('Cannot generate message: No politician selected.');
        // TODO: Provide user feedback (e.g., alert, message in sidebar/modal)
        showModal('Error', 'Please select a politician from the search results first.');
        return;
    }

    const context = {
        politicianName: currentPolitician.name,
        politicianParty: currentPolitician.party,
        politicianState: currentPolitician.state,
        briefThemes: latestCommandBriefContext.themes,
        briefActions: latestCommandBriefContext.actions
    };

    console.log('Using context for generation:', context);
    
    // TODO: Display generating message (modal or dedicated panel?)
    showModal('Generating Message', `Generating ${messageType} for ${context.politicianName}...<br>WarRoom Focus: ${context.briefThemes.join(', ') || 'None specified'}`);

    // Simulate AI generation delay
    setTimeout(() => {
        let simulatedOutput = `--- Simulated ${messageType.toUpperCase()} Draft ---\n`;
        simulatedOutput += `To: ${messageType === 'email' || messageType === 'letter' ? '[Recipient List/Address]' : 'Public'}\n`;
        simulatedOutput += `From: MAGA Ops (For Campaign Use)\n`;
        simulatedOutput += `Subject: ${messageType !== 'social' ? `Regarding ${context.politicianName} and ${context.briefThemes[0] || 'Current Issues'}` : 'N/A'}\n\n`;

        simulatedOutput += `**(Cheeky & Authoritative Tone)**\n`;
        simulatedOutput += `Friends, Patriots! Let's talk about ${context.politicianName} (${context.politicianParty}-${context.politicianState}). `; 
        if (context.briefThemes.length > 0) {
            simulatedOutput += `Right now, the vital issue is **${context.briefThemes[0]}**, just like the WarRoom Command Brief highlighted. `;
        }
        simulatedOutput += `[Insert AI-generated content here, tailored to ${messageType}, incorporating politician details and brief context, avoiding prohibited content.]\n\n`;
        if (context.briefActions.length > 0) {
            simulatedOutput += `Action Item Ref: Consider the call to action regarding ${context.briefActions[0].target || 'key objectives'}.\n`;
        }
        simulatedOutput += `**(End Draft - Requires Review & Edit)**`;

        console.log('Simulated Output:', simulatedOutput);
        // TODO: Display final output (modal or dedicated panel?)
        showModal(`${messageType.toUpperCase()} Draft`, simulatedOutput.replace(/\n/g, '<br>'));

    }, 1500);
}

// Setup event listeners
function setupEventListeners() {
    console.log('Setting up event listeners');
    
    // Add null check for searchInput
    if (searchInput) { 
        // Search input - when user types
        searchInput.addEventListener('input', function() {
            if (this.value.trim().length > 0) {
                applySearch();
            } else {
                if (politiciansList) politiciansList.style.display = 'none';
            }
        });
    } else {
        console.error('Search input element not found during setupEventListeners');
    }
    
    // Back button in detail view - return to list
    const backButton = document.getElementById('back-button');
    if (backButton) {
        backButton.addEventListener('click', function() {
            // Show welcome view again
            if (welcomeView) welcomeView.style.display = 'block';

            // Show list, hide detail view
            const politicianListContainer = document.getElementById('politicians-container');
            const politicianDetailView = document.getElementById('politician-detail');
            
            if (politicianListContainer) politicianListContainer.style.display = 'block';
            if (politicianDetailView) politicianDetailView.style.display = 'none';
            
            // Clear current politician
            currentPolitician = null;
            
            // Add null check
            if (searchInput && searchInput.value.trim().length > 0) { 
                if (politiciansList) politiciansList.style.display = 'block';
            }
        });
    }

    // Modal close button and overlay
    const modalCloseBtn = document.querySelector('#output-modal .modal-close-btn');
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', hideModal);
    }
    
    const modalOverlay = document.getElementById('output-modal-overlay');
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function(e) {
            if (e.target === modalOverlay) {
                hideModal();
            }
        });
    }

    // Card tabs listener
    if (cardTabs) { // Add null check for NodeList
        cardTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                showTab(tab.dataset.tab);
            });
        });
    } else {
        console.error('Card tabs not found during setupEventListeners');
    }

    // Fetch tweet button listener
    if (fetchTweetBtn) {
        fetchTweetBtn.addEventListener('click', fetchLatestTweet);
    }

    // Analyze tweet button listener
    if (analyzeTweetBtn) {
        analyzeTweetBtn.addEventListener('click', analyzeLatestTweetWithAI);
    }

    // App title click listener (go home)
    if (appTitle) {
        appTitle.addEventListener('click', () => {
            showView('welcome-view');
            if (politiciansList) politiciansList.style.display = 'none'; 
            if (searchInput) searchInput.value = '';
        });
    }

    // Navigation buttons
    if (navHomeBtn) { 
        navHomeBtn.addEventListener('click', () => {
            // Go to profile if available, else welcome
            if (currentPolitician) {
                showView('profile-view');
            } else {
                showView('welcome-view');
            }
            if (politiciansList) politiciansList.style.display = 'none'; // Hide list
            if (searchInput) searchInput.value = ''; // Clear search
        });
    }

    if (navResourcesBtn) { 
        navResourcesBtn.addEventListener('click', () => {
            showView('resources-view');
            if (politiciansList) politiciansList.style.display = 'none'; // Hide list
            if (searchInput) searchInput.value = ''; // Clear search
        });
    }
    
    // NEW: Actions Nav Button
    if (navActionsBtn) { 
        navActionsBtn.addEventListener('click', () => {
            showView('actions-view');
            if (politiciansList) politiciansList.style.display = 'none'; // Hide list
            if (searchInput) searchInput.value = ''; // Clear search
        });
    }

    // Resource Article list click listener
    if (articleList) { 
        articleList.addEventListener('click', (event) => {
            const articleItem = event.target.closest('.article-item');
            if (articleItem && articleItem.dataset.index) {
                showArticleContent(parseInt(articleItem.dataset.index, 10));
            }
        });
    }

    // Back to articles button
    if (backToArticlesBtn) { 
        backToArticlesBtn.addEventListener('click', () => {
            if (articleContentContainer) articleContentContainer.style.display = 'none';
            if (articleListContainer) articleListContainer.style.display = 'block';
        });
    }

    // Find Target / Begin Campaign button listener
    if (findTargetBtn) {
        findTargetBtn.addEventListener('click', () => {
            // TODO: Implement campaign workflow start
            console.log('Begin Campaign clicked - initiate workflow');
            // For now, maybe just focus the search?
            showView('welcome-view'); // Stay on welcome or switch to a dedicated view
            if (searchInput) searchInput.focus();
            // Or initiate campaign step 1
            // showView('campaign-workflow'); // Need to implement campaign view logic
            // showCampaignStep(1);
        });
    }

    // Back to search (from claim eval placeholder)
    if (backToSearchBtn) {
        backToSearchBtn.addEventListener('click', () => {
            showView('welcome-view');
            if (searchInput) searchInput.focus();
        });
    }

    // Copy response buttons (using delegation on AI response area)
    if (aiResponse) { 
        aiResponse.addEventListener('click', (event) => {
            const copyButton = event.target.closest('.copy-btn');
            if (copyButton) {
                const parentResponseOption = copyButton.closest('.response-option');
                if (parentResponseOption) {
                    const textarea = parentResponseOption.querySelector('textarea');
                    if (textarea && textarea.value) {
                        navigator.clipboard.writeText(textarea.value)
                            .then(() => {
                                console.log('Response copied to clipboard');
                                // Optional: Show brief confirmation
                                const originalText = copyButton.innerHTML;
                                copyButton.innerHTML = '<i class="fas fa-check"></i> Copied!';
                                setTimeout(() => { copyButton.innerHTML = originalText; }, 1500);
                            })
                            .catch(err => {
                                console.error('Failed to copy text: ', err);
                            });
                    }
                }
            }
        });
    }

    // NEW: Report generation button listener (delegated)
    if (analysisActions) {
        analysisActions.addEventListener('click', (event) => {
            const reportButton = event.target.closest('.report-btn');
            if (reportButton && reportButton.dataset.reportType) {
                requestAnalysisReport(reportButton.dataset.reportType);
            }
        });
    }

    // NEW: Close report button listener
    if (closeReportBtn) {
        closeReportBtn.addEventListener('click', () => {
            if (reportOutputArea) reportOutputArea.style.display = 'none';
            if (reportOutputContent) reportOutputContent.textContent = ''; // Clear content
        });
    }

    // NEW: Process Command Brief Button
    if (processBriefBtn) { 
        processBriefBtn.addEventListener('click', () => {
            if (commandBriefInput && actionItemsDisplay) { 
                const emailContent = commandBriefInput.value;
                if (emailContent.trim()) {
                    parseEmailForActions(emailContent);
                } else {
                    actionItemsDisplay.innerHTML = '<p class="no-actions-message">Please paste email content into the text area above first.</p>';
                }
            }
        });
    }

    // NEW: Sidebar Message Generator Button Listeners (using delegation is better if adding/removing buttons)
    // Simple direct listeners for now:
    if (generateSocialBtn) generateSocialBtn.addEventListener('click', () => generateCampaignMessage('social'));
    if (generateEmailBtn) generateEmailBtn.addEventListener('click', () => generateCampaignMessage('email'));
    if (generateArticleBtn) generateArticleBtn.addEventListener('click', () => generateCampaignMessage('article'));
    if (generateLetterBtn) generateLetterBtn.addEventListener('click', () => generateCampaignMessage('letter'));
    if (generatePressReleaseBtn) generatePressReleaseBtn.addEventListener('click', () => generateCampaignMessage('press-release'));
    if (generateSpeechSnippetBtn) generateSpeechSnippetBtn.addEventListener('click', () => generateCampaignMessage('speech-snippet'));

    // Add more listeners as needed

    // Setup tab listeners
    setupTabListeners();

    // Politician list click listener (using event delegation)
    if (politiciansList) { // Add null check
        politiciansList.addEventListener('click', (event) => {
            const listItem = event.target.closest('.politician-item');
            if (listItem && listItem.dataset.id) {
                const politicianId = listItem.dataset.id;
                getPoliticianDetails(politicianId);
            }
        });
    } else {
        console.error('Politicians list element not found during setupEventListeners');
    }
}

// IPC Listeners (Example - adapt as needed)
/*
window.electronAPI.on('analysis-report-result', (event, { reportType, data, error }) => {
    if (error) {
        console.error(`Error generating report (${reportType}):`, error);
        reportOutputContent.textContent = `Error generating report: ${error}`;
    } else {
        console.log(`Received report result for ${reportType}:`, data);
        // Format and display the 'data' object appropriately
        reportOutputContent.textContent = JSON.stringify(data, null, 2); // Simple JSON display for now
    }
});
*/

// Utility functions (if any remain)

// IPC events
window.electronAPI.on('app:data-updated', () => {
    loadPoliticians();
});

// Show a modal with title and content
function showModal(title, content) {
    const modalOverlay = document.getElementById('output-modal-overlay');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');
    
    // Set modal content
    modalTitle.textContent = title;
    modalContent.innerHTML = content;
    
    // Show the modal
    modalOverlay.classList.add('visible');
}

// Hide the modal
function hideModal() {
    const modalOverlay = document.getElementById('output-modal-overlay');
    // Hide the modal
    modalOverlay.classList.remove('visible');
}

/**
 * Loads and displays the latest WarRoom campaigns
 */
function loadWarRoomCampaigns() {
    // This would normally fetch data from an API
    // For now, we'll use mock data
    const warRoomCampaigns = [
        {
            id: 'WR-2023-001',
            title: 'Mid-Term Election Push',
            status: 'Active',
            participants: 1423,
            created: '2023-08-15'
        },
        {
            id: 'WR-2023-002',
            title: 'Battleground States Initiative',
            status: 'Active',
            participants: 892,
            created: '2023-09-02'
        },
        {
            id: 'WR-2023-003',
            title: 'Youth Voter Outreach',
            status: 'Planning',
            participants: 246,
            created: '2023-10-10'
        }
    ];
    
    // Create HTML content for the modal
    let content = `
        <div class="warroom-campaigns">
            <p>The following campaigns are currently active in the WarRoom. Click on any campaign to join or get more information.</p>
            <table class="warroom-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Campaign</th>
                        <th>Status</th>
                        <th>Participants</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add rows for each campaign
    warRoomCampaigns.forEach(campaign => {
        content += `
            <tr class="warroom-campaign-row" data-id="${campaign.id}">
                <td>${campaign.id}</td>
                <td>${campaign.title}</td>
                <td><span class="status-badge status-${campaign.status.toLowerCase()}">${campaign.status}</span></td>
                <td>${campaign.participants}</td>
                <td>${campaign.date}</td>
            </tr>
        `;
    });
    
    content += `
                </tbody>
            </table>
            <div class="warroom-action-buttons">
                <button class="btn primary-btn" id="join-warroom-btn">Join Selected Campaign</button>
                <button class="btn secondary-btn" id="create-warroom-btn">Create New Campaign</button>
            </div>
        </div>
    `;
    
    // Update the modal with the campaigns
    showModal('WarRoom Campaigns', content);
    
    // Add event listeners to the rows for selection
    document.querySelectorAll('.warroom-campaign-row').forEach(row => {
        row.addEventListener('click', () => {
            document.querySelectorAll('.warroom-campaign-row').forEach(r => r.classList.remove('selected'));
            row.classList.add('selected');
        });
    });
    
    // Add event listener for join button
    document.getElementById('join-warroom-btn').addEventListener('click', () => {
        const selectedRow = document.querySelector('.warroom-campaign-row.selected');
        if (selectedRow) {
            const campaignId = selectedRow.getAttribute('data-id');
            const campaignName = selectedRow.querySelector('td:nth-child(2)').textContent;
            showModal('Join Campaign', `You are joining the "${campaignName}" campaign. You will be connected with other participants working toward the same goals.`);
        } else {
            showModal('Selection Required', 'Please select a campaign to join first.');
        }
    });
    
    // Add event listener for create button
    document.getElementById('create-warroom-btn').addEventListener('click', () => {
        showModal('Create Campaign', 'The campaign creation tool will be available in the next update. Stay tuned!');
    });
}

// Handle search
function applySearch() {
    // Debounce search to prevent too many requests
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        // Use direct DOM query each time (more resilient approach)
        const searchInputElement = document.getElementById('politician-search-input'); 
        const politiciansListElement = document.getElementById('politicians-list');
        
        if (!searchInputElement || !politiciansListElement) {
            console.error(`[applySearch] Required elements not found: 
              searchInput=${!!searchInputElement}, 
              politiciansList=${!!politiciansListElement}`);
            return; // Exit early if elements aren't found
        }
        
        const searchTerm = searchInputElement.value.trim();
        
        if (searchTerm.length === 0) {
            politiciansListElement.style.display = 'none';
            return;
        }
        
        // Show loading indicator - USE CORRECT VARIABLE NAME
        const searchIndicator = document.getElementById('politician-search-indicator'); // Get element here
        if (searchIndicator) {
            searchIndicator.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
            searchIndicator.style.display = 'block';
        }
        
        // Log the search attempt
        console.log(`[applySearch] Searching for: "${searchTerm}"`);
        
        // Call the IPC function to search politicians
        window.appUtils.safeIpcCall(
            'search-politicians',
            { searchTerm },
            (results) => {
                // Hide loading indicator
                if (searchIndicator) searchIndicator.style.display = 'none';
                
                console.log(`[applySearch] Got ${results ? results.length : 0} results for "${searchTerm}"`);
                
                // Priority matching: any name part starting with the term
                const termLower = searchTerm.toLowerCase();
                let matches = results.filter(p => {
                    if (!p.name) return false;
                    // Split full name into words and test startsWith
                    return p.name.split(/\s+/).some(part => part.toLowerCase().startsWith(termLower));
                });
                // Fallback to substring match if no part-start matches
                if (matches.length === 0) {
                    matches = results.filter(p => p.name && p.name.toLowerCase().includes(termLower));
                }
                // Limit to first 50 results
                const displayedResults = matches.slice(0, 50);
                // Show results
                renderPoliticiansList(displayedResults);
                politiciansListElement.style.display = 'block';
            },
            (error) => {
                console.error('Error searching politicians:', error);
                // Hide loading indicator on error too
                if (searchIndicator) searchIndicator.style.display = 'none'; 
                politiciansListElement.innerHTML = `
                    <li class="politician-item error">
                        <i class="fas fa-exclamation-triangle"></i>
                        Error searching targets: ${error.message || 'Unknown error'}
                    </li>
                `;
                politiciansListElement.style.display = 'block';
            }
        );
    }, 300); // 300ms debounce
}

// Show detailed politician profile
function showPoliticianProfile(politician) {
    console.log('Showing profile for politician:', politician);
    
    // Save current politician globally
    currentPolitician = politician;
    
    // Switch views - hide politician list, show detail view
    const politicianListContainer = document.getElementById('politicians-container');
    const politicianDetailView = document.getElementById('politician-detail');
    
    // Hide entire welcome view and show detail view
    if (welcomeView) welcomeView.style.display = 'none';
    if (politicianDetailView) politicianDetailView.style.display = 'flex';
    
    // Reset to profile tab when showing a new politician
    switchTab('profile');
    
    // Get the detail content container
    const detailContent = document.getElementById('detail-content');
    if (!detailContent) {
        console.error('Detail content container not found');
        return;
    }
    
    // Get the contact details container
    const contactDetails = document.getElementById('contact-details');
    if (!contactDetails) {
        console.error('Contact details container not found');
        return;
    }
    
    // Determine party class for styling
    let partyClass = 'independent';
    let partyName = 'Independent';
    
    if (politician.party && politician.party.toLowerCase().includes('republican')) {
        partyClass = 'republican';
        partyName = 'Republican';
    } else if (politician.party && politician.party.toLowerCase().includes('democrat')) {
        partyClass = 'democrat';
        partyName = 'Democrat';
    }
    
    // Build the PROFILE tab content
    let profileHtml = `
        <div class="detail-name">${politician.name || 'Unknown'}</div>
        <div class="detail-subtitle">
            <span class="detail-party ${partyClass}">${partyName}</span>
            <span class="detail-role">${politician.role || 'Target'}</span>
            ${politician.state ? `<span class="detail-state">${politician.state}</span>` : ''}
            ${politician.district ? `<span class="detail-district">District ${politician.district}</span>` : ''}
        </div>
        
        <div class="detail-section">
            <h3 class="section-title">Biography</h3>
            <div class="section-content">
                ${politician.biography ? 
                  `<p>${politician.biography}</p>` : 
                  `<div class="empty-state small">
                      <i class="fas fa-info-circle"></i>
                      <p>No biography information available</p>
                   </div>`
                }
            </div>
        </div>
        
        <div class="detail-section">
            <h3 class="section-title">Social Media</h3>
            <div class="section-content">
                ${politician.twitter || politician.facebook || politician.youtube ? 
                  `<div class="social-links">
                      ${politician.twitter ? 
                        `<a href="https://twitter.com/${politician.twitter}" target="_blank" class="social-link twitter">
                           <i class="fab fa-twitter"></i> @${politician.twitter}
                         </a>` : ''}
                      ${politician.facebook ? 
                        `<a href="${politician.facebook}" target="_blank" class="social-link facebook">
                           <i class="fab fa-facebook"></i> Facebook
                         </a>` : ''}
                      ${politician.youtube ? 
                        `<a href="${politician.youtube}" target="_blank" class="social-link youtube">
                           <i class="fab fa-youtube"></i> YouTube
                         </a>` : ''}
                  </div>` : 
                  `<div class="empty-state small">
                      <i class="fas fa-info-circle"></i>
                      <p>No social media accounts found</p>
                   </div>`
                }
            </div>
        </div>
    `;
    
    // Build the CONTACT tab content
    let contactHtml = `
        <div class="contact-info">
            ${politician.phone ? 
              `<div class="contact-item">
                  <div class="contact-icon"><i class="fas fa-phone"></i></div>
                  <div class="contact-details">
                      <div class="contact-label">Office Phone</div>
                      <div class="contact-value">${politician.phone}</div>
                      <button class="btn small primary-btn call-btn" data-phone="${politician.phone}" data-tooltip="Initiate a direct call to this target">
                          <i class="fas fa-phone"></i> Call
                      </button>
                  </div>
              </div>` : ''}
              
            ${politician.office ? 
              `<div class="contact-item">
                  <div class="contact-icon"><i class="fas fa-building"></i></div>
                  <div class="contact-details">
                      <div class="contact-label">Office Address</div>
                      <div class="contact-value">${politician.office}</div>
                  </div>
              </div>` : ''}
              
            ${politician.website ? 
              `<div class="contact-item">
                  <div class="contact-icon"><i class="fas fa-globe"></i></div>
                  <div class="contact-details">
                      <div class="contact-label">Website</div>
                      <div class="contact-value">
                          <a href="${politician.website}" target="_blank" rel="noopener noreferrer">${politician.website}</a>
                      </div>
                      <button class="btn small secondary-btn website-btn" data-url="${politician.website}" data-tooltip="Open target's website in your browser">
                          <i class="fas fa-external-link-alt"></i> Visit
                      </button>
                  </div>
              </div>` : ''}
        </div>
        
        ${!politician.phone && !politician.office && !politician.website ? 
          `<div class="empty-state">
              <i class="fas fa-address-card"></i>
              <p>No contact information available for this target</p>
           </div>` : ''}
        
        <div class="detail-actions">
            <button id="generate-email-btn" class="btn secondary-btn" data-tooltip="Generate a strategic email to this target">
                <i class="fas fa-envelope"></i> Generate Email
            </button>
            <button id="generate-letter-btn" class="btn secondary-btn" data-tooltip="Create a formal letter for this target">
                <i class="fas fa-file-alt"></i> Generate Letter
            </button>
        </div>
    `;
    
    // Update the tab content
    detailContent.innerHTML = profileHtml;
    contactDetails.innerHTML = contactHtml;
    
    // Add event listeners to the buttons
    const callBtns = document.querySelectorAll('.call-btn');
    callBtns.forEach(btn => {
        const phoneNumber = btn.getAttribute('data-phone');
        if (phoneNumber) {
            btn.addEventListener('click', () => {
                const cleanPhone = phoneNumber.replace(/\D/g, '');
                window.location.href = `tel:${cleanPhone}`;
            });
        }
    });
    
    const websiteBtns = document.querySelectorAll('.website-btn');
    websiteBtns.forEach(btn => {
        const url = btn.getAttribute('data-url');
        if (url) {
            btn.addEventListener('click', () => {
                window.electronAPI.openExternal(url);
            });
        }
    });
    
    const emailBtn = document.getElementById('generate-email-btn');
    if (emailBtn) {
        emailBtn.addEventListener('click', () => {
            generateCampaignMessage('email');
        });
    }
    
    const letterBtn = document.getElementById('generate-letter-btn');
    if (letterBtn) {
        letterBtn.addEventListener('click', () => {
            generateCampaignMessage('letter');
        });
    }
}

// Function to switch tabs
function switchTab(tabId) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.tab-button').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Add active class to selected tab and content
    document.querySelector(`.tab-button[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(`${tabId}-tab`).classList.add('active');
}

// Add this inside the setupEventListeners function
function setupTabListeners() {
    // Tab switching functionality
    document.querySelectorAll('.tab-button').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
} 