class FinSightChat {
    constructor() {
        this.messages = [];
        this.currentChatId = null;
        this.chatHistory = this.loadChatHistory();
        this.isTyping = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadWelcomeScreen();
        this.updateChatHistory();
    }
    
    initializeElements() {
        // Main elements
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.welcomeScreen = document.getElementById('welcomeScreen');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.chatTitle = document.getElementById('chatTitle');
        
        // Sidebar elements
        this.sidebar = document.getElementById('sidebar');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.chatHistoryList = document.getElementById('chatHistoryList');
        this.toggleSidebarBtn = document.getElementById('toggleSidebar');
        
        // Action buttons
        this.clearChatBtn = document.getElementById('clearChatBtn');
        this.exportChatBtn = document.getElementById('exportChatBtn');
        this.settingsBtn = document.getElementById('settingsBtn');
    }
    
    bindEvents() {
        // Send message events
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.autoResizeTextarea());
        
        // Example queries
        document.querySelectorAll('.example-query').forEach(query => {
            query.addEventListener('click', () => {
                const queryText = query.dataset.query;
                this.messageInput.value = queryText;
                this.sendMessage();
            });
        });
        
        // Sidebar and navigation
        this.newChatBtn.addEventListener('click', () => this.startNewChat());
        this.toggleSidebarBtn.addEventListener('click', () => this.toggleSidebar());
        this.clearChatBtn.addEventListener('click', () => this.clearCurrentChat());
        this.exportChatBtn.addEventListener('click', () => this.exportChat());
        
