/**
 * Aegis JavaScript API
 * 
 * This file is injected into WebKit2GTK and provides the bridge
 * between your frontend JavaScript and the Python backend.
 * 
 * @version 0.1.0
 */

(function () {
    'use strict';

    // ==================== Internal Bridge ====================

    let callbackId = 0;
    const pendingCallbacks = new Map();
    const progressCallbacks = new Map();  // For async progress updates

    /**
     * Resolve a callback from Python
     */
    window.__aegisResolve = function (response) {
        const callback = pendingCallbacks.get(response.callbackId);
        if (callback) {
            pendingCallbacks.delete(response.callbackId);
            progressCallbacks.delete(response.callbackId);  // Cleanup progress callback
            if (response.success) {
                callback.resolve(response.data);
            } else {
                callback.reject(new Error(response.error));
            }
        }
    };

    /**
     * Handle progress updates from Python (for async operations)
     */
    window.__aegisProgress = function (response) {
        const callback = progressCallbacks.get(response.callbackId);
        if (callback) {
            callback(response.data);
        }
    };

    /**
     * Send a message to Python backend
     */
    function invoke(action, payload = {}) {
        return new Promise((resolve, reject) => {
            const id = ++callbackId;
            pendingCallbacks.set(id, { resolve, reject });

            const message = JSON.stringify({
                action: action,
                payload: payload,
                callbackId: id
            });

            // Send to Python via WebKit message handler
            if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.aegis) {
                window.webkit.messageHandlers.aegis.postMessage(message);
            } else {
                reject(new Error('Aegis bridge not available'));
            }
        });
    }

    /**
     * Check if an API is allowed by preload
     */
    function isAllowed(api) {
        const allowed = window.__aegisAllowedAPIs || ['*'];
        if (allowed.includes('*')) return true;
        if (allowed.includes(api)) return true;

        // Check namespace (e.g., 'dialog' allows 'dialog.open')
        const namespace = api.split('.')[0];
        return allowed.includes(namespace);
    }

    /**
     * Create a guarded API function
     */
    function guardedInvoke(action) {
        return function (payload) {
            if (!isAllowed(action)) {
                return Promise.reject(new Error(`API '${action}' is not allowed by preload`));
            }
            return invoke(action, payload);
        };
    }

    /**
     * Invoke an async action with progress callback
     * @param {string} action - The action name
     * @param {object} payload - The payload
     * @param {function} onProgress - Progress callback function
     */
    function invokeWithProgress(action, payload, onProgress) {
        return new Promise((resolve, reject) => {
            if (!isAllowed(action)) {
                reject(new Error(`API '${action}' is not allowed by preload`));
                return;
            }

            const id = ++callbackId;
            pendingCallbacks.set(id, { resolve, reject });

            // Register progress callback if provided
            if (onProgress && typeof onProgress === 'function') {
                progressCallbacks.set(id, onProgress);
            }

            const message = JSON.stringify({
                action: action,
                payload: payload,
                callbackId: id
            });

            if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.aegis) {
                window.webkit.messageHandlers.aegis.postMessage(message);
            } else {
                reject(new Error('Aegis bridge not available'));
            }
        });
    }

    // ==================== Public Aegis API ====================

    const Aegis = {
        /**
         * Read file or directory contents
         * 
         * @example
         * // Read a file
         * const result = await Aegis.read({ path: '/home/user', file: 'data.txt' });
         * console.log(result.content);
         * 
         * // List directory
         * const dir = await Aegis.read({ path: '/home/user/documents' });
         * console.log(dir.entries);
         */
        read: guardedInvoke('read'),

        /**
         * Write content to a file
         * 
         * @example
         * await Aegis.write({
         *     path: '/home/user',
         *     file: 'output.txt',
         *     content: 'Hello, World!'
         * });
         * 
         * // Append to file
         * await Aegis.write({
         *     path: '/home/user',
         *     file: 'log.txt',
         *     content: 'New line\n',
         *     append: true
         * });
         */
        write: guardedInvoke('write'),

        /**
         * Execute Python or shell commands
         * 
         * @example
         * // Run shell command
         * const result = await Aegis.run({ sh: 'ls -la' });
         * console.log(result.output);
         * 
         * // Run Python code
         * const pyResult = await Aegis.run({ py: '2 + 2' });
         * console.log(pyResult.output); // "4"
         */
        run: guardedInvoke('run'),

        /**
         * Check if file/directory exists
         * 
         * @example
         * const info = await Aegis.exists({ path: '/home/user/file.txt' });
         * if (info.exists && info.isFile) {
         *     console.log('File exists!');
         * }
         */
        exists: guardedInvoke('exists'),

        /**
         * Create directory
         * 
         * @example
         * await Aegis.mkdir({ path: '/home/user/new-folder', recursive: true });
         */
        mkdir: guardedInvoke('mkdir'),

        /**
         * Remove file or directory
         * 
         * @example
         * await Aegis.remove({ path: '/home/user/old-file.txt' });
         * 
         * // Remove directory recursively
         * await Aegis.remove({ path: '/home/user/old-folder', recursive: true });
         */
        remove: guardedInvoke('remove'),

        /**
         * Copy file or directory
         * 
         * @example
         * await Aegis.copy({
         *     src: '/home/user/file.txt',
         *     dest: '/home/user/backup/file.txt'
         * });
         */
        copy: guardedInvoke('copy'),

        // ==================== Async Operations with Progress ====================

        /**
         * Run command asynchronously with streaming output
         * 
         * @param {object} options - Command options
         * @param {string} options.sh - Shell command to execute
         * @param {function} onProgress - Progress callback, called with each output line
         * @returns {Promise<{output: string, exitCode: number}>}
         * 
         * @example
         * const result = await Aegis.runAsync(
         *     { sh: 'apt install htop' },
         *     (progress) => {
         *         console.log(progress.line);  // Each line of output
         *     }
         * );
         */
        runAsync: function (options, onProgress) {
            return invokeWithProgress('run.async', options, onProgress);
        },

        /**
         * Download file with progress updates
         * 
         * @param {object} options - Download options
         * @param {string} options.url - URL to download from
         * @param {string} options.dest - Destination file path
         * @param {function} onProgress - Progress callback
         * @returns {Promise<{success: boolean, path: string, size: number}>}
         * 
         * @example
         * const result = await Aegis.download(
         *     { 
         *         url: 'https://example.com/file.zip',
         *         dest: '/home/user/downloads/file.zip'
         *     },
         *     (progress) => {
         *         progressBar.style.width = progress.percent + '%';
         *         statusText.textContent = `${progress.downloaded} / ${progress.total}`;
         *     }
         * );
         */
        download: function (options, onProgress) {
            return invokeWithProgress('download', options, onProgress);
        },

        /**
         * Copy file or directory with progress updates (for large files)
         * 
         * @param {object} options - Copy options
         * @param {string} options.src - Source path
         * @param {string} options.dest - Destination path
         * @param {function} onProgress - Progress callback
         * @returns {Promise<{success: boolean, src: string, dest: string}>}
         * 
         * @example
         * await Aegis.copyAsync(
         *     { src: '/path/to/large-folder', dest: '/path/to/backup' },
         *     (progress) => {
         *         console.log(`${progress.percent.toFixed(1)}% - ${progress.current}`);
         *     }
         * );
         */
        copyAsync: function (options, onProgress) {
            return invokeWithProgress('copy.async', options, onProgress);
        },

        /**
         * Move/rename file or directory
         * 
         * @example
         * await Aegis.move({
         *     src: '/home/user/old-name.txt',
         *     dest: '/home/user/new-name.txt'
         * });
         */
        move: guardedInvoke('move'),

        /**
         * Get/set environment variables
         * 
         * @example
         * // Get single variable
         * const home = await Aegis.env({ name: 'HOME' });
         * 
         * // Set variable
         * await Aegis.env({ name: 'MY_VAR', value: 'hello' });
         * 
         * // Get all variables
         * const allEnv = await Aegis.env({});
         */
        env: guardedInvoke('env'),

        // ==================== Dialog API ====================

        dialog: {
            /**
             * Open file dialog
             * 
             * @example
             * const result = await Aegis.dialog.open({
             *     title: 'Select Files',
             *     multiple: true,
             *     filters: [
             *         { name: 'Images', extensions: ['png', 'jpg', 'gif'] },
             *         { name: 'All Files', extensions: ['*'] }
             *     ]
             * });
             * console.log(result.path);
             */
            open: guardedInvoke('dialog.open'),

            /**
             * Save file dialog
             * 
             * @example
             * const result = await Aegis.dialog.save({
             *     title: 'Save As',
             *     defaultName: 'document.txt'
             * });
             * if (result.path) {
             *     await Aegis.write({ path: result.path, content: 'Content' });
             * }
             */
            save: guardedInvoke('dialog.save'),

            /**
             * Show message dialog
             * 
             * @example
             * // Info dialog
             * await Aegis.dialog.message({
             *     type: 'info',
             *     title: 'Success',
             *     message: 'Operation completed!'
             * });
             * 
             * // Confirmation dialog
             * const confirm = await Aegis.dialog.message({
             *     type: 'question',
             *     title: 'Confirm',
             *     message: 'Are you sure?',
             *     buttons: 'yesno'
             * });
             * if (confirm.response) {
             *     // User clicked Yes
             * }
             */
            message: guardedInvoke('dialog.message')
        },

        // ==================== App Control API ====================

        app: {
            /**
             * Quit the application
             */
            quit: guardedInvoke('app.quit'),

            /**
             * Minimize the window
             */
            minimize: guardedInvoke('app.minimize'),

            /**
             * Toggle maximize
             */
            maximize: guardedInvoke('app.maximize'),

            /**
             * Get system paths
             * 
             * @example
             * const home = await Aegis.app.getPath({ name: 'home' });
             * const downloads = await Aegis.app.getPath({ name: 'downloads' });
             * 
             * // Available: home, desktop, documents, downloads, music, pictures, videos, temp, app
             */
            getPath: guardedInvoke('app.getPath')
        },

        // ==================== Window Control API ====================

        window: {
            /**
             * Make an element draggable for window movement
             * Call this on mousedown of your titlebar element
             * 
             * @example
             * // In your HTML: <div class="titlebar" id="titlebar">...</div>
             * // In your JS:
             * document.getElementById('titlebar').addEventListener('mousedown', (e) => {
             *     if (e.target.closest('.titlebar-btn')) return; // Don't drag on buttons
             *     Aegis.window.startDrag();
             * });
             */
            startDrag: guardedInvoke('window.startDrag'),

            /**
             * Start window resize from edge
             * 
             * @param {string} edge - Edge to resize from: n, s, e, w, ne, nw, se, sw
             * 
             * @example
             * // Create resize handles in your CSS/HTML, then:
             * document.querySelector('.resize-se').addEventListener('mousedown', () => {
             *     Aegis.window.resize({ edge: 'se' });
             * });
             */
            resize: guardedInvoke('window.resize'),

            /**
             * Set window size
             * 
             * @example
             * await Aegis.window.setSize({ width: 1024, height: 768 });
             */
            setSize: guardedInvoke('window.setSize'),

            /**
             * Get current window size
             * 
             * @example
             * const { width, height } = await Aegis.window.getSize();
             */
            getSize: guardedInvoke('window.getSize'),

            /**
             * Set window position
             * 
             * @example
             * await Aegis.window.setPosition({ x: 100, y: 100 });
             */
            setPosition: guardedInvoke('window.setPosition'),

            /**
             * Get current window position
             * 
             * @example
             * const { x, y } = await Aegis.window.getPosition();
             */
            getPosition: guardedInvoke('window.getPosition'),

            /**
             * Helper: Setup moveBar on an element
             * Makes the specified element a drag handle for the window
             * 
             * @param {string|Element} selector - CSS selector or element
             * @param {Object} options - Options
             * @param {string} options.exclude - Selector for elements that should NOT trigger drag
             * 
             * @example
             * // Make titlebar draggable, but not buttons
             * Aegis.window.moveBar('#titlebar', { exclude: '.titlebar-btn' });
             */
            moveBar: function (selector, options = {}) {
                const element = typeof selector === 'string'
                    ? document.querySelector(selector)
                    : selector;

                if (!element) {
                    console.warn('[Aegis] moveBar: Element not found:', selector);
                    return;
                }

                element.addEventListener('mousedown', (e) => {
                    // Only left mouse button
                    if (e.button !== 0) return;

                    // Check if click is on excluded element
                    if (options.exclude && e.target.closest(options.exclude)) {
                        console.log('[Aegis] moveBar: excluded element clicked');
                        return;
                    }

                    console.log('[Aegis] moveBar: starting drag at', e.screenX, e.screenY);

                    // Start window drag with screen coordinates
                    Aegis.window.startDrag({
                        x: e.screenX,
                        y: e.screenY,
                        button: e.button + 1  // GTK uses 1-based buttons
                    }).then(r => console.log('[Aegis] startDrag result:', r))
                        .catch(err => console.error('[Aegis] startDrag error:', err));
                });

                console.log('[Aegis] moveBar attached to:', selector);
            },

            /**
             * Helper: Setup resize handles on elements
             * 
             * @param {Object} handles - Map of selector to edge
             * 
             * @example
             * Aegis.window.resizeHandles({
             *     '.resize-n': 'n',
             *     '.resize-s': 's',
             *     '.resize-e': 'e',
             *     '.resize-w': 'w',
             *     '.resize-ne': 'ne',
             *     '.resize-nw': 'nw',
             *     '.resize-se': 'se',
             *     '.resize-sw': 'sw'
             * });
             */
            resizeHandles: function (handles) {
                for (const [selector, edge] of Object.entries(handles)) {
                    const element = document.querySelector(selector);
                    if (element) {
                        element.addEventListener('mousedown', (e) => {
                            if (e.button !== 0) return;
                            Aegis.window.resize({
                                edge,
                                x: e.screenX,
                                y: e.screenY,
                                button: e.button + 1
                            });
                        });
                    }
                }
                console.log('[Aegis] Resize handles attached');
            }
        },

        // ==================== Configuration API ====================

        /**
         * Expose specific APIs (used in preload.js)
         * 
         * @example
         * Aegis.expose(['read', 'write', 'dialog']);
         */
        expose: function (apis) {
            window.__aegisAllowedAPIs = apis;
        },

        /**
         * Expose all APIs (use with caution!)
         */
        exposeAll: function () {
            window.__aegisAllowedAPIs = ['*'];
        },

        /**
         * Configure Aegis behavior
         * 
         * @example
         * Aegis.config({
         *     allowRemoteContent: false,
         *     enableDevTools: true
         * });
         */
        config: function (options) {
            window.__aegisConfig = { ...window.__aegisConfig, ...options };
        },

        /**
         * Register a custom handler (for custom Python actions)
         * 
         * @example
         * // In preload.js:
         * Aegis.handle('customAction', async (data) => {
         *     return await Aegis.run({ py: `custom_function(${data.value})` });
         * });
         * 
         * // In your app:
         * const result = await Aegis.invoke('customAction', { value: 42 });
         */
        handle: function (name, handler) {
            Aegis._customHandlers = Aegis._customHandlers || {};
            Aegis._customHandlers[name] = handler;
        },

        /**
         * Invoke a custom handler or built-in action
         */
        invoke: async function (action, payload) {
            // Check for custom handler first
            if (Aegis._customHandlers && Aegis._customHandlers[action]) {
                return await Aegis._customHandlers[action](payload);
            }
            // Fall back to built-in
            return invoke(action, payload);
        },

        // ==================== DOM Utilities ====================

        /**
         * Version of Aegis
         */
        version: '0.2.0',

        /**
         * Check if running in Aegis environment
         */
        isAegis: function () {
            return !!(window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.aegis);
        },

        // ==================== Element Selection ====================

        /**
         * Get single element by selector
         */
        get: function (selector) {
            if (typeof selector !== 'string') return selector;
            if (selector.startsWith('#') && !selector.includes(' ') && !selector.includes('.')) {
                return document.getElementById(selector.slice(1));
            }
            return document.querySelector(selector);
        },

        /**
         * Get all elements by selector
         */
        getAll: function (selector) {
            return document.querySelectorAll(selector);
        },

        // ==================== Event Shortcuts ====================

        /**
         * Universal event listener
         */
        on: function (selector, events, handler, options = {}) {
            const elements = typeof selector === 'string' ? Aegis.getAll(selector) : [selector];
            const eventList = events.split(' ');
            elements.forEach(el => {
                eventList.forEach(event => {
                    el.addEventListener(event.trim(), handler, options);
                });
            });
            return elements;
        },

        /**
         * One-time event listener
         */
        once: function (selector, events, handler) {
            return Aegis.on(selector, events, handler, { once: true });
        },

        /**
         * Remove event listener
         */
        off: function (selector, events, handler) {
            const elements = typeof selector === 'string' ? Aegis.getAll(selector) : [selector];
            const eventList = events.split(' ');
            elements.forEach(el => {
                eventList.forEach(event => {
                    el.removeEventListener(event.trim(), handler);
                });
            });
            return elements;
        },

        /**
         * Click shortcut
         */
        click: function (selector, handler) {
            return Aegis.on(selector, 'click', handler);
        },

        /**
         * Submit shortcut
         */
        submit: function (selector, handler) {
            return Aegis.on(selector, 'submit', handler);
        },

        /**
         * Change shortcut
         */
        change: function (selector, handler) {
            return Aegis.on(selector, 'change', handler);
        },

        /**
         * Input shortcut
         */
        input: function (selector, handler) {
            return Aegis.on(selector, 'input', handler);
        },

        /**
         * Hover shortcut (mouseenter + mouseleave)
         */
        hover: function (selector, onEnter, onLeave) {
            Aegis.on(selector, 'mouseenter', onEnter);
            if (onLeave) Aegis.on(selector, 'mouseleave', onLeave);
        },

        /**
         * Key press shortcut
         */
        keypress: function (selector, handler) {
            return Aegis.on(selector, 'keydown', handler);
        },

        // ==================== Element Creation ====================

        /**
         * Create element with options
         */
        create: function (tag, options = {}) {
            const el = document.createElement(tag);
            if (options.id) el.id = options.id;
            if (options.class) el.className = options.class;
            if (options.html) el.innerHTML = options.html;
            if (options.text) el.textContent = options.text;
            if (options.value !== undefined) el.value = options.value;
            if (options.attrs) {
                Object.entries(options.attrs).forEach(([key, value]) => {
                    el.setAttribute(key, value);
                });
            }
            if (options.style) {
                Object.assign(el.style, options.style);
            }
            if (options.data) {
                Object.entries(options.data).forEach(([key, value]) => {
                    el.dataset[key] = value;
                });
            }
            if (options.on) {
                Object.entries(options.on).forEach(([event, handler]) => {
                    el.addEventListener(event, handler);
                });
            }
            if (options.children) {
                options.children.forEach(child => el.appendChild(child));
            }
            if (options.parent) {
                const parent = Aegis.get(options.parent);
                if (parent) parent.appendChild(el);
            }
            return el;
        },

        // ==================== Class Manipulation ====================

        addClass: function (selector, ...classes) {
            const el = Aegis.get(selector);
            if (el) el.classList.add(...classes);
            return el;
        },

        removeClass: function (selector, ...classes) {
            const el = Aegis.get(selector);
            if (el) el.classList.remove(...classes);
            return el;
        },

        toggleClass: function (selector, className, force) {
            const el = Aegis.get(selector);
            if (el) el.classList.toggle(className, force);
            return el;
        },

        hasClass: function (selector, className) {
            const el = Aegis.get(selector);
            return el ? el.classList.contains(className) : false;
        },

        // ==================== Style Manipulation ====================

        css: function (selector, styles) {
            const el = Aegis.get(selector);
            if (el && styles) Object.assign(el.style, styles);
            return el;
        },

        hide: function (selector) {
            const el = Aegis.get(selector);
            if (el) el.style.display = 'none';
            return el;
        },

        show: function (selector, display = 'block') {
            const el = Aegis.get(selector);
            if (el) el.style.display = display;
            return el;
        },

        toggleDisplay: function (selector) {
            const el = Aegis.get(selector);
            if (el) el.style.display = el.style.display === 'none' ? '' : 'none';
            return el;
        },

        // ==================== Content Manipulation ====================

        attr: function (selector, name, value) {
            const el = Aegis.get(selector);
            if (!el) return null;
            if (value === undefined) return el.getAttribute(name);
            el.setAttribute(name, value);
            return el;
        },

        data: function (selector, key, value) {
            const el = Aegis.get(selector);
            if (!el) return null;
            if (value === undefined) return el.dataset[key];
            el.dataset[key] = value;
            return el;
        },

        html: function (selector, content) {
            const el = Aegis.get(selector);
            if (!el) return null;
            if (content === undefined) return el.innerHTML;
            el.innerHTML = content;
            return el;
        },

        text: function (selector, content) {
            const el = Aegis.get(selector);
            if (!el) return null;
            if (content === undefined) return el.textContent;
            el.textContent = content;
            return el;
        },

        val: function (selector, value) {
            const el = Aegis.get(selector);
            if (!el) return null;
            if (value === undefined) return el.value;
            el.value = value;
            return el;
        },

        // ==================== DOM Manipulation ====================

        each: function (selector, callback) {
            const elements = typeof selector === 'string' ? Aegis.getAll(selector) : selector;
            elements.forEach((el, i) => callback(el, i));
            return elements;
        },

        removeEl: function (selector) {
            const el = Aegis.get(selector);
            if (el && el.parentNode) el.parentNode.removeChild(el);
            return el;
        },

        append: function (parent, child) {
            const p = Aegis.get(parent);
            const c = typeof child === 'string' ? Aegis.get(child) : child;
            if (p && c) p.appendChild(c);
            return p;
        },

        prepend: function (parent, child) {
            const p = Aegis.get(parent);
            const c = typeof child === 'string' ? Aegis.get(child) : child;
            if (p && c) p.insertBefore(c, p.firstChild);
            return p;
        },

        empty: function (selector) {
            const el = Aegis.get(selector);
            if (el) el.innerHTML = '';
            return el;
        },

        // ==================== JSON Utilities ====================

        parseJSON: function (str, fallback = null) {
            try {
                return JSON.parse(str);
            } catch (e) {
                return fallback;
            }
        },

        stringify: function (obj, pretty = false) {
            return JSON.stringify(obj, null, pretty ? 2 : 0);
        },

        // ==================== Storage Utilities ====================

        storage: {
            get: function (key, fallback = null) {
                try {
                    const value = localStorage.getItem(key);
                    return value ? JSON.parse(value) : fallback;
                } catch (e) {
                    return fallback;
                }
            },
            set: function (key, value) {
                try {
                    localStorage.setItem(key, JSON.stringify(value));
                    return true;
                } catch (e) {
                    return false;
                }
            },
            remove: function (key) {
                localStorage.removeItem(key);
            },
            clear: function () {
                localStorage.clear();
            }
        },

        // ==================== Animation Utilities ====================

        fadeIn: function (selector, duration = 300) {
            const el = Aegis.get(selector);
            if (!el) return;
            el.style.opacity = '0';
            el.style.display = '';
            el.style.transition = `opacity ${duration}ms ease`;
            requestAnimationFrame(() => {
                el.style.opacity = '1';
            });
            return el;
        },

        fadeOut: function (selector, duration = 300) {
            const el = Aegis.get(selector);
            if (!el) return;
            el.style.transition = `opacity ${duration}ms ease`;
            el.style.opacity = '0';
            setTimeout(() => {
                el.style.display = 'none';
            }, duration);
            return el;
        },

        // ==================== Utility Functions ====================

        ready: function (callback) {
            if (document.readyState !== 'loading') {
                callback();
            } else {
                document.addEventListener('DOMContentLoaded', callback);
            }
        },

        debounce: function (func, wait) {
            let timeout;
            return function (...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        },

        throttle: function (func, limit) {
            let inThrottle;
            return function (...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        delay: function (ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        },

        /**
         * Generate unique ID
         */
        uid: function (prefix = 'aegis') {
            return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        },

        // ==================== Form Utilities ====================

        form: {
            /**
             * Serialize form to object
             */
            serialize: function (selector) {
                const form = Aegis.get(selector);
                if (!form) return {};
                const data = {};
                const formData = new FormData(form);
                formData.forEach((value, key) => {
                    if (data[key]) {
                        if (!Array.isArray(data[key])) data[key] = [data[key]];
                        data[key].push(value);
                    } else {
                        data[key] = value;
                    }
                });
                return data;
            },

            /**
             * Reset form
             */
            reset: function (selector) {
                const form = Aegis.get(selector);
                if (form) form.reset();
                return form;
            },

            /**
             * Fill form with data
             */
            fill: function (selector, data) {
                const form = Aegis.get(selector);
                if (!form) return;
                Object.entries(data).forEach(([name, value]) => {
                    const field = form.querySelector(`[name="${name}"]`);
                    if (field) {
                        if (field.type === 'checkbox') {
                            field.checked = !!value;
                        } else if (field.type === 'radio') {
                            const radio = form.querySelector(`[name="${name}"][value="${value}"]`);
                            if (radio) radio.checked = true;
                        } else {
                            field.value = value;
                        }
                    }
                });
                return form;
            },

            /**
             * Simple validation
             */
            validate: function (selector, rules = {}) {
                const form = Aegis.get(selector);
                if (!form) return { valid: false, errors: ['Form not found'] };
                const errors = [];
                Object.entries(rules).forEach(([name, rule]) => {
                    const field = form.querySelector(`[name="${name}"]`);
                    const value = field?.value || '';
                    if (rule.required && !value.trim()) {
                        errors.push(`${name} is required`);
                    }
                    if (rule.minLength && value.length < rule.minLength) {
                        errors.push(`${name} must be at least ${rule.minLength} characters`);
                    }
                    if (rule.pattern && !rule.pattern.test(value)) {
                        errors.push(`${name} is invalid`);
                    }
                    if (rule.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                        errors.push(`${name} must be a valid email`);
                    }
                });
                return { valid: errors.length === 0, errors };
            }
        },

        // ==================== HTTP/Fetch Utilities ====================

        http: {
            /**
             * GET request
             */
            get: async function (url, options = {}) {
                const response = await fetch(url, { method: 'GET', ...options });
                return options.raw ? response : response.json();
            },

            /**
             * POST request
             */
            post: async function (url, data, options = {}) {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...options.headers },
                    body: JSON.stringify(data),
                    ...options
                });
                return options.raw ? response : response.json();
            },

            /**
             * PUT request
             */
            put: async function (url, data, options = {}) {
                const response = await fetch(url, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json', ...options.headers },
                    body: JSON.stringify(data),
                    ...options
                });
                return options.raw ? response : response.json();
            },

            /**
             * DELETE request
             */
            delete: async function (url, options = {}) {
                const response = await fetch(url, { method: 'DELETE', ...options });
                return options.raw ? response : response.json();
            }
        },

        // ==================== Cookie Utilities ====================

        cookie: {
            get: function (name) {
                const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
                return match ? decodeURIComponent(match[2]) : null;
            },
            set: function (name, value, days = 365, path = '/') {
                const expires = new Date(Date.now() + days * 864e5).toUTCString();
                document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=${path}`;
            },
            remove: function (name, path = '/') {
                document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=${path}`;
            }
        },

        // ==================== URL Utilities ====================

        url: {
            /**
             * Get query parameters as object
             */
            params: function (url = window.location.href) {
                const params = {};
                new URL(url).searchParams.forEach((v, k) => params[k] = v);
                return params;
            },

            /**
             * Get single parameter
             */
            param: function (name, url = window.location.href) {
                return new URL(url).searchParams.get(name);
            },

            /**
             * Build URL with params
             */
            build: function (base, params = {}) {
                const url = new URL(base, window.location.origin);
                Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
                return url.toString();
            },

            /**
             * Get current path
             */
            path: function () {
                return window.location.pathname;
            },

            /**
             * Get hash without #
             */
            hash: function () {
                return window.location.hash.slice(1);
            }
        },

        // ==================== String Utilities ====================

        string: {
            capitalize: function (str) {
                return str.charAt(0).toUpperCase() + str.slice(1);
            },

            titleCase: function (str) {
                return str.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
            },

            camelCase: function (str) {
                return str.replace(/[-_\s]+(.)?/g, (_, c) => c ? c.toUpperCase() : '');
            },

            kebabCase: function (str) {
                return str.replace(/([a-z])([A-Z])/g, '$1-$2').replace(/[\s_]+/g, '-').toLowerCase();
            },

            snakeCase: function (str) {
                return str.replace(/([a-z])([A-Z])/g, '$1_$2').replace(/[\s-]+/g, '_').toLowerCase();
            },

            slugify: function (str) {
                return str.toLowerCase().trim()
                    .replace(/[^\w\s-]/g, '').replace(/[\s_-]+/g, '-').replace(/^-+|-+$/g, '');
            },

            truncate: function (str, length, suffix = '...') {
                return str.length > length ? str.slice(0, length) + suffix : str;
            },

            pad: function (str, length, char = ' ', end = false) {
                str = String(str);
                return end ? str.padEnd(length, char) : str.padStart(length, char);
            },

            reverse: function (str) {
                return str.split('').reverse().join('');
            },

            count: function (str, search) {
                return (str.match(new RegExp(search, 'g')) || []).length;
            },

            between: function (str, start, end) {
                const s = str.indexOf(start) + start.length;
                const e = str.indexOf(end, s);
                return s > start.length - 1 && e > -1 ? str.slice(s, e) : '';
            },

            template: function (str, data) {
                return str.replace(/\{\{(\w+)\}\}/g, (_, key) => data[key] ?? '');
            }
        },

        // ==================== Array Utilities ====================

        array: {
            unique: function (arr) {
                return [...new Set(arr)];
            },

            shuffle: function (arr) {
                const a = [...arr];
                for (let i = a.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [a[i], a[j]] = [a[j], a[i]];
                }
                return a;
            },

            chunk: function (arr, size) {
                const chunks = [];
                for (let i = 0; i < arr.length; i += size) {
                    chunks.push(arr.slice(i, i + size));
                }
                return chunks;
            },

            flatten: function (arr, depth = Infinity) {
                return arr.flat(depth);
            },

            compact: function (arr) {
                return arr.filter(Boolean);
            },

            first: function (arr, n = 1) {
                return n === 1 ? arr[0] : arr.slice(0, n);
            },

            last: function (arr, n = 1) {
                return n === 1 ? arr[arr.length - 1] : arr.slice(-n);
            },

            sample: function (arr) {
                return arr[Math.floor(Math.random() * arr.length)];
            },

            groupBy: function (arr, key) {
                return arr.reduce((groups, item) => {
                    const k = typeof key === 'function' ? key(item) : item[key];
                    (groups[k] = groups[k] || []).push(item);
                    return groups;
                }, {});
            },

            sortBy: function (arr, key, desc = false) {
                return [...arr].sort((a, b) => {
                    const va = typeof key === 'function' ? key(a) : a[key];
                    const vb = typeof key === 'function' ? key(b) : b[key];
                    return desc ? (vb > va ? 1 : -1) : (va > vb ? 1 : -1);
                });
            },

            diff: function (arr1, arr2) {
                return arr1.filter(x => !arr2.includes(x));
            },

            intersect: function (arr1, arr2) {
                return arr1.filter(x => arr2.includes(x));
            },

            range: function (start, end, step = 1) {
                const arr = [];
                for (let i = start; i <= end; i += step) arr.push(i);
                return arr;
            }
        },

        // ==================== Object Utilities ====================

        object: {
            clone: function (obj) {
                return JSON.parse(JSON.stringify(obj));
            },

            merge: function (...objects) {
                return objects.reduce((acc, obj) => ({ ...acc, ...obj }), {});
            },

            isEmpty: function (obj) {
                return Object.keys(obj).length === 0;
            },

            pick: function (obj, keys) {
                return keys.reduce((acc, key) => {
                    if (key in obj) acc[key] = obj[key];
                    return acc;
                }, {});
            },

            omit: function (obj, keys) {
                return Object.fromEntries(Object.entries(obj).filter(([k]) => !keys.includes(k)));
            },

            keys: function (obj) {
                return Object.keys(obj);
            },

            values: function (obj) {
                return Object.values(obj);
            },

            entries: function (obj) {
                return Object.entries(obj);
            },

            fromEntries: function (entries) {
                return Object.fromEntries(entries);
            },

            get: function (obj, path, fallback = undefined) {
                return path.split('.').reduce((o, k) => (o || {})[k], obj) ?? fallback;
            },

            set: function (obj, path, value) {
                const keys = path.split('.');
                const last = keys.pop();
                const target = keys.reduce((o, k) => (o[k] = o[k] || {}), obj);
                target[last] = value;
                return obj;
            }
        },

        // ==================== Date Utilities ====================

        date: {
            now: function () {
                return new Date();
            },

            format: function (date, format = 'YYYY-MM-DD') {
                const d = new Date(date);
                const pad = n => String(n).padStart(2, '0');
                return format
                    .replace('YYYY', d.getFullYear())
                    .replace('MM', pad(d.getMonth() + 1))
                    .replace('DD', pad(d.getDate()))
                    .replace('HH', pad(d.getHours()))
                    .replace('mm', pad(d.getMinutes()))
                    .replace('ss', pad(d.getSeconds()));
            },

            ago: function (date) {
                const seconds = Math.floor((Date.now() - new Date(date)) / 1000);
                const intervals = [
                    [31536000, 'year'], [2592000, 'month'], [86400, 'day'],
                    [3600, 'hour'], [60, 'minute'], [1, 'second']
                ];
                for (const [secs, unit] of intervals) {
                    const n = Math.floor(seconds / secs);
                    if (n >= 1) return `${n} ${unit}${n > 1 ? 's' : ''} ago`;
                }
                return 'just now';
            },

            isToday: function (date) {
                const d = new Date(date);
                const today = new Date();
                return d.toDateString() === today.toDateString();
            },

            isYesterday: function (date) {
                const d = new Date(date);
                const yesterday = new Date(Date.now() - 864e5);
                return d.toDateString() === yesterday.toDateString();
            },

            add: function (date, amount, unit = 'day') {
                const d = new Date(date);
                const ms = { second: 1000, minute: 60000, hour: 3600000, day: 864e5 };
                return new Date(d.getTime() + amount * (ms[unit] || ms.day));
            },

            diff: function (date1, date2, unit = 'day') {
                const ms = Math.abs(new Date(date1) - new Date(date2));
                const divisors = { second: 1000, minute: 60000, hour: 3600000, day: 864e5 };
                return Math.floor(ms / (divisors[unit] || divisors.day));
            }
        },

        // ==================== Number Utilities ====================

        number: {
            format: function (num, decimals = 0, locale = 'pt-BR') {
                return new Intl.NumberFormat(locale, {
                    minimumFractionDigits: decimals,
                    maximumFractionDigits: decimals
                }).format(num);
            },

            currency: function (num, currency = 'BRL', locale = 'pt-BR') {
                return new Intl.NumberFormat(locale, {
                    style: 'currency',
                    currency
                }).format(num);
            },

            clamp: function (num, min, max) {
                return Math.min(Math.max(num, min), max);
            },

            random: function (min = 0, max = 100) {
                return Math.floor(Math.random() * (max - min + 1)) + min;
            },

            percent: function (value, total) {
                return total ? Math.round((value / total) * 100) : 0;
            },

            bytes: function (bytes, decimals = 2) {
                if (bytes === 0) return '0 B';
                const k = 1024;
                const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
            },

            ordinal: function (n) {
                const s = ['th', 'st', 'nd', 'rd'];
                const v = n % 100;
                return n + (s[(v - 20) % 10] || s[v] || s[0]);
            }
        },

        // ==================== Clipboard Utilities ====================

        clipboard: {
            copy: async function (text) {
                try {
                    await navigator.clipboard.writeText(text);
                    return true;
                } catch (e) {
                    // Fallback
                    const ta = document.createElement('textarea');
                    ta.value = text;
                    ta.style.position = 'fixed';
                    ta.style.opacity = '0';
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    return true;
                }
            },

            paste: async function () {
                try {
                    return await navigator.clipboard.readText();
                } catch (e) {
                    return null;
                }
            }
        },

        // ==================== Toast/Notification ====================

        toast: function (message, options = {}) {
            const { duration = 3000, type = 'info', position = 'bottom-right' } = options;

            // Create container if not exists
            let container = document.getElementById('aegis-toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'aegis-toast-container';
                container.style.cssText = `
                    position: fixed; z-index: 99999; display: flex; flex-direction: column; gap: 10px;
                    ${position.includes('top') ? 'top: 20px' : 'bottom: 20px'};
                    ${position.includes('left') ? 'left: 20px' : 'right: 20px'};
                `;
                document.body.appendChild(container);
            }

            const colors = { info: '#3498db', success: '#2ecc71', warning: '#f39c12', error: '#e74c3c' };
            const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌' };

            const toast = document.createElement('div');
            toast.style.cssText = `
                background: ${colors[type] || colors.info}; color: white; padding: 12px 20px;
                border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                font-family: -apple-system, sans-serif; font-size: 14px;
                display: flex; align-items: center; gap: 10px;
                animation: aegisToastIn 0.3s ease;
                max-width: 350px;
            `;
            toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
            container.appendChild(toast);

            // Add animation styles if not exist
            if (!document.getElementById('aegis-toast-styles')) {
                const style = document.createElement('style');
                style.id = 'aegis-toast-styles';
                style.textContent = `
                    @keyframes aegisToastIn { from { opacity: 0; transform: translateX(100px); } }
                    @keyframes aegisToastOut { to { opacity: 0; transform: translateX(100px); } }
                `;
                document.head.appendChild(style);
            }

            setTimeout(() => {
                toast.style.animation = 'aegisToastOut 0.3s ease forwards';
                setTimeout(() => toast.remove(), 300);
            }, duration);

            return toast;
        },

        // ==================== Random Utilities ====================

        random: {
            int: function (min = 0, max = 100) {
                return Math.floor(Math.random() * (max - min + 1)) + min;
            },

            float: function (min = 0, max = 1, decimals = 2) {
                return parseFloat((Math.random() * (max - min) + min).toFixed(decimals));
            },

            bool: function (probability = 0.5) {
                return Math.random() < probability;
            },

            pick: function (arr) {
                return arr[Math.floor(Math.random() * arr.length)];
            },

            color: function () {
                return '#' + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0');
            },

            uuid: function () {
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
                    const r = Math.random() * 16 | 0;
                    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
                });
            }
        },

        // ==================== Validation Utilities ====================

        is: {
            email: function (str) {
                return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(str);
            },
            url: function (str) {
                try { new URL(str); return true; } catch { return false; }
            },
            number: function (val) {
                return typeof val === 'number' && !isNaN(val);
            },
            string: function (val) {
                return typeof val === 'string';
            },
            array: function (val) {
                return Array.isArray(val);
            },
            object: function (val) {
                return val !== null && typeof val === 'object' && !Array.isArray(val);
            },
            function: function (val) {
                return typeof val === 'function';
            },
            empty: function (val) {
                if (val == null) return true;
                if (Array.isArray(val) || typeof val === 'string') return val.length === 0;
                if (typeof val === 'object') return Object.keys(val).length === 0;
                return false;
            },
            mobile: function () {
                return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            }
        },

        // ==================== Log Utilities ====================

        log: {
            info: function (...args) {
                console.log('%c[INFO]', 'color: #3498db; font-weight: bold;', ...args);
            },
            success: function (...args) {
                console.log('%c[SUCCESS]', 'color: #2ecc71; font-weight: bold;', ...args);
            },
            warn: function (...args) {
                console.log('%c[WARN]', 'color: #f39c12; font-weight: bold;', ...args);
            },
            error: function (...args) {
                console.log('%c[ERROR]', 'color: #e74c3c; font-weight: bold;', ...args);
            },
            debug: function (...args) {
                console.log('%c[DEBUG]', 'color: #9b59b6; font-weight: bold;', ...args);
            },
            table: function (data) {
                console.table(data);
            }
        }
    };

    // ==================== Expose to Window ====================

    // Make Aegis available globally
    window.Aegis = Aegis;

    // Also expose as module if applicable
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = Aegis;
    }

    console.log('%c⚡ Aegis v' + Aegis.version + ' loaded', 'color: #00ff88; font-weight: bold;');

})();
