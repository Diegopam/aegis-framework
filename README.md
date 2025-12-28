# ⚡ Aegis Framework

**A lightweight alternative to Electron for Linux desktop apps.**

Create desktop applications with HTML, CSS, and JavaScript that package into ~200KB AppImages instead of 150MB!

## 📊 Size Comparison

| Framework | Typical App Size | Aegis App |
|-----------|-----------------|-----------|
| **Electron** | 150-200 MB | - |
| **Aegis** | - | **~200 KB** |

**That's 700x smaller!**

---

## 🚀 Installation

```bash
# Install globally
npm install -g aegis-framework

# Create new project
aegis init my-app
cd my-app

# Run development
aegis dev

# Build AppImage
aegis build
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

---

# 🛠️ Aegis Utility API

Aegis includes a powerful utility API that simplifies common JavaScript patterns. No more repetitive code!

---

## 📌 Event Handling

### Aegis.click(selector, handler)
Add click event to element(s).

```javascript
// Add click to button
Aegis.click('#my-button', () => {
    alert('Clicked!');
});

// Works with multiple elements
Aegis.click('.card', (e) => {
    console.log('Card clicked:', e.target);
});
```

### Aegis.on(selector, events, handler)
Add any event(s) to element(s).

```javascript
// Single event
Aegis.on('#input', 'focus', () => console.log('Focused!'));

// Multiple events at once!
Aegis.on('.field', 'focus blur', (e) => {
    console.log(e.type); // 'focus' or 'blur'
});
```

### Aegis.once(selector, events, handler)
Event that fires only once.

```javascript
Aegis.once('#start-btn', 'click', () => {
    initializeApp();
});
```

### More Event Shortcuts

```javascript
Aegis.submit('#form', handler);    // Form submit
Aegis.change('#select', handler);  // Select change
Aegis.input('#search', handler);   // Input typing
Aegis.keypress('#input', handler); // Key press

// Hover with enter and leave
Aegis.hover('#card', 
    () => console.log('Mouse entered'),
    () => console.log('Mouse left')
);
```

---

## 🏗️ Element Selection

### Aegis.get(selector)
Get single element.

```javascript
const btn = Aegis.get('#my-button');
const first = Aegis.get('.card');
```

### Aegis.getAll(selector)
Get all elements.

```javascript
const cards = Aegis.getAll('.card');
cards.forEach(card => console.log(card));
```

---

## ✨ Element Creation

### Aegis.create(tag, options)
Create elements with all properties at once.

```javascript
// Simple element
const div = Aegis.create('div', {
    id: 'my-div',
    class: 'card active',
    html: '<h1>Title</h1><p>Content</p>'
});

// Complete example
Aegis.create('button', {
    id: 'submit-btn',
    class: 'btn btn-primary',
    text: 'Click Me',
    attrs: { type: 'submit', disabled: false },
    style: { backgroundColor: 'blue', color: 'white' },
    data: { userId: '123', action: 'submit' },
    on: { 
        click: () => alert('Clicked!'),
        mouseenter: () => console.log('Hover')
    },
    parent: '#form'  // Auto-append to parent
});
```

---

## 🎨 Class Manipulation

```javascript
Aegis.addClass('#el', 'active', 'visible');
Aegis.removeClass('#el', 'hidden');
Aegis.toggleClass('#el', 'active');

if (Aegis.hasClass('#el', 'active')) {
    console.log('Element is active');
}
```

---

## 💅 Style Manipulation

```javascript
// Set styles
Aegis.css('#el', {
    color: 'red',
    fontSize: '18px',
    backgroundColor: '#333'
});

// Show/Hide
Aegis.hide('#modal');
Aegis.show('#modal');
Aegis.toggleDisplay('#menu');

// Animations
Aegis.fadeIn('#modal', 300);
Aegis.fadeOut('#modal', 300);
```

---

## 📝 Content Manipulation

```javascript
// HTML content
Aegis.html('#container', '<h1>New Content</h1>');
const content = Aegis.html('#container'); // Get

// Text content
Aegis.text('#title', 'Hello World');

// Input values
Aegis.val('#input', 'New value');
const value = Aegis.val('#input'); // Get

// Attributes
Aegis.attr('#link', 'href', 'https://example.com');

// Data attributes
Aegis.data('#el', 'userId', '123');
const userId = Aegis.data('#el', 'userId');
```

---

## 📋 Form Utilities

### Aegis.form.serialize(selector)
Convert form to object.

```javascript
const data = Aegis.form.serialize('#my-form');
// { name: 'John', email: 'john@email.com' }
```

### Aegis.form.fill(selector, data)
Fill form with data.

```javascript
Aegis.form.fill('#my-form', {
    name: 'John',
    email: 'john@email.com',
    newsletter: true
});
```

### Aegis.form.validate(selector, rules)
Validate form fields.

```javascript
const result = Aegis.form.validate('#my-form', {
    name: { required: true, minLength: 3 },
    email: { required: true, email: true },
    password: { required: true, minLength: 8 }
});

