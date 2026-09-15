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

    let API_BASE;

    chrome.storage.local.get(['apiBase'], function(r) {
        API_BASE = r.apiBase || 'http://localhost:8000';
        checkConnection();
        updateEmailCount();
    });

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

        chrome.identity.getAuthToken({ interactive: true }, function(token) {
            if (chrome.runtime.lastError) {
                googleSignInBtn.disabled = false;
                googleSignInBtn.textContent = 'Sign in with Google';
                addMessage('Could not sign in: ' + chrome.runtime.lastError.message + '. Enter your details manually below.', 'bot');
                return;
            }

            if (token) {
                fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
                    headers: { 'Authorization': 'Bearer ' + token }
                })
                .then(r => r.json())
                .then(userInfo => {
                    googleSignInBtn.disabled = false;
                    googleSignInBtn.textContent = 'Sign in with Google';

                    if (userInfo.email) {
                        userNameInput.value = userInfo.name || userInfo.email.split('@')[0];
                        userEmailInput.value = userInfo.email;
                        chrome.storage.local.set({ gmailToken: token });
                        addMessage('Signed in as ' + userInfo.email + '. Click "Get Started" to continue.', 'bot');
                    } else {
                        addMessage('Could not get user info. Enter your details manually below.', 'bot');
                    }
                })
                .catch(() => {
                    googleSignInBtn.disabled = false;
                    googleSignInBtn.textContent = 'Sign in with Google';
                    addMessage('Error getting user info. Enter your details manually below.', 'bot');
                });
            } else {
                googleSignInBtn.disabled = false;
                googleSignInBtn.textContent = 'Sign in with Google';
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
    }

    function scanInbox() {
        scanBtn.disabled = true;
        scanBtn.textContent = 'Scanning...';
        addMessage('Connecting to Gmail API...', 'bot');

        chrome.runtime.sendMessage({ action: 'scanInbox', maxResults: 50 }, async (response) => {
            scanBtn.disabled = false;
            scanBtn.textContent = 'Scan Inbox';

            if (!response) {
                addMessage('Could not connect to Gmail. Please try again.', 'bot');
                return;
            }

            if (response.error) {
                addMessage('Error: ' + response.error, 'bot');
                return;
            }

            const emails = response.emails || [];
            if (emails.length === 0) {
                addMessage('No emails found in your inbox.', 'bot');
                return;
            }

            addMessage('Found ' + emails.length + ' emails. Indexing...', 'bot');

            const formattedEmails = emails.map(e => ({
                sender: e.sender_name || e.from || 'Unknown',
                subject: e.subject || '(no subject)',
                snippet: e.snippet || '',
                date: e.date_display || e.date || '',
                body: e.body || ''
            }));

            try {
                const r = await fetch(API_BASE + '/api/emails/ingest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ emails: formattedEmails })
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
