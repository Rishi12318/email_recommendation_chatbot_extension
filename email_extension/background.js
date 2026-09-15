importScripts('gmail-api.js');

chrome.runtime.onInstalled.addListener(() => console.log('Email Assistant installed'));

async function handleGmailAction(request, sendResponse) {
    if (request.action === 'scanInbox') {
        try {
            const result = await fetchEmailsViaApi(request.maxResults || 50);
            sendResponse(result);
        } catch (e) {
            sendResponse({ error: 'Failed to fetch emails: ' + e.message });
        }
        return;
    }

    if (request.action === 'getOpenEmail') {
        const tabs = await chrome.tabs.query({ url: 'https://mail.google.com/*' });
        if (tabs.length === 0) {
            sendResponse({ error: 'Gmail not open' });
            return;
        }
        const tabId = tabs[0].id;
        await ensureContentScript(tabId);
        try {
            const response = await chrome.tabs.sendMessage(tabId, request);
            sendResponse(response || { error: 'No response from Gmail' });
        } catch (e) {
            sendResponse({ error: 'Content script not responding. Try refreshing Gmail.' });
        }
        return;
    }

    if (request.action === 'getUserProfile') {
        try {
            const profile = await getUserProfile();
            sendResponse(profile || { error: 'Could not get user profile' });
        } catch (e) {
            sendResponse({ error: e.message });
        }
        return;
    }

    if (request.action === 'signOut') {
        try {
            const token = await getAuthToken(false);
            if (token) {
                chrome.identity.removeCachedAuthToken({ token }, () => {
                    sendResponse({ success: true });
                });
                return;
            }
        } catch (e) {}
        sendResponse({ success: true });
        return;
    }
}

async function ensureContentScript(tabId) {
    try {
        await chrome.scripting.executeScript({
            target: { tabId },
            files: ['content.js']
        });
    } catch (e) {
        // Already injected, that's fine
    }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'scanInbox' || request.action === 'getOpenEmail' ||
        request.action === 'getUserProfile' || request.action === 'signOut') {
        handleGmailAction(request, sendResponse);
        return true;
    }
});
