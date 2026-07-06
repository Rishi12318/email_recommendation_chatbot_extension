const API_BASE = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const chatArea = document.getElementById('chat-area');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const statusEl = document.getElementById('status');
    const settingsBtn = document.getElementById('settings-btn');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const setupSection = document.getElementById('setup-section');
    const scanBtn = document.getElementById('scan-btn');
    const emailCount = document.getElementById('email-count');
    const openGmailBtn = document.getElementById('open-gmail-btn');

    loadSettings();
    checkConnection();
    updateEmailCount();

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });
    settingsBtn.addEventListener('click', toggleSettings);
    saveSettingsBtn.addEventListener('click', saveSettings);
    scanBtn.addEventListener('click', scanInbox);
    openGmailBtn.addEventListener('click', () => {
        chrome.tabs.create({ url: 'https://mail.google.com' });
    });

    function loadSettings() {
        chrome.storage.local.get(['userName'], function(result) {
            if (result.userName) {
                document.getElementById('user-name').value = result.userName;
                document.getElementById('user-email').value = result.userEmail || '';
                document.getElementById('user-profession').value = result.userProfession || '';
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
            alert('Please fill in all fields.');
            return;
        }
        chrome.storage.local.set({ userName: name, userEmail: email, userProfession: profession }, function() {
            setupSection.classList.remove('visible');
            showChat();
            fetch(API_BASE + '/api/user/profile', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, profession })
            }).catch(() => {});
        });
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

    function scanInbox() {
        scanBtn.disabled = true;
        scanBtn.textContent = 'Scanning...';
        addMessage('Scanning Gmail...', 'bot');

        chrome.runtime.sendMessage({ action: 'scanInbox' }, async (response) => {
            scanBtn.disabled = false;
            scanBtn.textContent = 'Scan Inbox';

            if (!response || response.error) {
                addMessage('Open Gmail first (mail.google.com) then try again.', 'bot');
                return;
            }

            const emails = response.emails || [];
            if (emails.length === 0) {
                addMessage('No emails found in your inbox view. Make sure you are on the inbox page.', 'bot');
                return;
            }

            addMessage(`Found ${emails.length} emails. Indexing...`, 'bot');

            try {
                const r = await fetch(API_BASE + '/api/emails/ingest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ emails })
                });
                const data = await r.json();
                addMessage(`Indexed ${data.indexed} emails. Ask me anything about your inbox!`, 'bot');
                updateEmailCount();
            } catch (e) {
                addMessage('Indexed locally. Ask me about your emails!', 'bot');
            }
        });
    }

    async function updateEmailCount() {
        try {
            const r = await fetch(API_BASE + '/api/gmail/emails');
            const data = await r.json();
            if (data.total) emailCount.textContent = `${data.total} emails`;
        } catch (e) {}
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
        const el = document.getElementById('typing-indicator');
        if (el) el.remove();
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;
        addMessage(text, 'user');
        userInput.value = '';
        showTyping();
        try {
            const r = await fetch(API_BASE + '/api/chat', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: [{ role: 'user', content: text }] })
            });
            const data = await r.json();
            removeTyping();
            addMessage(data.reply || 'No response', 'bot');
        } catch (e) {
            removeTyping();
            addMessage('Error: Cannot reach server. Is it running?', 'bot');
        }
    }

    async function checkConnection() {
        try {
            const r = await fetch(API_BASE + '/health');
            if (r.ok) {
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
