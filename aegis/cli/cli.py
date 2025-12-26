#!/usr/bin/env python3
"""
Aegis CLI - Command Line Interface for Aegis Framework

Usage:
    aegis init [name]     Create a new Aegis project
    aegis dev             Run in development mode (hot-reload)
    aegis run             Run the project
    aegis build           Build AppImage
    aegis --version       Show version
    aegis --help          Show help
"""

import argparse
import os
import sys
import shutil
import json
import subprocess
import signal
from pathlib import Path


class AegisCLI:
    """Aegis Command Line Interface"""
    
    VERSION = "0.1.0"
    
    def __init__(self):
        self.parser = self._create_parser()
        self.templates_dir = Path(__file__).parent.parent / 'templates'
    
    def _create_parser(self):
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            prog='aegis',
            description='Aegis - Lightweight AppImage Framework',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  aegis init my-app      Create a new project called 'my-app'
  aegis dev              Start development server with hot-reload
  aegis build            Package as AppImage
            """
        )
        
        parser.add_argument(
            '--version', '-v',
            action='version',
            version=f'Aegis v{self.VERSION}'
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Commands')
        
        # init command
        init_parser = subparsers.add_parser('init', help='Create a new Aegis project')
        init_parser.add_argument('name', nargs='?', default='.', help='Project name or directory')
        init_parser.add_argument('--template', '-t', default='default', help='Project template')
        
        # dev command
        dev_parser = subparsers.add_parser('dev', help='Run in development mode')
        dev_parser.add_argument('--port', '-p', type=int, default=8080, help='Dev server port')
        dev_parser.add_argument('--no-reload', action='store_true', help='Disable hot-reload')
        
        # run command
        run_parser = subparsers.add_parser('run', help='Run the project')
        run_parser.add_argument('--config', '-c', help='Config file path')
        
        # build command
        build_parser = subparsers.add_parser('build', help='Build AppImage')
        build_parser.add_argument('--output', '-o', help='Output directory')
        build_parser.add_argument('--name', '-n', help='AppImage name')
        
        return parser
    
    def run(self, args=None):
        """Run the CLI"""
        parsed = self.parser.parse_args(args)
        
        if parsed.command is None:
            self.parser.print_help()
            return 0
        
        commands = {
            'init': self.cmd_init,
            'dev': self.cmd_dev,
            'run': self.cmd_run,
            'build': self.cmd_build
        }
        
        handler = commands.get(parsed.command)
        if handler:
            return handler(parsed)
        
        return 1
    
    def cmd_init(self, args):
        """Initialize a new Aegis project"""
        project_name = args.name
        
        # Determine project directory
        if project_name == '.':
            project_dir = Path.cwd()
            project_name = project_dir.name
        else:
            project_dir = Path.cwd() / project_name
        
        print(f"⚡ Creating Aegis project: {project_name}")
        
        # Check if directory exists and is not empty
        if project_dir.exists() and any(project_dir.iterdir()):
            print(f"⚠️  Directory '{project_dir}' is not empty.")
            response = input("Continue anyway? [y/N] ")
            if response.lower() != 'y':
                return 1
        
        # Create project directory
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create project structure
        self._create_project_files(project_dir, project_name)
        
        print(f"""
✅ Project created successfully!

Next steps:
  cd {project_name}
  aegis dev

