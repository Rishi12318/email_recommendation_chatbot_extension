chrome.runtime.onInstalled.addListener(() => {
    console.log('Email Assistant extension installed');
});

chrome.action.onClicked.addListener((tab) => {
    chrome.action.openPopup();
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getApiUrl') {
        sendResponse({ url: 'http://localhost:8000' });
    }
});
