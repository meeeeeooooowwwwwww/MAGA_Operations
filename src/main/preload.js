const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Get and search politicians
  getLegislators: () => ipcRenderer.invoke('get-politicians'),
  getPoliticianDetails: (id) => ipcRenderer.invoke('get-politician-details', id),
  
  // Tweet analysis
  analyzeTweet: (politicianId) => ipcRenderer.invoke('analyze-tweet', politicianId),
  getLatestTweet: (politicianId) => ipcRenderer.invoke('get-latest-tweet', politicianId),
  
  // Get all politicians (for sidebar list)
  getPoliticians: () => ipcRenderer.invoke('get-politicians')
});

// --- BEGIN CONSOLE LOG FORWARDING ---
// Forward console logs from renderer to main process
const originalConsoleLog = console.log;
const originalConsoleWarn = console.warn;
const originalConsoleError = console.error;

function formatLogMessage(level, args) {
    // Convert args to strings, handling objects/arrays
    const messageParts = args.map(arg => {
        if (typeof arg === 'object' && arg !== null) {
            try {
                return JSON.stringify(arg);
            } catch (e) {
                return '[Unserializable Object]';
            }
        }
        return String(arg);
    });
    return messageParts.join(' ');
}

console.log = (...args) => {
    originalConsoleLog.apply(console, args);
    ipcRenderer.send('log-message', {
        timestamp: new Date().toISOString(),
        level: 'info',
        message: formatLogMessage('info', args)
    });
};

console.warn = (...args) => {
    originalConsoleWarn.apply(console, args);
    ipcRenderer.send('log-message', {
        timestamp: new Date().toISOString(),
        level: 'warn',
        message: formatLogMessage('warn', args)
    });
};

console.error = (...args) => {
    originalConsoleError.apply(console, args);
    ipcRenderer.send('log-message', {
        timestamp: new Date().toISOString(),
        level: 'error',
        message: formatLogMessage('error', args)
    });
};
// --- END CONSOLE LOG FORWARDING --- 