if (!result.valid) {
    console.log(result.errors);
}
```

### Aegis.form.reset(selector)
Reset form fields.

```javascript
Aegis.form.reset('#my-form');
```

---

## 🌐 HTTP Requests

```javascript
// GET
const users = await Aegis.http.get('/api/users');

// POST
const newUser = await Aegis.http.post('/api/users', {
    name: 'John',
    email: 'john@email.com'
});

// PUT
await Aegis.http.put('/api/users/1', { name: 'Jane' });

// DELETE
await Aegis.http.delete('/api/users/1');

// Get raw response
const response = await Aegis.http.get('/api/data', { raw: true });
console.log(response.status);
```

---

## 🍪 Cookie Utilities

```javascript
// Set cookie (expires in 30 days)
Aegis.cookie.set('theme', 'dark', 30);

// Get cookie
const theme = Aegis.cookie.get('theme');

// Remove cookie
Aegis.cookie.remove('theme');
```

---

## 🔗 URL Utilities

```javascript
// Get all URL parameters
const params = Aegis.url.params();
// { page: '1', sort: 'name' }

// Get single parameter
const page = Aegis.url.param('page');

// Build URL with params
const url = Aegis.url.build('/search', { q: 'hello', page: 1 });
// '/search?q=hello&page=1'

// Get current path
const path = Aegis.url.path();

// Get hash
const hash = Aegis.url.hash();
```

---

## 📝 String Utilities

```javascript
Aegis.string.capitalize('hello');      // 'Hello'
Aegis.string.titleCase('hello world'); // 'Hello World'
Aegis.string.camelCase('hello-world'); // 'helloWorld'
Aegis.string.kebabCase('helloWorld');  // 'hello-world'
Aegis.string.snakeCase('helloWorld');  // 'hello_world'
Aegis.string.slugify('Hello World!');  // 'hello-world'

Aegis.string.truncate('Long text here', 8);  // 'Long tex...'
Aegis.string.reverse('hello');               // 'olleh'
Aegis.string.count('hello', 'l');            // 2

// Template strings
Aegis.string.template('Hello {{name}}!', { name: 'World' });
// 'Hello World!'
```

---

## 📦 Array Utilities

```javascript
Aegis.array.unique([1, 2, 2, 3]);     // [1, 2, 3]
Aegis.array.shuffle([1, 2, 3, 4]);   // [3, 1, 4, 2]
Aegis.array.chunk([1,2,3,4,5], 2);   // [[1,2], [3,4], [5]]
Aegis.array.flatten([[1,2], [3,4]]); // [1, 2, 3, 4]
Aegis.array.compact([0, 1, false, 2, '', 3]); // [1, 2, 3]

Aegis.array.first([1, 2, 3]);    // 1
Aegis.array.last([1, 2, 3]);     // 3
Aegis.array.sample([1, 2, 3]);   // Random item

Aegis.array.range(1, 5);         // [1, 2, 3, 4, 5]
Aegis.array.diff([1,2,3], [2,3,4]); // [1]
Aegis.array.intersect([1,2,3], [2,3,4]); // [2, 3]

// Group by key
Aegis.array.groupBy(users, 'role');
// { admin: [...], user: [...] }

// Sort by key
Aegis.array.sortBy(users, 'name');
Aegis.array.sortBy(users, 'age', true); // Descending
```

---

## 🗃️ Object Utilities

```javascript
Aegis.object.clone(obj);           // Deep clone
Aegis.object.merge(obj1, obj2);    // Merge objects
Aegis.object.isEmpty({});          // true

Aegis.object.pick(obj, ['name', 'email']); // Pick keys
Aegis.object.omit(obj, ['password']);      // Omit keys

Aegis.object.keys(obj);            // Object.keys
Aegis.object.values(obj);          // Object.values
Aegis.object.entries(obj);         // Object.entries

// Deep get/set
Aegis.object.get(user, 'address.city', 'Unknown');
Aegis.object.set(user, 'address.city', 'New York');
```

---

## 📅 Date Utilities

```javascript
Aegis.date.now();                  // Current date
Aegis.date.format(date, 'YYYY-MM-DD');
Aegis.date.format(date, 'DD/MM/YYYY HH:mm');

Aegis.date.ago(date);              // '5 minutes ago'
Aegis.date.isToday(date);          // true/false
Aegis.date.isYesterday(date);      // true/false

Aegis.date.add(date, 7, 'day');    // Add 7 days
Aegis.date.diff(date1, date2, 'day'); // Days between
```

---

## 🔢 Number Utilities

```javascript
Aegis.number.format(1234567);       // '1.234.567' (pt-BR)
Aegis.number.currency(1234.56);     // 'R$ 1.234,56'
Aegis.number.currency(1234, 'USD', 'en-US');  // '$1,234.00'

Aegis.number.clamp(15, 0, 10);      // 10
Aegis.number.random(1, 100);        // Random int
Aegis.number.percent(25, 100);      // 25
Aegis.number.bytes(1536000);        // '1.46 MB'
Aegis.number.ordinal(3);            // '3rd'
```

---

## 📋 Clipboard

```javascript
// Copy text
await Aegis.clipboard.copy('Hello World!');

