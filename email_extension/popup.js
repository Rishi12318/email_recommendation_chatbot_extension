const API_URL = 'http://localhost:8000/api/chat';

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const chatArea = document.getElementById('chat-area');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const statusEl = document.getElementById('status');
    const settingsBtn = document.getElementById('settings-btn');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const setupSection = document.getElementById('setup-section');

    loadSettings();
    checkConnection();

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });

    settingsBtn.addEventListener('click', toggleSettings);
    saveSettingsBtn.addEventListener('click', saveSettings);

    function loadSettings() {
        chrome.storage.local.get(['userName', 'userEmail', 'userProfession'], function(result) {
            if (result.userName) {
                document.getElementById('user-name').value = result.userName;
                document.getElementById('user-email').value = result.userEmail;
                document.getElementById('user-profession').value = result.userProfession;
                showChat();
            } else {
                showSetup();
            }
        });
    }

    function saveSettings() {
        const name = document.getElementById('user-name').value.trim();
        const email = document.getElementById('user-email').value.trim();
        const profession = document.getElementById('user-profession').value;

        if (!name || !email || !profession) {
            alert('Please fill in all fields and select your profession.');
            return;
        }

        chrome.storage.local.set({
            userName: name,
            userEmail: email,
            userProfession: profession
        }, function() {
            setupSection.classList.remove('visible');
            showChat();
            sendUserProfile(name, email, profession);
        });
    }

    async function sendUserProfile(name, email, profession) {
        try {
            await fetch('http://localhost:8000/api/user/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, profession })
            });
        } catch (error) {
            console.error('Failed to save profile:', error);
        }
    }

    function toggleSettings() {
        setupSection.classList.toggle('visible');
    }

    function showSetup() {
        setupSection.style.display = 'block';
        chatArea.style.display = 'none';
    }

    function showChat() {
        setupSection.style.display = 'none';
        chatArea.style.display = 'flex';
        userInput.focus();
    }

    function addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `msg ${sender === 'user' ? 'user-msg' : 'bot-msg'}`;
        msgDiv.textContent = text;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function showTyping() {
        const typing = document.createElement('div');
        typing.className = 'msg bot-msg typing';
        typing.id = 'typing-indicator';
        typing.textContent = '...';
        chatBox.appendChild(typing);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function removeTyping() {
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        userInput.value = '';
        showTyping();

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: [{ role: 'user', content: text }]
                })
            });
            const data = await response.json();
            removeTyping();
            addMessage(data.reply || 'No response', 'bot');
        } catch (error) {
            removeTyping();
            addMessage('Error: Could not reach server. Is the backend running?', 'bot');
            console.error('Chat error:', error);
        }
    }

    async function checkConnection() {
        try {
            const response = await fetch('http://localhost:8000/health');
            if (response.ok) {
                statusEl.textContent = 'Connected';
                statusEl.style.color = '#34a853';
            } else {
                statusEl.textContent = 'Disconnected';
                statusEl.style.color = '#ea4335';
            }
        } catch {
            statusEl.textContent = 'Disconnected';
            statusEl.style.color = '#ea4335';
        }
    }
});
