"""
Aegis Window Manager
Manages WebKit2GTK windows with full customization support
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')

from gi.repository import Gtk, WebKit2, Gdk, GLib
import json
import os
import threading
import urllib.request
import shutil


class AegisWindow(Gtk.Window):
    """
    A WebKit2GTK-based window with Aegis bridge integration
    """
    
    def __init__(self, config=None):
        super().__init__()
        
        self.config = config or {}
        self._setup_window()
        self._setup_webview()
        self._setup_bridge()
        
    def _setup_window(self):
        """Configure the main window"""
        # Window properties from config
        title = self.config.get('title', 'Aegis App')
        width = self.config.get('width', 1200)
        height = self.config.get('height', 800)
        resizable = self.config.get('resizable', True)
        decorated = self.config.get('frame', True)
        
        self.set_title(title)
        self.set_default_size(width, height)
        self.set_resizable(resizable)
        self.set_decorated(decorated)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Handle close
        self.connect('destroy', Gtk.main_quit)
        
        # Frameless window support
        if not decorated:
            self._setup_frameless()
    
    def _setup_frameless(self):
        """Setup frameless window with drag support"""
        self.set_app_paintable(True)
        
        # Enable dragging from anywhere
        self.drag_start_x = 0
        self.drag_start_y = 0
        
    def _setup_webview(self):
        """Setup WebKit2GTK webview"""
        # Create webview with settings
        self.webview = WebKit2.WebView()
        settings = self.webview.get_settings()
        
        # Enable developer tools
        settings.set_enable_developer_extras(True)
        settings.set_enable_javascript(True)
        settings.set_javascript_can_access_clipboard(True)
        settings.set_enable_write_console_messages_to_stdout(True)
        
        # Allow file access
        settings.set_allow_file_access_from_file_urls(True)
        settings.set_allow_universal_access_from_file_urls(True)
        
        # Hardware acceleration - disabled by default for compatibility
        # nouveau and some other drivers have issues with GPU acceleration
        settings.set_hardware_acceleration_policy(
            WebKit2.HardwareAccelerationPolicy.NEVER
        )
        
        # Disable context menu if configured
        if not self.config.get('contextMenu', True):
            self.webview.connect('context-menu', lambda *args: True)
        
        # Add to window
        self.add(self.webview)
        
    def _setup_bridge(self):
        """Setup JavaScript bridge for IPC"""
        # Get user content manager
        self.content_manager = self.webview.get_user_content_manager()
        
        # Register message handler for Aegis calls
        self.content_manager.register_script_message_handler('aegis')
        self.content_manager.connect(
            'script-message-received::aegis',
            self._on_message_received
        )
        
        # Pending callbacks for async responses
        self._pending_callbacks = {}
        self._callback_id = 0
        
    def _on_message_received(self, content_manager, js_result):
        """Handle messages from JavaScript"""
        callback_id = None
        try:
            # WebKit2 4.1 uses get_js_value()
            js_value = js_result.get_js_value()
            data = json.loads(js_value.to_string())
            
            action = data.get('action')
            payload = data.get('payload', {})
            callback_id = data.get('callbackId')
            
            print(f"[Aegis] Action: {action}, Payload: {payload}")
            
            # Check if this is an async action
            async_actions = {'run.async', 'download', 'copy.async'}
            
            if action in async_actions:
                # Handle in background thread - response sent via callback
                self._process_async_action(action, payload, callback_id)
            else:
                # Sync action - process and respond immediately
                result = self._process_action(action, payload)
                if callback_id:
                    self._send_response(callback_id, result)
                
        except Exception as e:
            print(f"[Aegis Bridge] Error: {e}")
            import traceback
            traceback.print_exc()
            if callback_id:
                self._send_error(callback_id, str(e))
    
    def _process_action(self, action, payload):
        """Process an Aegis action and return result"""
        handlers = {
            'read': self._handle_read,
            'write': self._handle_write,
            'run': self._handle_run,
            'exists': self._handle_exists,
            'mkdir': self._handle_mkdir,
            'remove': self._handle_remove,
            'copy': self._handle_copy,
            'move': self._handle_move,
            'dialog.open': self._handle_dialog_open,
            'dialog.save': self._handle_dialog_save,
            'dialog.message': self._handle_dialog_message,
            'app.quit': self._handle_app_quit,
            'app.minimize': self._handle_app_minimize,
            'app.maximize': self._handle_app_maximize,
            'app.getPath': self._handle_app_get_path,
            'window.startDrag': self._handle_window_start_drag,
            'window.resize': self._handle_window_resize,
            'window.setSize': self._handle_window_set_size,
            'window.getSize': self._handle_window_get_size,
            'window.setPosition': self._handle_window_set_position,
            'window.getPosition': self._handle_window_get_position,
        }
        
        handler = handlers.get(action)
        if handler:
            return handler(payload)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _send_response(self, callback_id, result):
        """Send successful response to JavaScript"""
        response = json.dumps({
            'callbackId': callback_id,
            'success': True,
            'data': result
        })
        script = f"window.__aegisResolve({response})"
        self.webview.evaluate_javascript(script, -1, None, None, None, None, None)
    
    def _send_error(self, callback_id, error):
        """Send error response to JavaScript"""
        response = json.dumps({
            'callbackId': callback_id,
            'success': False,
            'error': error
        })
        script = f"window.__aegisResolve({response})"
        self.webview.evaluate_javascript(script, -1, None, None, None, None, None)
    
    # ==================== Action Handlers ====================
    
    def _handle_read(self, payload):
        """Read file or directory contents"""
        path = payload.get('path', '.')
        file = payload.get('file')
        
        if file:
            # Read single file
            full_path = os.path.join(path, file)
            with open(full_path, 'r', encoding='utf-8') as f:
                return {'content': f.read(), 'path': full_path}
        else:
            # List directory
            entries = []
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                try:
                    stat = os.stat(full_path)
                    entries.append({
                        'name': entry,
                        'isDirectory': os.path.isdir(full_path),
                        'isFile': os.path.isfile(full_path),
                        'size': stat.st_size if os.path.isfile(full_path) else 0,
                        'modified': stat.st_mtime
                    })
                except (PermissionError, OSError):
                    # Skip files we can't access
                    entries.append({
                        'name': entry,
                        'isDirectory': False,
                        'isFile': True,
                        'size': 0,
                        'modified': 0
                    })
            return {'entries': entries, 'path': path}
    
    def _handle_write(self, payload):
        """Write content to file"""
        path = payload.get('path', '.')
        file = payload.get('file')
        content = payload.get('content', '')
        
        full_path = os.path.join(path, file)
        
        # Create directories if needed
        os.makedirs(os.path.dirname(full_path) or '.', exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {'success': True, 'path': full_path}
    
    def _handle_run(self, payload):
        """Execute Python or shell commands"""
        import subprocess
        
        if 'py' in payload:
            # Execute Python code
            try:
                result = eval(payload['py'])
                return {'output': str(result), 'exitCode': 0}
            except:
                exec_globals = {}
                exec(payload['py'], exec_globals)
                return {'output': '', 'exitCode': 0}
                
        elif 'sh' in payload:
            # Execute shell command
            result = subprocess.run(
                payload['sh'],
                shell=True,
                capture_output=True,
                text=True
            )
            return {
                'output': result.stdout,
                'error': result.stderr,
                'exitCode': result.returncode
            }
        
        return {'error': 'No command specified'}
    
    def _handle_exists(self, payload):
        """Check if path exists"""
        path = payload.get('path')
        return {
            'exists': os.path.exists(path),
            'isFile': os.path.isfile(path),
            'isDirectory': os.path.isdir(path)
        }
    
    def _handle_mkdir(self, payload):
        """Create directory"""
        path = payload.get('path')
        recursive = payload.get('recursive', True)
        
        if recursive:
            os.makedirs(path, exist_ok=True)
        else:
            os.mkdir(path)
        
        return {'success': True, 'path': path}
    
    def _handle_remove(self, payload):
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
    
    def _handle_copy(self, payload):
        """Copy file or directory"""
        import shutil
        src = payload.get('src')
        dest = payload.get('dest')
        
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
        
        return {'success': True, 'dest': dest}
    
    def _handle_move(self, payload):
        """Move/rename file or directory"""
        import shutil
        src = payload.get('src')
        dest = payload.get('dest')
        
        shutil.move(src, dest)
        return {'success': True, 'dest': dest}
    
    def _handle_dialog_open(self, payload):
        """Open file dialog"""
        dialog = Gtk.FileChooserDialog(
            title=payload.get('title', 'Open File'),
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add filters
        filters = payload.get('filters', [])
        for f in filters:
            file_filter = Gtk.FileFilter()
            file_filter.set_name(f.get('name', 'Files'))
            for ext in f.get('extensions', ['*']):
                file_filter.add_pattern(f'*.{ext}')
            dialog.add_filter(file_filter)
        
        response = dialog.run()
        result = None
        
        if response == Gtk.ResponseType.OK:
            if payload.get('multiple'):
                result = dialog.get_filenames()
            else:
                result = dialog.get_filename()
        
        dialog.destroy()
        return {'path': result}
    
    def _handle_dialog_save(self, payload):
        """Save file dialog"""
        dialog = Gtk.FileChooserDialog(
            title=payload.get('title', 'Save File'),
            parent=self,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        dialog.set_do_overwrite_confirmation(True)
        
        if payload.get('defaultName'):
            dialog.set_current_name(payload['defaultName'])
        
        response = dialog.run()
        result = dialog.get_filename() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        
        return {'path': result}
    
    def _handle_dialog_message(self, payload):
        """Show message dialog"""
        msg_type = {
            'info': Gtk.MessageType.INFO,
            'warning': Gtk.MessageType.WARNING,
            'error': Gtk.MessageType.ERROR,
            'question': Gtk.MessageType.QUESTION
        }.get(payload.get('type', 'info'), Gtk.MessageType.INFO)
        
        buttons = Gtk.ButtonsType.OK
        if payload.get('buttons') == 'yesno':
            buttons = Gtk.ButtonsType.YES_NO
        elif payload.get('buttons') == 'okcancel':
            buttons = Gtk.ButtonsType.OK_CANCEL
        
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=msg_type,
            buttons=buttons,
            text=payload.get('title', ''),
        )
        dialog.format_secondary_text(payload.get('message', ''))
        
        response = dialog.run()
        dialog.destroy()
        
        return {'response': response == Gtk.ResponseType.OK or response == Gtk.ResponseType.YES}
    
    def _handle_app_quit(self, payload):
        """Quit the application"""
        Gtk.main_quit()
        return {'success': True}
    
    def _handle_app_minimize(self, payload):
        """Minimize the window"""
        self.iconify()
        return {'success': True}
    
    def _handle_app_maximize(self, payload):
        """Toggle maximize"""
        if self.is_maximized():
            self.unmaximize()
        else:
            self.maximize()
        return {'success': True}
    
    def _handle_app_get_path(self, payload):
        """Get system paths with proper localization"""
        import subprocess
        name = payload.get('name', 'home')
        
        # Use xdg-user-dir for localized paths
        xdg_mapping = {
            'desktop': 'DESKTOP',
            'documents': 'DOCUMENTS',
            'downloads': 'DOWNLOAD',
            'music': 'MUSIC',
            'pictures': 'PICTURES',
            'videos': 'VIDEOS',
            'templates': 'TEMPLATES',
            'publicshare': 'PUBLICSHARE'
        }
        
        if name in xdg_mapping:
            try:
                result = subprocess.run(
                    ['xdg-user-dir', xdg_mapping[name]],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    return {'path': result.stdout.strip()}
            except:
                pass
        
        # Fallback paths
        home = os.path.expanduser('~')
        paths = {
            'home': home,
            'temp': '/tmp',
            'app': os.getcwd(),
            'root': '/'
        }
        
        return {'path': paths.get(name, home)}
    
    # ==================== Window Control Handlers ====================
    
    def _handle_window_start_drag(self, payload):
        """Start window drag operation - coordinates from JS"""
        x = payload.get('x', 0)
        y = payload.get('y', 0)
        button = payload.get('button', 1)
        
        # Use GLib.idle_add for thread safety
        def do_move():
            try:
                self.begin_move_drag(
                    button,
                    int(x),
                    int(y),
                    Gdk.CURRENT_TIME
                )
            except Exception as e:
                print(f"[Aegis] Move drag error: {e}")
            return False
        
        GLib.idle_add(do_move)
        return {'success': True}
    
    def _handle_window_resize(self, payload):
        """Start window resize operation"""
        edge = payload.get('edge', 'se')
        x = payload.get('x', 0)
        y = payload.get('y', 0)
        button = payload.get('button', 1)
        
        # Map edge name to Gdk.WindowEdge
        edges = {
            'n': Gdk.WindowEdge.NORTH,
            's': Gdk.WindowEdge.SOUTH,
            'e': Gdk.WindowEdge.EAST,
            'w': Gdk.WindowEdge.WEST,
            'ne': Gdk.WindowEdge.NORTH_EAST,
            'nw': Gdk.WindowEdge.NORTH_WEST,
            'se': Gdk.WindowEdge.SOUTH_EAST,
            'sw': Gdk.WindowEdge.SOUTH_WEST
        }
        
        gdk_edge = edges.get(edge, Gdk.WindowEdge.SOUTH_EAST)
        
        def do_resize():
            try:
                self.begin_resize_drag(
                    gdk_edge,
                    button,
                    int(x),
                    int(y),
                    Gdk.CURRENT_TIME
                )
            except Exception as e:
                print(f"[Aegis] Resize drag error: {e}")
            return False
        
        GLib.idle_add(do_resize)
        return {'success': True}
    
    def _handle_window_set_size(self, payload):
        """Set window size"""
        width = payload.get('width')
        height = payload.get('height')
        
        if width and height:
            self.resize(width, height)
        
        return {'success': True}
    
    def _handle_window_get_size(self, payload):
        """Get current window size"""
        width, height = self.get_size()
        return {'width': width, 'height': height}
    
    def _handle_window_set_position(self, payload):
        """Set window position"""
        x = payload.get('x')
        y = payload.get('y')
        
        if x is not None and y is not None:
            self.move(x, y)
        
        return {'success': True}
    
    def _handle_window_get_position(self, payload):
        """Get current window position"""
        x, y = self.get_position()
        return {'x': x, 'y': y}

    # ==================== Public API ====================
    
    def load_file(self, path):
        """Load HTML file into webview"""
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        self.webview.load_uri(f'file://{path}')
    
    def load_url(self, url):
        """Load URL into webview"""
        self.webview.load_uri(url)
    
    def inject_aegis_api(self, preload_path=None):
        """Inject the Aegis JavaScript API"""
        # Load the Aegis API script
        api_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 'runtime', 'aegis-api.js'
        )
        
        with open(api_path, 'r') as f:
            api_script = f.read()
        
        # Load preload script if provided
        preload_script = ''
        if preload_path and os.path.exists(preload_path):
            with open(preload_path, 'r') as f:
                preload_script = f.read()
        
        # Combine scripts
        full_script = api_script + '\n' + preload_script
        
        # Inject at document start
        user_script = WebKit2.UserScript(
            full_script,
            WebKit2.UserContentInjectedFrames.ALL_FRAMES,
            WebKit2.UserScriptInjectionTime.START,
            None, None
        )
        self.content_manager.add_script(user_script)
    
    # ==================== Async Action Handlers ====================
    
    def _process_async_action(self, action, payload, callback_id):
        """Process async actions in background threads"""
        handlers = {
            'run.async': self._handle_run_async,
            'download': self._handle_download,
            'copy.async': self._handle_copy_async,
        }
        
        handler = handlers.get(action)
        if handler:
            # Start background thread
            thread = threading.Thread(
                target=handler,
                args=(payload, callback_id),
                daemon=True
            )
            thread.start()
        else:
            GLib.idle_add(self._send_error, callback_id, f"Unknown async action: {action}")
    
    def _send_progress(self, callback_id, progress_data):
        """Send progress update to JavaScript (must be called via GLib.idle_add)"""
        response = json.dumps({
            'callbackId': callback_id,
            'type': 'progress',
            'data': progress_data
        })
        script = f"window.__aegisProgress({response})"
        self.webview.evaluate_javascript(script, -1, None, None, None, None, None)
        return False  # Don't repeat
    
    def _handle_run_async(self, payload, callback_id):
        """Execute command asynchronously with streaming output"""
        import subprocess
        
        try:
            cmd = payload.get('sh', '')
            
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            output_lines = []
            
            # Stream output line by line
            for line in process.stdout:
                output_lines.append(line)
                GLib.idle_add(self._send_progress, callback_id, {
                    'type': 'output',
                    'line': line.rstrip('\n')
                })
            
            process.wait()
            
            # Send final result
            result = {
                'output': ''.join(output_lines),
                'exitCode': process.returncode
            }
            GLib.idle_add(self._send_response, callback_id, result)
            
        except Exception as e:
            GLib.idle_add(self._send_error, callback_id, str(e))
    
    def _handle_download(self, payload, callback_id):
        """Download file with progress updates"""
        try:
            url = payload.get('url')
            dest = payload.get('dest')
            
            # Create request
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Aegis/0.1.0'
            })
            
            response = urllib.request.urlopen(req, timeout=30)
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
            
            with open(dest, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Send progress update
                    progress = {
                        'downloaded': downloaded,
                        'total': total_size,
                        'percent': (downloaded / total_size * 100) if total_size else 0
                    }
                    GLib.idle_add(self._send_progress, callback_id, progress)
            
            # Send completion
            result = {
                'success': True,
                'path': dest,
                'size': downloaded
            }
            GLib.idle_add(self._send_response, callback_id, result)
            
        except Exception as e:
            GLib.idle_add(self._send_error, callback_id, str(e))
    
    def _handle_copy_async(self, payload, callback_id):
        """Copy files/directories with progress (for large files)"""
        try:
            src = payload.get('src')
            dest = payload.get('dest')
            
            if os.path.isdir(src):
                # Copy directory
                def copy_with_progress(src_dir, dest_dir):
                    total_files = sum([len(files) for _, _, files in os.walk(src_dir)])
                    copied = 0
                    
                    for root, dirs, files in os.walk(src_dir):
                        rel_path = os.path.relpath(root, src_dir)
                        dest_path = os.path.join(dest_dir, rel_path)
                        os.makedirs(dest_path, exist_ok=True)
                        
                        for file in files:
                            src_file = os.path.join(root, file)
                            dest_file = os.path.join(dest_path, file)
                            shutil.copy2(src_file, dest_file)
                            copied += 1
                            
                            GLib.idle_add(self._send_progress, callback_id, {
                                'copied': copied,
                                'total': total_files,
                                'percent': (copied / total_files * 100) if total_files else 100,
                                'current': file
                            })
                
                copy_with_progress(src, dest)
            else:
                # Copy single file with progress
                file_size = os.path.getsize(src)
                copied = 0
                
                with open(src, 'rb') as fsrc:
                    with open(dest, 'wb') as fdest:
                        while True:
                            chunk = fsrc.read(8192)
                            if not chunk:
                                break
                            fdest.write(chunk)
                            copied += len(chunk)
                            
                            GLib.idle_add(self._send_progress, callback_id, {
                                'copied': copied,
                                'total': file_size,
                                'percent': (copied / file_size * 100) if file_size else 100
                            })
            
            result = {'success': True, 'src': src, 'dest': dest}
            GLib.idle_add(self._send_response, callback_id, result)
            
        except Exception as e:
            GLib.idle_add(self._send_error, callback_id, str(e))
    
    def run(self):
        """Show window and start main loop"""
        self.show_all()
        Gtk.main()
