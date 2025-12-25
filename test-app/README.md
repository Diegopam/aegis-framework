# test-app

An application built with [Aegis Framework](https://github.com/your-repo/aegis).

## Getting Started

```bash
# Development mode
aegis dev

# Build AppImage
aegis build
```

## Project Structure

```
test-app/
├── aegis.config.json    # Project configuration
├── src/
│   ├── index.html       # Main HTML
│   ├── styles.css       # Styles
│   ├── app.js           # JavaScript
│   └── preload.js       # Security configuration
└── assets/
    └── icon.png         # App icon
```

## Aegis API

```javascript
// Read files
const content = await Aegis.read({ path: '.', file: 'data.txt' });

// Write files
await Aegis.write({ path: '.', file: 'output.txt', content: 'Hello!' });

// Run commands
const result = await Aegis.run({ sh: 'ls -la' });

// Dialogs
await Aegis.dialog.message({ type: 'info', title: 'Hello', message: 'World!' });
```

## License

MIT
