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

---

# ⚡ Aegis Utility API

Aegis includes a powerful utility API that simplifies common JavaScript patterns!

## Event Shortcuts

```javascript
// Click event (works on single or multiple elements!)
Aegis.click('#btn', () => alert('Clicked!'));
Aegis.click('.card', (e) => console.log(e.target));

// More event shortcuts
Aegis.submit('#form', handler);
Aegis.change('#select', handler);
Aegis.input('#search', handler);
Aegis.keypress('#input', handler);

// Hover with enter/leave
Aegis.hover('#card', onEnter, onLeave);

// Universal event binding
Aegis.on('.field', 'focus blur', handler);  // Multiple events!
Aegis.once('#btn', 'click', handler);       // Fire once only
```

## Element Selection & Manipulation

```javascript
// Select elements
const el = Aegis.get('#my-id');
const all = Aegis.getAll('.cards');

// Create elements
Aegis.create('div', {{
    id: 'my-div',
    class: 'card active',
    html: '<h1>Hello!</h1>',
    style: {{ color: 'red' }},
    on: {{ click: handler }},
    parent: '#container'
}});

// Classes
Aegis.addClass('#el', 'active');
Aegis.removeClass('#el', 'hidden');
Aegis.toggleClass('#el', 'visible');

// Styles & Visibility
Aegis.css('#el', {{ color: 'blue', fontSize: '18px' }});
Aegis.hide('#modal');
Aegis.show('#modal');
Aegis.fadeIn('#el', 300);
Aegis.fadeOut('#el', 300);

// Content
Aegis.html('#container', '<p>New content</p>');
Aegis.text('#title', 'Hello World');
Aegis.val('#input', 'value');
```

## Forms

```javascript
// Serialize form to object
const data = Aegis.form.serialize('#my-form');
// {{ name: 'John', email: 'john@email.com' }}

// Fill form with data
Aegis.form.fill('#form', {{ name: 'Jane', email: 'jane@email.com' }});

// Validate
const result = Aegis.form.validate('#form', {{
    email: {{ required: true, email: true }},
    password: {{ required: true, minLength: 8 }}
}});
if (!result.valid) console.log(result.errors);
```

## HTTP Requests

```javascript
const users = await Aegis.http.get('/api/users');
await Aegis.http.post('/api/users', {{ name: 'John' }});
await Aegis.http.put('/api/users/1', {{ name: 'Jane' }});
await Aegis.http.delete('/api/users/1');
```

## String Utilities

```javascript
Aegis.string.capitalize('hello');       // 'Hello'
Aegis.string.slugify('Hello World!');   // 'hello-world'
Aegis.string.camelCase('hello-world');  // 'helloWorld'
Aegis.string.truncate('Long text', 5);  // 'Long ...'
Aegis.string.template('Hi {{{{name}}}}!', {{ name: 'John' }}); // 'Hi John!'
```

## Array Utilities

```javascript
Aegis.array.unique([1, 2, 2, 3]);        // [1, 2, 3]
Aegis.array.shuffle([1, 2, 3]);          // Random order
Aegis.array.groupBy(users, 'role');      // Group by key
Aegis.array.sortBy(users, 'name');       // Sort by key
Aegis.array.chunk([1,2,3,4,5], 2);       // [[1,2], [3,4], [5]]
```

## Object Utilities

```javascript
Aegis.object.clone(obj);                 // Deep clone
Aegis.object.merge(obj1, obj2);          // Merge
Aegis.object.pick(obj, ['name']);        // Pick keys
Aegis.object.get(user, 'address.city');  // Deep get
```

## Date Utilities

```javascript
Aegis.date.format(date, 'YYYY-MM-DD');   // '2024-12-28'
Aegis.date.ago(date);                     // '5 minutes ago'
Aegis.date.isToday(date);                 // true/false
```

## Number Utilities

```javascript
Aegis.number.format(1234567);             // '1.234.567'
Aegis.number.currency(1234.56);           // 'R$ 1.234,56'
Aegis.number.bytes(1536000);              // '1.46 MB'
```

## Toast Notifications

