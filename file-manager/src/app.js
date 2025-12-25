/**
 * Windows 10 File Manager - Built with Aegis
 * Complete file manager using the Aegis API
 */

class FileManager {
    constructor() {
        // State
        this.currentPath = '';
        this.history = [];
        this.historyIndex = -1;
        this.selectedItems = new Set();
        this.clipboard = { items: [], cut: false };
        this.isListView = false;
        this.homePath = '';

        // DOM Elements
        this.fileGrid = document.getElementById('file-grid');
        this.pathInput = document.getElementById('path-input');
        this.searchInput = document.getElementById('search-input');
        this.itemCount = document.getElementById('item-count');
        this.selectedCount = document.getElementById('selected-count');
        this.contextMenu = document.getElementById('context-menu');
        this.propertiesModal = document.getElementById('properties-modal');

        this.init();
    }

    async init() {
        // Check if Aegis is available
        if (!Aegis.isAegis()) {
            this.showError('Aegis não está disponível. Execute com: aegis dev');
            return;
        }

        // Get home path
        const home = await Aegis.app.getPath({ name: 'home' });
        this.homePath = home.path;

        // Update sidebar with LOCALIZED paths
        await this.updateSidebarPaths();

        // Setup event listeners
        this.setupEventListeners();

        // Setup window drag on titlebar (exclude buttons)
        Aegis.window.moveBar('#titlebar', { exclude: '.titlebar-btn, .titlebar-controls' });

        // Setup resize handles for frameless window
        Aegis.window.resizeHandles({
            '.resize-n': 'n',
            '.resize-s': 's',
            '.resize-e': 'e',
            '.resize-w': 'w',
            '.resize-ne': 'ne',
            '.resize-nw': 'nw',
            '.resize-se': 'se',
            '.resize-sw': 'sw'
        });

        // Navigate to home
        await this.navigateTo(this.homePath);
    }

    async updateSidebarPaths() {
        // Get localized paths using xdg-user-dir
        const pathNames = {
            'desktop': 'Área de Trabalho',
            'downloads': 'Downloads',
            'documents': 'Documentos',
            'pictures': 'Imagens',
            'music': 'Músicas',
            'videos': 'Vídeos'
        };

        const items = document.querySelectorAll('.sidebar-item[data-path]');

        for (const item of items) {
            let pathKey = item.dataset.path;

            // Handle $HOME/xxx paths
            if (pathKey.startsWith('$HOME/')) {
                const folderName = pathKey.replace('$HOME/', '').toLowerCase();

                // Map to xdg names
                const xdgMap = {
                    'desktop': 'desktop',
                    'downloads': 'downloads',
                    'documents': 'documents',
                    'pictures': 'pictures',
                    'music': 'music',
                    'videos': 'videos'
                };

                if (xdgMap[folderName]) {
                    try {
                        const result = await Aegis.app.getPath({ name: xdgMap[folderName] });
                        item.dataset.path = result.path;
                    } catch (e) {
                        // Fallback to English name
                        item.dataset.path = `${this.homePath}/${folderName.charAt(0).toUpperCase() + folderName.slice(1)}`;
                    }
                } else {
                    item.dataset.path = pathKey.replace('$HOME', this.homePath);
                }
            } else if (pathKey === '$HOME') {
                item.dataset.path = this.homePath;
            }
        }
    }