// Paste text
const text = await Aegis.clipboard.paste();
```

---

## 🔔 Toast Notifications

```javascript
Aegis.toast('Hello World!');

Aegis.toast('Success!', { type: 'success' });
Aegis.toast('Warning!', { type: 'warning' });
Aegis.toast('Error!', { type: 'error' });

Aegis.toast('Custom toast', {
    type: 'info',
    duration: 5000,
    position: 'top-right'  // top-left, bottom-left, bottom-right
});
```

---

## 🎲 Random Utilities

```javascript
Aegis.random.int(1, 100);          // Random integer
Aegis.random.float(0, 1);          // Random float
Aegis.random.bool();               // true or false
Aegis.random.pick(['a', 'b', 'c']); // Random item
Aegis.random.color();              // '#a3f2c1'
Aegis.random.uuid();               // 'xxxxxxxx-xxxx-4xxx-...'
```

---

## ✅ Validation

```javascript
Aegis.is.email('test@email.com');  // true
Aegis.is.url('https://example.com'); // true
Aegis.is.number(123);              // true
Aegis.is.string('hello');          // true
Aegis.is.array([1, 2, 3]);         // true
Aegis.is.object({ a: 1 });         // true
Aegis.is.empty([]);                // true
Aegis.is.mobile();                 // true if mobile device
```

---

## 💾 Storage

```javascript
// Save data (auto JSON stringify)
Aegis.storage.set('user', { name: 'John', age: 30 });

// Get data (auto JSON parse)
const user = Aegis.storage.get('user');

// With fallback
const theme = Aegis.storage.get('theme', 'light');

// Remove
Aegis.storage.remove('user');

// Clear all
Aegis.storage.clear();
```

---

## 📜 Logging

```javascript
Aegis.log.info('Info message');
Aegis.log.success('Success message');
Aegis.log.warn('Warning message');
Aegis.log.error('Error message');
Aegis.log.debug('Debug message');
Aegis.log.table(data);
```

---

## ⏱️ Timing Utilities

```javascript
// Debounce (wait until user stops typing)
const search = Aegis.debounce((query) => {
    fetchResults(query);
}, 300);

Aegis.input('#search', (e) => search(e.target.value));

// Throttle (max once per interval)
const scroll = Aegis.throttle(() => {
    updatePosition();
}, 100);

Aegis.on(window, 'scroll', scroll);

// Delay (promise-based setTimeout)
await Aegis.delay(1000);
console.log('1 second later');

// Ready (DOM loaded)
Aegis.ready(() => {
    console.log('DOM is ready!');
});
```

---

## 🔌 Backend API (Python Bridge)

### File Operations

```javascript
// Read directory
const dir = await Aegis.read({ path: '/home/user' });

// Read file
const file = await Aegis.read({ path: '/home', file: 'notes.txt' });

// Write file
await Aegis.write({ path: '/home', file: 'notes.txt', content: 'Hello!' });

// Check if exists
const info = await Aegis.exists({ path: '/home/user/file.txt' });

// Create directory
await Aegis.mkdir({ path: '/home/user/new-folder' });

// Delete file/folder
await Aegis.remove({ path: '/home/user/old-file.txt' });

// Copy
await Aegis.copy({ src: '/path/from', dest: '/path/to' });

// Move
await Aegis.move({ src: '/path/from', dest: '/path/to' });
```

### Downloads (with aria2c turbo!)

```javascript
await Aegis.download(
    { 
        url: 'https://example.com/file.zip',
        dest: '/home/user/file.zip',
        connections: 16  // Multi-connection download!
    },
    (progress) => {
        console.log(progress.percent + '%');
        console.log(progress.speed); // '5.2 MiB/s'
    }
);
```

### Run Commands

```javascript
// Shell command
const result = await Aegis.run({ sh: 'ls -la' });

// Async command (UI doesn't freeze!)
await Aegis.runAsync(
    { sh: 'apt update' },
    (progress) => console.log(progress.line)
);
```

### Dialogs

```javascript
// Message
await Aegis.dialog.message({
    type: 'info',  // info, warning, error, question
    title: 'Hello',
    message: 'World!'
});

// Open file
const file = await Aegis.dialog.open({
    title: 'Select File',
    filters: [{ name: 'Images', extensions: ['png', 'jpg'] }]
});

// Save file
const path = await Aegis.dialog.save({
    title: 'Save As',
    defaultName: 'document.txt'
});
```

### Window Control

```javascript
await Aegis.app.minimize();
await Aegis.app.maximize();
await Aegis.app.quit();

// For frameless windows
Aegis.window.moveBar('#titlebar', { exclude: '.btn' });
Aegis.window.resizeHandles({
    '.resize-n': 'n', '.resize-se': 'se'
});
```

---

## 🔒 Security (preload.js)

Control which APIs are exposed:

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

---

## 📜 License

MIT © Diego

---

**Made with ❤️ for the Linux community**
