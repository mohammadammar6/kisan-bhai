const updateLang = document.documentElement.lang === "hi" ? "hi-IN" : "en-IN";

function makeExternalLink(url, label, className = "") {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "https:") return null;
    const link = document.createElement("a");
    link.href = parsed.href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = label;
    if (className) link.className = className;
    return link;
  } catch {
    return null;
  }
}

function renderFarmerNews(items) {
  const root = document.getElementById("farmerNews");
  root.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "text-muted mb-0";
    empty.textContent = updateLang === "hi-IN"
      ? "इस राज्य के लिए अभी समाचार उपलब्ध नहीं हैं। बाद में फिर देखें।"
      : "No recent headlines found for this state. Please check again later.";
    root.append(empty);
    return;
  }

  for (const item of items) {
    const article = document.createElement("article");
    article.className = "farmer-news-item";
    const link = makeExternalLink(item.url, item.title, "farmer-news-title");
    if (link) article.append(link);
    const meta = document.createElement("div");
    meta.className = "farmer-news-meta";
    const source = document.createElement("span");
    source.textContent = item.source || (updateLang === "hi-IN" ? "समाचार स्रोत" : "News source");
    meta.append(source);
    if (item.published) {
      const date = new Date(item.published);
      if (!Number.isNaN(date.getTime())) {
        const time = document.createElement("time");
        time.dateTime = date.toISOString();
        time.textContent = new Intl.DateTimeFormat(updateLang, { day: "numeric", month: "short" }).format(date);
        meta.append(time);
      }
    }
    article.append(meta);
    root.append(article);
  }
}

function renderFarmerSchemes(items) {
  const root = document.getElementById("farmerSchemes");
  root.replaceChildren();
  for (const item of items) {
    const row = document.createElement("article");
    row.className = `farmer-scheme-item ${item.kind === "state" ? "state-scheme" : ""}`;
    const link = makeExternalLink(item.url, item.title, "farmer-scheme-title");
    if (link) row.append(link);
    const description = document.createElement("p");
    description.textContent = item.description;
    row.append(description);
    const arrow = document.createElement("span");
    arrow.className = "scheme-arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "↗";
    row.append(arrow);
    root.append(row);
  }
}

async function loadFarmerUpdates() {
  const content = document.getElementById("farmerUpdatesContent");
  if (!content || content.hidden) return;
  const newsRoot = document.getElementById("farmerNews");
  const schemesRoot = document.getElementById("farmerSchemes");
  try {
    const response = await fetch("/api/farmer-updates", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("Updates request failed");
    const data = await response.json();
    document.getElementById("farmerUpdatesSubtitle").textContent = updateLang === "hi-IN"
      ? `${data.state_display} के लिए कृषि समाचार और आधिकारिक योजना लिंक।`
      : `Agriculture headlines and official scheme links for ${data.state_display}.`;
    renderFarmerNews(data.news || []);
    renderFarmerSchemes(data.schemes || []);
  } catch {
    newsRoot.textContent = updateLang === "hi-IN"
      ? "समाचार अभी लोड नहीं हो पाए। कृपया बाद में फिर प्रयास करें।"
      : "News could not be loaded right now. Please try again later.";
    schemesRoot.textContent = updateLang === "hi-IN"
      ? "योजना लिंक लोड नहीं हो पाए।"
      : "Scheme links could not be loaded.";
  }
}

window.addEventListener("load", loadFarmerUpdates);
