# ⚡ Aegis Framework

**A lightweight alternative to Electron for Linux desktop apps.**

Create desktop applications with HTML, CSS, and JavaScript that package into ~200KB AppImages instead of 150MB!

## 📊 Size Comparison

| Framework | Typical App Size | Aegis App |
|-----------|-----------------|-----------|
| **Electron** | 150-200 MB | - |
| **Aegis** | - | **~200 KB** |

**That's 700x smaller!**

## 🚀 Installation

```bash
# Install globally via npm
npm install -g aegis-framework

# Or use npx without installing
npx aegis-framework init my-app
```

### System Requirements (Linux only)

```bash
# Ubuntu/Debian
sudo apt install python3 python3-gi gir1.2-webkit2-4.1

# Fedora
sudo dnf install python3 python3-gobject webkit2gtk4.1

# Arch
sudo pacman -S python python-gobject webkit2gtk-4.1
```

## 🏁 Quick Start

```bash
# Create a new project
aegis init my-app

# Enter the directory
cd my-app

# Start development server
aegis dev

# Build AppImage
aegis build
```

## 📁 Project Structure

```
my-app/
├── aegis.config.json    # Configuration
├── src/
│   ├── index.html       # Main HTML
│   ├── styles.css       # Styles
│   ├── app.js           # JavaScript
│   └── preload.js       # Security config
└── assets/
    └── icon.png         # App icon
```

## 🔌 API Reference

### File Operations

```javascript
// Read directory
const dir = await Aegis.read({ path: '/home/user' });
console.log(dir.entries);

// Read file
const file = await Aegis.read({ path: '/home/user', file: 'data.txt' });
console.log(file.content);

// Write file
await Aegis.write({
    path: '/home/user',
    file: 'output.txt',
    content: 'Hello World!'
});

// Check existence
const info = await Aegis.exists({ path: '/home/user/file.txt' });

// Create directory
await Aegis.mkdir({ path: '/home/user/new-folder' });

// Delete
await Aegis.remove({ path: '/home/user/old-file.txt' });

// Copy
await Aegis.copy({ src: '/path/from', dest: '/path/to' });

// Move/Rename
await Aegis.move({ src: '/path/from', dest: '/path/to' });
```

### Dialogs

```javascript
// Message dialog
await Aegis.dialog.message({
    type: 'info',  // info, warning, error, question
    title: 'Hello',
    message: 'World!'
});

// Confirmation dialog
const result = await Aegis.dialog.message({
    type: 'question',
    title: 'Confirm',
    message: 'Are you sure?',
    buttons: 'yesno'
});
if (result.response) { /* User clicked Yes */ }

// Open file dialog
const file = await Aegis.dialog.open({
    title: 'Select File',
    filters: [{ name: 'Images', extensions: ['png', 'jpg'] }]
});

// Save file dialog
const savePath = await Aegis.dialog.save({
    title: 'Save As',
    defaultName: 'document.txt'
});
```

### App Control

```javascript
// Window controls
await Aegis.app.minimize();
await Aegis.app.maximize();
await Aegis.app.quit();

// Get system paths (localized!)
const home = await Aegis.app.getPath({ name: 'home' });
const docs = await Aegis.app.getPath({ name: 'documents' });
// Also: desktop, downloads, music, pictures, videos
```

### Window Control (Frameless)

```javascript
// Make element draggable for window movement
Aegis.window.moveBar('#titlebar', { exclude: '.btn' });

// Setup resize handles
Aegis.window.resizeHandles({
    '.resize-n': 'n',
    '.resize-s': 's',
    '.resize-se': 'se'
    // etc: e, w, ne, nw, sw
});

// Get/set size
const size = await Aegis.window.getSize();
await Aegis.window.setSize({ width: 1024, height: 768 });

// Get/set position
const pos = await Aegis.window.getPosition();
await Aegis.window.setPosition({ x: 100, y: 100 });
```

### Run Commands

```javascript
// Shell command
const result = await Aegis.run({ sh: 'ls -la' });
console.log(result.output);

// Python code
const py = await Aegis.run({ py: '2 + 2' });
console.log(py.output);  // "4"
```

## 🔒 Security (preload.js)

Control which APIs are exposed to your frontend:

```javascript
// src/preload.js
Aegis.expose([
    'read',     // Allow file reading
    'write',    // Allow file writing
    'dialog',   // Allow dialogs
    'app',      // Allow app control
    'window',   // Allow window control
    // Omit 'run' to prevent command execution!
]);
```

## ⚙️ Configuration (aegis.config.json)

```json
{
    "name": "my-app",
    "title": "My Application",
    "version": "1.0.0",
    "main": "src/index.html",
    "preload": "src/preload.js",
    "width": 1200,
    "height": 800,
    "frame": true,
    "resizable": true,
    "icon": "assets/icon.png"
}
```

Set `"frame": false` for frameless window (custom titlebar).

## 🤔 Why Aegis?

| Feature | Electron | Aegis |
|---------|----------|-------|
| Size | ~150 MB | **~200 KB** |
| Backend | Node.js | **Python** |
| Renderer | Chromium (bundled) | **WebKit2GTK (system)** |
| Platform | Cross-platform | **Linux** |
| RAM Usage | High | **Low** |

Aegis uses the WebKit that's already installed on Linux systems, so apps are tiny!

## 📜 License

MIT © Diego

---

Made with ❤️ for the Linux community
