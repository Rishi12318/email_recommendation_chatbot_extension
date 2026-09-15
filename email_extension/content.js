function extractEmailText() {
  const selectors = [
    ".a3s",
    "[data-message-id] .a3s",
    ".ii.gt .a3s",
    "div[role='listitem'] .a3s",
    ".bzrq .a3s",
  ];

  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el && el.innerText.trim().length > 10) {
      return el.innerText.trim();
    }
  }

  const allBodies = document.querySelectorAll(".a3s");
  if (allBodies.length > 0) {
    const last = allBodies[allBodies.length - 1];
    if (last.innerText.trim().length > 10) {
      return last.innerText.trim();
    }
  }

  return null;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "extractEmail") {
    const emailText = extractEmailText();
    if (emailText) {
      sendResponse({ email: emailText });
    } else {
      sendResponse({ email: null, error: "No email body found. Open an email in Gmail." });
    }
  }
  return true;
});
