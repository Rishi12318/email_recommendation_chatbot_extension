chrome.runtime.onInstalled.addListener(() => console.log('Email Assistant installed'));

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'scanInbox' || request.action === 'getOpenEmail') {
        chrome.tabs.query({ url: 'https://mail.google.com/*' }, (tabs) => {
            if (tabs.length === 0) {
                sendResponse({ error: 'Gmail not open' });
                return;
            }
            chrome.tabs.sendMessage(tabs[0].id, request, (response) => {
                sendResponse(response || { error: 'No response from Gmail' });
            });
        });
        return true;
    }
});
