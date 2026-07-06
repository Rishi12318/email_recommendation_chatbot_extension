// popup.js
const API_URL = 'http://localhost:8000/api/chat';

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const statusEl = document.getElementById('status');
    const settingsBtn = document.getElementById('settings-btn');
    const saveSettingsBtn = document.getElementById('save-settings-btn');

    // Load saved settings
    loadSettings();

    checkConnection();

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });

    settingsBtn.addEventListener('click', toggleSettings);
    saveSettingsBtn.addEventListener('click', saveSettings);

    // ============================================================
    // SETTINGS FUNCTIONS
    // ============================================================

    function loadSettings() {
        chrome.storage.local.get(['userName', 'userEmail', 'userProfession'], function(result) {
            if (result.userName) {
                document.getElementById('user-name').value = result.userName;
            }
            if (result.userEmail) {
                document.getElementById('user-email').value = result.userEmail;
            }
            if (result.userProfession) {
                document.getElementById('user-profession').value = result.userProfession;
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
            alert('Settings saved!');
            // Send profession to backend
            sendUserProfile(name, email, profession);
        });
    }

    async function sendUserProfile(name, email, profession) {
        try {
            const response = await fetch('http://localhost:8000/api/user/profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${await getToken()}`
                },
                body: JSON.stringify({
                    name: name,
                    email: email,
                    profession: profession
                })
            });
            const data = await response.json();
            console.log('Profile saved:', data);
        } catch (error) {
            console.error('Failed to save profile:', error);
        }
    }

    function toggleSettings() {
        const settingsSection = document.getElementById('settings-section');
        if (settingsSection.style.display === 'none') {
            settingsSection.style.display = 'block';
        } else {
            settingsSection.style.display = 'none';
        }
    }

    // ============================================================
    // CHAT FUNCTIONS
    // ============================================================

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
                statusEl.textContent = '● Connected';
                statusEl.style.color = '#34a853';
            } else {
                statusEl.textContent = '● Disconnected';
                statusEl.style.color = '#ea4335';
            }
        } catch {
            statusEl.textContent = '● Disconnected';
            statusEl.style.color = '#ea4335';
        }
    }
});