Happy coding! 🚀
        """)
        
        return 0
    
    def _create_project_files(self, project_dir, project_name):
        """Create all project files from templates"""
        
        # Create subdirectories
        (project_dir / 'src').mkdir(exist_ok=True)
        (project_dir / 'assets').mkdir(exist_ok=True)
        
        # Configuration file
        config = {
            'name': project_name,
            'title': project_name.replace('-', ' ').title(),
            'version': '1.0.0',
            'main': 'src/index.html',
            'preload': 'src/preload.js',
            'width': 1200,
            'height': 800,
            'resizable': True,
            'frame': True,
            'devTools': True,
            'contextMenu': True,
            'icon': 'assets/icon.png',
            'description': 'An Aegis application'
        }
        
        with open(project_dir / 'aegis.config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        # Main HTML
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="app">
        <header class="header">
            <h1>⚡ {project_name}</h1>
            <p>Built with Aegis Framework</p>
        </header>
        
        <main class="main">
            <div class="card">
                <h2>Welcome to Aegis!</h2>
                <p>Edit <code>src/index.html</code> to get started.</p>
                
                <div class="demo">
                    <button id="btn-read" class="btn">📂 Read File</button>
                    <button id="btn-run" class="btn">⚡ Run Command</button>
                    <button id="btn-dialog" class="btn btn-primary">💬 Show Dialog</button>
                </div>
                
                <pre id="output" class="output">Output will appear here...</pre>
            </div>
        </main>
        
        <footer class="footer">
            Powered by Aegis v0.1.0 | WebKit2GTK + Python
        </footer>
    </div>
    
    <script src="app.js"></script>
</body>
</html>
'''
        with open(project_dir / 'src' / 'index.html', 'w') as f:
            f.write(html_content)
        
        # Styles
        css_content = '''/* Aegis App Styles */
:root {
    --primary: #00ff88;
    --primary-dark: #00cc6a;
    --bg: #0a0a0f;
    --bg-card: #12121a;
    --text: #ffffff;
    --text-muted: #888899;
    --border: #2a2a3a;
    --radius: 12px;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

.header {
    text-align: center;
    padding: 3rem 2rem;
    background: linear-gradient(180deg, #1a1a2a 0%, var(--bg) 100%);
}

.header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, var(--primary), #00aaff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.header p {
    color: var(--text-muted);
}

.main {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
}

.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 2rem;
    max-width: 600px;
    width: 100%;
}

.card h2 {
    margin-bottom: 1rem;
}

.card p {
    color: var(--text-muted);
    margin-bottom: 1.5rem;
}

.card code {
    background: #2a2a3a;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-family: 'Fira Code', monospace;
}

.demo {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.btn {
    padding: 0.75rem 1.5rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg);
    color: var(--text);
    cursor: pointer;
    font-size: 1rem;
    transition: all 0.2s;
}

.btn:hover {
    background: #1a1a2a;
    border-color: var(--primary);
}

.btn-primary {
    background: var(--primary);
    color: #000;
    border-color: var(--primary);
}

.btn-primary:hover {
    background: var(--primary-dark);
}

.output {
    background: #000;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    font-family: 'Fira Code', monospace;
    font-size: 0.9rem;
    color: var(--primary);
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
}

.footer {
    text-align: center;
    padding: 1.5rem;
    color: var(--text-muted);
    font-size: 0.9rem;
    border-top: 1px solid var(--border);
}
'''
        with open(project_dir / 'src' / 'styles.css', 'w') as f:
            f.write(css_content)
        
        # JavaScript
        js_content = '''/**
 * Aegis App - Main JavaScript
 */

// Wait for Aegis to be ready
document.addEventListener('DOMContentLoaded', async () => {
    const output = document.getElementById('output');
    
    // Check if running in Aegis
    if (!Aegis.isAegis()) {
        output.textContent = 'Not running in Aegis environment.\\nRun with: aegis dev';
        return;
    }
    
    output.textContent = '✅ Aegis is ready!\\n\\nClick a button to test the API.';
    
    // Read file button
    document.getElementById('btn-read').addEventListener('click', async () => {
        try {
            const result = await Aegis.read({ path: '.' });
            output.textContent = 'Directory contents:\\n\\n' + 
                result.entries.map(e => `${e.isDirectory ? '📁' : '📄'} ${e.name}`).join('\\n');
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
        }
    });
    
    // Run command button
    document.getElementById('btn-run').addEventListener('click', async () => {
        try {
            const result = await Aegis.run({ sh: 'uname -a' });
            output.textContent = 'System info:\\n\\n' + result.output;
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
                message: 'This is a native GTK dialog.\\nPretty cool, right?'
            });
            output.textContent = 'Dialog closed! Response: ' + JSON.stringify(result);
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
        }
    });
});
'''
        with open(project_dir / 'src' / 'app.js', 'w') as f:
            f.write(js_content)
        
        # Preload
        preload_content = '''/**
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
'''
        with open(project_dir / 'src' / 'preload.js', 'w') as f:
            f.write(preload_content)
        
        # README
        readme_content = f'''# {project_name}

An application built with [Aegis Framework](https://github.com/Diegopam/aegis-framework) - the lightweight alternative to Electron!

## 🚀 Quick Start

```bash
# Development mode (with hot-reload)
aegis dev

# Run in production mode  
aegis run

# Build AppImage (~200KB!)
aegis build
```

## 📁 Project Structure

```
{project_name}/
├── aegis.config.json    # App configuration (size, title, etc.)
├── src/
│   ├── index.html       # Main HTML entry point
│   ├── styles.css       # Your styles
│   ├── app.js           # Your JavaScript code
│   └── preload.js       # Security: control which APIs are exposed
└── assets/
    └── icon.png         # App icon (256x256 recommended)
```

## 🔌 Aegis API Reference

### File Operations

```javascript
// Read directory contents
const dir = await Aegis.read({{ path: '/home/user' }});
console.log(dir.entries);  // [{{ name: 'file.txt', isFile: true, size: 1234 }}, ...]

// Read file content
const file = await Aegis.read({{ path: '/home/user', file: 'data.txt' }});
console.log(file.content);

// Write file
await Aegis.write({{
    path: '/home/user',
    file: 'output.txt',
    content: 'Hello, Aegis!'
}});

// Check if file/directory exists
const info = await Aegis.exists({{ path: '/home/user/file.txt' }});
if (info.exists && info.isFile) {{
    console.log('File exists!');
}}

// Create directory
await Aegis.mkdir({{ path: '/home/user/new-folder' }});

// Delete file or directory
await Aegis.remove({{ path: '/home/user/old-file.txt' }});
await Aegis.remove({{ path: '/home/user/old-folder', recursive: true }});

// Copy file or directory
await Aegis.copy({{
    src: '/home/user/file.txt',
    dest: '/home/user/backup/file.txt'
}});

// Move/rename file or directory
await Aegis.move({{
    src: '/home/user/old-name.txt',
    dest: '/home/user/new-name.txt'
}});
```

### Execute Commands

```javascript
// Run shell command
const result = await Aegis.run({{ sh: 'ls -la' }});
console.log(result.output);
console.log(result.exitCode);

// Run Python code
const pyResult = await Aegis.run({{ py: 'print(2 + 2)' }});
console.log(pyResult.output);  // "4"

// Run async command with streaming output (no UI freeze!)
await Aegis.runAsync(
    {{ sh: 'apt update' }},
    (progress) => {{
        console.log(progress.line);  // Each line as it comes
    }}
);
```

### Dialogs

```javascript
// Info dialog
await Aegis.dialog.message({{
    type: 'info',
    title: 'Success',
    message: 'Operation completed!'
}});

// Confirmation dialog
const confirm = await Aegis.dialog.message({{
    type: 'question',
    title: 'Confirm',
    message: 'Are you sure?',
    buttons: 'yesno'
}});
if (confirm.response) {{
    // User clicked Yes
}}

// Open file dialog
const file = await Aegis.dialog.open({{
    title: 'Select a file',
    filters: [{{ name: 'Images', extensions: ['png', 'jpg', 'gif'] }}]
}});
console.log(file.path);

// Save file dialog
const savePath = await Aegis.dialog.save({{
    title: 'Save as',
    defaultName: 'document.txt'
}});
```

### Download with Progress

```javascript
// Download file with progress bar
await Aegis.download(
    {{
        url: 'https://example.com/file.zip',
        dest: '/home/user/downloads/file.zip'
    }},
    (progress) => {{
        const percent = progress.percent.toFixed(1);
        progressBar.style.width = percent + '%';
        statusText.textContent = `${{progress.downloaded}} / ${{progress.total}} bytes`;
    }}
);
```

### App Control

```javascript
// Window controls
Aegis.app.minimize();
Aegis.app.maximize();
Aegis.app.quit();

// Get system paths (localized for your language!)
const home = await Aegis.app.getPath({{ name: 'home' }});
const docs = await Aegis.app.getPath({{ name: 'documents' }});  // Returns "Documentos" on pt-BR
const downloads = await Aegis.app.getPath({{ name: 'downloads' }});
// Also: desktop, music, pictures, videos
```

### Window Control (Frameless Windows)

```javascript
// Make element draggable for window movement
Aegis.window.moveBar('#titlebar', {{ exclude: '.btn-close' }});

// Setup resize handles
Aegis.window.resizeHandles({{
    '.resize-n': 'n',
    '.resize-s': 's',
    '.resize-se': 'se',
    // Options: n, s, e, w, ne, nw, se, sw
}});

// Get/set window size
const size = await Aegis.window.getSize();
await Aegis.window.setSize({{ width: 1024, height: 768 }});

// Get/set window position
const pos = await Aegis.window.getPosition();
await Aegis.window.setPosition({{ x: 100, y: 100 }});
```

## 🔒 Security (preload.js)

Control which APIs your app can access:

```javascript
// src/preload.js
Aegis.expose([
    'read',      // File reading
    'write',     // File writing
    'run',       // Command execution
    'dialog',    // Native dialogs
    'app',       // App control
    'window',    // Window control
    'download',  // Download with progress
    'exists',    // File existence
    'mkdir',     // Create directories
    'remove',    // Delete files
    'copy',      // Copy files
    'move'       // Move/rename files
]);

// For maximum security, only expose what you need!
// If you omit 'run', the app cannot execute shell commands
```

## ⚙️ Configuration (aegis.config.json)

```json
{{
    "name": "{project_name}",
    "title": "My Awesome App",
    "version": "1.0.0",
    "main": "src/index.html",
    "preload": "src/preload.js",
    "width": 1200,
    "height": 800,
    "resizable": true,
    "frame": true,
    "icon": "assets/icon.png"
}}
```

| Option | Description |
|--------|-------------|
| `frame` | Set to `false` for frameless window (custom titlebar) |
| `resizable` | Allow window resizing |
| `width/height` | Initial window size |
| `devTools` | Enable right-click → Inspect Element |

## 📦 Building AppImage

```bash
aegis build
```

This creates a portable AppImage (~200KB!) in the `dist/` folder.

**Note:** The AppImage requires `python3-gi` and `gir1.2-webkit2-4.1` on the target system.

## 🆚 Why Aegis over Electron?

| Aspect | Electron | Aegis |
|--------|----------|-------|
| App Size | ~150 MB | **~200 KB** |
| Backend | Node.js | Python |
| Renderer | Chromium (bundled) | WebKit2GTK (system) |
| RAM Usage | High (~100MB+) | Low (~30MB) |
| Platform | Cross-platform | Linux |

## 📚 Learn More

- [Aegis GitHub](https://github.com/Diegopam/aegis-framework)
- [npm Package](https://www.npmjs.com/package/aegis-framework)

## License

MIT
'''
        with open(project_dir / 'README.md', 'w') as f:
            f.write(readme_content)
        
        # .gitignore
        gitignore_content = '''# Aegis
dist/
*.AppImage
*.AppDir/

# Python
__pycache__/
*.pyc
.venv/

# Node (if using npm for frontend)
node_modules/

# IDE
.vscode/
.idea/
'''
        with open(project_dir / '.gitignore', 'w') as f:
            f.write(gitignore_content)
        
        print(f"  📁 Created project structure")
        print(f"  📄 aegis.config.json")
        print(f"  📄 src/index.html")
        print(f"  📄 src/styles.css")
        print(f"  📄 src/app.js")
        print(f"  📄 src/preload.js")
        print(f"  📄 README.md")
    
    def cmd_dev(self, args):
        """Run in development mode"""
        print("⚡ Starting Aegis in development mode...")
        
        # Check for config
        if not Path('aegis.config.json').exists():
            print("❌ No aegis.config.json found. Run 'aegis init' first.")
            return 1
        
        # Import and run
        try:
            from aegis.core.aegis import AegisApp
            app = AegisApp()
            
            # Enable dev tools
            app.config['devTools'] = True
            
            print(f"📂 Loading: {app.config.get('main', 'index.html')}")
            print("🔄 Hot-reload: Enabled (save files to refresh)")
            print("🛠️  DevTools: Right-click → Inspect Element")
            print("")
            
            app.run()
            
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("Make sure you have installed: python3-gi gir1.2-webkit2-4.1")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
        
        return 0
    
    def cmd_run(self, args):
        """Run the project (production mode)"""
        print("⚡ Running Aegis application...")
        
        config_path = args.config or 'aegis.config.json'
        
        if not Path(config_path).exists():
            print(f"❌ Config not found: {config_path}")
            return 1
        
        try:
            from aegis.core.aegis import AegisApp
            app = AegisApp(config_path)
            app.config['devTools'] = False
            app.run()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
        
        return 0
    
    def cmd_build(self, args):
        """Build AppImage"""
        print("📦 Building AppImage...")
        
        if not Path('aegis.config.json').exists():
            print("❌ No aegis.config.json found.")
            return 1
        
        try:
            from aegis.builder.builder import AegisBuilder
            
            builder = AegisBuilder()
            output = args.output or 'dist'
            name = args.name
            
            appimage_path = builder.build(output_dir=output, name=name)
            
            print(f"\n✅ AppImage created: {appimage_path}")
            print(f"   Size: {Path(appimage_path).stat().st_size / 1024 / 1024:.1f} MB")
            
        except Exception as e:
            print(f"❌ Build failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        return 0


def main():
    """Entry point for CLI"""
    cli = AegisCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()
