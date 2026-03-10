let state = {
    categoryId: null,
    categoryName: null,
    basePrice: 0,
    history: [],
    requirements: {
        is_hosted: true,
        monthly_fee: 0
    },
    checkoutReady: false,
    checkoutUrl: null
};

function saveState() {
    sessionStorage.setItem('botBuilderState', JSON.stringify(state));
}

function loadState() {
    const saved = sessionStorage.getItem('botBuilderState');
    if (saved) {
        try {
            return JSON.parse(saved);
        } catch (e) {
            console.error(e);
        }
    }
    return null;
}

const chatHistoryEl = document.getElementById('chat-history');
const initialSelectionEl = document.getElementById('category-selection');
const inputAreaEl = document.getElementById('chat-input-area');
const inputField = document.getElementById('user-input');

function selectCategory(id, name, price) {
    state.categoryId = id;
    state.categoryName = name;
    state.basePrice = parseFloat(price);
    state.history = [];
    state.checkoutReady = false;
    state.checkoutUrl = null;
    
    saveState();
    
    // Hide grid, show chat
    initialSelectionEl.style.display = 'none';
    chatHistoryEl.style.display = 'flex';
    inputAreaEl.style.display = 'flex';
    
    appendMessage('user', `I want to build a ${name}.`);
    
    // Init Gemini conversation
    processAiResponse(`I want to build a ${name}.`);
}

function handleKeyPress(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
}

function sendMessage() {
    const text = inputField.value.trim();
    if (!text) return;
    
    appendMessage('user', text);
    inputField.value = '';
    
    processAiResponse(text);
}

function appendMessage(sender, text, id = null) {
    const msgDiv = document.createElement('div');
    if (id) msgDiv.id = id;
    msgDiv.classList.add('chat-message');
    msgDiv.classList.add(sender === 'ai' ? 'message-ai' : 'message-user');
    msgDiv.innerHTML = `<strong>${sender === 'ai' ? 'Bot Butler AI' : 'You'}:</strong> ${text}`;
    chatHistoryEl.appendChild(msgDiv);
    chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
}

function processAiResponse(userInput) {
    state.history.push({ role: 'user', parts: [userInput] });
    
    const typingId = 'typing-' + Date.now();
    appendMessage('ai', '...', typingId);
    
    fetch('/api/bots/builder/chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            category_id: state.categoryId,
            history: state.history
        })
    })
    .then(r => r.json())
    .then(data => {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        
        if (data.success) {
            let aiText = data.reply;
            state.history.push({ role: 'model', parts: [aiText] }); // save AI reply to local history
            
            if (aiText.includes('[CHECKOUT_READY')) {
                // Parse AI JSON tag
                const match = aiText.match(/\[CHECKOUT_READY:\s*(\{.*\})\s*\]/);
                if (match) {
                    try {
                        const checkoutData = JSON.parse(match[1]);
                        state.requirements.is_hosted = checkoutData.is_hosted;
                        state.requirements.monthly_fee = checkoutData.monthly_fee;
                    } catch (e) {
                         console.error("Failed to parse checkout JSON", e);
                    }
                }
                
                state.checkoutReady = true;
                saveState();
                
                aiText = aiText.replace(/\[CHECKOUT_READY.*?\]/, '').trim();
                appendMessage('ai', aiText);
                
                // Show checkout button
                let btnText = `Confirm & Checkout (${state.basePrice}€ Setup)`;
                if (state.requirements.monthly_fee > 0) {
                     btnText = `Confirm & Checkout (${state.basePrice}€ Setup + ${state.requirements.monthly_fee}€/mo)`;
                }
                inputAreaEl.innerHTML = `<button class="btn-primary" style="width:100%" onclick="submitCheckout()">` + btnText + `</button>`;
            } else {
                saveState();
                appendMessage('ai', aiText);
                inputField.focus();
            }
        } else {
            appendMessage('ai', `❌ <strong>Error:</strong> ${data.error}`);
        }
    })
    .catch(error => {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        
        console.error('Error:', error);
        appendMessage('ai', `❌ <strong>Network Error.</strong> Could not reach the AI server.`);
    });
}

