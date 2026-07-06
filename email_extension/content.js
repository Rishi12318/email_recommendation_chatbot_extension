// content.js
console.log('Email Assistant content script loaded');

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getEmailContent') {
        const content = getGmailContent();
        const subject = getGmailSubject();
        const from = getGmailSender();
        sendResponse({ content, subject, sender: from });
    }
});

function getGmailContent() {
    const selectors = ['.ii.gt', '.a3s.aiL', '[role="presentation"]', '.msg-body'];
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return element.innerText.trim();
        }
    }
    return 'No email content found';
}

function getGmailSubject() {
    const selectors = ['.hP', '[data-thread-perm-id]', '.subject'];
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return element.innerText.trim();
        }
    }
    return 'No subject found';
}

function getGmailSender() {
    const selectors = ['.gD', '.GO', '[email]'];
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return element.innerText.trim() || element.getAttribute('email') || 'Unknown sender';
        }
    }
    return 'Unknown sender';
}