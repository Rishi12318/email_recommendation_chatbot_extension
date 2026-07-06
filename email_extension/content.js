console.log('Email Assistant content script loaded');

function getEmailList() {
    const emails = [];
    const selectors = [
        'tr.zA', 'tr[role="row"]', '.zA', '[role="main"] .yW',
        'table[role="list"] tr', '.Cp tbody tr'
    ];
    let rows = null;
    for (const sel of selectors) {
        rows = document.querySelectorAll(sel);
        if (rows.length > 0) break;
    }
    if (!rows || rows.length === 0) return emails;
    for (const row of rows) {
        const sender = getText(row, '.yW .yX, .yW, [email]');
        const subjectEl = row.querySelector('.y6, .bog, [data-thread-id] span, .xY .y2');
        const subject = subjectEl ? subjectEl.textContent.trim() : '';
        const snippet = getText(row, '.y2, .xY, .tf');
        const date = getText(row, '.xW span, .xq span, .WA span');
        if (sender || subject) {
            emails.push({ sender, subject, snippet, date });
        }
    }
    return emails;
}

function getOpenEmail() {
    const selectors = {
        sender: ['.gD', '.GO', '[email]', '.gD span'],
        subject: ['.hP', '[data-thread-perm-id]', '.ha', '.hr'],
        body: ['.ii.gt', '.a3s.aiL', '[role="presentation"] .a3s', '.msg-body']
    };
    const sender = findText(selectors.sender);
    const subject = findText(selectors.subject);
    const body = findText(selectors.body);
    return { sender, subject, body };
}

function getText(parent, selector) {
    const el = parent.querySelector(selector);
    return el ? el.textContent.trim() : '';
}

function findText(selectors) {
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el) return el.textContent.trim();
    }
    return '';
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'scanInbox') {
        const list = getEmailList();
        sendResponse({ type: 'inbox', emails: list, count: list.length });
    } else if (request.action === 'getOpenEmail') {
        const email = getOpenEmail();
        sendResponse({ type: 'open', email });
    }
});