    setupEventListeners() {
        // Titlebar controls
        document.getElementById('btn-minimize').addEventListener('click', () => Aegis.app.minimize());
        document.getElementById('btn-maximize').addEventListener('click', () => Aegis.app.maximize());
        document.getElementById('btn-close').addEventListener('click', () => Aegis.app.quit());

        // Navigation buttons
        document.getElementById('btn-back').addEventListener('click', () => this.goBack());
        document.getElementById('btn-forward').addEventListener('click', () => this.goForward());
        document.getElementById('btn-up').addEventListener('click', () => this.goUp());

        // Sidebar items
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.addEventListener('click', () => {
                const path = item.dataset.path;
                if (path) this.navigateTo(path);
            });
        });

        // Ribbon buttons
        document.getElementById('btn-new-folder').addEventListener('click', () => this.createFolder());
        document.getElementById('btn-new-file').addEventListener('click', () => this.createFile());
        document.getElementById('btn-copy').addEventListener('click', () => this.copy());
        document.getElementById('btn-cut').addEventListener('click', () => this.cut());
        document.getElementById('btn-paste').addEventListener('click', () => this.paste());
        document.getElementById('btn-delete').addEventListener('click', () => this.delete());
        document.getElementById('btn-rename').addEventListener('click', () => this.rename());
        document.getElementById('btn-properties').addEventListener('click', () => this.showProperties());

        // View toggle
        document.getElementById('btn-grid-view').addEventListener('click', () => this.setGridView());
        document.getElementById('btn-list-view').addEventListener('click', () => this.setListView());

        // Address bar
        this.pathInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.navigateTo(this.pathInput.value);
            }
        });
        this.pathInput.addEventListener('focus', () => {
            this.pathInput.readOnly = false;
            this.pathInput.select();
        });
        this.pathInput.addEventListener('blur', () => {
            this.pathInput.readOnly = true;
        });

        // Search
        this.searchInput.addEventListener('input', () => this.filterFiles());

        // File area click (deselect)
        this.fileGrid.addEventListener('click', (e) => {
            if (e.target === this.fileGrid) {
                this.deselectAll();
            }
        });

        // Context menu
        document.addEventListener('contextmenu', (e) => this.showContextMenu(e));
        document.addEventListener('click', () => this.hideContextMenu());

        // Context menu actions
        document.querySelectorAll('.context-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const action = item.dataset.action;
                this.handleContextAction(action);
            });
        });

        // Modal
        document.getElementById('close-properties').addEventListener('click', () => this.hideProperties());
        document.getElementById('btn-ok-properties').addEventListener('click', () => this.hideProperties());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Note: Window drag is handled by Aegis.window.moveBar() in init()
    }

    // ==================== Navigation ====================

    async navigateTo(path) {
        try {
            // Check if path exists
            const exists = await Aegis.exists({ path });
            if (!exists.exists) {
                await Aegis.dialog.message({
                    type: 'error',
                    title: 'Erro',
                    message: `Caminho não encontrado: ${path}`
                });
                return;
            }

            if (!exists.isDirectory) {
                // Open file with default application
                await Aegis.run({ sh: `xdg-open "${path}"` });
                return;
            }

            // Update history
            if (this.currentPath !== path) {
                this.history = this.history.slice(0, this.historyIndex + 1);
                this.history.push(path);
                this.historyIndex = this.history.length - 1;
            }

            this.currentPath = path;
            this.pathInput.value = path;
            this.deselectAll();

            // Update sidebar active state
            document.querySelectorAll('.sidebar-item').forEach(item => {
                item.classList.toggle('active', item.dataset.path === path);
            });

            // Load files
            await this.loadFiles(path);

            // Update navigation buttons
            this.updateNavButtons();

        } catch (err) {
            console.error('Navigation error:', err);
            this.showError(err.message);
        }
    }

    async loadFiles(path) {
        this.fileGrid.innerHTML = '<div class="loading">Carregando</div>';

        try {
            const result = await Aegis.read({ path });
            const entries = result.entries || [];

            // Sort: folders first, then alphabetically
            entries.sort((a, b) => {
                if (a.isDirectory && !b.isDirectory) return -1;
                if (!a.isDirectory && b.isDirectory) return 1;
                return a.name.localeCompare(b.name);
            });

            // Filter hidden files (optional)
            const visibleEntries = entries.filter(e => !e.name.startsWith('.'));

            if (visibleEntries.length === 0) {
                this.fileGrid.innerHTML = `
                    <div class="empty-state">
                        <span class="empty-state-icon">📂</span>
                        <span class="empty-state-text">Esta pasta está vazia</span>
                    </div>
                `;
            } else {
                this.fileGrid.innerHTML = '';
                visibleEntries.forEach(entry => {
                    this.fileGrid.appendChild(this.createFileItem(entry));
                });
            }

            // Update status bar
            this.itemCount.textContent = `${visibleEntries.length} itens`;

        } catch (err) {
            this.fileGrid.innerHTML = `
                <div class="empty-state">
                    <span class="empty-state-icon">⚠️</span>
                    <span class="empty-state-text">Erro ao carregar: ${err.message}</span>
                </div>
            `;
        }
    }

    createFileItem(entry) {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.dataset.name = entry.name;
        item.dataset.path = `${this.currentPath}/${entry.name}`;
        item.dataset.isDirectory = entry.isDirectory;
        item.dataset.size = entry.size;
        item.dataset.modified = entry.modified;

        const icon = this.getFileIcon(entry);
        const size = entry.isDirectory ? '' : this.formatSize(entry.size);
        const date = entry.modified ? this.formatDate(entry.modified) : '';

        if (this.isListView) {
            item.innerHTML = `
                <span class="file-icon">${icon}</span>
                <span class="file-name">${entry.name}</span>
                <div class="file-meta">
                    <span>${date}</span>
                    <span>${entry.isDirectory ? 'Pasta' : this.getFileType(entry.name)}</span>
                    <span>${size}</span>
                </div>
            `;
        } else {
            item.innerHTML = `
                <span class="file-icon">${icon}</span>
                <span class="file-name">${entry.name}</span>
            `;
        }

        // Click handlers
        item.addEventListener('click', (e) => {
            if (e.ctrlKey) {
                this.toggleSelection(item);
            } else {
                this.selectItem(item);
            }
        });

        item.addEventListener('dblclick', () => {
            const path = item.dataset.path;
            this.navigateTo(path);
        });

        return item;
    }

    getFileIcon(entry) {
        if (entry.isDirectory) return '📁';

        const ext = entry.name.split('.').pop().toLowerCase();
        const icons = {
            // Documents
            'pdf': '📕',
            'doc': '📘', 'docx': '📘',
            'xls': '📗', 'xlsx': '📗',
            'ppt': '📙', 'pptx': '📙',
            'txt': '📄',
            'md': '📝',
            // Code
            'js': '📜', 'ts': '📜',
            'py': '🐍',
            'html': '🌐', 'css': '🎨',
            'json': '📋', 'xml': '📋',
            'java': '☕', 'c': '🔧', 'cpp': '🔧',
            // Media
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'svg': '🖼️', 'webp': '🖼️',
            'mp3': '🎵', 'wav': '🎵', 'ogg': '🎵', 'flac': '🎵',
            'mp4': '🎬', 'mkv': '🎬', 'avi': '🎬', 'mov': '🎬', 'webm': '🎬',
            // Archives
            'zip': '📦', 'rar': '📦', '7z': '📦', 'tar': '📦', 'gz': '📦',
            // Executables
            'exe': '⚙️', 'msi': '⚙️', 'deb': '📦', 'rpm': '📦', 'AppImage': '⚙️',
            'sh': '⚡', 'bash': '⚡',
            // Others
            'iso': '💿',
            'conf': '⚙️', 'cfg': '⚙️', 'ini': '⚙️',
        };

        return icons[ext] || '📄';
    }

    getFileType(name) {
        const ext = name.split('.').pop().toLowerCase();
        const types = {
            'pdf': 'Documento PDF',
            'doc': 'Documento Word', 'docx': 'Documento Word',
            'xls': 'Planilha Excel', 'xlsx': 'Planilha Excel',
            'txt': 'Arquivo de Texto',
            'jpg': 'Imagem JPEG', 'jpeg': 'Imagem JPEG',
            'png': 'Imagem PNG', 'gif': 'Imagem GIF',
            'mp3': 'Áudio MP3', 'mp4': 'Vídeo MP4',
            'zip': 'Arquivo ZIP', 'rar': 'Arquivo RAR',
            'js': 'JavaScript', 'py': 'Python', 'html': 'HTML',
        };
        return types[ext] || `Arquivo ${ext.toUpperCase()}`;
    }

    formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    formatDate(timestamp) {
        const date = new Date(timestamp * 1000);
        return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    }

    goBack() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.navigateTo(this.history[this.historyIndex]);
        }
    }

    goForward() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this.navigateTo(this.history[this.historyIndex]);
        }
    }

    goUp() {
        const parent = this.currentPath.split('/').slice(0, -1).join('/') || '/';
        this.navigateTo(parent);
    }

    updateNavButtons() {
        document.getElementById('btn-back').disabled = this.historyIndex <= 0;
        document.getElementById('btn-forward').disabled = this.historyIndex >= this.history.length - 1;
        document.getElementById('btn-up').disabled = this.currentPath === '/';
    }

    // ==================== Selection ====================

    selectItem(item) {
        this.deselectAll();
        item.classList.add('selected');
        this.selectedItems.add(item.dataset.path);
        this.updateSelectionCount();
    }

    toggleSelection(item) {
        if (item.classList.contains('selected')) {
            item.classList.remove('selected');
            this.selectedItems.delete(item.dataset.path);
        } else {
            item.classList.add('selected');
            this.selectedItems.add(item.dataset.path);
        }
        this.updateSelectionCount();
    }

    deselectAll() {
        document.querySelectorAll('.file-item.selected').forEach(item => {
            item.classList.remove('selected');
        });
        this.selectedItems.clear();
        this.updateSelectionCount();
    }

    updateSelectionCount() {
        if (this.selectedItems.size > 0) {
            this.selectedCount.textContent = `${this.selectedItems.size} selecionado(s)`;
        } else {
            this.selectedCount.textContent = '';
        }
    }

    // ==================== File Operations ====================

    async createFolder() {
        const name = prompt('Nome da nova pasta:', 'Nova Pasta');
        if (!name) return;

        try {
            const path = `${this.currentPath}/${name}`;
            await Aegis.mkdir({ path });
            await this.loadFiles(this.currentPath);
        } catch (err) {
            await Aegis.dialog.message({
                type: 'error',
                title: 'Erro',
                message: `Não foi possível criar a pasta: ${err.message}`
            });
        }
    }

    async createFile() {
        const name = prompt('Nome do novo arquivo:', 'Novo Arquivo.txt');
        if (!name) return;

        try {
            await Aegis.write({
                path: this.currentPath,
                file: name,
                content: ''
            });
            await this.loadFiles(this.currentPath);
        } catch (err) {
            await Aegis.dialog.message({
                type: 'error',
                title: 'Erro',
                message: `Não foi possível criar o arquivo: ${err.message}`
            });
        }
    }

    copy() {
        this.clipboard = {
            items: [...this.selectedItems],
            cut: false
        };
        console.log('Copied:', this.clipboard.items);
    }

    cut() {
        this.clipboard = {
            items: [...this.selectedItems],
            cut: true
        };
        console.log('Cut:', this.clipboard.items);
    }

    async paste() {
        if (this.clipboard.items.length === 0) return;

        try {
            for (const src of this.clipboard.items) {
                const name = src.split('/').pop();
                const dest = `${this.currentPath}/${name}`;

                if (this.clipboard.cut) {
                    await Aegis.move({ src, dest });
                } else {
                    await Aegis.copy({ src, dest });
                }
            }

            if (this.clipboard.cut) {
                this.clipboard = { items: [], cut: false };
            }

            await this.loadFiles(this.currentPath);
        } catch (err) {
            await Aegis.dialog.message({
                type: 'error',
                title: 'Erro',
                message: `Erro ao colar: ${err.message}`
            });
        }
    }

    async delete() {
        if (this.selectedItems.size === 0) return;

        const confirm = await Aegis.dialog.message({
            type: 'question',
            title: 'Confirmar Exclusão',
            message: `Deseja excluir ${this.selectedItems.size} item(s)?`,
            buttons: 'yesno'
        });

        if (!confirm.response) return;

        try {
            for (const path of this.selectedItems) {
                await Aegis.remove({ path, recursive: true });
            }
            await this.loadFiles(this.currentPath);
        } catch (err) {
            await Aegis.dialog.message({
                type: 'error',
                title: 'Erro',
                message: `Erro ao excluir: ${err.message}`
            });
        }
    }

    async rename() {
        if (this.selectedItems.size !== 1) return;

        const oldPath = [...this.selectedItems][0];
        const oldName = oldPath.split('/').pop();
        const newName = prompt('Novo nome:', oldName);

        if (!newName || newName === oldName) return;

        try {
            const newPath = oldPath.replace(oldName, newName);
            await Aegis.move({ src: oldPath, dest: newPath });
            await this.loadFiles(this.currentPath);
        } catch (err) {
            await Aegis.dialog.message({
                type: 'error',
                title: 'Erro',
                message: `Erro ao renomear: ${err.message}`
            });
        }
    }

    async showProperties() {
        if (this.selectedItems.size !== 1) return;

        const path = [...this.selectedItems][0];
        const item = document.querySelector(`.file-item[data-path="${path}"]`);

        if (!item) return;

        document.getElementById('prop-icon').textContent = item.querySelector('.file-icon').textContent;
        document.getElementById('prop-name').textContent = item.dataset.name;
        document.getElementById('prop-type').textContent = item.dataset.isDirectory === 'true' ? 'Pasta' : this.getFileType(item.dataset.name);
        document.getElementById('prop-location').textContent = this.currentPath;
        document.getElementById('prop-size').textContent = item.dataset.isDirectory === 'true' ? '-' : this.formatSize(parseInt(item.dataset.size));
        document.getElementById('prop-modified').textContent = item.dataset.modified ? this.formatDate(parseFloat(item.dataset.modified)) : '-';

        this.propertiesModal.classList.add('visible');
    }

    hideProperties() {
        this.propertiesModal.classList.remove('visible');
    }

    // ==================== View ====================

    setGridView() {
        this.isListView = false;
        this.fileGrid.classList.remove('list-view');
        document.getElementById('btn-grid-view').classList.add('active');
        document.getElementById('btn-list-view').classList.remove('active');
        this.loadFiles(this.currentPath);
    }

    setListView() {
        this.isListView = true;
        this.fileGrid.classList.add('list-view');
        document.getElementById('btn-list-view').classList.add('active');
        document.getElementById('btn-grid-view').classList.remove('active');
        this.loadFiles(this.currentPath);
    }

    filterFiles() {
        const query = this.searchInput.value.toLowerCase();
        document.querySelectorAll('.file-item').forEach(item => {
            const name = item.dataset.name.toLowerCase();
            item.style.display = name.includes(query) ? '' : 'none';
        });
    }

    // ==================== Context Menu ====================

    showContextMenu(e) {
        e.preventDefault();

        // If right-clicked on a file, select it
        const fileItem = e.target.closest('.file-item');
        if (fileItem && !fileItem.classList.contains('selected')) {
            this.selectItem(fileItem);
        }

        this.contextMenu.style.left = `${e.clientX}px`;
        this.contextMenu.style.top = `${e.clientY}px`;
        this.contextMenu.classList.add('visible');
    }

    hideContextMenu() {
        this.contextMenu.classList.remove('visible');
    }

    handleContextAction(action) {
        switch (action) {
            case 'open':
                if (this.selectedItems.size === 1) {
                    this.navigateTo([...this.selectedItems][0]);
                }
                break;
            case 'copy': this.copy(); break;
            case 'cut': this.cut(); break;
            case 'paste': this.paste(); break;
            case 'delete': this.delete(); break;
            case 'rename': this.rename(); break;
            case 'properties': this.showProperties(); break;
        }
    }

    // ==================== Keyboard ====================

    handleKeyboard(e) {
        if (e.target.tagName === 'INPUT') return;

        switch (e.key) {
            case 'Delete':
                this.delete();
                break;
            case 'F2':
                this.rename();
                break;
            case 'F5':
                this.loadFiles(this.currentPath);
                break;
            case 'Escape':
                this.deselectAll();
                break;
            case 'a':
                if (e.ctrlKey) {
                    e.preventDefault();
                    document.querySelectorAll('.file-item').forEach(item => {
                        item.classList.add('selected');
                        this.selectedItems.add(item.dataset.path);
                    });
                    this.updateSelectionCount();
                }
                break;
            case 'c':
                if (e.ctrlKey) this.copy();
                break;
            case 'x':
                if (e.ctrlKey) this.cut();
                break;
            case 'v':
                if (e.ctrlKey) this.paste();
                break;
            case 'Backspace':
                this.goUp();
                break;
        }
    }

    // ==================== Utilities ====================

    showError(message) {
        this.fileGrid.innerHTML = `
            <div class="empty-state">
                <span class="empty-state-icon">❌</span>
                <span class="empty-state-text">${message}</span>
            </div>
        `;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.fileManager = new FileManager();
});
