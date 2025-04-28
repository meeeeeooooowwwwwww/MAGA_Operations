// generate-intel.js

console.log('[generate-intel.js] Script loaded');

document.addEventListener('DOMContentLoaded', () => {
    console.log('[generate-intel.js] DOMContentLoaded event fired');

    // --- Sidebar Navigation --- 
    const homeSidebarButton = document.getElementById('nav-home');
    const exploreSidebarButton = document.getElementById('nav-explore');
    const generateSidebarButton = document.getElementById('nav-generate');
    const settingsSidebarButton = document.getElementById('nav-settings-sidebar');

    // --- Output Type Selection --- 
    const generationTypeButtons = document.querySelectorAll('.generation-type-btn');
    const briefOptions = document.getElementById('brief-options');
    const postOptions = document.getElementById('post-options');
    const emailOptions = document.getElementById('email-options');
    const generateTypeLabel = document.getElementById('generate-type-label');

    // --- Form Elements --- 
    const targetPoliticiansInput = document.getElementById('target-politicians');
    const selectedPoliticiansDiv = document.getElementById('selected-politicians');
    const targetInfluencersInput = document.getElementById('target-influencers');
    const selectedInfluencersDiv = document.getElementById('selected-influencers');
    const keyTopicsInput = document.getElementById('key-topics');
    const generateButton = document.getElementById('generate-btn');

    // --- Output Area --- 
    const generationOutputDiv = document.getElementById('generation-output');
    const outputTextarea = document.getElementById('output-textarea');
    const copyOutputButton = document.getElementById('copy-output-btn');
    const refineOutputButton = document.getElementById('refine-output-btn');

    let currentGenerationType = 'brief'; // Default

    // --- Event Listeners ---

    // Helper for navigation
    const navigateTo = (url) => {
        console.log(`[generate-intel.js] Navigating to ${url}...`);
        window.location.href = url;
    };

    // Sidebar Navigation
    if (homeSidebarButton) homeSidebarButton.addEventListener('click', () => navigateTo('landing.html'));
    if (exploreSidebarButton) exploreSidebarButton.addEventListener('click', () => {
        // Need to decide where Explore goes - maybe politician view first?
        console.log('[generate-intel.js] Explore button clicked (Placeholder Navigation)');
        navigateTo('politician-view.html'); 
    });
    if (generateSidebarButton) generateSidebarButton.addEventListener('click', () => navigateTo('generate-intel.html')); // Already here
    if (settingsSidebarButton) settingsSidebarButton.addEventListener('click', () => console.log('[generate-intel.js] Settings button clicked (Placeholder)'));

    // Output Type Selection
    generationTypeButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Update active button state
            generationTypeButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // Update current type and visible options
            currentGenerationType = button.dataset.type;
            briefOptions.style.display = (currentGenerationType === 'brief') ? 'block' : 'none';
            postOptions.style.display = (currentGenerationType === 'post') ? 'block' : 'none';
            emailOptions.style.display = (currentGenerationType === 'email') ? 'block' : 'none';
            
            // Update generate button label
             generateTypeLabel.textContent = button.textContent.trim();
             console.log(`[generate-intel.js] Switched generation type to: ${currentGenerationType}`);
        });
    });

    // TODO: Add autocomplete/selection logic for politicians and influencers inputs

    // Generate Button Click
    generateButton.addEventListener('click', () => {
        console.log('[generate-intel.js] Generate button clicked');
        generationOutputDiv.style.display = 'block';
        outputTextarea.value = `Generating ${currentGenerationType}...

Targets:
 Politicans: ${targetPoliticiansInput.value || 'None'}
 Influencers: ${targetInfluencersInput.value || 'None'}

Topics: ${keyTopicsInput.value || 'None'}

Options: ${JSON.stringify(getOptions())}

(AI interaction not implemented yet)`;
        
        // In a real scenario, collect data and send to main process via IPC
        // e.g., window.electronAPI.generateIntelligence({ type: currentGenerationType, ... })
    });
    
    // Copy Button Click
    copyOutputButton.addEventListener('click', () => {
        outputTextarea.select();
        document.execCommand('copy');
        console.log('[generate-intel.js] Output copied to clipboard');
        // Maybe show a temporary confirmation message
    });

    // Function to get selected options based on type
    function getOptions() {
        const options = {};
        if (currentGenerationType === 'brief') {
            options.includeSummary = document.getElementById('brief-include-summary').checked;
            options.includeFunding = document.getElementById('brief-include-funding').checked;
            options.includeSources = document.getElementById('brief-include-sources').checked;
        } else if (currentGenerationType === 'post') {
            options.platform = document.getElementById('post-platform').value;
            options.tone = document.getElementById('post-tone').value;
        } else if (currentGenerationType === 'email') {
            options.recipientType = document.getElementById('email-recipient').value;
        }
        return options;
    }

}); 