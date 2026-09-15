const GMAIL_API_BASE = 'https://gmail.googleapis.com/gmail/v1/users/me';

function getAuthToken(interactive = false) {
    return new Promise((resolve, reject) => {
        chrome.identity.getAuthToken({ interactive }, (token) => {
            if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message));
                return;
            }
            if (!token) {
                reject(new Error('No auth token received'));
                return;
            }
            resolve(token);
        });
    });
}

function removeCachedAuthToken(token) {
    return new Promise((resolve) => {
        chrome.identity.removeCachedAuthToken({ token }, () => {
            resolve();
        });
    });
}

async function fetchWithAuth(url, token) {
    const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (response.status === 401) {
        await removeCachedAuthToken(token);
        throw new Error('Token expired');
    }
    if (!response.ok) {
        throw new Error(`Gmail API error: ${response.status}`);
    }
    return response.json();
}

function parseSender(rawFrom) {
    if (!rawFrom || rawFrom === 'Unknown') {
        return { name: 'Unknown', email: '' };
    }
    const match = rawFrom.match(/^"?(.+?)"?\s*<(.+?)>/);
    if (match) {
        return { name: match[1].trim(), email: match[2].trim() };
    }
    if (rawFrom.includes('@')) {
        return { name: rawFrom.split('@')[0].trim(), email: rawFrom.trim() };
    }
    return { name: rawFrom.trim(), email: '' };
}

function parseDate(rawDate) {
    if (!rawDate) {
        return { raw: '', iso: '', display: '' };
    }
    try {
        const dt = new Date(rawDate);
        if (isNaN(dt.getTime())) {
            return { raw: rawDate, iso: '', display: rawDate };
        }
        return {
            raw: rawDate,
            iso: dt.toISOString(),
            display: dt.toLocaleDateString('en-US', {
                year: 'numeric', month: 'short', day: 'numeric',
                hour: '2-digit', minute: '2-digit'
            })
        };
    } catch (e) {
        return { raw: rawDate, iso: '', display: rawDate };
    }
}

function extractBody(payload) {
    try {
        if (payload.parts) {
            for (const part of payload.parts) {
                if (part.mimeType === 'text/plain' && part.body && part.body.data) {
                    return atob(part.body.data.replace(/-/g, '+').replace(/_/g, '/'));
                }
                if (part.parts) {
                    const result = extractBody(part);
                    if (result) return result;
                }
            }
        }
        if (payload.body && payload.body.data) {
            return atob(payload.body.data.replace(/-/g, '+').replace(/_/g, '/'));
        }
    } catch (e) {
        console.error('Error extracting body:', e);
    }
    return '';
}

async function fetchEmailsViaApi(maxResults = 50) {
    let token;
    try {
        token = await getAuthToken(false);
    } catch (e) {
        try {
            token = await getAuthToken(true);
        } catch (e2) {
            return { error: 'Could not authenticate with Google. Please sign in with your Google account.' };
        }
    }

    const emails = [];
    let pageToken = null;
    let fetched = 0;

    try {
        while (fetched < maxResults) {
            const batchSize = Math.min(50, maxResults - fetched);
            let url = `${GMAIL_API_BASE}/messages?maxResults=${batchSize}&q=in:inbox`;
            if (pageToken) {
                url += `&pageToken=${pageToken}`;
            }

            let data;
            try {
                data = await fetchWithAuth(url, token);
            } catch (e) {
                if (e.message === 'Token expired') {
                    token = await getAuthToken(true);
                    data = await fetchWithAuth(url, token);
                } else {
                    throw e;
                }
            }

            const messages = data.messages || [];
            if (messages.length === 0) break;

            for (const msg of messages) {
                try {
                    const msgUrl = `${GMAIL_API_BASE}/messages/${msg.id}?format=full`;
                    const msgData = await fetchWithAuth(msgUrl, token);

                    const headers = {};
                    for (const h of (msgData.payload.headers || [])) {
                        headers[h.name] = h.value;
                    }

                    const body = extractBody(msgData.payload);
                    const sender = parseSender(headers.From || 'Unknown');
                    const dateInfo = parseDate(headers.Date || '');

                    emails.push({
                        id: msgData.id,
                        subject: headers.Subject || '(no subject)',
                        sender_name: sender.name,
                        sender_email: sender.email,
                        from: headers.From || 'Unknown',
                        date: dateInfo.raw,
                        date_iso: dateInfo.iso,
                        date_display: dateInfo.display,
                        snippet: msgData.snippet || '',
                        body: (body || '').substring(0, 2000)
                    });
                } catch (e) {
                    console.error('Error fetching message:', msg.id, e);
                    continue;
                }
            }

            fetched += messages.length;
            pageToken = data.nextPageToken;
            if (!pageToken) break;
        }

        return { emails, total: emails.length };
    } catch (e) {
        return { error: e.message };
    }
}

async function getUserProfile() {
    try {
        const token = await getAuthToken(false);
        const data = await fetchWithAuth(`${GMAIL_API_BASE}/profile`, token);
        return {
            email: data.emailAddress,
            name: data.emailAddress.split('@')[0]
        };
    } catch (e) {
        return null;
    }
}

if (typeof module !== 'undefined') {
    module.exports = { fetchEmailsViaApi, getUserProfile, getAuthToken };
}
