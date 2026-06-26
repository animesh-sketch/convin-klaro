# 💬 Convin Chat Widget - Integration Guide

## Overview

The Convin Chat Widget is an embeddable chat interface that can be added to any website. It provides a beautiful, modern chat experience for your customers.

---

## 🚀 Quick Start

### Option 1: Embed as HTML File

1. **Host the widget file:**
   - Upload `chat_widget.html` to your web server
   - Make it accessible via a public URL

2. **Add to your website:**
   ```html
   <iframe 
       src="https://your-domain.com/chat_widget.html" 
       width="400" 
       height="600"
       frameborder="0"
       style="border-radius: 16px; box-shadow: 0 5px 40px rgba(0,0,0,0.16);">
   </iframe>
   ```

### Option 2: Embed as JavaScript Widget

1. **Host the JavaScript file:**
   - Upload `chat_widget.js` to your web server
   - Make it accessible via a public URL

2. **Add to your website (one line):**
   ```html
   <script src="https://your-domain.com/chat_widget.js"></script>
   ```

   That's it! The widget will automatically appear in the bottom-right corner.

---

## ⚙️ Configuration

### JavaScript Widget Options

```javascript
// Before loading the widget, configure it:
<script>
  window.ConvinChatConfig = {
    apiUrl: 'https://your-api.com/chat',
    position: 'bottom-right',  // bottom-right, bottom-left, top-right, top-left
    theme: 'light',             // light, dark
    customerId: 'user-123',     // Optional: user identifier
    title: '💬 Chat',          // Custom title
    subtitle: 'We reply in minutes'  // Custom subtitle
  };
</script>
<script src="https://your-domain.com/chat_widget.js"></script>
```

---

## 📱 Positioning

You can customize the widget position by modifying the CSS:

### Bottom Right (Default)
```css
.chat-widget-container {
    bottom: 20px;
    right: 20px;
}
```

### Bottom Left
```css
.chat-widget-container {
    bottom: 20px;
    left: 20px;
}
```

### Top Right
```css
.chat-widget-container {
    top: 20px;
    right: 20px;
}
```

---

## 🎨 Customization

### Change Colors

Modify the gradient colors in `chat_widget.js`:

```javascript
// Find this in the styles:
.convin-widget-header {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    // Change #3b82f6 and #8b5cf6 to your brand colors
}
```

### Change Size

```javascript
.convin-widget-container {
    width: 380px;    // Adjust width
    height: 600px;   // Adjust height
}
```

### Customize Messages

Update the welcome message text in the widget HTML section.

---

## 🔌 API Integration

### Connect to Your Backend

```javascript
// In chat_widget.js, modify the send function:
ConvinChatWidget.send = function() {
    const input = document.getElementById('convin-input');
    const message = input.value.trim();

    if (!message) return;

    this.addMessage(message, 'user');
    input.value = '';

    // Send to your API
    fetch('YOUR_API_ENDPOINT', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            customerId: CONFIG.customerId,
            timestamp: new Date()
        })
    })
    .then(res => res.json())
    .then(data => {
        // Add AI response to chat
        this.addMessage(data.reply, 'assistant');
    })
    .catch(err => {
        this.addMessage('Sorry, there was an error. Please try again.', 'assistant');
    });
};
```

---

## 📊 Tracking & Analytics

### Track Widget Usage

```javascript
// Add custom tracking:
window.ConvinChatWidget.trackEvent = function(event, data) {
    console.log('Event:', event, data);
    
    // Send to your analytics service
    fetch('YOUR_ANALYTICS_ENDPOINT', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event, data, customerId: CONFIG.customerId })
    });
};

// Usage:
window.ConvinChatWidget.trackEvent('chat_opened', {});
window.ConvinChatWidget.trackEvent('message_sent', { text: 'user message' });
```

---

## 🔐 Security

### Protect Your API

1. **Use CORS headers** on your backend
2. **Validate requests** on the server
3. **Rate limit** messages per customer
4. **Sanitize input** to prevent XSS attacks
5. **Use HTTPS** for all communications

---

## 📝 Examples

### Example 1: React Component

```jsx
import { useEffect } from 'react';

function ChatWidget() {
    useEffect(() => {
        // Load the widget script
        const script = document.createElement('script');
        script.src = 'https://your-domain.com/chat_widget.js';
        script.async = true;
        document.body.appendChild(script);
    }, []);

    return null; // Widget renders itself
}

export default ChatWidget;
```

### Example 2: Next.js

```jsx
import Script from 'next/script';

export default function Layout({ children }) {
    return (
        <>
            {children}
            <Script src="https://your-domain.com/chat_widget.js" />
        </>
    );
}
```

### Example 3: WordPress

Add to your theme's `footer.php`:

```php
<?php
    echo '<script src="https://your-domain.com/chat_widget.js"></script>';
?>
```

---

## 🐛 Troubleshooting

### Widget not appearing?
- Check if JavaScript is enabled
- Verify the script URL is accessible
- Check browser console for errors
- Ensure no JavaScript errors on the page

### Messages not sending?
- Check API endpoint is correct
- Verify CORS is configured
- Check network tab in DevTools
- Check server logs for errors

### Styling issues?
- Clear browser cache
- Check for CSS conflicts
- Use DevTools to inspect elements
- Verify font imports are working

---

## 📞 Support

For issues or questions:
- Email: support@convin.ai
- Documentation: https://docs.convin.ai
- GitHub: https://github.com/convin/chat-widget

---

## 📄 File Structure

```
convin-klaro/
├── app.py                          # Main Streamlit app
├── chat_widget.html                # Standalone HTML widget
├── chat_widget.js                  # Embeddable JavaScript widget
├── WIDGET_INTEGRATION_GUIDE.md     # This file
├── kb_files/                       # Knowledge base files
└── requirements.txt                # Python dependencies
```

---

## 🎯 Next Steps

1. **Host the widget files** on your server
2. **Update the API endpoint** to point to your backend
3. **Test the widget** on a test page
4. **Customize colors and messages** to match your brand
5. **Deploy to production**

Enjoy your new chat widget! 🚀