        // Responsive design
        this.handleResponsiveDesign();
    }
    
    autoResizeTextarea() {
        const textarea = this.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
    
    handleResponsiveDesign() {
        const checkWidth = () => {
            if (window.innerWidth <= 768) {
                this.toggleSidebarBtn.style.display = 'block';
            } else {
                this.toggleSidebarBtn.style.display = 'none';
                this.sidebar.classList.remove('open');
            }
        };
        
        checkWidth();
        window.addEventListener('resize', checkWidth);
    }
    
    toggleSidebar() {
        this.sidebar.classList.toggle('open');
    }
    
    loadWelcomeScreen() {
        this.welcomeScreen.style.display = 'flex';
    }
    
    hideWelcomeScreen() {
        this.welcomeScreen.style.display = 'none';
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isTyping) return;
        
        // Hide welcome screen on first message
        this.hideWelcomeScreen();
        
        // Add user message
        this.addMessage('user', message);
        this.messageInput.value = '';
        this.autoResizeTextarea();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send to AI chat endpoint
            const response = await this.callChatAPI(message);
            this.hideTypingIndicator();
            
            // Add AI response
            this.addMessage('assistant', response.response, response.data);
            
            // Save to chat history
            this.saveChatToHistory();
            
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('assistant', 'I apologize, but I encountered an error processing your request. Please try again.', null, true);
            console.error('Chat API error:', error);
        }
    }
    
    async callChatAPI(message) {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                chat_id: this.currentChatId,
                context: this.getRecentContext()
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    getRecentContext() {
        // Return last 5 messages for context
        return this.messages.slice(-5).map(msg => ({
            role: msg.type,
            content: msg.text
        }));
    }
    
    addMessage(type, text, data = null, isError = false) {
        const message = {
            id: Date.now(),
            type,
            text,
            data,
            timestamp: new Date(),
            isError
        };
        
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }
    
    renderMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.type}`;
        messageDiv.dataset.messageId = message.id;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = message.type === 'user' ? 
            '<i class="fas fa-user"></i>' : 
            '<i class="fas fa-robot"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        
        if (message.isError) {
            messageText.style.color = 'var(--error-500)';
        }
        
        // Format message text (support for markdown-like formatting)
        messageText.innerHTML = this.formatMessageText(message.text);
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = this.formatTime(message.timestamp);
        
        content.appendChild(messageText);
        
        // Add data visualization if present
        if (message.data) {
            const dataViz = this.createDataVisualization(message.data);
            if (dataViz) {
                content.appendChild(dataViz);
            }
        }
        
        content.appendChild(messageTime);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        this.messagesContainer.appendChild(messageDiv);
    }
    
    formatMessageText(text) {
        // Basic markdown-like formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code style="background: var(--gray-100); padding: 0.125rem 0.25rem; border-radius: 0.25rem; font-family: monospace;">$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    createDataVisualization(data) {
        if (!data || typeof data !== 'object') return null;
        
        const dataCard = document.createElement('div');
        dataCard.className = 'data-card';
        
        // Handle different data types
        if (data.stock_data) {
            return this.createStockDataCard(data.stock_data);
        } else if (data.portfolio_data) {
            return this.createPortfolioDataCard(data.portfolio_data);
        } else if (data.economic_data) {
            return this.createEconomicDataCard(data.economic_data);
        } else if (data.metrics) {
            return this.createMetricsCard(data.metrics);
        }
        
        return null;
    }
    
    createStockDataCard(stockData) {
        const card = document.createElement('div');
        card.className = 'data-card';
        
        const header = document.createElement('div');
        header.className = 'data-card-header';
        header.innerHTML = `
            <i class="fas fa-chart-line"></i>
            <span class="data-card-title">${stockData.symbol || 'Stock Data'}</span>
        `;
        
        const metrics = document.createElement('div');
        
        if (stockData.price) {
            metrics.appendChild(this.createMetricRow('Current Price', `$${stockData.price}`));
        }
        if (stockData.change) {
            const changeClass = stockData.change >= 0 ? 'positive' : 'negative';
            metrics.appendChild(this.createMetricRow('Change', stockData.change, changeClass));
        }
        if (stockData.volume) {
            metrics.appendChild(this.createMetricRow('Volume', stockData.volume.toLocaleString()));
        }
        
        card.appendChild(header);
        card.appendChild(metrics);
        return card;
    }
    
    createPortfolioDataCard(portfolioData) {
        const card = document.createElement('div');
        card.className = 'data-card';
        
        const header = document.createElement('div');
        header.className = 'data-card-header';
        header.innerHTML = `
            <i class="fas fa-briefcase"></i>
            <span class="data-card-title">Portfolio Performance</span>
        `;
        
        const metrics = document.createElement('div');
        
        if (portfolioData.ytd_return) {
            const returnClass = portfolioData.ytd_return >= 0 ? 'positive' : 'negative';
            metrics.appendChild(this.createMetricRow('YTD Return', `${portfolioData.ytd_return}%`, returnClass));
        }
        if (portfolioData.benchmark_return) {
            const benchmarkClass = portfolioData.benchmark_return >= 0 ? 'positive' : 'negative';
            metrics.appendChild(this.createMetricRow('S&P 500 YTD', `${portfolioData.benchmark_return}%`, benchmarkClass));
        }
        if (portfolioData.total_value) {
            metrics.appendChild(this.createMetricRow('Total Value', `$${portfolioData.total_value.toLocaleString()}`));
        }
        
        card.appendChild(header);
        card.appendChild(metrics);
        return card;
    }
    
    createEconomicDataCard(economicData) {
        const card = document.createElement('div');
        card.className = 'data-card';
        
        const header = document.createElement('div');
        header.className = 'data-card-header';
        header.innerHTML = `
            <i class="fas fa-globe-americas"></i>
            <span class="data-card-title">Economic Indicators</span>
        `;
        
        const metrics = document.createElement('div');
        
        if (economicData.inflation_rate) {
            metrics.appendChild(this.createMetricRow('Inflation Rate', `${economicData.inflation_rate}%`));
        }
        if (economicData.gdp_growth) {
            const gdpClass = economicData.gdp_growth >= 0 ? 'positive' : 'negative';
            metrics.appendChild(this.createMetricRow('GDP Growth', `${economicData.gdp_growth}%`, gdpClass));
        }
        if (economicData.unemployment_rate) {
            metrics.appendChild(this.createMetricRow('Unemployment', `${economicData.unemployment_rate}%`));
        }
        
        card.appendChild(header);
        card.appendChild(metrics);
        return card;
    }
    
    createMetricsCard(metrics) {
        const card = document.createElement('div');
        card.className = 'data-card';
        
        const header = document.createElement('div');
        header.className = 'data-card-header';
        header.innerHTML = `
            <i class="fas fa-chart-bar"></i>
            <span class="data-card-title">Key Metrics</span>
        `;
        
        const metricsContainer = document.createElement('div');
        
        Object.entries(metrics).forEach(([key, value]) => {
            const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            metricsContainer.appendChild(this.createMetricRow(label, value));
        });
        
        card.appendChild(header);
        card.appendChild(metricsContainer);
        return card;
    }
    
    createMetricRow(label, value, className = '') {
        const row = document.createElement('div');
        row.className = 'data-metric';
        
        const labelSpan = document.createElement('span');
        labelSpan.className = 'metric-label';
        labelSpan.textContent = label;
        
        const valueSpan = document.createElement('span');
        valueSpan.className = `metric-value ${className}`;
        valueSpan.textContent = value;
        
        row.appendChild(labelSpan);
        row.appendChild(valueSpan);
        
        return row;
    }
    
    formatTime(timestamp) {
        return timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    showTypingIndicator() {
        this.isTyping = true;
        this.typingIndicator.classList.add('active');
        this.sendBtn.disabled = true;
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.isTyping = false;
        this.typingIndicator.classList.remove('active');
        this.sendBtn.disabled = false;
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }
    
    startNewChat() {
        this.messages = [];
        this.currentChatId = null;
        this.messagesContainer.innerHTML = '';
        this.loadWelcomeScreen();
        this.chatTitle.textContent = 'Financial AI Assistant';
        
        // Clear active chat in history
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
    }
    
    clearCurrentChat() {
        if (confirm('Are you sure you want to clear this conversation?')) {
            this.startNewChat();
        }
    }
    
    exportChat() {
        if (this.messages.length === 0) {
            alert('No messages to export');
            return;
        }
        
        const chatData = {
            title: this.chatTitle.textContent,
            timestamp: new Date().toISOString(),
            messages: this.messages.map(msg => ({
                type: msg.type,
                text: msg.text,
                timestamp: msg.timestamp.toISOString()
            }))
        };
        
        const blob = new Blob([JSON.stringify(chatData, null, 2)], { 
            type: 'application/json' 
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `finsight-chat-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    saveChatToHistory() {
        if (this.messages.length === 0) return;
        
        const chatId = this.currentChatId || Date.now().toString();
        this.currentChatId = chatId;
        
        const firstUserMessage = this.messages.find(msg => msg.type === 'user');
        const title = firstUserMessage ? 
            firstUserMessage.text.substring(0, 50) + (firstUserMessage.text.length > 50 ? '...' : '') :
            'New Conversation';
        
        const chatData = {
            id: chatId,
            title,
            messages: this.messages,
            lastUpdated: new Date(),
            preview: this.messages[this.messages.length - 1]?.text.substring(0, 100) || ''
        };
        
        this.chatHistory[chatId] = chatData;
        localStorage.setItem('finsight_chat_history', JSON.stringify(this.chatHistory));
        this.updateChatHistory();
        this.chatTitle.textContent = title;
    }
    
    loadChatHistory() {
        try {
            const stored = localStorage.getItem('finsight_chat_history');
            return stored ? JSON.parse(stored) : {};
        } catch (error) {
            console.error('Error loading chat history:', error);
            return {};
        }
    }
    
    updateChatHistory() {
        this.chatHistoryList.innerHTML = '';
        
        const sortedChats = Object.values(this.chatHistory)
            .sort((a, b) => new Date(b.lastUpdated) - new Date(a.lastUpdated));
        
        if (sortedChats.length === 0) {
            this.chatHistoryList.innerHTML = '<p style="color: var(--gray-500); font-size: 0.875rem; text-align: center; padding: 1rem;">No conversations yet</p>';
            return;
        }
        
        sortedChats.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item';
            if (chat.id === this.currentChatId) {
                chatItem.classList.add('active');
            }
            
            chatItem.innerHTML = `
                <div class="chat-item-title">${chat.title}</div>
                <div class="chat-item-preview">${chat.preview}</div>
                <div class="chat-item-time">${this.formatChatTime(chat.lastUpdated)}</div>
            `;
            
            chatItem.addEventListener('click', () => this.loadChat(chat.id));
            this.chatHistoryList.appendChild(chatItem);
        });
    }
    
    formatChatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffHours = diffMs / (1000 * 60 * 60);
        const diffDays = diffMs / (1000 * 60 * 60 * 24);
        
        if (diffHours < 1) {
            return 'Just now';
        } else if (diffHours < 24) {
            return `${Math.floor(diffHours)}h ago`;
        } else if (diffDays < 7) {
            return `${Math.floor(diffDays)}d ago`;
        } else {
            return date.toLocaleDateString();
        }
    }
    
    loadChat(chatId) {
        const chat = this.chatHistory[chatId];
        if (!chat) return;
        
        this.currentChatId = chatId;
        this.messages = chat.messages.map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
        }));
        
        this.hideWelcomeScreen();
        this.messagesContainer.innerHTML = '';
        
        this.messages.forEach(message => {
            this.renderMessage(message);
        });
        
        this.chatTitle.textContent = chat.title;
        this.scrollToBottom();
        
        // Update active state in history
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-chat-id="${chatId}"]`)?.classList.add('active');
        
        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            this.sidebar.classList.remove('open');
        }
    }
}

// Initialize the chat application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.finSightChat = new FinSightChat();
});

// Handle page visibility for better UX
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.finSightChat) {
        // Refresh status when page becomes visible
        // Could add status check here
    }
}); 