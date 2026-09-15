console.log('Email Assistant content script loaded');

function getEmailList() {
    const emails = [];
    const rowSelectors = [
        'tr.zA',
        'tr[role="row"]',
        '[role="list"] tr',
        'table tbody tr',
        '.Cp tbody tr',
        '[role="main"] table tbody tr',
    ];
    let rows = null;
    for (const sel of rowSelectors) {
        rows = document.querySelectorAll(sel);
        if (rows.length > 0) break;
    }
    if (!rows || rows.length === 0) return emails;

    for (const row of rows) {
        const sender = extractSender(row);
        const subject = extractSubject(row);
        const date = extractDate(row);
        const snippet = extractSnippet(row);
        if (sender || subject) {
            emails.push({ sender, subject, snippet, date });
        }
    }
    return emails;
}

function extractSender(row) {
    const strategies = [
        () => {
            const el = row.querySelector('[email]');
            return el ? (el.getAttribute('email') || el.textContent.trim()) : '';
        },
        () => {
            const el = row.querySelector('.yW .yX, .yW');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = row.querySelector('.yP, .yW span[email], .zF');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = row.querySelector('td[role="gridcell"]:first-child span[email]');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const cells = row.querySelectorAll('td');
            if (cells.length > 0) {
                const el = cells[0].querySelector('span[bdo], span');
                return el ? el.textContent.trim() : '';
            }
            return '';
        },
        () => {
            const el = row.querySelector('[data-hovercard-with-id] span, [data-name]');
            return el ? el.textContent.trim() : '';
        },
    ];
    for (const fn of strategies) {
        const val = fn();
        if (val && val.length > 0 && val.length < 200) return val;
    }
    return '';
}

function extractSubject(row) {
    const strategies = [
        () => {
            const el = row.querySelector('.y6, .bog');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = row.querySelector('[data-thread-id] span');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = row.querySelector('.xY .y2');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = row.querySelector('td[role="gridcell"] span[class]');
            const text = el ? el.textContent.trim() : '';
            if (text && text.length > 5) return text;
            return '';
        },
        () => {
            const cells = row.querySelectorAll('td[role="gridcell"]');
            for (const cell of cells) {
                const spans = cell.querySelectorAll('span');
                for (const sp of spans) {
                    const text = sp.textContent.trim();
                    if (text.length > 10 && !text.includes('@')) return text;
                }
            }
            return '';
        },
    ];
    for (const fn of strategies) {
        const val = fn();
        if (val && val.length > 0) return val;
    }
    return '';
}

function extractDate(row) {
    const strategies = [
        () => {
            const el = row.querySelector('.xW span, .xq span, .WA span');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = row.querySelector('td[role="gridcell"] span[title]');
            return el ? (el.getAttribute('title') || el.textContent.trim()) : '';
        },
        () => {
            const el = row.querySelector('td[role="gridcell"]:last-child span');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const cells = row.querySelectorAll('td[role="gridcell"]');
            if (cells.length >= 2) {
                const lastCell = cells[cells.length - 1];
                const el = lastCell.querySelector('span');
                return el ? el.textContent.trim() : '';
            }
            return '';
        },
        () => {
            const el = row.querySelector('[data-hovercard-with-id] + td span');
            return el ? el.textContent.trim() : '';
        },
    ];
    for (const fn of strategies) {
        const val = fn();
        if (val && val.length > 0 && val.length < 50) return val;
    }
    return '';
}

function extractSnippet(row) {
    const strategies = [
        () => {
            const el = row.querySelector('.y2, .xY, .tf');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = row.querySelector('td[role="gridcell"] span[class*="snippet"]');
            return el ? el.textContent.trim() : '';
        },
    ];
    for (const fn of strategies) {
        const val = fn();
        if (val && val.length > 0) return val;
    }
    return '';
}

function getOpenEmail() {
    const senderStrategies = [
        () => {
            const el = document.querySelector('.gD, [email]');
            return el ? (el.getAttribute('email') || el.textContent.trim()) : '';
        },
        () => {
            const el = document.querySelector('.go, .gD span');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = document.querySelector('[data-hovercard-with-id]');
            return el ? el.textContent.trim() : '';
        },
    ];
    const subjectStrategies = [
        () => {
            const el = document.querySelector('.hP, [data-thread-perm-id]');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = document.querySelector('.ha, .hr');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = document.querySelector('h2, [role="heading"]');
            return el ? el.textContent.trim() : '';
        },
    ];
    const bodyStrategies = [
        () => {
            const el = document.querySelector('.ii.gt, .a3s.aiL');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = document.querySelector('[role="presentation"] .a3s');
            return el ? el.textContent.trim() : '';
        },
        () => {
            const el = document.querySelector('.msg-body, .a3s');
            return el ? el.textContent.trim() : '';
        },
    ];
    const dateStrategies = [
        () => {
            const el = document.querySelector('.g3 span[title]');
            return el ? (el.getAttribute('title') || el.textContent.trim()) : '';
        },
        () => {
            const el = document.querySelector('.g3 span');
            return el ? el.textContent.trim() : '';
        },
    ];

    const sender = findTextFromStrategies(senderStrategies);
    const subject = findTextFromStrategies(subjectStrategies);
    const body = findTextFromStrategies(bodyStrategies);
    const date = findTextFromStrategies(dateStrategies);
    return { sender, subject, body, date };
}

function findTextFromStrategies(strategies) {
    for (const fn of strategies) {
        try {
            const val = fn();
            if (val && val.length > 0) return val;
        } catch (e) {
            continue;
        }
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
