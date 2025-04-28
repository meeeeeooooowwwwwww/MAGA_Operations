/**
 * MAGA Ops Political Influencer Database
 * Front-end JavaScript to handle UI interactions
 */

console.log('[influencer-search.js] Script loaded');

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('[influencer-search.js] DOMContentLoaded event fired');

  // Initialize standard sidebar navigation
  window.appUtils.initializeSidebarNavigation('explore-influencers'); // Pass current page identifier

  // Elements
  const searchInput = document.getElementById('search-input');
  const searchButton = document.getElementById('search-button');
  const topInfluencersButton = document.getElementById('top-influencers-button');
  const ideologyMapButton = document.getElementById('ideology-map-button');
  const browseButton = document.getElementById('browse-button');
  const resultsContainer = document.getElementById('results-container');
  const loadingIndicator = document.getElementById('loading-indicator');
  const errorMessage = document.getElementById('error-message');
  const browseOptions = document.getElementById('browse-options');
  const categoryButtons = document.getElementById('category-buttons');
  const affiliationButtons = document.getElementById('affiliation-buttons');
  const suggestionsList = document.getElementById('search-suggestions');
  const modal = document.getElementById('influencer-modal');
  const modalCloseBtn = document.getElementById('modal-close');
  const modalContent = document.getElementById('influencer-detail-content');

  let debounceTimer;

  // Python Bridge for API calls
  const pythonBridge = {
    execute: async (command, ...args) => {
      // Show loading indicator
      if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
      }
      
      try {
        // Call the actual Python script via the exposed API
        console.log(`[Frontend] Sending IPC python-bridge via electronAPI.invoke: ${command}`, args);
        // Use the API exposed by preload.js
        const resultString = await window.electronAPI.invoke('python-bridge', command, ...args);
        console.log(`[Frontend] Received IPC python-bridge result string:`, resultString);
        
        // Parse the JSON string result from the main process
        const result = JSON.parse(resultString);
        console.log(`[Frontend] Parsed IPC result:`, result);
        
        return result; // Return the parsed result from Python

      } catch (error) {
        console.error('IPC bridge or JSON parsing error:', error);
        if (errorMessage) {
          errorMessage.textContent = `Error processing request: ${error.message || 'Unknown error'}`;
          errorMessage.style.display = 'block';
        }
        // Return a consistent error structure
        return { success: false, error: error.message || 'Unknown error' };
      } finally {
        // Hide loading indicator
        if (loadingIndicator) {
          loadingIndicator.style.display = 'none';
        }
      }
    }
  };

  // Event Listeners
  if (searchButton) {
    searchButton.addEventListener('click', () => {
      console.log('[influencer-search.js] Search button clicked.');
      const query = searchInput.value.trim();
      if (query) {
        console.log(`[influencer-search.js] Performing search for: ${query}`);
        performSearch(query);
      }
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      const query = searchInput.value.trim();

      if (query.length >= 2) {
        debounceTimer = setTimeout(() => {
          console.log(`[influencer-search.js] Debounced input, showing suggestions for: ${query}`);
          showSearchSuggestions(query);
        }, 300);
      } else {
        hideSuggestions();
      }
    });

    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        console.log('[influencer-search.js] Enter key pressed in search input.');
        const query = searchInput.value.trim();
        if (query) {
          console.log(`[influencer-search.js] Performing search for: ${query}`);
          hideSuggestions();
          performSearch(query);
        }
      }
    });
    
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !suggestionsList.contains(e.target)) {
            hideSuggestions();
        }
    });
  }

  if (topInfluencersButton) {
    topInfluencersButton.addEventListener('click', () => {
      showTopInfluencers();
    });
  }

  if (ideologyMapButton) {
    ideologyMapButton.addEventListener('click', () => {
      showIdeologyMap();
    });
  }

  if (browseButton) {
    browseButton.addEventListener('click', () => {
      showBrowseOptions();
    });
  }

  // Modal Close Button
  if (modalCloseBtn) {
    modalCloseBtn.addEventListener('click', closeModal);
  }

  // Close modal if clicking outside the content
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) { // Check if the click was directly on the overlay
        closeModal();
      }
    });
  }

  // Sidebar Quick Actions
  if (topInfluencersButton) {
    topInfluencersButton.addEventListener('click', () => {
      console.log('[influencer-search.js] Top Influencers clicked');
      hideSecondaryPanels();
      showLoading();
      // Example IPC call
      window.electronAPI.getTopInfluencers({ limit: 20 });
    });
  }
  
  window.appUtils.addPlaceholderListener(browseButton, 'Browse by Category');
  window.appUtils.addPlaceholderListener(browseButton, 'Browse by Affiliation');
  window.appUtils.addPlaceholderListener(ideologyMapButton, 'Ideology Map');
  // TODO: Implement panel display logic for category/affiliation/map browsing

  // Search function
  async function performSearch(query) {
    hideSuggestions();
    // Clear previous results and errors
    clearResults();
    
    // Execute search
    const response = await pythonBridge.execute('search', query);
    
    if (response.success) {
      displaySearchResults(response.data);
    } else {
      showError(response.error || 'Search failed');
    }
  }

  // Display search results
  function displaySearchResults(results) {
    if (!results || results.length === 0) {
      resultsContainer.innerHTML = '<p>No results found</p>';
      return;
    }

    const resultsHTML = results.map(influencer => `
      <div class="influencer-card" data-id="${influencer.id}">
        <h3>${influencer.name}</h3>
        <p class="category">${influencer.category || 'Unknown category'}</p>
        <p class="description">${influencer.bio || 'No description available'}</p>
        <button class="view-details-button" data-id="${influencer.id}">View Details</button>
      </div>
    `).join('');

    const finalHTML = `
      <h2>Search Results</h2>
      <div class="results-grid">
        ${resultsHTML}
      </div>
    `;

    resultsContainer.innerHTML = finalHTML;

    console.log('[influencer-search.js] Updated resultsContainer.innerHTML with:', finalHTML);

    // Add event listeners to view details buttons
    document.querySelectorAll('.view-details-button').forEach(button => {
      button.addEventListener('click', (e) => {
        const influencerId = e.target.getAttribute('data-id');
        console.log(`Navigating to entity detail for influencer ID: ${influencerId}`);
        // Pass parameters via query string
        window.location.href = `entity-detail.html?type=influencer&id=${influencerId}`;
      });
    });
  }

  // Show top influencers
  async function showTopInfluencers(category = null, limit = 10) {
    clearResults();
    
    const response = await pythonBridge.execute('top', category, limit);
    
    if (response.success) {
      const resultsHTML = response.data.map(influencer => `
        <div class="influencer-card" data-id="${influencer.id}">
          <h3>${influencer.name}</h3>
          <p class="category">${influencer.category || 'Unknown category'}</p>
          <p class="rank">Rank: ${influencer.rank || 'N/A'}</p>
          <p class="mentions">Mentions: ${influencer.mentions || 0}</p>
          <button class="view-details-button" data-id="${influencer.id}">View Details</button>
        </div>
      `).join('');

      resultsContainer.innerHTML = `
        <h2>Top Influencers ${category ? `in ${category}` : ''}</h2>
        <div class="results-grid">
          ${resultsHTML}
        </div>
      `;

      // Add event listeners to view details buttons (UPDATED to navigate)
      document.querySelectorAll('.view-details-button').forEach(button => {
        button.addEventListener('click', (e) => {
          const influencerId = e.target.getAttribute('data-id');
          console.log(`Navigating to entity detail for influencer ID: ${influencerId}`);
          window.location.href = `entity-detail.html?type=influencer&id=${influencerId}`;
        });
      });
    } else {
      showError(response.error || 'Failed to load top influencers');
    }
  }

  // Show ideology map
  async function showIdeologyMap() {
    clearResults();
    
    const response = await pythonBridge.execute('ideology');
    
    if (response.success) {
      const data = response.data;
      
      // Create a visual representation of the ideology distribution
      const maxValue = Math.max(...Object.values(data));
      
      const barChartHTML = Object.entries(data).map(([ideology, count]) => {
        const percentage = (count / maxValue) * 100;
        return `
          <div class="ideology-bar">
            <div class="ideology-label">${ideology}</div>
            <div class="bar-container">
              <div class="bar" style="width: ${percentage}%" data-value="${count}"></div>
            </div>
            <div class="ideology-count">${count}</div>
          </div>
        `;
      }).join('');

      resultsContainer.innerHTML = `
        <h2>Ideological Distribution</h2>
        <div class="ideology-chart">
          ${barChartHTML}
        </div>
        <div class="ideology-legend">
          <div class="legend-item">
            <div class="legend-color left-wing"></div>
            <div>Left Wing</div>
          </div>
          <div class="legend-item">
            <div class="legend-color moderate-left"></div>
            <div>Moderate Left</div>
          </div>
          <div class="legend-item">
            <div class="legend-color center"></div>
            <div>Center</div>
          </div>
          <div class="legend-item">
            <div class="legend-color moderate-right"></div>
            <div>Moderate Right</div>
          </div>
          <div class="legend-item">
            <div class="legend-color right-wing"></div>
            <div>Right Wing</div>
          </div>
        </div>
      `;
    } else {
      showError(response.error || 'Failed to load ideology data');
    }
  }

  // Show browse options
  async function showBrowseOptions() {
    clearResults();
    
    if (browseOptions) {
      browseOptions.style.display = 'block';
    }
    
    // Load categories
    const categoriesResponse = await pythonBridge.execute('categories');
    if (categoriesResponse.success && categoryButtons) {
      const categoryHTML = categoriesResponse.data.map(category => `
        <button class="category-button" data-id="${category.id}">${category.name}</button>
      `).join('');
      
      categoryButtons.innerHTML = categoryHTML;
      
      // Add event listeners
      document.querySelectorAll('.category-button').forEach(button => {
        button.addEventListener('click', (e) => {
          const categoryId = e.target.getAttribute('data-id');
          const categoryName = e.target.textContent;
          showTopInfluencers(categoryName);
        });
      });
    }
    
    // Load affiliations
    const affiliationsResponse = await pythonBridge.execute('affiliations');
    if (affiliationsResponse.success && affiliationButtons) {
      const affiliationHTML = affiliationsResponse.data.map(affiliation => `
        <button class="affiliation-button" data-id="${affiliation.id}">${affiliation.name}</button>
      `).join('');
      
      affiliationButtons.innerHTML = affiliationHTML;
      
      // Add event listeners
      document.querySelectorAll('.affiliation-button').forEach(button => {
        button.addEventListener('click', (e) => {
          const affiliationId = e.target.getAttribute('data-id');
          const affiliationName = e.target.textContent;
          showAffiliationResults(affiliationName);
        });
      });
    }
  }

  // Show affiliation results
  async function showAffiliationResults(affiliation) {
    clearResults();
    
    if (browseOptions) {
      browseOptions.style.display = 'none';
    }
    
    const response = await pythonBridge.execute('affiliation', affiliation);
    
    if (response.success) {
      const resultsHTML = response.data.map(influencer => `
        <div class="influencer-card" data-id="${influencer.id}">
          <h3>${influencer.name}</h3>
          <p class="category">${influencer.category || 'Unknown category'}</p>
          <p class="affiliation">${affiliation}</p>
          <button class="view-details-button" data-id="${influencer.id}">View Details</button>
        </div>
      `).join('');

      resultsContainer.innerHTML = `
        <h2>Influencers affiliated with ${affiliation}</h2>
        <div class="results-grid">
          ${resultsHTML}
        </div>
      `;

      // Add event listeners to view details buttons (UPDATED to navigate)
      document.querySelectorAll('.view-details-button').forEach(button => {
        button.addEventListener('click', (e) => {
          const influencerId = e.target.getAttribute('data-id');
          console.log(`Navigating to entity detail for influencer ID: ${influencerId}`);
          window.location.href = `entity-detail.html?type=influencer&id=${influencerId}`;
        });
      });
    } else {
      showError(response.error || `Failed to load influencers for ${affiliation}`);
    }
  }

  // Helper functions
  function clearResults() {
    if (resultsContainer) {
      resultsContainer.innerHTML = '';
    }
    
    if (errorMessage) {
      errorMessage.style.display = 'none';
    }
    
    if (browseOptions) {
      browseOptions.style.display = 'none';
    }
  }

  function showError(message) {
    if (errorMessage) {
      errorMessage.textContent = message;
      errorMessage.style.display = 'block';
    }
  }

  // Function to show search suggestions
  async function showSearchSuggestions(query) {
    const response = await pythonBridge.execute('search', query, 5);

    suggestionsList.innerHTML = '';

    if (response.success && response.data && response.data.length > 0) {
        response.data.forEach(influencer => {
            const li = document.createElement('li');
            li.classList.add('suggestion-item');
            li.textContent = influencer.name;
            li.addEventListener('click', () => {
                searchInput.value = influencer.name;
                hideSuggestions();
                performSearch(influencer.name);
            });
            suggestionsList.appendChild(li);
        });
        suggestionsList.style.display = 'block';
    } else {
        hideSuggestions();
        if (!response.success) {
             console.error('Error fetching suggestions:', response.error);
        }
    }
  }

  // Function to hide suggestions
  function hideSuggestions() {
      if (suggestionsList) {
         suggestionsList.innerHTML = '';
         suggestionsList.style.display = 'none';
      }
  }

  function closeModal() {
    if (modal) {
      modal.style.display = 'none';
    }
  }

  function showLoading() {
    if (loadingIndicator) {
      loadingIndicator.style.display = 'flex';
    }
  }

  function hideLoading() {
    if (loadingIndicator) {
      loadingIndicator.style.display = 'none';
    }
  }
  
  function hideSecondaryPanels() {
    // Hide category, affiliation, ideology panels
    if (browseOptions) browseOptions.style.display = 'none';
  }

  // Ensure no remnants of mock functions exist below this line

}); // Closing bracket for DOMContentLoaded