function submitCheckout() {
    inputAreaEl.innerHTML = `<button class="btn-primary" style="width:100%" disabled>Processing... Please hold.</button>`;
    
    // Pass the entire AI chat transcript as requirements
    const payload = {
        category_id: state.categoryId,
        requirements_json: { chat_transcript: state.history },
        consulting_requested: false,
        contact_info: "See chat transcript"
    };

    fetch('/api/bots/checkout/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (response.status === 401) {
            return response.json().then(errData => { throw errData; });
        }
        return response.json();
    })
    .then(data => {
        if (data.success && data.checkout_url) {
            appendMessage('ai', `Redirecting you to our secure Stripe checkout...`);
            state.checkoutUrl = data.checkout_url;
            saveState();
            window.location.href = data.checkout_url;
        } else {
            appendMessage('ai', `❌ <strong>Error:</strong> ${data.error || 'Unknown error occurred.'}`);
            inputAreaEl.innerHTML = `<button class="btn-primary" style="width:100%" onclick="submitCheckout()">Retry Checkout</button>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (error && error.requires_login) {
            appendMessage('ai', `<strong>Authentication Required</strong><br>To securely manage your bot, toggle it on/off, and request custom adjustments in the future, please create a free account or log in first.<br><br><a href="/auth/login/?next=/#builder" class="btn-outline" style="display:inline-block; margin-top:10px; margin-right:10px;">Login</a> <a href="/register/?next=/#builder" class="btn-primary" style="display:inline-block; margin-top:10px;">Register</a>`);
            
            let btnText = `Checkout (${state.basePrice}€)`;
            if (state.requirements && state.requirements.monthly_fee > 0) {
                 btnText = `Checkout (${state.basePrice}€ + ${state.requirements.monthly_fee}€/mo)`;
            }
            inputAreaEl.innerHTML = `<button class="btn-primary" style="width:100%" onclick="submitCheckout()">` + btnText + `</button>`;
        } else {
            appendMessage('ai', `❌ <strong>Network Error.</strong> Could not reach the server.`);
            inputAreaEl.innerHTML = `<button class="btn-primary" style="width:100%" onclick="submitCheckout()">Retry Checkout</button>`;
        }
    });
}

// Initialization: Check if there's a saved state on page load
window.addEventListener('DOMContentLoaded', () => {
    const savedState = loadState();
    if (savedState && savedState.categoryId) {
        // Restore state object
        state = savedState;
        
        // Hide selection grid
        initialSelectionEl.style.display = 'none';
        
        // Show chat UI
        chatHistoryEl.style.display = 'flex';
        inputAreaEl.style.display = 'flex';
        
        // Re-render history
        chatHistoryEl.innerHTML = '';
        state.history.forEach(msg => {
            const isAi = msg.role === 'model';
            const senderName = isAi ? 'Bot Butler AI' : 'You';
            const text = msg.parts[0];
            
            const msgDiv = document.createElement('div');
            msgDiv.classList.add('chat-message');
            msgDiv.classList.add(isAi ? 'message-ai' : 'message-user');
            msgDiv.innerHTML = `<strong>${senderName}:</strong> ${text}`;
            chatHistoryEl.appendChild(msgDiv);
        });
        
        // Scroll to bottom
        chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
        
        // Restore checkout button if it was ready
        if (state.checkoutReady) {
            let btnText = `Confirm & Checkout (${state.basePrice}€ Setup)`;
            if (state.requirements && state.requirements.monthly_fee > 0) {
                 btnText = `Confirm & Checkout (${state.basePrice}€ Setup + ${state.requirements.monthly_fee}€/mo)`;
            }
            inputAreaEl.innerHTML = `<button class="btn-primary" style="width:100%" onclick="submitCheckout()">` + btnText + `</button>`;
        }
    }
});
