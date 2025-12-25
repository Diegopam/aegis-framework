"""
Aegis App - Main Application Class
High-level API for creating Aegis applications
"""

import os
import json
from aegis.core.window import AegisWindow


class AegisApp:
    """
    Main entry point for Aegis applications
    
    Usage:
        app = AegisApp()
        app.run()
    """
    
    def __init__(self, config_path=None):
        """
        Initialize Aegis application
        
        Args:
            config_path: Path to aegis.config.json (optional)
        """
        self.config = self._load_config(config_path)
        self.window = None
        self.project_dir = os.getcwd()
        
    def _load_config(self, config_path=None):
        """Load configuration from aegis.config.json"""
        if config_path is None:
            config_path = 'aegis.config.json'
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            'name': 'Aegis App',
            'title': 'Aegis App',
            'version': '1.0.0',
            'main': 'index.html',
            'preload': 'preload.js',
            'width': 1200,
            'height': 800,
            'resizable': True,
            'frame': True,
            'devTools': True,
            'contextMenu': True
        }
    
    def create_window(self, **options):
        """
        Create a new window with optional overrides
        
        Args:
            **options: Override config options for this window
        """
        window_config = {**self.config, **options}
        self.window = AegisWindow(window_config)
        
        # Inject Aegis API
        preload_path = os.path.join(self.project_dir, self.config.get('preload', 'preload.js'))
        self.window.inject_aegis_api(preload_path)
        
        return self.window
    
    def run(self):
        """Start the application"""
        if self.window is None:
            self.create_window()
        
        # Load main HTML file
        main_file = os.path.join(self.project_dir, self.config.get('main', 'index.html'))
        self.window.load_file(main_file)
        
        # Start the main loop
        self.window.run()


def run_app(config_path=None):
    """
    Convenience function to run an Aegis app
    
    Args:
        config_path: Optional path to config file
    """
    app = AegisApp(config_path)
    app.run()


# Allow running as module: python -m aegis.core.aegis
if __name__ == '__main__':
    run_app()
