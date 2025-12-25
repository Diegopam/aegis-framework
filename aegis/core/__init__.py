"""
Aegis Core Module
Contains window management and IPC bridge
"""

# Lazy imports to allow CLI to work without GTK
def __getattr__(name):
    if name == 'AegisApp':
        from aegis.core.aegis import AegisApp
        return AegisApp
    elif name == 'AegisWindow':
        from aegis.core.window import AegisWindow
        return AegisWindow
    raise AttributeError(f"module 'aegis.core' has no attribute '{name}'")

__all__ = ['AegisApp', 'AegisWindow']
