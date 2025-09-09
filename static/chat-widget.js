/**
 * 悬浮聊天窗口组件
 * 提供智能问答功能的悬浮窗口界面
 */

class ChatWidget {
    constructor() {
        this.isOpen = false;
        this.conversationHistory = [];
        this.currentResults = [];
        this.isTyping = false;
        
        this.init();
    }
    
    init() {
        this.createWidget();
        this.bindEvents();
        this.loadWelcomeMessage();
    }
    
    createWidget() {
        // 创建聊天按钮
        const button = document.createElement('button');
        button.className = 'chat-widget-button';
        button.innerHTML = '<i class="fas fa-robot"></i>';
        button.id = 'chatWidgetButton';
        
        // 创建聊天窗口
        const container = document.createElement('div');
        container.className = 'chat-widget-container';
        container.id = 'chatWidgetContainer';
        container.innerHTML = this.getWidgetHTML();
        
        // 添加到页面
        document.body.appendChild(button);
        document.body.appendChild(container);
        
        // 存储引用
        this.button = button;
        this.container = container;
        this.messagesContainer = container.querySelector('.chat-widget-messages');
        this.inputField = container.querySelector('.chat-widget-input-field');
        this.sendButton = container.querySelector('.chat-widget-send-btn');
        this.kbPanel = container.querySelector('.chat-widget-kb-panel');
    }
    
