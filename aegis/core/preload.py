"""
Aegis Preload Security System
Parses preload.js to determine which APIs should be exposed
"""

import re
import json
import os
from typing import Set, Dict, Any, List


class PreloadManager:
    """
    Manages the preload security configuration
    
    The preload.js file defines which Aegis APIs are exposed to the frontend.
    This provides a security layer to prevent malicious code from accessing
    sensitive system operations.
    """
    
    def __init__(self):
        self.allowed_apis: Set[str] = set()
        self.custom_handlers: Dict[str, str] = {}
        self.config: Dict[str, Any] = {}
    
    def load(self, preload_path: str) -> bool:
        """
        Load and parse a preload.js file
        
        Args:
            preload_path: Path to preload.js
            
        Returns:
            True if loaded successfully
        """
        if not os.path.exists(preload_path):
            return False
        
        with open(preload_path, 'r') as f:
            content = f.read()
        
        self._parse_preload(content)
        return True
    
    def _parse_preload(self, content: str):
        """Parse preload.js content to extract configuration"""
        
        # Look for Aegis.expose() calls
        # Aegis.expose(['read', 'write', 'run'])
        expose_pattern = r'Aegis\.expose\s*\(\s*\[(.*?)\]\s*\)'
        matches = re.findall(expose_pattern, content, re.DOTALL)
        
        for match in matches:
            # Extract API names from the array
            apis = re.findall(r'["\'](\w+(?:\.\w+)*)["\']', match)
            self.allowed_apis.update(apis)
        
        # Look for Aegis.exposeAll() - expose everything
        if 'Aegis.exposeAll()' in content:
            self.allowed_apis = {'*'}
        
        # Look for Aegis.config() calls
        config_pattern = r'Aegis\.config\s*\(\s*(\{.*?\})\s*\)'
        config_matches = re.findall(config_pattern, content, re.DOTALL)
        
        for match in config_matches:
            try:
                # Try to parse as JSON (basic JS object syntax)
                # Replace single quotes with double quotes for JSON
                json_str = match.replace("'", '"')
                self.config.update(json.loads(json_str))
            except json.JSONDecodeError:
                pass
        
        # Look for custom handler definitions
        # Aegis.handle('myAction', async (data) => { ... })
        handler_pattern = r'Aegis\.handle\s*\(\s*["\'](\w+)["\']\s*,'
        handler_matches = re.findall(handler_pattern, content)
        
        for handler_name in handler_matches:
            self.custom_handlers[handler_name] = content
    
    def is_api_allowed(self, api_name: str) -> bool:
        """
        Check if an API is allowed
        
        Args:
            api_name: Full API name (e.g., 'read', 'dialog.open')
            
        Returns:
            True if the API is allowed
        """
        # If exposeAll was used, everything is allowed
        if '*' in self.allowed_apis:
            return True
        
        # Check exact match
        if api_name in self.allowed_apis:
            return True
        
        # Check namespace match (e.g., 'dialog' allows 'dialog.open')
        namespace = api_name.split('.')[0]
        if namespace in self.allowed_apis:
            return True
        
        # If no APIs are explicitly allowed, allow all by default
        # (for backwards compatibility and ease of use)
        if not self.allowed_apis:
            return True
        
        return False
    
    def get_allowed_list(self) -> List[str]:
        """Get list of allowed APIs"""
        return list(self.allowed_apis)
    
    def generate_js_config(self) -> str:
        """Generate JavaScript configuration for the frontend"""
        if '*' in self.allowed_apis:
            allowed_js = '["*"]'
        else:
            allowed_js = json.dumps(list(self.allowed_apis))
        
        return f"""
// Aegis Preload Configuration (auto-generated)
window.__aegisAllowedAPIs = {allowed_js};
window.__aegisConfig = {json.dumps(self.config)};
"""


def create_default_preload() -> str:
    """Generate default preload.js content"""
    return '''/**
 * Aegis Preload Configuration
 * 
 * This file controls which Aegis APIs are exposed to your frontend.
 * For security, only expose the APIs you actually need.
 */

// Expose specific APIs
Aegis.expose([
    'read',        // File reading
    'write',       // File writing
    'run',         // Command execution
    'dialog',      // Native dialogs (open, save, message)
    'app',         // App control (quit, minimize, maximize)
    'exists',      // Check file/directory existence
    'mkdir',       // Create directories
    'env'          // Environment variables
]);

// Or expose everything (not recommended for production):
// Aegis.exposeAll();

// Optional: Configure Aegis behavior
Aegis.config({
    allowRemoteContent: false,
    enableDevTools: true
});
'''
