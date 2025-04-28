// MAGA_Ops/src/renderer/entity-detail.js

console.log('[entity-detail.js] Script loaded');

document.addEventListener('DOMContentLoaded', () => {
    console.log('[entity-detail.js] DOMContentLoaded event fired');

    // --- Global State --- //
    let currentEntityType = null;
    let currentEntityId = null;
    let currentEntityData = null;
    // Add flags to track if type-specific data has been loaded
    let votingRecordLoaded = false;
    let committeesLoaded = false;
    let metricsLoaded = false;
    let stancesLoaded = false;
    // Add state for latest tweet analysis results
    let latestTweetAnalysisData = null;

    // --- DOM Elements --- //
    const entityNameEl = document.getElementById('entity-name');
    const entityMetaEl = document.getElementById('entity-meta');
    const entityBioEl = document.getElementById('entity-bio');
    const contactInfoEl = document.getElementById('contact-info');
    // ... (add other common elements: connections, funding lists etc.)
    const backButton = document.getElementById('back-button');
    const tabsContainer = document.getElementById('entity-tabs');
    const tabContentsContainer = document.querySelector('.card-content'); // Parent for tab contents

    // Social Tab Specific
    const twitterSection = document.getElementById('twitter-section');
    const latestTweetEl = document.getElementById('latest-tweet');
    const analyzeTweetBtn = document.getElementById('analyze-tweet-btn');
    const tweetAnalysisSection = document.getElementById('tweet-analysis-section');
    const analysisListEl = document.getElementById('analysis-list');

    // Placeholders for Type-Specific Content
    const politicianSpecificContent = document.getElementById('politician-specific-content');
    const influencerSpecificContent = document.getElementById('influencer-specific-content');
    const reportsTabContent = document.getElementById('reports-tab-content'); // Assuming reports are common

    // Sidebar Actions Area
    const entitySpecificActions = document.getElementById('entity-specific-actions');
    const entityActionButtons = document.getElementById('entity-action-buttons');

    // NEW: Modal Elements
    const generationModalOverlay = document.getElementById('generation-modal-overlay');
    const generationModalTitle = document.getElementById('generation-modal-title');
    const generationModalTextarea = document.getElementById('generation-modal-textarea');
    const generationModalCloseBtn = document.getElementById('generation-modal-close-btn');
    const generationModalCloseBtnFooter = document.getElementById('generation-modal-close-btn-footer');
    const generationModalCopyBtn = document.getElementById('generation-modal-copy-btn');
    // NEW: Error Display Element
    const errorDisplayArea = document.getElementById('error-display-area');
    let errorTimeout = null; // Variable to hold the timeout ID

    // --- Initialization --- //
    initializeView();
    setupEventListeners();

    // --- Functions --- //

    function initializeView() {
        console.log('[entity-detail.js] Initializing view...');
        // 1. Get Entity Type and ID from URL parameters
        const params = new URLSearchParams(window.location.search);
        currentEntityType = params.get('type'); // e.g., 'politician', 'influencer'
        currentEntityId = params.get('id');

        if (!currentEntityType || !currentEntityId) {
            console.error('Entity type or ID missing from URL parameters.');
            displayError('Could not load entity: Type or ID missing.');
            // Potentially redirect back or show an error message prominently
            return;
        }

        console.log(`[entity-detail.js] Loading ${currentEntityType} with ID: ${currentEntityId}`);

        // 2. Fetch initial data
        fetchAndDisplayEntityData();

        // 3. Update sidebar navigation (optional - depends on desired active state)
        window.appUtils.initializeSidebarNavigation('explore-data'); // Or pass entity type?
    }

    async function fetchAndDisplayEntityData() {
        setLoadingState(true);
        try {
            // Request basic profile info from the coordinator
            const requestPayload = {
                type: 'fetch',
                entity_type: currentEntityType,
                entity_id: currentEntityId,
                field: 'base_profile' // Define 'base_profile' as needed in coordinator/DB
            };
            const result = await sendPythonRequest(requestPayload);

            if (result && result.success) {
                currentEntityData = result.data;
                console.log('[entity-detail.js] Received entity data:', currentEntityData);
                populateCommonUI(currentEntityData);
                setupEntityTypeSpecificUI(currentEntityData);
            } else {
                throw new Error(result?.error || 'Failed to fetch entity data.');
            }
        } catch (error) {
            console.error('Error fetching entity data:', error);
            displayError(`Error loading ${currentEntityType} data: ${error.message}`);
        } finally {
            setLoadingState(false);
        }
    }

    function populateCommonUI(data) {
        entityNameEl.textContent = data.name || 'Name Unavailable';
        entityBioEl.textContent = data.bio || data.description || 'No description available.';

        // Populate Meta Badges (Party, State, Type)
        entityMetaEl.innerHTML = ''; // Clear previous
        if (data.type_label) { // Add a type label (e.g., Politician, Influencer)
             addMetaBadge(data.type_label, 'badge-entity-type');
        }
        if (data.party) {
            addMetaBadge(data.party, `badge-${data.party.toLowerCase()}`);
        }
        if (data.state) {
            addMetaBadge(data.state, 'badge-state');
        }
        // Add more common badges as needed (e.g., status, chamber for politicians)

        // Populate Contact Info (Example - needs more robust handling)
        contactInfoEl.innerHTML = ''; // Clear previous
        if (data.phone) addContactItem('phone', 'Office Phone', data.phone);
        if (data.email) addContactItem('envelope', 'Email', data.email);
        if (data.website) addContactItem('globe', 'Website', data.website, true);

        // Populate Connections & Funding (Placeholders - need data)
        populateList(document.getElementById('associated-entities-list'), data.connections, 'No connections found.');
        populateList(document.getElementById('key-funding-list'), data.funding, 'No funding info found.');

        // Populate Social Media Tab
        if (data.twitter_handle) {
            twitterSection.style.display = 'block';
            latestTweetEl.innerHTML = '<p class="tweet-content">Tweet data will be loaded on demand or shown here.</p>';
            // Show evaluate button IF it's a politician
            if (currentEntityType === 'politician') {
                analyzeTweetBtn.style.display = 'inline-block';
                analyzeTweetBtn.disabled = false;
                analyzeTweetBtn.textContent = 'Evaluate Latest Tweet with AI';
            }
        } else {
            twitterSection.style.display = 'none';
        }
    }

    function addMetaBadge(text, className) {
        const badge = document.createElement('span');
        badge.classList.add('badge');
        if (className) badge.classList.add(className);
        badge.textContent = text;
        entityMetaEl.appendChild(badge);
    }

    function addContactItem(icon, label, value, isLink = false) { 
        // Simplified version - adapt from politician-view if needed
        const item = document.createElement('div');
        item.classList.add('contact-item-simple'); // Use a simpler class?
        item.innerHTML = `<i class="fas fa-${icon}"></i> <strong>${label}:</strong> ${isLink ? `<a href="${value}" target="_blank">${value}</a>` : value}`;
        contactInfoEl.appendChild(item);
    }

    function populateList(listElement, items, emptyMessage) {
        listElement.innerHTML = '';
        if (items && items.length > 0) {
            items.forEach(item => {
                const li = document.createElement('li');
                // TODO: Format list item content properly (links, details)
                li.textContent = JSON.stringify(item); // Basic display for now
                listElement.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = emptyMessage;
            listElement.appendChild(li);
        }
    }

    function setupEntityTypeSpecificUI(data) {
        console.log(`Setting up UI for type: ${currentEntityType}`);
        // Hide all specific content first
        politicianSpecificContent.style.display = 'none';
        influencerSpecificContent.style.display = 'none';
        reportsTabContent.style.display = 'none'; // Hide reports initially

        // Remove existing type-specific tabs
        tabsContainer.querySelectorAll('.type-specific-tab').forEach(tab => tab.remove());

        // Show entity-specific sidebar actions container
        entitySpecificActions.style.display = 'block';
        entityActionButtons.innerHTML = ''; // Clear old buttons

        // --- Politician Specific --- //
        if (currentEntityType === 'politician') {
            politicianSpecificContent.style.display = 'block'; // Show the container

            // Add Tabs
            addTab('voting', 'Voting Record', true);
            addTab('committees', 'Committees', true);
            addTab('reports', 'Analysis & Reports', true);

            // Add Sidebar Actions
            addSidebarAction('view-voting-record', 'fas fa-check-double', 'View Voting Record');
            if (data.twitter_handle) {
                 addSidebarAction('analyze-tweet-sidebar-btn', 'fas fa-magic', 'Evaluate Tweet', handleAnalyzeTweetClick);
            }

            // --- Fetch Static Politician Data (Voting, Committees) ---
            // Request this data once when the view loads, relying on backend cache/db
            fetchAndPopulateList('voting_record', document.getElementById('voting-record-list'), 'No voting record available in database.');
            fetchAndPopulateList('committees', document.getElementById('committee-list'), 'No committee assignments available in database.');

        } 
        // --- Influencer Specific --- //
        else if (currentEntityType === 'influencer') {
            influencerSpecificContent.style.display = 'block';

            // Add Tabs
            addTab('metrics', 'Key Metrics', true);
            addTab('stances', 'Stances & Narratives', true);
             addTab('reports', 'Analysis & Reports', true); // Add reports for influencers too

            // Add Sidebar Actions
            addSidebarAction('view-influencer-metrics', 'fas fa-chart-line', 'View Metrics');
            if (data.twitter_handle) { // Add evaluate button for influencers too?
                 addSidebarAction('analyze-tweet-sidebar-btn', 'fas fa-magic', 'Evaluate Tweet', handleAnalyzeTweetClick);
            }

             // Initiate fetching type-specific data (will be done when tab is clicked or later)
            // fetchAndDisplayMetrics(); // Example: Call functions later or on tab click
            // fetchAndDisplayStances();
            // Clear lists initially
            populateList(document.getElementById('influencer-metrics-list'), [], 'Loading metrics...');
            populateList(document.getElementById('influencer-stances-list'), [], 'Loading stances...');
        }

        // Activate the first tab by default
        showTab('info'); 
    }

    function addTab(tabId, tabLabel, isTypeSpecific = false) {
        const tab = document.createElement('div');
        tab.classList.add('card-tab');
        if (isTypeSpecific) {
            tab.classList.add('type-specific-tab');
        }
        tab.dataset.tab = tabId;
        tab.textContent = tabLabel;
        tab.addEventListener('click', () => showTab(tabId));
        tabsContainer.appendChild(tab);
    }

     function addSidebarAction(id, iconClass, text, clickHandler) {
        const button = document.createElement('button');
        button.id = id;
        button.classList.add('sidebar-btn');
        button.innerHTML = `<i class="${iconClass}"></i> ${text}`;
        if (clickHandler) {
            button.addEventListener('click', clickHandler);
        }
        entityActionButtons.appendChild(button);
    }

    function showTab(tabId) {
        console.log(`[entity-detail.js] Showing tab: ${tabId}`);
        // Deactivate all tabs
        tabsContainer.querySelectorAll('.card-tab').forEach(tab => tab.classList.remove('active'));
        // Hide all tab content panels
        // Refined: Select only direct children '.tab-content' to avoid nested issues
        tabContentsContainer.querySelectorAll(':scope > .tab-content, :scope > #politician-specific-content > .tab-content, :scope > #influencer-specific-content > .tab-content').forEach(content => {
             if (content) content.style.display = 'none';
         });
         // Also hide the wrapper divs initially
         politicianSpecificContent.style.display = 'none';
         influencerSpecificContent.style.display = 'none';

        // Activate the selected tab
        const activeTab = tabsContainer.querySelector(`.card-tab[data-tab="${tabId}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }

        // Show the corresponding content panel and fetch data if needed
        let contentPanel = document.getElementById(`${tabId}-tab-content`);

        // Determine if it's a type-specific tab requiring data fetch
        let fetchFunction = null;
        let loadedFlag = true; // Assume loaded unless it's a fetchable tab

        if (currentEntityType === 'politician') {
             politicianSpecificContent.style.display = 'block'; // Show the container for politician tabs
            if (tabId === 'voting') {
                contentPanel = document.getElementById('voting-tab-content');
                loadedFlag = votingRecordLoaded;
                if (!loadedFlag) fetchFunction = fetchAndDisplayVotingRecord;
            } else if (tabId === 'committees') {
                contentPanel = document.getElementById('committees-tab-content');
                loadedFlag = committeesLoaded;
                if (!loadedFlag) fetchFunction = fetchAndDisplayCommittees;
            }
        } else if (currentEntityType === 'influencer') {
             influencerSpecificContent.style.display = 'block'; // Show the container for influencer tabs
             if (tabId === 'metrics') {
                 contentPanel = document.getElementById('metrics-tab-content');
                 loadedFlag = metricsLoaded;
                 if (!loadedFlag) fetchFunction = fetchAndDisplayMetrics;
             } else if (tabId === 'stances') {
                 contentPanel = document.getElementById('stances-tab-content');
                 loadedFlag = stancesLoaded;
                 if (!loadedFlag) fetchFunction = fetchAndDisplayStances;
             }
        }

        // Handle common tabs ('info', 'reports', potentially others)
        if (!contentPanel) {
            if (tabId === 'info') {
                contentPanel = document.getElementById('info-tab-content');
            } else if (tabId === 'reports') {
                contentPanel = document.getElementById('reports-tab-content');
                // Ensure the correct parent container is visible if needed (e.g., if reports are nested)
                 if (currentEntityType === 'politician') politicianSpecificContent.style.display = 'block';
                 else if (currentEntityType === 'influencer') influencerSpecificContent.style.display = 'block';
                // TODO: Add logic to fetch reports if needed, similar to other tabs
            }
        }

        if (contentPanel) {
            contentPanel.style.display = 'block';
             // Fetch data if needed and not already loaded
             if (fetchFunction && !loadedFlag) {
                 console.log(`[entity-detail.js] Fetching data for tab: ${tabId}`);
                 fetchFunction(); // Call the specific fetch function
             }
        } else {
            console.warn(`Content panel not found for tab: ${tabId}. Defaulting to 'info'.`);
            // Show the 'info' tab as a fallback
            document.getElementById('info-tab-content').style.display = 'block';
            const infoTab = tabsContainer.querySelector('.card-tab[data-tab="info"]');
            if (infoTab) infoTab.classList.add('active');
            // Ensure type-specific containers are hidden if we default to 'info'
            politicianSpecificContent.style.display = 'none';
            influencerSpecificContent.style.display = 'none';
        }
    }

    async function handleAnalyzeTweetClick() {
        console.log('Analyze Tweet button clicked');
        if (!currentEntityData || !currentEntityData.twitter_handle || currentEntityType !== 'politician') {
            console.error('Cannot analyze tweet: Missing data or wrong entity type.');
            // Maybe show a user message?
            return;
        }

        setLoadingState(true, 'Evaluating tweet...');
        analysisListEl.innerHTML = '<li><i class="fas fa-spinner fa-spin"></i> Generating AI analysis...</li>';
        tweetAnalysisSection.style.display = 'block';
        analyzeTweetBtn.disabled = true;
        analyzeTweetBtn.textContent = 'Analyzing...';

        try {
            const requestPayload = {
                type: 'evaluate_latest_post',
                entity_type: currentEntityType,
                entity_id: currentEntityId,
                context: {
                    twitter_handle: currentEntityData.twitter_handle
                }
            };
            const result = await sendPythonRequest(requestPayload);

            if (result && result.success) {
                console.log('Received AI evaluation:', result.data);
                displayEvaluationResults(result.data);
            } else {
                throw new Error(result?.error || 'Failed to evaluate tweet.');
            }
        } catch (error) {
            console.error('Error evaluating tweet:', error);
            analysisListEl.innerHTML = `<li class="error">Error evaluating tweet: ${error.message}</li>`;
        } finally {
            setLoadingState(false);
             analyzeTweetBtn.disabled = false;
             analyzeTweetBtn.textContent = 'Re-evaluate Tweet';
        }
    }

    function displayEvaluationResults(data) {
        analysisListEl.innerHTML = ''; // Clear loading/error
        latestTweetAnalysisData = data; // Store the full data object

        if (!data || !data.ai_evaluation) {
             analysisListEl.innerHTML = '<li class="error">Invalid analysis data received.</li>';
             return;
        }

        const evalData = data.ai_evaluation;

        // Display Tweet Info (Optional - could update latestTweetEl directly)
        if (data.tweet) {
             const tweetDate = data.tweet.timestamp ? new Date(data.tweet.timestamp * 1000).toLocaleDateString() : 'Unknown date';
             latestTweetEl.innerHTML = `
                <div class="tweet-card">
                    <div class="tweet-header">
                         <span class="twitter-handle">@${currentEntityData.twitter_handle.replace(/^@/, '')}</span>
                         <span class="tweet-date">${tweetDate}</span>
                     </div>
                     <p class="tweet-content">${data.tweet.text || '[No text]'}</p>
                 </div>`;
        }

        // Display AI Analysis
        addAnalysisItem('Sentiment', `${evalData.sentiment_classification} (${evalData.sentiment_justification})`);
        addAnalysisItem('Main Topics', evalData.main_topics, true);
        addAnalysisItem('Suggested Local Data', evalData.suggested_local_data, true);

        tweetAnalysisSection.style.display = 'block';
    }

     function addAnalysisItem(label, value, isArray = false) {
        const li = document.createElement('li');
        let valueHtml = '';

        if (isArray && Array.isArray(value) && value.length > 0) {
            valueHtml = value.map(item => `<span class="analysis-badge">${item}</span>`).join(' ');
        } else if (isArray && (!Array.isArray(value) || value.length === 0)) {
             valueHtml = '<span class="analysis-badge none">None</span>';
        } else {
            valueHtml = value; // Simple text value
        }

        li.innerHTML = `<strong>${label}:</strong> ${valueHtml}`;
        analysisListEl.appendChild(li);
    }

    // NEW: Handler for Intelligence Generation Buttons
    async function handleGenerateIntelClick(event) {
        const button = event.target.closest('.generate-btn');
        if (!button) return;

        const format = button.dataset.format; // e.g., 'email', 'post', 'reply'
        console.log(`[entity-detail.js] Generation requested for format: ${format}`);

        // Check if we have the necessary context
        if (!currentEntityData) {
            displayError('Cannot generate: Entity data not loaded.');
            return;
        }
        if (!latestTweetAnalysisData || !latestTweetAnalysisData.tweet || !latestTweetAnalysisData.ai_evaluation) {
            displayError('Cannot generate: Tweet analysis data not available. Please evaluate the tweet first.');
            return;
        }

        // Gather context
        const generationContext = {
            entity: {
                id: currentEntityId,
                type: currentEntityType,
                name: currentEntityData.name,
                // Add other relevant base profile fields? Party, State, etc.
                party: currentEntityData.party,
                state: currentEntityData.state,
                twitter_handle: currentEntityData.twitter_handle
            },
            triggering_post: latestTweetAnalysisData.tweet,
            post_evaluation: latestTweetAnalysisData.ai_evaluation,
            // Include manually updated data fields if needed for context?
            // Example: voting_record: currentEntityData.voting_record (could be large!)
            // Example: committees: currentEntityData.committees
        };

        const requestPayload = {
            type: 'generate_intel',
            format: format,
            context: generationContext
        };

        console.log('[entity-detail.js] Preparing generate_intel request:', requestPayload);
        // TODO: Show loading state in a generation output area?
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';

        try {
            // --- Remove Simulation Block --- 
            /* 
            console.log('Simulating backend call for generate_intel...');
            await new Promise(resolve => setTimeout(resolve, 1500)); // Wait 1.5 seconds
            const simulatedResponse = {
                success: true,
                data: {
                    generated_text: `This is a simulated ${format} generated based on the tweet by ${currentEntityData.name}.\n\nTweet Text: ${latestTweetAnalysisData.tweet.text}\nSentiment: ${latestTweetAnalysisData.ai_evaluation.sentiment_classification}\nTopics: ${latestTweetAnalysisData.ai_evaluation.main_topics.join(', ')}`
                }
            };
            console.log('Simulated backend response:', simulatedResponse);
            alert(`Generated ${format}:\n\n${simulatedResponse.data.generated_text}`); // Simple alert for now
            */
            // ----------------------------- //

            // --- Activate Actual Backend Call --- //
            const result = await sendPythonRequest(requestPayload);
            if (result && result.success) {
                console.log('[entity-detail.js] Received generated content:', result.data);
                // Display the generated text in the UI (using a modal - to be implemented)
                displayGeneratedContent(format, result.data.generated_text);
            } else {
                throw new Error(result?.error || `Failed to generate ${format}.`);
            }
            // --------------------------------- //
        } catch (error) {
            console.error(`Error generating ${format}:`, error);
            displayError(`Generation failed for ${format}: ${error.message}`);
        } finally {
            button.disabled = false;
            // Restore original button text based on format?
             if (format === 'email') button.textContent = 'Draft Email';
             else if (format === 'post') button.textContent = 'Draft Social Post';
             else if (format === 'reply') button.textContent = 'Draft Reply';
             else button.innerHTML = '<i class="fas fa-magic"></i> Generate'; // Fallback
        }
    }

    // NEW: Function to display generated content in the modal
    function displayGeneratedContent(format, text) {
        if (!generationModalOverlay || !generationModalTitle || !generationModalTextarea) {
            console.error('Generation modal elements not found.');
            // Fallback to alert if modal is broken
            alert(`Generated ${format}:\n\n${text}`);
            return;
        }

        // Set modal content
        generationModalTitle.textContent = `Generated ${format.charAt(0).toUpperCase() + format.slice(1)}`; // Capitalize format
        generationModalTextarea.value = text;

        // Show the modal
        generationModalOverlay.style.display = 'flex';
    }

    // NEW: Function to hide the generation modal
    function hideGenerationModal() {
        if (generationModalOverlay) {
            generationModalOverlay.style.display = 'none';
        }
    }

    function setupEventListeners() {
        // Back Button
        backButton.addEventListener('click', () => {
            console.log('Back button clicked - using history.back()');
            history.back();
        });

        // Analyze Tweet Button (listener added conditionally in populateCommonUI)
        analyzeTweetBtn.addEventListener('click', handleAnalyzeTweetClick);

        // Add listeners for dynamically added tabs/buttons if needed (use event delegation)
        tabsContainer.addEventListener('click', (event) => {
            if (event.target.classList.contains('card-tab')) {
                 showTab(event.target.dataset.tab);
            }
        });

        // Listener for dynamically added sidebar action buttons
         entityActionButtons.addEventListener('click', (event) => {
            const button = event.target.closest('.sidebar-btn');
            if (button) {
                 console.log(`Sidebar action clicked: ${button.id}`);
                 // Handler logic was attached directly when creating button
                 // Or add specific checks here if needed
            }
        });

        // Listener for Intelligence Generation Buttons
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('generate-btn')) {
                handleGenerateIntelClick(event);
            }
        });

        // Listener for dynamically added update buttons
        tabContentsContainer.addEventListener('click', handleManualUpdateClick);

        // NEW: Modal Event Listeners
        if (generationModalCloseBtn) {
            generationModalCloseBtn.addEventListener('click', hideGenerationModal);
        }
        if (generationModalCloseBtnFooter) {
             generationModalCloseBtnFooter.addEventListener('click', hideGenerationModal);
        }
        if (generationModalCopyBtn) {
            generationModalCopyBtn.addEventListener('click', () => {
                if (generationModalTextarea) {
                    generationModalTextarea.select(); // Select the text
                    try {
                        navigator.clipboard.writeText(generationModalTextarea.value);
                        // Optional: Show feedback like changing button text temporarily
                        generationModalCopyBtn.textContent = 'Copied!';
                        setTimeout(() => { generationModalCopyBtn.textContent = 'Copy Text'; }, 1500);
                    } catch (err) {
                        console.error('Failed to copy text: ', err);
                        // Maybe show an error message to the user
                         alert('Failed to copy text to clipboard.');
                    }
                }
            });
        }
         // Optional: Close modal if overlay is clicked
         if (generationModalOverlay) {
             generationModalOverlay.addEventListener('click', (event) => {
                 if (event.target === generationModalOverlay) { // Only if overlay itself is clicked
                     hideGenerationModal();
                 }
             });
         }
    }

    // --- Utility Functions --- //

    async function sendPythonRequest(payload) {
        const requestJsonString = JSON.stringify(payload);
        console.log(`[Frontend] Sending python-bridge request: ${requestJsonString}`);
        try {
            const resultString = await window.electronAPI.invoke('python-bridge', requestJsonString);
            console.log(`[Frontend] Received python-bridge response string: ${resultString}`);
            if (!resultString) {
                 throw new Error('Received empty response from backend bridge.');
            }
            const result = JSON.parse(resultString);
             return result;
        } catch (error) {
            console.error('Error invoking python-bridge or parsing response:', error, "Raw string:", resultString || '(empty)');
             // Return an error structure consistent with successful responses
            return { success: false, error: `Frontend bridge error: ${error.message}` };
        }
    }

    function setLoadingState(isLoading, message = 'Loading...') {
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
             const messageEl = loadingIndicator.querySelector('p');
             if (messageEl) messageEl.textContent = message;
            loadingIndicator.style.display = isLoading ? 'flex' : 'none';
        }
    }

    function displayError(message) {
        console.error('Displaying Error:', message);
        // alert(`Error: ${message}`); // Replace alert

        if (errorDisplayArea) {
            errorDisplayArea.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`; // Add icon
            errorDisplayArea.style.display = 'block';

            // Clear previous timeout if exists
            if (errorTimeout) {
                clearTimeout(errorTimeout);
            }

            // Set timeout to hide the error message after 7 seconds
            errorTimeout = setTimeout(() => {
                errorDisplayArea.style.display = 'none';
                errorTimeout = null;
            }, 7000); 
        } else {
            // Fallback to alert if the display area isn't found
            alert(`Error: ${message}`);
        }

         if(entityNameEl) entityNameEl.textContent = 'Error Loading'; // Keep this part?
    }

    // --- Type-Specific Data Fetching Functions --- //

    async function fetchAndPopulateList(field, listElement, emptyMessage) {
        if (!listElement) return;
        listElement.innerHTML = `<li><i class="fas fa-spinner fa-spin"></i> Loading ${field.replace('_',' ')}...</li>`; // Loading message
        try {
            const requestPayload = {
                type: 'fetch',
                entity_type: currentEntityType,
                entity_id: currentEntityId,
                field: field 
            };
            const result = await sendPythonRequest(requestPayload);
            if (result && result.success) {
                populateList(listElement, result.data, emptyMessage);
            } else {
                throw new Error(result?.error || `Failed to fetch ${field}.`);
            }
        } catch (error) {
            console.error(`Error fetching ${field}:`, error);
            populateList(listElement, [], `<li class="error">Error loading ${field}: ${error.message}</li>`);
        }
    }

    async function fetchAndDisplayMetrics() {
        console.log('[entity-detail.js] Fetching influencer metrics...');
        // TODO: Implement backend request and UI update
        // Set flag on success: metricsLoaded = true;
    }

    async function fetchAndDisplayStances() {
        console.log('[entity-detail.js] Fetching influencer stances...');
        // TODO: Implement backend request and UI update
        // Set flag on success: stancesLoaded = true;
    }

    // NEW: Function to handle manual update button clicks
    async function handleManualUpdateClick(event) {
        const button = event.target.closest('.update-btn');
        if (!button) return;

        const fieldToUpdate = button.dataset.field;
        const listElement = document.getElementById(`${fieldToUpdate}-list`); // Assumes convention: field_name-list
        // Find the specific list ID based on field (more robust)
        let targetListId = null;
        if (fieldToUpdate === 'voting_record') targetListId = 'voting-record-list';
        else if (fieldToUpdate === 'committees') targetListId = 'committee-list';
        else if (fieldToUpdate === 'metrics') targetListId = 'influencer-metrics-list';
        else if (fieldToUpdate === 'stances') targetListId = 'influencer-stances-list';
        // Add other mappings if needed
        
        const targetListElement = targetListId ? document.getElementById(targetListId) : null;

        if (!fieldToUpdate || !targetListElement) {
            console.error('Could not determine field or list element for update button.', button);
            displayError('Update failed: Internal configuration error.');
            return;
        }

        console.log(`[entity-detail.js] Manual update requested for field: ${fieldToUpdate}`);
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'; // Show loading state on button
        targetListElement.innerHTML = `<li><i class="fas fa-spinner fa-spin"></i> Fetching latest ${fieldToUpdate.replace('_',' ')}...</li>`; // Show loading in list

        try {
            const requestPayload = {
                type: 'force_fetch', // Special type to force live fetch
                entity_type: currentEntityType,
                entity_id: currentEntityId,
                field: fieldToUpdate
            };
            const result = await sendPythonRequest(requestPayload);

            if (result && result.success) {
                console.log(`[entity-detail.js] Received forced update data for ${fieldToUpdate}:`, result.data);
                
                // --- Update currentEntityData --- //
                if (!currentEntityData) currentEntityData = {}; // Initialize if somehow null
                currentEntityData[fieldToUpdate] = result.data; // Update the specific field
                console.log('[entity-detail.js] Updated currentEntityData:', currentEntityData);
                // --------------------------------- //

                // populateList needs the appropriate empty message for the field
                let emptyMessage = `No ${fieldToUpdate.replace('_',' ')} data found after update.`; // Generic empty message
                // Could refine empty messages based on field
                 if (fieldToUpdate === 'voting_record') emptyMessage = 'No recent voting record found after update.';
                 else if (fieldToUpdate === 'committees') emptyMessage = 'No committee assignments found after update.';
                 // Add more specific messages...

                populateList(targetListElement, result.data, emptyMessage);
            } else {
                throw new Error(result?.error || `Failed to force fetch ${fieldToUpdate}.`);
            }
        } catch (error) {
            console.error(`Error force fetching ${fieldToUpdate}:`, error);
            populateList(targetListElement, [], `<li class="error">Error updating ${fieldToUpdate}: ${error.message}</li>`);
            displayError(`Update failed for ${fieldToUpdate}: ${error.message}`); // Show general error too
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-sync-alt"></i>'; // Restore button icon
        }
    }

}); // End DOMContentLoaded 