```javascript
Aegis.toast('Hello!');
Aegis.toast('Success!', {{ type: 'success' }});
Aegis.toast('Error!', {{ type: 'error', duration: 5000 }});
```

## Storage

```javascript
Aegis.storage.set('user', {{ name: 'John' }});  // Auto JSON
Aegis.storage.get('user');                       // Auto parse
Aegis.storage.remove('user');
```

## Validation

```javascript
Aegis.is.email('test@email.com');   // true
Aegis.is.url('https://...');        // true
Aegis.is.empty([]);                 // true
Aegis.is.mobile();                  // true if mobile
```

## More Utilities

```javascript
await Aegis.clipboard.copy('text');       // Copy to clipboard
Aegis.debounce(fn, 300);                  // Debounce
Aegis.throttle(fn, 100);                  // Throttle
await Aegis.delay(1000);                  // Wait 1 second
Aegis.uid('card');                        // 'card-123456789-abc'
Aegis.random.uuid();                      // Full UUID
```

---

# 🔌 Backend API (Python Bridge)

## File Operations

```javascript
// Read directory contents
const dir = await Aegis.read({{ path: '/home/user' }});
console.log(dir.entries);

// Read file content
const file = await Aegis.read({{ path: '/home/user', file: 'data.txt' }});

// Write file
await Aegis.write({{
    path: '/home/user',
    file: 'output.txt',
    content: 'Hello, Aegis!'
}});

// Check if exists
const info = await Aegis.exists({{ path: '/home/user/file.txt' }});

// Create directory
await Aegis.mkdir({{ path: '/home/user/new-folder' }});

// Delete
await Aegis.remove({{ path: '/home/user/old-file.txt' }});

// Copy & Move
await Aegis.copy({{ src: '/from', dest: '/to' }});
await Aegis.move({{ src: '/from', dest: '/to' }});
```

## Execute Commands

```javascript
// Shell command
const result = await Aegis.run({{ sh: 'ls -la' }});

// Async with streaming (UI doesn't freeze!)
await Aegis.runAsync(
    {{ sh: 'long-command' }},
    (progress) => console.log(progress.line)
);
```

## Dialogs

```javascript
await Aegis.dialog.message({{ type: 'info', title: 'Hi', message: 'Hello!' }});
const file = await Aegis.dialog.open({{ title: 'Select file' }});
const path = await Aegis.dialog.save({{ title: 'Save as' }});
```

## Download with Progress

```javascript
await Aegis.download(
    {{ url: 'https://example.com/file.zip', dest: '/path/file.zip' }},
    (progress) => console.log(progress.percent + '%')
);
```

## App Control

```javascript
Aegis.app.minimize();
Aegis.app.maximize();
Aegis.app.quit();
const home = await Aegis.app.getPath({{ name: 'home' }});
```

## Window Control (Frameless)

```javascript
Aegis.window.moveBar('#titlebar', {{ exclude: '.btn-close' }});
Aegis.window.resizeHandles({{ '.resize-se': 'se' }});
```

---

## 🔒 Security (preload.js)

```javascript
Aegis.expose([
    'read', 'write', 'run', 'dialog', 'app', 'window',
    'download', 'exists', 'mkdir', 'remove', 'copy', 'move'
]);
// Omit 'run' to prevent shell command execution!
```

## ⚙️ Configuration (aegis.config.json)

```json
{{
    "name": "{project_name}",
    "title": "My App",
    "width": 1200,
    "height": 800,
    "frame": true,
    "resizable": true
}}
```

## 📦 Build AppImage

```bash
aegis build
```

Creates a portable ~200KB AppImage in `dist/`.

## 🆚 Aegis vs Electron

| Aspect | Electron | Aegis |
|--------|----------|-------|
| App Size | ~150 MB | **~200 KB** |
| RAM Usage | ~100 MB | ~30 MB |
| Platform | Cross-platform | Linux |

## 📚 More Info

- [GitHub](https://github.com/Diegopam/aegis-framework)
- [npm](https://www.npmjs.com/package/aegis-framework)

MIT License
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
