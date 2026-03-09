let state = {
    categoryId: null,
    categoryName: null,
    basePrice: 0,
    chatStage: 0,
    requirements: {},
    consultingRequested: false,
    contactInfo: ""
};

const chatHistoryEl = document.getElementById('chat-history');
const initialSelectionEl = document.getElementById('category-selection');
const inputAreaEl = document.getElementById('chat-input-area');
const inputField = document.getElementById('user-input');

function selectCategory(id, name, price) {
    state.categoryId = id;
    state.categoryName = name;
    state.basePrice = parseFloat(price);
    
    // Hide grid, show chat
    initialSelectionEl.style.display = 'none';
    chatHistoryEl.style.display = 'flex';
    inputAreaEl.style.display = 'flex';
    
    appendMessage('user', `I want to build a ${name}.`);
    
    setTimeout(() => {
        appendMessage('ai', `Excellent choice! A ${name} is a powerful automation tool. Please describe in detail what specific actions, commands, or workflows this bot should handle for you.`);
        state.chatStage = 1;
        inputField.focus();
    }, 600);
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

function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('chat-message');
    msgDiv.classList.add(sender === 'ai' ? 'message-ai' : 'message-user');
    msgDiv.innerHTML = `<strong>${sender === 'ai' ? 'Bot Butler AI' : 'You'}:</strong> ${text}`;
    chatHistoryEl.appendChild(msgDiv);
    chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
}

function processAiResponse(userInput) {
    // Simulate thinking delay
    const typingDelay = 1200;
    
    setTimeout(() => {
        if (state.chatStage === 1) {
            state.requirements.core_description = userInput;
            appendMessage('ai', `I've analyzed your prompt. For this architecture, we will need to handle state management and API webhooks. Are there any external APIs or databases this bot needs to connect to? (Reply with details, or "No").`);
            state.chatStage = 2;
        } 
        else if (state.chatStage === 2) {
            state.requirements.integrations = userInput;
            appendMessage('ai', `Perfect. I have drafted the full technical specification for your ${state.categoryName}.<br><br><b>Consulting Upsell:</b> Would you like to personally speak with one of our Lead Developers to verify these details before we begin coding? (This includes a priority architecture review for a +150€ premium fee).<br><br>Reply "Yes" or "No".`);
            state.chatStage = 3;
        }
        else if (state.chatStage === 3) {
            const isYes = userInput.toLowerCase().includes('yes') || userInput.toLowerCase() === 'y';
            state.consultingRequested = isYes;
            
            appendMessage('ai', `Understood. Finally, please provide an email address or phone number so we can deliver the bot to you (and contact you if you chose the consulting option).`);
            state.chatStage = 4;
        }
        else if (state.chatStage === 4) {
            state.contactInfo = userInput;
            
            let finalPrice = state.basePrice;
            if (state.consultingRequested) finalPrice += 150;
            
            let eta = "24-48 Hours";
            const nameLower = state.categoryName.toLowerCase();
            if (nameLower.includes("scraping") || nameLower.includes("data")) {
                eta = "3-5 Days";
            } else if (nameLower.includes("trading") || nameLower.includes("voice") || nameLower.includes("support")) {
                eta = "5-7 Days";
            }
            
            appendMessage('ai', `Thank you! Here is your final summary:<br>
            - <strong>Bot Type:</strong> ${state.categoryName}<br>
            - <strong>Consulting Requested:</strong> ${state.consultingRequested ? 'Yes (+150€)' : 'No'}<br>
            - <strong>Total Estimated Price:</strong> ${finalPrice}€<br>
            - <strong>Estimated Delivery:</strong> ${eta}<br><br>
            Click the button below to complete your secure checkout and automatically deploy the architecture draft to our secure servers.`);
            
            // Hide text input, show checkout button
            inputAreaEl.innerHTML = `<button class="btn-primary" style="width:100%" onclick="submitCheckout()">Confirm & Checkout (${finalPrice}€)</button>`;
            state.chatStage = 5;
        }
    }, typingDelay);
}

function submitCheckout() {
    inputAreaEl.innerHTML = `<button class="btn-primary" style="width:100%" disabled>Processing... Please hold.</button>`;
    
    const payload = {
        category_id: state.categoryId,
        requirements_json: state.requirements,
        consulting_requested: state.consultingRequested,
        contact_info: state.contactInfo
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
            window.location.href = data.checkout_url;
        } else {
            appendMessage('ai', `❌ <strong>Error:</strong> ${data.error || 'Unknown error occurred.'}`);
            inputAreaEl.innerHTML = `<button class="btn-primary" style="width:100%" onclick="submitCheckout()">Retry Checkout</button>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (error && error.requires_login) {
            appendMessage('ai', `<strong>Authentication Required</strong><br>To securely manage your bot, toggle it on/off, and request custom adjustments in the future, please create a free account or log in first.<br><br><a href="/auth/login/" class="btn-outline" style="display:inline-block; margin-top:10px; margin-right:10px;">Login</a> <a href="/register/" class="btn-primary" style="display:inline-block; margin-top:10px;">Register</a>`);
            inputAreaEl.innerHTML = `<button class="btn-primary" style="width:100%" onclick="submitCheckout()">Checkout (${finalPrice}€)</button>`.replace('finalPrice', state.basePrice + (state.consultingRequested ? 150 : 0));
        } else {
            appendMessage('ai', `❌ <strong>Network Error.</strong> Could not reach the server.`);
            inputAreaEl.innerHTML = `<button class="btn-primary" style="width:100%" onclick="submitCheckout()">Retry Checkout</button>`;
        }
    });
}
