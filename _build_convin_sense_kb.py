"""
Build a Convin Sense knowledge base from the official convin.ai website.
Scrapes product, solution, pricing, and integration pages, then runs a
2-pass Claude extraction and merges results into kb_store.json.
"""
import json, re, os, sys, time
import requests
from bs4 import BeautifulSoup
import anthropic

# ── API key ───────────────────────────────────────────────────────
api_key = ""
secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
with open(secrets_path) as f:
    for line in f:
        if "ANTHROPIC_API_KEY" in line:
            api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
if not api_key:
    sys.exit("No ANTHROPIC_API_KEY found")

client = anthropic.Anthropic(api_key=api_key)
HEADERS = {"User-Agent": "Mozilla/5.0 (ConvinBot/1.0)"}
MAX_CTX = 560_000
BATCH   = 4

# ── Pages to scrape ───────────────────────────────────────────────
PAGES = [
    # Core product
    ("https://convin.ai/",                                                   "Convin Platform Overview"),
    ("https://convin.ai/product/product-overview",                           "Convin Products Overview"),
    ("https://convin.ai/product/automated-virtual-ai-agents",               "AI Phone Call Agent"),
    ("https://convin.ai/product/real-time-assist-agent",                     "Real-Time Assist Agent"),
    ("https://convin.ai/product/contact-center-conversation-intelligence",   "Conversation Intelligence"),
    ("https://convin.ai/product/automated-quality-management",               "Automated Quality Management"),
    ("https://convin.ai/product/convin-insights",                            "Convin Insights – Voice of Customer"),
    ("https://convin.ai/product/coaching",                                   "Convin Coaching"),
    ("https://convin.ai/product/learning-management-system",                 "Convin LMS"),
    # Pricing & company
    ("https://convin.ai/pricing",                                            "Convin Pricing"),
    ("https://convin.ai/about-us",                                           "About Convin"),
    ("https://convin.ai/integrations",                                       "Convin Integrations"),
    # Use cases
    ("https://convin.ai/solutions/use-case/convin-for-sales",                "Convin for Sales"),
    ("https://convin.ai/solutions/use-case/convin-for-customer-success",     "Convin for Customer Success"),
    ("https://convin.ai/solutions/use-case/convin-for-collections",          "Convin for Collections"),
    ("https://convin.ai/solutions/use-case/convin-for-compliance",           "Convin for Compliance"),
    ("https://convin.ai/solutions/use-case/lead-qualification",              "Lead Qualification"),
    ("https://convin.ai/solutions/use-case/convin-for-retention",            "Customer Retention"),
    # Industries
    ("https://convin.ai/solutions/industry/healthcare",                      "Convin for Healthcare"),
    ("https://convin.ai/solutions/industry/banking",                         "Convin for Banking & Finance"),
    ("https://convin.ai/solutions/industry/bpo",                             "Convin for BPOs"),
    ("https://convin.ai/solutions/industry/insurance",                       "Convin for Insurance"),
    ("https://convin.ai/solutions/industry/home-services",                   "Convin for Home Services"),
    # Convin Sense (activate)
    ("https://activate.convin.ai/",                                          "Convin Sense – AI Sales Activation"),
]

# ── Scraper ───────────────────────────────────────────────────────
def scrape(url, label):
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        if r.status_code != 200:
            print(f"  ⚠  {r.status_code} — {url}")
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script","style","nav","footer","header","aside","noscript","svg"]):
            t.decompose()
        text = "\n".join(
            p.get_text(" ", strip=True)
            for p in soup.find_all(["h1","h2","h3","h4","h5","p","li","td","blockquote","span"])
            if len(p.get_text(strip=True)) > 25
        )
        return {"url": url, "title": label, "content": text[:22000], "size": len(text[:22000])}
    except Exception as e:
        print(f"  ✗ {url}: {e}")
        return None

print(f"Scraping {len(PAGES)} pages …")
pages = []
for i, (url, label) in enumerate(PAGES):
    pg = scrape(url, label)
    if pg:
        pages.append(pg)
        print(f"  [{i+1}/{len(PAGES)}] ✓ {label} ({pg['size']:,} ch)")
    time.sleep(0.3)
print(f"\nScraped {len(pages)} pages, {sum(p['size'] for p in pages):,} total chars\n")

# ── Claude extraction ─────────────────────────────────────────────
def _extract(prompt: str) -> list[dict]:
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt, "cache_control": {"type": "ephemeral"}}
        ]}],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )
    raw = re.sub(r"^```[a-z]*\n?", "", r.content[0].text.strip())
    raw = re.sub(r"\n?```$", "", raw)
    try:
        items = json.loads(raw)
    except:
        pairs = re.findall(r'"question"\s*:\s*"([^"]+)"[^}]*"answer"\s*:\s*"([^"]+)"', raw)
        return [{"category": "Convin Platform", "question": q, "answer": a} for q, a in pairs]
    return [
        {
            "category": str(i.get("category", "Convin Platform")),
            "question":  str(i.get("question", i.get("q", ""))),
            "answer":    str(i.get("answer",   i.get("a", ""))),
        }
        for i in items if isinstance(i, dict) and i.get("question")
    ]

