/**
 * Convin Chat Widget
 * Embeddable chat widget for websites
 * Usage: <script src="path/to/chat_widget.js"></script>
 */

(function() {
    // Check if widget already exists
    if (window.ConvinChatWidget) return;

    // Configuration
    const CONFIG = {
        apiUrl: 'https://your-api-endpoint.com/chat',
        position: 'bottom-right',
        theme: 'light',
        customerId: 'guest-' + Math.random().toString(36).substr(2, 9)
    };

    // Create styles
    const styles = `
        .convin-widget-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 380px;
            height: 600px;
            border-radius: 16px;
            box-shadow: 0 5px 40px rgba(0, 0, 0, 0.16);
            background: white;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
            z-index: 9999;
            animation: convin-slideUp 0.3s ease-out;
        }

        @keyframes convin-slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .convin-widget-header {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
        }

        .convin-widget-header h3 {
            font-size: 1.1rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.5px;
        }

        .convin-widget-header p {
            font-size: 0.75rem;
            opacity: 0.9;
            margin: 4px 0 0 0;
        }

        .convin-close-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            cursor: pointer;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 1.2rem;
            transition: all 0.3s ease;
        }

        .convin-close-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .convin-widget-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            background: #f9fafb;
        }

        .convin-message {
            display: flex;
            gap: 8px;
            animation: convin-fadeIn 0.3s ease-out;
        }

        @keyframes convin-fadeIn {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .convin-message.user {
            justify-content: flex-end;
        }

        .convin-message-content {
            max-width: 75%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 0.9rem;
            line-height: 1.5;
            word-wrap: break-word;
        }

        .convin-message.user .convin-message-content {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .convin-message.assistant .convin-message-content {
            background: white;
            color: #374151;
            border: 1px solid #e5e7eb;
            border-bottom-left-radius: 4px;
        }

        .convin-welcome {
            text-align: center;
            padding: 24px 16px;
            color: #6b7280;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        }

        .convin-welcome-icon {
            font-size: 2.5rem;
            margin-bottom: 12px;
        }

        .convin-welcome h4 {
            font-size: 1rem;
            margin: 12px 0 6px 0;
            color: #374151;
        }

        .convin-welcome p {
            font-size: 0.85rem;
            color: #9ca3af;
            margin: 0;
        }

        .convin-widget-input {
            padding: 12px;
            background: white;
            border-top: 1px solid #e5e7eb;
            display: flex;
            gap: 8px;
        }

        .convin-widget-input input {
            flex: 1;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 0.9rem;
            font-family: 'Poppins', sans-serif;
            background: #f9fafb;
            transition: all 0.3s ease;
        }

        .convin-widget-input input:focus {
            outline: none;
            border-color: #3b82f6;
            background: white;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .convin-send-btn {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border: none;
            padding: 10px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .convin-send-btn:hover {
            transform: translateY(-2px);
        }

        .convin-widget-messages::-webkit-scrollbar {
            width: 6px;
        }

        .convin-widget-messages::-webkit-scrollbar-thumb {
            background: #d1d5db;
            border-radius: 3px;
        }

        @media (max-width: 480px) {
            .convin-widget-container {
                width: 100%;
                height: 100%;
                border-radius: 0;
                bottom: 0;
                right: 0;
            }
        }
    `;

    // Create widget HTML
    const widgetHTML = `
        <div class="convin-widget-container" id="convin-widget">
            <div class="convin-widget-header">
                <div>
                    <h3>💬 Convin Support</h3>
                    <p>We usually reply in minutes</p>
                </div>
                <button class="convin-close-btn" onclick="window.ConvinChatWidget.toggle()">✕</button>
            </div>
            <div class="convin-widget-messages" id="convin-messages">
                <div class="convin-welcome">
                    <div>
                        <div class="convin-welcome-icon">👋</div>
                        <h4>Welcome to Convin Support</h4>
                        <p>How can we help you today?</p>
                    </div>
                </div>
            </div>
            <div class="convin-widget-input">
                <input type="text" id="convin-input" placeholder="Type your message..." />
                <button class="convin-send-btn" onclick="window.ConvinChatWidget.send()">📤</button>
            </div>
        </div>
    `;

    // Initialize widget
    function init() {
        // Create style element
        const styleEl = document.createElement('style');
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);

        // Create widget container
        const container = document.createElement('div');
        container.innerHTML = widgetHTML;
        document.body.appendChild(container);

        // Setup event listeners
        const input = document.getElementById('convin-input');
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                window.ConvinChatWidget.send();
            }
        });

        console.log('✅ Convin Chat Widget Loaded');
    }

    // Widget API
    window.ConvinChatWidget = {
        toggle: function() {
            const widget = document.getElementById('convin-widget');
            widget.style.display = widget.style.display === 'none' ? 'flex' : 'none';
        },

        send: function() {
            const input = document.getElementById('convin-input');
            const message = input.value.trim();

            if (!message) return;

            this.addMessage(message, 'user');
            input.value = '';
            input.focus();

            // Simulate response
            setTimeout(() => {
                const responses = [
                    '👋 Thanks for reaching out! How can I help?',
                    '💡 Great question! Let me assist you.',
                    '📞 I\'m here to help. What do you need?',
                    '✨ How can I make your day better?'
                ];
                const response = responses[Math.floor(Math.random() * responses.length)];
                this.addMessage(response, 'assistant');
            }, 800);
        },

        addMessage: function(text, sender) {
            const container = document.getElementById('convin-messages');

            // Clear welcome message
            const welcome = container.querySelector('.convin-welcome');
            if (welcome && container.children.length === 1) {
                welcome.remove();
            }

            const msgEl = document.createElement('div');
            msgEl.className = `convin-message ${sender}`;
            msgEl.innerHTML = `<div class="convin-message-content">${this.escapeHtml(text)}</div>`;

            container.appendChild(msgEl);
            container.scrollTop = container.scrollHeight;
        },

        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        setCustomerId: function(id) {
            CONFIG.customerId = id;
        },

        setApiUrl: function(url) {
            CONFIG.apiUrl = url;
        }
    };

    // Load widget when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
