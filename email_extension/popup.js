const API_BASE = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const chatArea = document.getElementById('chat-area');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const statusEl = document.getElementById('status');
    const settingsBtn = document.getElementById('settings-btn');
    const setupSection = document.getElementById('setup-section');
    const scanBtn = document.getElementById('scan-btn');
    const emailCount = document.getElementById('email-count');
    const openGmailBtn = document.getElementById('open-gmail-btn');
    const gmailStatus = document.getElementById('gmail-status');
    const googleSignInBtn = document.getElementById('google-signin-btn');
    const userNameInput = document.getElementById('user-name');
    const userEmailInput = document.getElementById('user-email');
    const professionSelect = document.getElementById('user-profession');

    checkConnection();

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });
    settingsBtn.addEventListener('click', toggleSettings);
    scanBtn.addEventListener('click', scanInbox);
    openGmailBtn.addEventListener('click', () => {
        chrome.tabs.create({ url: 'https://mail.google.com' });
    });

    document.getElementById('save-settings-btn').addEventListener('click', saveSettings);

    if (googleSignInBtn) {
        googleSignInBtn.addEventListener('click', signInWithGoogle);
    }

    loadSettings();

    function loadSettings() {
        chrome.storage.local.get(['userName', 'userEmail', 'userProfession', 'signedIn'], function(result) {
            if (result.signedIn) {
                userNameInput.value = result.userName || '';
                userEmailInput.value = result.userEmail || '';
                professionSelect.value = result.userProfession || '';
                showChat();
            } else {
                showSetup();
            }
        });
    }

    function signInWithGoogle() {
        googleSignInBtn.disabled = true;
        googleSignInBtn.textContent = 'Signing in...';

        chrome.identity.getProfileUserInfo({ 'accountStatus': 'ANY' }, function(userInfo) {
            googleSignInBtn.disabled = false;
            googleSignInBtn.textContent = 'Sign in with Google';

            if (chrome.runtime.lastError) {
                addMessage('Could not sign in: ' + chrome.runtime.lastError.message + '. Enter your details manually below.', 'bot');
                return;
            }
            if (userInfo && userInfo.email) {
                userNameInput.value = userInfo.name || userInfo.email.split('@')[0];
                userEmailInput.value = userInfo.email;
                addMessage('Signed in as ' + userInfo.email + '. Click "Get Started" to continue.', 'bot');
            } else {
                addMessage('Not signed into Chrome with a Google account. Enter your details manually below.', 'bot');
            }
        });
    }

    function saveSettings() {
        const name = userNameInput.value.trim();
        const email = userEmailInput.value.trim();
        const profession = professionSelect.value;
        if (!name || !email || !profession) {
            alert('Please fill in all fields or sign in with Google.');
            return;
        }
        chrome.storage.local.set({
            userName: name, userEmail: email, userProfession: profession, signedIn: true
        }, function() {
            setupSection.classList.remove('visible');
            showChat();
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
        updateEmailCount();
        checkGmailOpen();
    }

    function checkGmailOpen() {
        chrome.tabs.query({ url: 'https://mail.google.com/*' }, function(tabs) {
            const isOpen = tabs.length > 0;
            gmailStatus.textContent = isOpen ? 'Gmail Open' : 'Gmail Closed';
            gmailStatus.className = 'gmail-status ' + (isOpen ? 'connected' : 'disconnected');
            if (isOpen) {
                openGmailBtn.classList.add('hidden');
            } else {
                openGmailBtn.classList.remove('hidden');
            }
        });
    }

    function scanInbox() {
        scanBtn.disabled = true;
        scanBtn.textContent = 'Scanning...';
        addMessage('Scanning Gmail...', 'bot');

        chrome.runtime.sendMessage({ action: 'scanInbox' }, async (response) => {
            scanBtn.disabled = false;
            scanBtn.textContent = 'Scan Inbox';
            if (!response) {
                addMessage('Could not reach Gmail. Try refreshing mail.google.com and try again.', 'bot');
                return;
            }
            if (response.error) {
                addMessage(response.error + '. Open mail.google.com, refresh the page, then try again.', 'bot');
                return;
            }
            const emails = response.emails || [];
            if (emails.length === 0) {
                addMessage('No emails found. Make sure you are on the inbox page and try again.', 'bot');
                return;
            }
            addMessage('Found ' + emails.length + ' emails. Indexing...', 'bot');
            try {
                const r = await fetch(API_BASE + '/api/emails/ingest', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ emails })
                });
                const data = await r.json();
                addMessage('Indexed ' + data.indexed + ' emails. Ask me anything!', 'bot');
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
            if (data.total) emailCount.textContent = data.total + ' emails';
        } catch (e) {}
    }

    function addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'msg ' + (sender === 'user' ? 'user-msg' : 'bot-msg');
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
