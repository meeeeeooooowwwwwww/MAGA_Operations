console.log('[landing.js] Script loaded');

document.addEventListener('DOMContentLoaded', () => {
    console.log('[landing.js] DOMContentLoaded event fired');
    
    // Initialize standard sidebar navigation
    window.appUtils.initializeSidebarNavigation('home');

    // --- Action Buttons --- 
    // Explore
    const explorePoliticiansButton = document.getElementById('action-explore-politicians'); 
    const exploreInfluencersButton = document.getElementById('action-explore-influencers');
    const exploreFundingButton = document.getElementById('action-explore-funding');
    // Generate
    const generateReportButton = document.getElementById('action-generate-report');
    const generatePostButton = document.getElementById('action-generate-post');
    const generateEmailButton = document.getElementById('action-generate-email');

    // --- Event Listeners --- 
    // (No longer need navigateTo helper here)

    // Action Buttons Navigation/Placeholders
    if (explorePoliticiansButton) explorePoliticiansButton.addEventListener('click', () => window.appUtils.navigateTo('politician-view.html'));
    if (exploreInfluencersButton) exploreInfluencersButton.addEventListener('click', () => window.appUtils.navigateTo('influencer-view.html'));
    window.appUtils.addPlaceholderListener(exploreFundingButton, 'Explore Funding & Donors');

    // Link Generate buttons to the new page
    if (generateReportButton) generateReportButton.addEventListener('click', () => window.appUtils.navigateTo('generate-intel.html?type=brief'));
    if (generatePostButton) generatePostButton.addEventListener('click', () => window.appUtils.navigateTo('generate-intel.html?type=post'));
    if (generateEmailButton) generateEmailButton.addEventListener('click', () => window.appUtils.navigateTo('generate-intel.html?type=email'));

}); 