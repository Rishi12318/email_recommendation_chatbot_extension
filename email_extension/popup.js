const DEFAULT_API_URL = "http://localhost:8000";

function getApiUrl() {
  return localStorage.getItem("api_url") || DEFAULT_API_URL;
}

function setApiUrl(url) {
  localStorage.setItem("api_url", url.replace(/\/+$/, ""));
}

function setStatus(text, type) {
  const el = document.getElementById("status");
  el.textContent = text;
  el.className = "badge";
  if (type === "ok") el.style.background = "#e8f5e9";
  else if (type === "error") el.style.background = "#ffebee";
  else if (type === "loading") el.style.background = "#fff3e0";
}

function showConfig() {
  document.getElementById("config-section").classList.toggle("visible");
}

async function extractEmailFromGmail() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) {
        resolve({ error: "No active tab" });
        return;
      }
      chrome.tabs.sendMessage(tabs[0].id, { action: "extractEmail" }, (response) => {
        if (chrome.runtime.lastError || !response || !response.email) {
          resolve({ error: "Could not extract email. Open an email in Gmail first." });
          return;
        }
        resolve({ email: response.email });
      });
    });
  });
}

async function getRecommendation(emailText) {
  const apiUrl = getApiUrl();
  const response = await fetch(`${apiUrl}/api/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: emailText }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `API error ${response.status}`);
  }
  return response.json();
}

document.addEventListener("DOMContentLoaded", () => {
  const apiInput = document.getElementById("api-url");
  apiInput.value = getApiUrl();

  document.getElementById("save-config").addEventListener("click", () => {
    setApiUrl(apiInput.value);
    setStatus("Config saved", "ok");
    setTimeout(() => setStatus("Ready", "ok"), 1500);
  });

  document.getElementById("extract-btn").addEventListener("click", async () => {
    setStatus("Extracting...", "loading");
    const result = await extractEmailFromGmail();
    if (result.error) {
      setStatus("Error", "error");
      document.getElementById("email-preview").innerHTML =
        `<p style="color:#c62828;font-size:12px">${result.error}</p>`;
      return;
    }
    const preview = document.getElementById("email-preview");
    preview.textContent = result.email;
    preview.dataset.emailText = result.email;
    document.getElementById("recommend-btn").disabled = false;
    setStatus("Email extracted", "ok");
  });

  document.getElementById("recommend-btn").addEventListener("click", async () => {
    const emailText = document.getElementById("email-preview").dataset.emailText;
    if (!emailText) return;

    setStatus("Generating reply...", "loading");
    document.getElementById("recommend-btn").disabled = true;

    try {
      const data = await getRecommendation(emailText);
      document.getElementById("reply-box").textContent = data.recommendation;
      document.getElementById("meta-info").textContent =
        `Category: ${data.category} | Similar emails found: ${data.similar_emails}`;
      document.getElementById("result-section").style.display = "block";
      setStatus("Done", "ok");
    } catch (err) {
      setStatus("Error", "error");
      document.getElementById("reply-box").textContent = `Error: ${err.message}`;
      document.getElementById("result-section").style.display = "block";
    }

    document.getElementById("recommend-btn").disabled = false;
  });

  document.getElementById("copy-btn").addEventListener("click", () => {
    const text = document.getElementById("reply-box").textContent;
    navigator.clipboard.writeText(text).then(() => {
      setStatus("Copied!", "ok");
      setTimeout(() => setStatus("Ready", "ok"), 1200);
    });
  });
});
