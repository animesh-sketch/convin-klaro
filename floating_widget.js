/**
 * Convin Floating Chat Widget
 * Embeddable draggable chat widget for websites
 * Usage: <script src="path/to/floating_widget.js"></script>
 */

(function() {
    if (window.ConvinFloatingWidget) return;

    // Widget HTML
    const widgetHTML = `
        <div class="convin-floating-container" id="convin-floating-container">
            <button class="convin-bubble" id="convin-bubble" title="Open chat">💬</button>
            <div class="convin-floating-widget" id="convin-floating-widget">
                <div class="convin-floating-header" id="convin-floating-header">
                    <div>
                        <h3>💬 Convin Support</h3>
                        <p>We usually reply in minutes <span class="convin-badge">LIVE</span></p>
                    </div>
                    <div class="convin-header-actions">
                        <button class="convin-minimize-btn" onclick="window.ConvinFloatingWidget.minimize()" title="Minimize">−</button>
                        <button class="convin-close-btn" onclick="window.ConvinFloatingWidget.close()" title="Close">✕</button>
                    </div>
                </div>
                <div class="convin-floating-messages" id="convin-floating-messages">
                    <div class="convin-welcome">
                        <div>
                            <div class="convin-welcome-icon">👋</div>
                            <h4>Welcome!</h4>
                            <p>How can we help you today?</p>
                        </div>
                    </div>
                </div>
                <div class="convin-floating-input">
                    <input type="text" id="convin-floating-input" placeholder="Type your message..." />
                    <button class="convin-floating-send" onclick="window.ConvinFloatingWidget.send()">📤</button>
                </div>
            </div>
        </div>
    `;

    // Styles
    const styles = `
        .convin-floating-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .convin-bubble {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            border: none;
            cursor: grab;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
            transition: all 0.3s ease;
            user-select: none;
        }

        .convin-bubble:hover {
            transform: scale(1.1);
            box-shadow: 0 8px 20px rgba(59, 130, 246, 0.6);
        }

        .convin-bubble:active {
            cursor: grabbing;
        }

        .convin-bubble.convin-hidden {
            display: none;
        }

        .convin-floating-widget {
            position: absolute;
            bottom: 90px;
            right: 0;
            width: 400px;
            height: 600px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 5px 40px rgba(0, 0, 0, 0.16);
            display: none;
            flex-direction: column;
            overflow: hidden;
            animation: convin-slideUp 0.3s ease-out;
        }

        .convin-floating-widget.convin-open {
            display: flex;
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

        .convin-floating-header {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: grab;
            user-select: none;
        }

        .convin-floating-header h3 {
            font-size: 1.1rem;
            font-weight: 700;
            margin: 0;
        }

        .convin-floating-header p {
            font-size: 0.75rem;
            opacity: 0.9;
            margin: 4px 0 0 0;
        }

        .convin-header-actions {
            display: flex;
            gap: 8px;
        }

        .convin-minimize-btn,
        .convin-close-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            cursor: pointer;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .convin-minimize-btn:hover,
        .convin-close-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .convin-floating-messages {
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

        .convin-message.convin-user {
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

        .convin-message.convin-user .convin-message-content {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .convin-message.convin-assistant .convin-message-content {
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
            margin-bottom: 6px;
            color: #374151;
        }

        .convin-welcome p {
            font-size: 0.85rem;
            color: #9ca3af;
        }

        .convin-badge {
            display: inline-block;
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.65rem;
            font-weight: 600;
            margin-left: 8px;
        }

        .convin-floating-input {
            padding: 12px;
            background: white;
            border-top: 1px solid #e5e7eb;
            display: flex;
            gap: 8px;
        }

        .convin-floating-input input {
            flex: 1;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 0.9rem;
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #f9fafb;
            transition: all 0.3s ease;
        }

        .convin-floating-input input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .convin-floating-send {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border: none;
            padding: 10px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .convin-floating-send:hover {
            transform: translateY(-2px);
        }

        .convin-floating-messages::-webkit-scrollbar {
            width: 6px;
        }

        .convin-floating-messages::-webkit-scrollbar-thumb {
            background: #d1d5db;
            border-radius: 3px;
        }

        @media (max-width: 480px) {
            .convin-floating-widget {
                width: 100%;
                height: 100%;
                bottom: 0;
                right: 0;
                border-radius: 0;
            }

            .convin-bubble {
                display: none;
            }
        }
    `;

    // Initialize
    function init() {
        // Add styles
        const styleEl = document.createElement('style');
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);

        // Add HTML
        const container = document.createElement('div');
        container.innerHTML = widgetHTML;
        document.body.appendChild(container);

        // Setup drag
        setupDrag();

        // Setup events
        document.getElementById('convin-bubble').addEventListener('click', () => {
            window.ConvinFloatingWidget.open();
        });

        document.getElementById('convin-floating-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                window.ConvinFloatingWidget.send();
            }
        });

        console.log('✅ Convin Floating Widget Loaded');
    }

    // Drag functionality
    function setupDrag() {
        const container = document.getElementById('convin-floating-container');
        const header = document.getElementById('convin-floating-header');
        const bubble = document.getElementById('convin-bubble');

        let isDragging = false;
        let currentX, currentY, initialX, initialY;

        const startDrag = (e) => {
            if (e.target.tagName === 'BUTTON') return;
            isDragging = true;
            initialX = e.clientX - container.offsetLeft;
            initialY = e.clientY - container.offsetTop;

            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', stopDrag);
        };

        const drag = (e) => {
            if (!isDragging) return;
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;

            const maxX = window.innerWidth - 70;
            const maxY = window.innerHeight - 70;

            currentX = Math.max(0, Math.min(currentX, maxX));
            currentY = Math.max(0, Math.min(currentY, maxY));

            container.style.bottom = 'auto';
            container.style.right = 'auto';
            container.style.left = currentX + 'px';
            container.style.top = currentY + 'px';
        };

        const stopDrag = () => {
            isDragging = false;
            document.removeEventListener('mousemove', drag);
            document.removeEventListener('mouseup', stopDrag);
        };

        bubble.addEventListener('mousedown', startDrag);
        header.addEventListener('mousedown', startDrag);
    }

    // Widget API
    window.ConvinFloatingWidget = {
        open: function() {
            document.getElementById('convin-floating-widget').classList.add('convin-open');
            document.getElementById('convin-bubble').classList.add('convin-hidden');
            document.getElementById('convin-floating-input').focus();
        },

        minimize: function() {
            document.getElementById('convin-floating-widget').classList.remove('convin-open');
            document.getElementById('convin-bubble').classList.remove('convin-hidden');
        },

        close: function() {
            this.minimize();
            document.getElementById('convin-floating-messages').innerHTML = `
                <div class="convin-welcome">
                    <div>
                        <div class="convin-welcome-icon">👋</div>
                        <h4>Welcome!</h4>
                        <p>How can we help you today?</p>
                    </div>
                </div>
            `;
        },

        send: function() {
            const input = document.getElementById('convin-floating-input');
            const message = input.value.trim();

            if (!message) return;

            this.addMessage(message, 'user');
            input.value = '';

            setTimeout(() => {
                const responses = [
                    '👋 Thanks for reaching out!',
                    '💡 Great question!',
                    '📞 I\'m here to help!',
                    '✨ How can I assist?'
                ];
                const response = responses[Math.floor(Math.random() * responses.length)];
                this.addMessage(response, 'assistant');
            }, 800);
        },

        addMessage: function(text, sender) {
            const container = document.getElementById('convin-floating-messages');
            const welcome = container.querySelector('.convin-welcome');
            if (welcome && container.children.length === 1) {
                welcome.remove();
            }

            const msgEl = document.createElement('div');
            msgEl.className = `convin-message convin-${sender}`;
            msgEl.innerHTML = `<div class="convin-message-content">${this.escapeHtml(text)}</div>`;

            container.appendChild(msgEl);
            container.scrollTop = container.scrollHeight;
        },

        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    };

    // Load when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
