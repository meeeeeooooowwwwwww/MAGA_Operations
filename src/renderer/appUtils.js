// Application utilities
// Provides helper functions for common tasks

// Safe IPC call wrapper
// In production, this would use actual IPC to communicate with the main process
// For now, this is a mock implementation
window.appUtils = {
    safeIpcCall: function(channel, data, successCallback, errorCallback) {
        console.log(`IPC call made to channel: ${channel} with data:`, data);
        
        // Mock implementation for the demo
        if (channel === 'search-politicians') {
            // Mock search results
            setTimeout(() => {
                const mockResults = [
                    { 
                        id: 'pol1', 
                        name: 'John Smith', 
                        role: 'Senator',
                        party: 'Republican',
                        state: 'TX' 
                    },
                    { 
                        id: 'pol2', 
                        name: 'Jane Doe', 
                        role: 'Representative',
                        party: 'Democrat',
                        state: 'CA',
                        district: '12'
                    },
                    { 
                        id: 'pol3', 
                        name: 'Michael Johnson', 
                        role: 'Senator',
                        party: 'Republican',
                        state: 'FL' 
                    },
                    { 
                        id: 'pol4', 
                        name: 'Emily Williams', 
                        role: 'Representative',
                        party: 'Democrat',
                        state: 'NY',
                        district: '9'
                    },
                    { 
                        id: 'pol5', 
                        name: 'James Wilson', 
                        role: 'Governor',
                        party: 'Independent',
                        state: 'CO'
                    }
                ];
                
                // Filter based on search term (case-insensitive)
                const filteredResults = mockResults.filter(pol => 
                    pol.name.toLowerCase().includes(data.toLowerCase()) ||
                    pol.role.toLowerCase().includes(data.toLowerCase()) ||
                    pol.state.toLowerCase().includes(data.toLowerCase()) ||
                    (pol.district && pol.district.includes(data))
                );
                
                successCallback(filteredResults);
            }, 500);
        }
        else if (channel === 'get-politician') {
            // Mock politician data
            setTimeout(() => {
                // Mock politician data based on ID
                let mockPolitician = null;
                
                if (data === 'pol1') {
                    mockPolitician = {
                        id: 'pol1',
                        name: 'John Smith',
                        role: 'Senator',
                        party: 'Republican',
                        state: 'TX',
                        bio: 'John Smith is a senior Senator from Texas with a focus on defense and energy policy. Prior to his Senate service, he was a business owner in the energy sector.',
                        committees: ['Armed Services', 'Energy and Natural Resources', 'Finance'],
                        recentVotes: [
                            { date: '2023-10-20', bill: 'S.1234', vote: 'Yes', description: 'Defense Appropriations Act' },
                            { date: '2023-10-15', bill: 'S.5678', vote: 'No', description: 'Climate Research Funding' }
                        ],
                        contacts: {
                            email: 'john.smith@senate.example.gov',
                            phone: '202-555-1234',
                            office: '123 Senate Office Building, Washington DC',
                            twitter: '@senatorsmith'
                        }
                    };
                }
                else if (data === 'pol2') {
                    mockPolitician = {
                        id: 'pol2',
                        name: 'Jane Doe',
                        role: 'Representative',
                        party: 'Democrat',
                        state: 'CA',
                        district: '12',
                        bio: 'Jane Doe represents California\'s 12th district with a focus on healthcare and education reform. She previously served on the San Francisco Board of Supervisors.',
                        committees: ['Education and Labor', 'Ways and Means', 'Science, Space, and Technology'],
                        recentVotes: [
                            { date: '2023-10-18', bill: 'H.R.2468', vote: 'Yes', description: 'Education Opportunity Act' },
                            { date: '2023-10-12', bill: 'H.R.3579', vote: 'Yes', description: 'Healthcare Expansion Act' }
                        ],
                        contacts: {
                            email: 'jane.doe@house.example.gov',
                            phone: '202-555-5678',
                            office: '456 House Office Building, Washington DC',
                            twitter: '@repdoe'
                        }
                    };
                }
                else if (data === 'pol3') {
                    mockPolitician = {
                        id: 'pol3',
                        name: 'Michael Johnson',
                        role: 'Senator',
                        party: 'Republican',
                        state: 'FL',
                        bio: 'Michael Johnson is a first-term Senator from Florida focused on economic policy and immigration reform. He previously served as Florida\'s State Treasurer.',
                        committees: ['Banking, Housing, and Urban Affairs', 'Commerce, Science, and Transportation', 'Small Business and Entrepreneurship'],
                        recentVotes: [
                            { date: '2023-10-17', bill: 'S.9012', vote: 'Yes', description: 'Small Business Relief Act' },
                            { date: '2023-10-10', bill: 'S.3456', vote: 'No', description: 'Immigration Reform Act' }
                        ],
                        contacts: {
                            email: 'michael.johnson@senate.example.gov',
                            phone: '202-555-9012',
                            office: '789 Senate Office Building, Washington DC',
                            twitter: '@senjohnson'
                        }
                    };
                }
                else if (data === 'pol4') {
                    mockPolitician = {
                        id: 'pol4',
                        name: 'Emily Williams',
                        role: 'Representative',
                        party: 'Democrat',
                        state: 'NY',
                        district: '9',
                        bio: 'Emily Williams represents New York\'s 9th district with a focus on urban development and financial regulation. She has a background in finance and public policy.',
                        committees: ['Financial Services', 'Oversight and Reform', 'Foreign Affairs'],
                        recentVotes: [
                            { date: '2023-10-19', bill: 'H.R.8765', vote: 'Yes', description: 'Financial Reform Act' },
                            { date: '2023-10-14', bill: 'H.R.1357', vote: 'No', description: 'Tax Relief Act' }
                        ],
                        contacts: {
                            email: 'emily.williams@house.example.gov',
                            phone: '202-555-1357',
                            office: '321 House Office Building, Washington DC',
                            twitter: '@repwilliams'
                        }
                    };
                }
                else if (data === 'pol5') {
                    mockPolitician = {
                        id: 'pol5',
                        name: 'James Wilson',
                        role: 'Governor',
                        party: 'Independent',
                        state: 'CO',
                        bio: 'James Wilson is serving his second term as Colorado\'s governor. He has focused on environmental conservation, renewable energy, and balanced budgets.',
                        recentActions: [
                            { date: '2023-10-16', action: 'Signed executive order on renewable energy targets' },
                            { date: '2023-10-08', action: 'Proposed state budget for fiscal year 2024' }
                        ],
                        contacts: {
                            email: 'governor@colorado.example.gov',
                            phone: '303-555-2468',
                            office: 'Colorado State Capitol, Denver CO',
                            twitter: '@govwilson'
                        }
                    };
                }
                
                // Return the mock data or null if not found
                successCallback(mockPolitician);
            }, 300);
        }
        else if (channel === 'search-influencers') {
            // Mock influencer search results
            setTimeout(() => {
                const mockResults = [
                    { 
                        id: 'inf1', 
                        name: 'Alex Media', 
                        platform: 'Twitter',
                        outlet: 'Independent',
                        followers: '1.2M',
                        type: 'journalist'
                    },
                    { 
                        id: 'inf2', 
                        name: 'Sarah Broadcast', 
                        platform: 'CNN',
                        outlet: 'CNN',
                        followers: '800K',
                        type: 'television'
                    },
                    { 
                        id: 'inf3', 
                        name: 'Mike Reporter', 
                        platform: 'Fox News',
                        outlet: 'Fox News',
                        followers: '1.5M',
                        type: 'television'
                    },
                    { 
                        id: 'inf4', 
                        name: 'Taylor Influencer', 
                        platform: 'Instagram',
                        outlet: 'Independent',
                        followers: '5.2M',
                        type: 'social'
                    }
                ];
                
                // Filter based on search term (case-insensitive)
                const filteredResults = mockResults.filter(inf => 
                    inf.name.toLowerCase().includes(data.toLowerCase()) ||
                    inf.platform.toLowerCase().includes(data.toLowerCase()) ||
                    inf.outlet.toLowerCase().includes(data.toLowerCase()) ||
                    inf.type.toLowerCase().includes(data.toLowerCase())
                );
                
                successCallback(filteredResults);
            }, 500); // Simulate network delay
        }
        else {
            // Unknown channel or error condition
            if (errorCallback) {
                errorCallback({ message: `Unknown IPC channel: ${channel}` });
            }
        }
    }
}; 