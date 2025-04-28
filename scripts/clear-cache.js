const fs = require('fs');
const path = require('path');

// Path to cache directory
const CACHE_DIR = path.join(__dirname, '..', 'cache');

/**
 * Clear the tweet cache
 */
function clearCache() {
    console.log('Clearing tweet cache...');
    
    if (!fs.existsSync(CACHE_DIR)) {
        console.log('Cache directory does not exist. Creating it...');
        fs.mkdirSync(CACHE_DIR, { recursive: true });
        console.log('Cache directory created.');
        return;
    }
    
    try {
        const files = fs.readdirSync(CACHE_DIR);
        
        if (files.length === 0) {
            console.log('Cache is already empty.');
            return;
        }
        
        let count = 0;
        
        files.forEach(file => {
            const filePath = path.join(CACHE_DIR, file);
            
            // Only remove JSON files to be safe
            if (file.endsWith('.json')) {
                fs.unlinkSync(filePath);
                count++;
            }
        });
        
        console.log(`Cache cleared. Removed ${count} cached files.`);
    } catch (error) {
        console.error('Error clearing cache:', error);
    }
}

clearCache(); 