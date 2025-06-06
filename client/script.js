class ChatClient {
    constructor() {
        this.apiUrl = 'http://localhost:5000';
        this.maxMessages = 50;
        this.chatMessages = [];
        this.initialize();
    }

    initialize() {
        this.setupElements();
        this.setupEventListeners();
        this.loadSettings();
        this.loadChatHistory();
        this.checkServerStatus();
        this.setWelcomeTime();
    }

    setupElements() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.messageForm = document.getElementById('messageForm');
        this.chatMessages = document.getElementById('chatMessages');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.charCounter = document.getElementById('charCounter');
        
        // Settings elements
        this.settingsBtn = document.getElementById('settingsBtn');
        this.settingsModal = document.getElementById('settingsModal');
        this.closeSettings = document.getElementById('closeSettings');
        this.saveSettings = document.getElementById('saveSettings');
        this.clearHistory = document.getElementById('clearHistory');
        this.apiUrlInput = document.getElementById('apiUrl');
        this.maxMessagesInput = document.getElementById('maxMessages');
    }

    setupEventListeners() {
        // Message form
        this.messageForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.messageInput.addEventListener('input', () => this.handleInputChange());
        this.messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));

        // Settings
        this.settingsBtn.addEventListener('click', () => this.openSettings());
        this.closeSettings.addEventListener('click', () => this.closeSettingsModal());
        this.saveSettings.addEventListener('click', () => this.saveSettingsData());
        this.clearHistory.addEventListener('click', () => this.clearChatHistory());

        // Modal close on background click
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) {
                this.closeSettingsModal();
            }
        });

        // Close modals with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeSettingsModal();
                this.closeSourcesModal();
            }
        });
    }

    setWelcomeTime() {
        const welcomeTime = document.getElementById('welcomeTime');
        if (welcomeTime) {
            welcomeTime.textContent = new Date().toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
    }

    handleInputChange() {
        const length = this.messageInput.value.length;
        this.charCounter.textContent = `${length}/1000`;
        this.sendButton.disabled = length === 0;
        
        // Auto-resize textarea
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!this.sendButton.disabled) {
                this.handleSubmit(e);
            }
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Add user message to UI
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.handleInputChange();
        
        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await this.sendMessage(message);
            this.hideTypingIndicator();
            
            if (response.answer) {
                this.addMessage(response.answer, 'bot', response.sources);
            } else {
                throw new Error('Empty response from server');
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addErrorMessage('Failed to get response. Please try again.', message);
            console.error('Error:', error);
        }
    }

    async sendMessage(message) {
        const response = await fetch(`${this.apiUrl}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    addMessage(content, sender, sources = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'user' ? '👤' : '🤖';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = content;

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        messageContent.appendChild(messageText);
        messageContent.appendChild(messageTime);

        // Add sources icon if sources exist
        if (sources && sources.length > 0) {
            const sourcesIcon = this.createSourcesIcon(sources);
            messageContent.appendChild(sourcesIcon);
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // Save to history
        this.saveChatMessage({ content, sender, sources, timestamp: Date.now() });
    }

    createSourcesIcon(sources) {
        const sourcesIcon = document.createElement('button');
        sourcesIcon.className = 'sources-icon';
        sourcesIcon.innerHTML = '📄';
        sourcesIcon.title = `View ${sources.length} source${sources.length > 1 ? 's' : ''}`;

        // Add count badge
        if (sources.length > 1) {
            const countBadge = document.createElement('span');
            countBadge.className = 'sources-count';
            countBadge.textContent = sources.length;
            sourcesIcon.appendChild(countBadge);
        }

        sourcesIcon.addEventListener('click', () => this.showSourcesModal(sources));
        
        return sourcesIcon;
    }

    showSourcesModal(sources) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('sourcesModal');
        if (!modal) {
            modal = this.createSourcesModal();
            document.body.appendChild(modal);
        }

        // Populate modal with sources
        const modalBody = modal.querySelector('.sources-modal-body');
        modalBody.innerHTML = '';

        sources.forEach((source, index) => {
            const sourceItem = document.createElement('div');
            sourceItem.className = 'source-item';

            const sourceTitle = document.createElement('div');
            sourceTitle.className = 'source-title';
            sourceTitle.textContent = source.title || `Source ${index + 1}`;

            const sourceSnippet = document.createElement('div');
            sourceSnippet.className = 'source-snippet';
            sourceSnippet.textContent = source.snippet || source.content || 'No preview available';

            sourceItem.appendChild(sourceTitle);
            sourceItem.appendChild(sourceSnippet);

            if (source.url) {
                const sourceUrl = document.createElement('a');
                sourceUrl.className = 'source-url';
                sourceUrl.href = source.url;
                sourceUrl.target = '_blank';
                sourceUrl.textContent = source.url;
                sourceItem.appendChild(sourceUrl);
            }

            if (source.metadata) {
                const sourceMeta = document.createElement('div');
                sourceMeta.className = 'source-meta';
                sourceMeta.textContent = `Type: ${source.metadata.type || 'Unknown'} | Score: ${(source.score || 0).toFixed(3)}`;
                sourceItem.appendChild(sourceMeta);
            }

            modalBody.appendChild(sourceItem);
        });

        modal.classList.add('show');
    }

    createSourcesModal() {
        const modal = document.createElement('div');
        modal.id = 'sourcesModal';
        modal.className = 'sources-modal';

        modal.innerHTML = `
            <div class="sources-modal-content">
                <div class="sources-modal-header">
                    <h3>📄 Sources</h3>
                    <button class="close-btn" onclick="chatClient.closeSourcesModal()">&times;</button>
                </div>
                <div class="sources-modal-body">
                    <!-- Sources will be populated here -->
                </div>
            </div>
        `;

        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeSourcesModal();
            }
        });

        return modal;
    }

    closeSourcesModal() {
        const modal = document.getElementById('sourcesModal');
        if (modal) {
            modal.classList.remove('show');
        }
    }

    addErrorMessage(errorText, originalMessage) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message error-message';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '⚠️';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = errorText;

        const retryBtn = document.createElement('button');
        retryBtn.className = 'retry-btn';
        retryBtn.textContent = 'Retry';
        retryBtn.onclick = () => {
            messageDiv.remove();
            this.messageInput.value = originalMessage;
            this.handleInputChange();
        };

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        messageText.appendChild(retryBtn);
        messageContent.appendChild(messageText);
        messageContent.appendChild(messageTime);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        this.typingIndicator.classList.add('show');
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.classList.remove('show');
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    async checkServerStatus() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            if (response.ok) {
                this.setStatus('online', 'Connected');
            } else {
                this.setStatus('offline', 'Server Error');
            }
        } catch (error) {
            this.setStatus('offline', 'Disconnected');
        }
    }

    setStatus(status, text) {
        this.statusDot.className = `status-dot ${status}`;
        this.statusText.textContent = text;
    }

    // Settings Management
    openSettings() {
        this.apiUrlInput.value = this.apiUrl;
        this.maxMessagesInput.value = this.maxMessages;
        this.settingsModal.classList.add('show');
    }

    closeSettingsModal() {
        this.settingsModal.classList.remove('show');
    }

    saveSettingsData() {
        this.apiUrl = this.apiUrlInput.value || 'http://localhost:5000';
        this.maxMessages = parseInt(this.maxMessagesInput.value) || 50;
        
        localStorage.setItem('chatSettings', JSON.stringify({
            apiUrl: this.apiUrl,
            maxMessages: this.maxMessages
        }));

        this.closeSettingsModal();
        this.checkServerStatus();
    }

    loadSettings() {
        const saved = localStorage.getItem('chatSettings');
        if (saved) {
            const settings = JSON.parse(saved);
            this.apiUrl = settings.apiUrl || 'http://localhost:5000';
            this.maxMessages = settings.maxMessages || 50;
        }
    }

    // Chat History Management
    saveChatMessage(message) {
        let history = JSON.parse(localStorage.getItem('chatHistory') || '[]');
        history.push(message);
        
        // Keep only the last maxMessages
        if (history.length > this.maxMessages) {
            history = history.slice(-this.maxMessages);
        }
        
        localStorage.setItem('chatHistory', JSON.stringify(history));
    }

    loadChatHistory() {
        const history = JSON.parse(localStorage.getItem('chatHistory') || '[]');
        history.forEach(msg => {
            if (msg.sender !== 'system') { // Skip system messages like welcome
                this.addMessage(msg.content, msg.sender, msg.sources);
            }
        });
    }

    clearChatHistory() {
        if (confirm('Are you sure you want to clear all chat history?')) {
            localStorage.removeItem('chatHistory');
            
            // Remove all messages except welcome message
            const messages = this.chatMessages.querySelectorAll('.message:not(.welcome-message)');
            messages.forEach(msg => msg.remove());
            
            this.closeSettingsModal();
        }
    }
}

// Initialize the chat client when the page loads
let chatClient;
document.addEventListener('DOMContentLoaded', () => {
    chatClient = new ChatClient();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.chatClient) {
        window.chatClient.checkServerStatus();
    }
}); 