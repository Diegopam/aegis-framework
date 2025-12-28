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