RULES = (
    "Rules:\n"
    "• ONLY facts from the content — no inventions.\n"
    "• EXHAUSTIVE — every feature, metric, use case, integration, pricing model, and process.\n"
    "• Answers: 2–5 clear sentences.\n"
    "• Use SPECIFIC category names matching the product area (e.g. 'AI Phone Call Agent',\n"
    "  'Real-Time Assist', 'Conversation Intelligence', 'Auto QA', 'Convin Insights',\n"
    "  'Pricing & Plans', 'Integrations', 'Company & Background', 'Sales Use Case',\n"
    "  'Healthcare', 'Banking & Finance', 'Compliance', etc.).\n"
    "• Return ONLY raw JSON: [{\"category\":\"...\",\"question\":\"...\",\"answer\":\"...\"},...]\n"
    "Extract the MAXIMUM number of Q&A pairs.\n\n"
)

all_new = []
batches = [pages[i:i+BATCH] for i in range(0, len(pages), BATCH)]

for bi, batch in enumerate(batches):
    ctx = "\n\n".join(
        f"=== PAGE: {p['title']} ===\nURL: {p['url']}\n\n{p['content']}"
        for p in batch
    )[:MAX_CTX]
    titles = " / ".join(p['title'][:35] for p in batch)
    print(f"\nBatch {bi+1}/{len(batches)}: {titles}")

    # Pass A — Features, metrics, definitions, integrations, pricing
    print("  Pass A (features, metrics, pricing, integrations)…")
    fa = _extract(
        "You are extracting a comprehensive knowledge base about the Convin AI platform.\n\n"
        "EXTRACT ALL of:\n"
        "• Product features and capabilities\n"
        "• Performance metrics and stats (27% CSAT, 60% lead automation, etc.)\n"
        "• Pricing models and plans\n"
        "• Integration partners and how they connect\n"
        "• Technical definitions and how things work\n"
        "• Company info, history, funding, and team\n\n"
        + RULES + "PAGES:\n" + ctx
    )
    print(f"    → {len(fa)} Q&As")
    all_new.extend(fa)

    # Pass B — Use cases, industries, scenarios, best practices
    print("  Pass B (use cases, industries, ROI, best practices)…")
    fb = _extract(
        "You are extracting scenario-based and industry knowledge from the Convin AI platform.\n\n"
        "EXTRACT ALL of:\n"
        "• Industry-specific use cases (healthcare, banking, insurance, BPO, home services)\n"
        "• Business use cases (sales, collections, compliance, retention, coaching)\n"
        "• ROI stories and quantified results\n"
        "• Best practices and setup recommendations\n"
        "• Troubleshooting and edge cases\n"
        "• What makes Convin different from alternatives\n\n"
        + RULES + "PAGES:\n" + ctx
    )
    print(f"    → {len(fb)} Q&As")
    all_new.extend(fb)

print(f"\n📊 Extracted {len(all_new)} Q&As from {len(pages)} pages")

# ── Merge into kb_store.json ──────────────────────────────────────
with open("kb_store.json") as f:
    kb = json.load(f)

# Add new pages to kb_links (skip existing URLs)
existing_urls = {l.get("url", "") for l in kb.get("kb_links", [])}
added_links = 0
for p in pages:
    if p["url"] not in existing_urls:
        kb.setdefault("kb_links", []).append({
            "url": p["url"], "title": p["title"],
            "content": p["content"],
            "added_at": "2026-04-17T00:00:00",
            "size": p["size"],
        })
        added_links += 1
print(f"📄 Added {added_links} new pages to kb_links")

# Merge + deduplicate all FAQs
combined = kb.get("kb_faqs", []) + all_new
seen, deduped = set(), []
for item in combined:
    k = item.get("question", "").lower().strip()
    if k and k not in seen:
        seen.add(k)
        deduped.append(item)

# Category breakdown
cats = {}
for i in deduped:
    cats[i["category"]] = cats.get(i["category"], 0) + 1
print(f"\n✅ Final: {len(deduped)} unique Q&As across {len(cats)} categories\n")
for cat, n in sorted(cats.items(), key=lambda x: -x[1])[:25]:
    print(f"   {n:>4}  {cat}")

kb["kb_faqs"] = deduped
with open("kb_store.json", "w") as f:
    json.dump(kb, f, ensure_ascii=False, indent=2)
print("\n💾 Saved to kb_store.json")
