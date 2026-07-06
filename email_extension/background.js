chrome.runtime.onInstalled.addListener(() => console.log('Email Assistant installed'));

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

async function handleGmailAction(request, sendResponse) {
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
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'scanInbox' || request.action === 'getOpenEmail') {
        handleGmailAction(request, sendResponse);
        return true;
    }
});
