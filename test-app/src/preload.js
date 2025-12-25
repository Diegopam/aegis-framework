/**
 * Aegis Preload Configuration
 * 
 * This file controls which Aegis APIs are exposed to your frontend.
 * For security, only expose the APIs you actually need.
 */

// Expose specific APIs
Aegis.expose([
    'read',     // File reading
    'write',    // File writing  
    'run',      // Command execution
    'dialog',   // Native dialogs
    'app',      // App control
    'exists',   // File existence check
    'mkdir',    // Create directories
    'env'       // Environment variables
]);

// Configure Aegis
Aegis.config({
    allowRemoteContent: false,
    enableDevTools: true
});

console.log('✅ Preload configured');
