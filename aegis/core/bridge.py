"""
Aegis Bridge - Python ↔ JavaScript Communication
Handles IPC messaging between frontend and backend
"""

import json
import os
import subprocess
import threading
from typing import Callable, Dict, Any, Optional


class AegisBridge:
    """
    Manages communication between Python backend and JavaScript frontend
    """
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._allowed_actions: set = set()
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register built-in action handlers"""
        self.register('read', self._handle_read)
        self.register('write', self._handle_write)
        self.register('run', self._handle_run)
        self.register('exists', self._handle_exists)
        self.register('mkdir', self._handle_mkdir)
        self.register('remove', self._handle_remove)
        self.register('copy', self._handle_copy)
        self.register('move', self._handle_move)
        self.register('env', self._handle_env)
    
    def register(self, action: str, handler: Callable):
        """
        Register a custom action handler
        
        Args:
            action: Action name (e.g., 'myAction')
            handler: Function that takes payload dict and returns result dict
        """
        self._handlers[action] = handler
    
    def allow(self, *actions: str):
        """
        Set which actions are allowed (preload security)
        
        Args:
            *actions: Action names to allow
        """
        self._allowed_actions.update(actions)
    
    def allow_all(self):
        """Allow all registered actions"""
        self._allowed_actions = set(self._handlers.keys())
    
    def is_allowed(self, action: str) -> bool:
        """Check if an action is allowed"""
        # If no restrictions set, allow all
        if not self._allowed_actions:
            return True
        return action in self._allowed_actions
    
    def process(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an action request
        
        Args:
            action: Action name
            payload: Action payload
            
        Returns:
            Result dictionary
        """
        if not self.is_allowed(action):
            raise PermissionError(f"Action '{action}' is not allowed by preload")
        
        handler = self._handlers.get(action)
        if not handler:
            raise ValueError(f"Unknown action: {action}")
        
        return handler(payload)
    
    # ==================== Built-in Handlers ====================
    
    def _handle_read(self, payload: Dict) -> Dict:
        """Read file contents"""
        path = payload.get('path', '.')
        file = payload.get('file')
        encoding = payload.get('encoding', 'utf-8')
        binary = payload.get('binary', False)
        
        if file:
            full_path = os.path.join(path, file)
        else:
            full_path = path
        
        if os.path.isdir(full_path):
            # List directory
            entries = []
            for entry in os.listdir(full_path):
                entry_path = os.path.join(full_path, entry)
                stat = os.stat(entry_path)
                entries.append({
                    'name': entry,
                    'isDirectory': os.path.isdir(entry_path),
                    'isFile': os.path.isfile(entry_path),
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
            return {'entries': entries, 'path': full_path}
        else:
            # Read file
            mode = 'rb' if binary else 'r'
            with open(full_path, mode, encoding=None if binary else encoding) as f:
                content = f.read()
                if binary:
                    import base64
                    content = base64.b64encode(content).decode('ascii')
            return {'content': content, 'path': full_path}
    
    def _handle_write(self, payload: Dict) -> Dict:
        """Write file contents"""
        path = payload.get('path', '.')
        file = payload.get('file')
        content = payload.get('content', '')
        encoding = payload.get('encoding', 'utf-8')
        append = payload.get('append', False)
        binary = payload.get('binary', False)
        
        if file:
            full_path = os.path.join(path, file)
        else:
            full_path = path
        
        # Create parent directories
        parent = os.path.dirname(full_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        
        mode = 'ab' if append and binary else 'a' if append else 'wb' if binary else 'w'
        
        with open(full_path, mode, encoding=None if binary else encoding) as f:
            if binary:
                import base64
                f.write(base64.b64decode(content))
            else:
                f.write(content)
        
        return {'success': True, 'path': full_path}
    
    def _handle_run(self, payload: Dict) -> Dict:
        """Execute commands"""
        if 'py' in payload:
            # Execute Python code
            code = payload['py']
            local_vars = {}
            try:
                # Try eval first (for expressions)
                result = eval(code)
                return {'output': str(result), 'exitCode': 0}
            except SyntaxError:
                # Fall back to exec (for statements)
                exec(code, {}, local_vars)
                return {'output': str(local_vars), 'exitCode': 0}
            except Exception as e:
                return {'error': str(e), 'exitCode': 1}
        
        elif 'sh' in payload:
            # Execute shell command
            cmd = payload['sh']
            cwd = payload.get('cwd', os.getcwd())
            timeout = payload.get('timeout', None)
            
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    timeout=timeout
                )
                return {
                    'output': result.stdout,
                    'error': result.stderr,
                    'exitCode': result.returncode
                }
            except subprocess.TimeoutExpired:
                return {'error': 'Command timed out', 'exitCode': -1}
            except Exception as e:
                return {'error': str(e), 'exitCode': -1}
        
        return {'error': 'No py or sh command specified', 'exitCode': -1}
    
    def _handle_exists(self, payload: Dict) -> Dict:
        """Check if path exists"""
        path = payload.get('path')
        return {
            'exists': os.path.exists(path),
            'isFile': os.path.isfile(path),
            'isDirectory': os.path.isdir(path)
        }
    
    def _handle_mkdir(self, payload: Dict) -> Dict:
        """Create directory"""
        path = payload.get('path')
        recursive = payload.get('recursive', True)
        
        if recursive:
            os.makedirs(path, exist_ok=True)
        else:
            os.mkdir(path)
        
        return {'success': True, 'path': path}
    
    def _handle_remove(self, payload: Dict) -> Dict:
        """Remove file or directory"""
        import shutil
        path = payload.get('path')
        recursive = payload.get('recursive', False)
        
        if os.path.isdir(path):
            if recursive:
                shutil.rmtree(path)
            else:
                os.rmdir(path)
        else:
            os.remove(path)
        
        return {'success': True}
    
    def _handle_copy(self, payload: Dict) -> Dict:
        """Copy file or directory"""
        import shutil
        src = payload.get('src')
        dest = payload.get('dest')
        
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
        
        return {'success': True, 'dest': dest}
    
    def _handle_move(self, payload: Dict) -> Dict:
        """Move/rename file or directory"""
        import shutil
        src = payload.get('src')
        dest = payload.get('dest')
        
        shutil.move(src, dest)
        return {'success': True, 'dest': dest}
    
    def _handle_env(self, payload: Dict) -> Dict:
        """Get/set environment variables"""
        name = payload.get('name')
        value = payload.get('value')
        
        if value is not None:
            # Set environment variable
            os.environ[name] = value
            return {'success': True}
        elif name:
            # Get single variable
            return {'value': os.environ.get(name)}
        else:
            # Get all variables
            return {'env': dict(os.environ)}