    getWidgetHTML() {
        return `
            <!-- 聊天头部 -->
            <div class="chat-widget-header">
                <div class="chat-widget-title">
                    <i class="fas fa-robot"></i>
                    AI智能问答
                </div>
                <div class="chat-widget-controls">
                    <button class="chat-widget-control-btn" id="chatWidgetKbToggle" title="知识库设置">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button class="chat-widget-control-btn" id="chatWidgetClear" title="清空对话">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button class="chat-widget-control-btn" id="chatWidgetClose" title="关闭">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            
            <!-- 知识库设置面板 -->
            <div class="chat-widget-kb-panel">
                <div class="chat-widget-kb-title">选择知识库字段</div>
                <div class="chat-widget-kb-options">
                    <label class="chat-widget-kb-option">
                        <input type="checkbox" value="title" checked>
                        标题
                    </label>
                    <label class="chat-widget-kb-option">
                        <input type="checkbox" value="content" checked>
                        内容
                    </label>
                    <label class="chat-widget-kb-option">
                        <input type="checkbox" value="summary" checked>
                        摘要
                    </label>
                    <label class="chat-widget-kb-option">
                        <input type="checkbox" value="sentiment_level" checked>
                        情感等级
                    </label>
                    <label class="chat-widget-kb-option">
                        <input type="checkbox" value="companies" checked>
                        相关企业
                    </label>
                    <label class="chat-widget-kb-option">
                        <input type="checkbox" value="publish_time" checked>
                        发布时间
                    </label>
                </div>
            </div>
            
            <!-- 消息区域 -->
            <div class="chat-widget-messages"></div>
            
            <!-- 输入区域 -->
            <div class="chat-widget-input">
                <div class="chat-widget-input-wrapper">
                    <textarea class="chat-widget-input-field" placeholder="输入您的问题..." rows="1"></textarea>
                    <button class="chat-widget-send-btn">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
                <div class="chat-widget-tips">
                    💡 按 Enter 发送消息，Shift+Enter 换行
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // 聊天按钮点击
        this.button.addEventListener('click', () => {
            this.toggle();
        });
        
        // 关闭按钮
        const closeBtn = this.container.querySelector('#chatWidgetClose');
        closeBtn.addEventListener('click', () => {
            this.close();
        });
        
        // 清空对话
        const clearBtn = this.container.querySelector('#chatWidgetClear');
        clearBtn.addEventListener('click', () => {
            this.clearChat();
        });
        
        // 知识库设置切换
        const kbToggleBtn = this.container.querySelector('#chatWidgetKbToggle');
        kbToggleBtn.addEventListener('click', () => {
            this.toggleKnowledgeBase();
        });
        
        // 发送消息
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // 输入框事件
        this.inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // 自动调整输入框高度
        this.inputField.addEventListener('input', () => {
            this.autoResizeInput();
        });
        
        // 点击外部关闭
        document.addEventListener('click', (e) => {
            if (this.isOpen && 
                !this.container.contains(e.target) && 
                !this.button.contains(e.target)) {
                this.close();
            }
        });
    }
    
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
    
    open() {
        this.isOpen = true;
        this.container.classList.add('show');
        this.button.classList.add('active');
        this.inputField.focus();
        
        // 更新搜索结果
        this.updateSearchResults();
    }
    
    close() {
        this.isOpen = false;
        this.container.classList.remove('show');
        this.button.classList.remove('active');
        this.kbPanel.classList.remove('show');
    }
    
    toggleKnowledgeBase() {
        this.kbPanel.classList.toggle('show');
    }
    
    loadWelcomeMessage() {
        const welcomeHTML = `
            <div class="chat-widget-welcome">
                <div class="chat-widget-welcome-title">👋 欢迎使用AI智能问答</div>
                <div class="chat-widget-welcome-text">
                    我是您的专属AI助手，可以基于搜索结果为您提供智能问答服务。<br><br>
                    <strong>使用提示：</strong><br>
                    • 先在主页面搜索数据<br>
                    • 我会基于搜索结果回答问题<br>
                    • 可在设置中选择分析字段<br>
                    • 支持连续对话
                </div>
            </div>
        `;
        this.messagesContainer.innerHTML = welcomeHTML;
    }
    
    async sendMessage() {
        const message = this.inputField.value.trim();
        if (!message || this.isTyping) return;
        
        // 添加用户消息
        this.addMessage('user', message);
        
        // 清空输入框
        this.inputField.value = '';
        this.autoResizeInput();
        
        // 显示AI正在输入
        this.showTyping();
        
        try {
            // 获取知识库字段
            const knowledgeBaseFields = this.getSelectedKnowledgeBaseFields();
            
            // 发送请求
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    search_results: this.currentResults,
                    knowledge_base_fields: knowledgeBaseFields,
                    conversation_history: this.conversationHistory
                })
            });
            
            const result = await response.json();
            
            // 隐藏输入状态
            this.hideTyping();
            
            if (result.success) {
                this.addMessage('ai', result.response);
                
                // 更新对话历史
                this.conversationHistory.push(
                    { role: 'user', content: message },
                    { role: 'assistant', content: result.response }
                );
                
                // 限制对话历史长度
                if (this.conversationHistory.length > 20) {
                    this.conversationHistory = this.conversationHistory.slice(-20);
                }
            } else {
                this.addMessage('ai', `抱歉，出现了错误：${result.error}`);
            }
            
        } catch (error) {
            this.hideTyping();
            this.addMessage('ai', `抱歉，网络连接出现问题：${error.message}`);
        }
    }
    
    addMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-widget-message ${sender}`;
        
        const now = new Date();
        const timeStr = now.toLocaleTimeString('zh-CN', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.innerHTML = `
            <div class="chat-widget-message-avatar">
                <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="chat-widget-message-content">
                <div class="chat-widget-message-bubble">${this.formatMessage(text)}</div>
                <div class="chat-widget-message-time">${timeStr}</div>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        return messageDiv;
    }
    
    formatMessage(text) {
        // 简单的文本格式化
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }
    
    showTyping() {
        this.isTyping = true;
        this.sendButton.disabled = true;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-widget-message ai';
        typingDiv.id = 'chatWidgetTyping';
        typingDiv.innerHTML = `
            <div class="chat-widget-message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="chat-widget-message-content">
                <div class="chat-widget-message-bubble">
                    <div class="chat-widget-typing">
                        正在思考中
                        <div class="chat-widget-typing-dots">
                            <div class="chat-widget-typing-dot"></div>
                            <div class="chat-widget-typing-dot"></div>
                            <div class="chat-widget-typing-dot"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTyping() {
        this.isTyping = false;
        this.sendButton.disabled = false;
        
        const typingDiv = document.getElementById('chatWidgetTyping');
        if (typingDiv) {
            typingDiv.remove();
        }
    }
    
    clearChat() {
        this.conversationHistory = [];
        this.loadWelcomeMessage();
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    autoResizeInput() {
        this.inputField.style.height = 'auto';
        this.inputField.style.height = Math.min(this.inputField.scrollHeight, 80) + 'px';
    }
    
    getSelectedKnowledgeBaseFields() {
        const checkboxes = this.kbPanel.querySelectorAll('input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }
    
    updateSearchResults() {
        // 尝试从全局变量获取当前搜索结果
        if (window.currentResults) {
            this.currentResults = window.currentResults;
        } else {
            this.currentResults = [];
        }
        
        // 如果有新的搜索结果，显示提示
        if (this.currentResults.length > 0 && this.isOpen) {
            const infoMessage = `搜索结果已更新，共找到 ${this.currentResults.length} 条结果。\n现在您可以基于这些数据向我提问了！`;
            this.addMessage('ai', infoMessage);
        }
    }
    
    // 公共方法：外部调用更新搜索结果
    setSearchResults(results) {
        this.currentResults = results || [];
        
        if (this.isOpen && results && results.length > 0) {
            const infoMessage = `✅ 搜索结果已更新，共找到 ${results.length} 条结果。\n现在您可以基于这些数据向我提问了！`;
            this.addMessage('ai', infoMessage);
        }
    }
}

// 全局聊天窗口实例
let chatWidget = null;

// 初始化聊天窗口
document.addEventListener('DOMContentLoaded', () => {
    chatWidget = new ChatWidget();
    
    // 将实例暴露到全局，方便其他脚本调用
    window.chatWidget = chatWidget;
});

// 监听搜索结果更新
document.addEventListener('searchResultsUpdated', (event) => {
    if (chatWidget) {
        chatWidget.setSearchResults(event.detail.results);
    }
});

// 兼容原有的函数名
window.updateChatSearchResults = function(results) {
    if (chatWidget) {
        chatWidget.setSearchResults(results);
    }
}; 