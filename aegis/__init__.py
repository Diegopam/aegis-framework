"""
Aegis - Lightweight AppImage Framework
A modern alternative to Electron using WebKit2GTK and Python
"""

__version__ = "0.1.0"
__author__ = "Diego"

# Lazy imports to allow CLI to work without GTK installed
def __getattr__(name):
    if name == 'AegisApp':
        from aegis.core.aegis import AegisApp
        return AegisApp
    elif name == 'AegisWindow':
        from aegis.core.window import AegisWindow
        return AegisWindow
    raise AttributeError(f"module 'aegis' has no attribute '{name}'")

__all__ = ['AegisApp', 'AegisWindow']
