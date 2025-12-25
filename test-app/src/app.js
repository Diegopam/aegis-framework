/**
 * Aegis App - Main JavaScript
 */

// Wait for Aegis to be ready
document.addEventListener('DOMContentLoaded', async () => {
    const output = document.getElementById('output');
    
    // Check if running in Aegis
    if (!Aegis.isAegis()) {
        output.textContent = 'Not running in Aegis environment.\nRun with: aegis dev';
        return;
    }
    
    output.textContent = '✅ Aegis is ready!\n\nClick a button to test the API.';
    
    // Read file button
    document.getElementById('btn-read').addEventListener('click', async () => {
        try {
            const result = await Aegis.read({ path: '.' });
            output.textContent = 'Directory contents:\n\n' + 
                result.entries.map(e => `${e.isDirectory ? '📁' : '📄'} ${e.name}`).join('\n');
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
        }
    });
    
    // Run command button
    document.getElementById('btn-run').addEventListener('click', async () => {
        try {
            const result = await Aegis.run({ sh: 'uname -a' });
            output.textContent = 'System info:\n\n' + result.output;
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
        }
    });
    
    // Dialog button
    document.getElementById('btn-dialog').addEventListener('click', async () => {
        try {
            const result = await Aegis.dialog.message({
                type: 'info',
                title: 'Hello from Aegis!',
                message: 'This is a native GTK dialog.\nPretty cool, right?'
            });
            output.textContent = 'Dialog closed! Response: ' + JSON.stringify(result);
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
        }
    });
});
