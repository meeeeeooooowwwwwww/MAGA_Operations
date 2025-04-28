// preload.js

const { contextBridge, ipcRenderer } = require('electron');

console.log('[Preload] Script loaded - Simplified Version');

// Expose necessary Electron APIs safely
contextBridge.exposeInMainWorld('electronAPI', {
  // Function to send logs to the main process
  log: (level, message) => {
    const timestamp = new Date().toISOString();
    // Note: Use ipcRenderer directly here, as this IS the preload script
    ipcRenderer.send('log-message', { timestamp, level, message }); 
  },
  // Function to invoke main process handlers and get a response
  invoke: (channel, ...args) => {
      console.log(`[Preload] Invoking '${channel}' with args:`, args);
      // Note: Use ipcRenderer directly here
      return ipcRenderer.invoke(channel, ...args);
  },
  // Function to listen to events from the main process
  on: (channel, callback) => {
      console.log(`[Preload] Setting up event listener for '${channel}'`);
      // Validate channel name
      if (typeof channel !== 'string' || !channel.startsWith('app:')) {
          console.error(`[Preload] Invalid channel name '${channel}'. Channel names must start with 'app:'`);
          return;
      }
      
      // Note: Using a function wrapper to ensure 'this' context in the callback
      const listener = (_, ...args) => callback(...args);
      ipcRenderer.on(channel, listener);
      
      // Return a function to remove the listener
      return () => {
          console.log(`[Preload] Removing event listener for '${channel}'`);
          ipcRenderer.removeListener(channel, listener);
      };
  }
});

console.log('[Preload] electronAPI (invoke, log) exposed. Console interception REMOVED for testing.');

// REMOVED Console Interception Logic for testing
/*
const originalConsole = { ...console };
console.log = (...args) => {
    originalConsole.log(...args);
    ipcRenderer.send('log-message', { timestamp: new Date().toISOString(), level: 'log', message: args.join(' ') });
};
console.warn = (...args) => {
    originalConsole.warn(...args);
    ipcRenderer.send('log-message', { timestamp: new Date().toISOString(), level: 'warn', message: args.join(' ') });
};
console.error = (...args) => {
    originalConsole.error(...args);
    ipcRenderer.send('log-message', { timestamp: new Date().toISOString(), level: 'error', message: args.join(' ') });
};
console.info = (...args) => {
    originalConsole.info(...args);
    ipcRenderer.send('log-message', { timestamp: new Date().toISOString(), level: 'info', message: args.join(' ') });
};
console.debug = (...args) => {
    originalConsole.debug(...args);
    ipcRenderer.send('log-message', { timestamp: new Date().toISOString(), level: 'debug', message: args.join(' ') });
};
*/