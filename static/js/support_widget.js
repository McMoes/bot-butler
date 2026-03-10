document.addEventListener('DOMContentLoaded', function() {
    // Inject the widget HTML structure
    const widgetHTML = `
        <div id="bb-support-widget-container">
            <div id="bb-support-trigger">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            </div>
            
            <div id="bb-support-window" class="bb-hidden">
                <div class="bb-support-header">
                    <h4>Bot Butler AI</h4>
                    <button id="bb-support-close">&times;</button>
                </div>
                <div class="bb-support-messages" id="bb-support-messages">
                    <div class="bb-message bb-bot">
                        Willkommen bei Bot Butler! Ich bin der KI-Assistent. Haben Sie Fragen zu unseren Automation Bots oder unseren Managed Hosting Tarifen?
                    </div>
                </div>
                <div class="bb-support-input">
                    <input type="text" id="bb-support-text" placeholder="Ihre Frage..." />
                    <button id="bb-support-send">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', widgetHTML);
    
    const trigger = document.getElementById('bb-support-trigger');
    const windowEl = document.getElementById('bb-support-window');
    const closeBtn = document.getElementById('bb-support-close');
    const sendBtn = document.getElementById('bb-support-send');
    const inputField = document.getElementById('bb-support-text');
    const messagesContainer = document.getElementById('bb-support-messages');
    
    let chatHistory = [];
    
    trigger.addEventListener('click', () => {
        windowEl.classList.toggle('bb-hidden');
    });
    
    closeBtn.addEventListener('click', () => {
        windowEl.classList.add('bb-hidden');
    });
    
    function addMessage(text, isUser) {
        const msgDiv = document.createElement('div');
        msgDiv.className = "bb-message " + (isUser ? "bb-user" : "bb-bot");
        msgDiv.innerHTML = text; // allow clear HTML for bot responses
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    async function sendMessage() {
        const text = inputField.value.trim();
        if (!text) return;
        
        inputField.value = '';
        addMessage(text, true);
        
        chatHistory.push({
            "role": "user",
            "parts": [text]
        });
        
        // Add loading indicator
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'bb-message bb-bot';
        loadingDiv.innerHTML = '<span class="bb-dot-typing"></span>';
        messagesContainer.appendChild(loadingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        try {
            const langCode = document.documentElement.lang || 'en';
            const url = "/" + langCode + "/api/bots/support/chat/";
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    history: chatHistory
                })
            });
            
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            
            const data = await response.json();
            
            if (data.reply) {
                addMessage(data.reply, false);
                chatHistory.push({
                    "role": "model",
                    "parts": [data.reply]
                });
            } else {
                addMessage(data.error || "Entschuldigung, es ist ein Fehler aufgetreten.", false);
            }
            
        } catch (e) {
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            addMessage("Netzwerkfehler. Bitte später erneut versuchen.", false);
        }
    }
    
    sendBtn.addEventListener('click', sendMessage);
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});
