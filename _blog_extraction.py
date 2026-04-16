"""
Blog extraction: scrape all convin.ai blog posts, run 2-pass FAQ extraction,
save results to kb_store.json.
"""
import json, re, os, sys, time
import requests
from bs4 import BeautifulSoup
import anthropic

# ── API key ───────────────────────────────────────────────────────
api_key = ""
with open(os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")) as f:
    for line in f:
        if "ANTHROPIC_API_KEY" in line:
            api_key = line.split("=",1)[1].strip().strip('"').strip("'")
if not api_key:
    sys.exit("No ANTHROPIC_API_KEY found")

client = anthropic.Anthropic(api_key=api_key)
HEADERS = {"User-Agent": "Mozilla/5.0 (ConvinBot/1.0)"}
MAX_CTX = 560_000
BATCH   = 4   # articles per Claude call

# ── Scrape helpers ────────────────────────────────────────────────
def scrape(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script","style","nav","footer","header","aside","noscript"]):
        t.decompose()
    title = (soup.title.string.strip() if soup.title else url)[:120]
    text = "\n".join(
        p.get_text(" ", strip=True)
        for p in soup.find_all(["h1","h2","h3","h4","h5","p","li","td","blockquote"])
        if len(p.get_text(strip=True)) > 20
    )
    return title, text[:20000]

# ── All blog URLs ─────────────────────────────────────────────────
BLOG_URLS = [
    "https://convin.ai/blog/after-hours-answering-operations-guide-escalations-dispatch",
    "https://convin.ai/blog/after-hours-answering-service-book-jobs",
    "https://convin.ai/blog/after-hours-answering-service-pricing",
    "https://convin.ai/blog/ai-phone-call",
    "https://convin.ai/blog/answering-service-cost-per-month",
    "https://convin.ai/blog/answering-service-cost-per-month-2026",
    "https://convin.ai/blog/automated-ai-calls-recover-unhappy-customers-using-online-reviews",
    "https://convin.ai/blog/best-after-hours-answering-service-what-to-look-for",
    "https://convin.ai/blog/call-answering-service-capture-every-lead",
    "https://convin.ai/blog/call-queue-management-rulebook-overflow-rules-callbacks",
    "https://convin.ai/blog/call-tracking-number-google-lsa-local-ads",
    "https://convin.ai/blog/call-tracking-pricing-models",
    "https://convin.ai/blog/crm-for-field-service-roi",
    "https://convin.ai/blog/customer-satisfaction-score-system-using-ai-follow-up-calls",
    "https://convin.ai/blog/electrician-answering-service-safety-intake-dispatch-rules",
    "https://convin.ai/blog/electricians-answering-checklist-multi-location-ops",
    "https://convin.ai/blog/field-service-management-software-evaluation",
    "https://convin.ai/blog/home-service-ai-calls-that-request-online-reviews-at-right-time",
    "https://convin.ai/blog/improve-customer-satisfaction-using-proactive-ai-phone-calls",
    "https://convin.ai/blog/office-managers-win-more-with-business-call-answering-service",
    "https://convin.ai/blog/plumber-answering-checklist-questions-non-negotiables",
    "https://convin.ai/blog/plumber-answering-service-what-ai-calls-must-capture",
    "https://convin.ai/blog/plumbing-answering-book-jobs-even-during-nights-weekends",
    "https://convin.ai/blog/service-agreement-sales-call-framework-for-home-service-teams",
    "https://convin.ai/blog/smarter-route-optimization-collect-availability-at-first-call",
]

# ── Scrape all pages ──────────────────────────────────────────────
print(f"Scraping {len(BLOG_URLS)} blog articles...")
pages = []
for i, url in enumerate(BLOG_URLS):
    try:
        title, text = scrape(url)
        pages.append({"url": url, "title": title, "content": text, "size": len(text)})
        print(f"  [{i+1}/{len(BLOG_URLS)}] ✓ {title[:60]} ({len(text):,} ch)")
    except Exception as e:
        print(f"  [{i+1}/{len(BLOG_URLS)}] ✗ {url[:60]}: {e}")
    time.sleep(0.25)

print(f"\nScraped {len(pages)} pages, {sum(p['size'] for p in pages):,} total chars\n")

# ── Claude extraction ──────────────────────────────────────────────
def _faq_call(prompt):
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        messages=[{"role":"user","content":[
            {"type":"text","text":prompt,"cache_control":{"type":"ephemeral"}}
        ]}],
        extra_headers={"anthropic-beta":"prompt-caching-2024-07-31"},
    )
    raw = re.sub(r"^```[a-z]*\n?","", r.content[0].text.strip())
    raw = re.sub(r"\n?```$","", raw)
    try:
        items = json.loads(raw)
    except:
        pairs = re.findall(r'"question"\s*:\s*"([^"]+)"[^}]*"answer"\s*:\s*"([^"]+)"', raw)
        return [{"category":"General","question":q,"answer":a} for q,a in pairs]
    return [
        {"category": str(i.get("category","General")),
         "question": str(i.get("question", i.get("q",""))),
         "answer":   str(i.get("answer",   i.get("a","")))}
        for i in items if isinstance(i,dict) and i.get("question")
    ]

all_new = []
batches = [pages[i:i+BATCH] for i in range(0, len(pages), BATCH)]

for bi, batch in enumerate(batches):
    ctx = "\n\n".join(
        f"=== BLOG: {p['title']} ===\nURL: {p['url']}\n\n{p['content']}"
        for p in batch
    )[:MAX_CTX]
    titles = " / ".join(p['title'][:40] for p in batch)
    print(f"Batch {bi+1}/{len(batches)}: {titles}")

    # Pass A — Factual Q&As, How-Tos, Definitions, Pricing
    print(f"  Pass A (facts, how-tos, definitions, pricing)...")
    fa = _faq_call(
        "You are a knowledge extraction expert analysing Convin Sense blog articles.\n\n"
        "EXTRACT EVERY possible Q&A. Cover ALL of:\n\n"
        "TYPE 1 — FACTUAL Q&As: What/Who/When/Where questions with direct answers\n"
        "TYPE 2 — HOW-TOs: How does X work? How do I set up Y? How to achieve Z?\n"
        "TYPE 3 — DEFINITIONS: What is X? What does Y mean? What is the difference between X and Y?\n"
        "TYPE 4 — PRICING & ROI: Any cost, pricing, plan, or ROI data → Category: 'Pricing & Costs'\n\n"
        "Rules:\n"
        "• EXHAUSTIVE — every fact, tip, stat, process, feature → Q&A\n"
        "• Category = the blog topic (e.g. 'After-Hours Answering', 'Call Tracking', 'AI Phone Calls')\n"
        "• Answers: 2–5 clear sentences\n"
        "• Return ONLY raw JSON: [{\"category\":\"...\",\"question\":\"...\",\"answer\":\"...\"},...]\n"
        "Extract MAXIMUM Q&A pairs.\n\n"
        "BLOGS:\n" + ctx
    )
    print(f"    → {len(fa)} Q&As")
    all_new.extend(fa)

    # Pass B — Scenarios, Use Cases, Best Practices, Troubleshooting
    print(f"  Pass B (scenarios, use cases, best practices, troubleshooting)...")
    fb = _faq_call(
        "You are a scenario and use-case analyst reading Convin Sense blog articles.\n\n"
        "EXTRACT scenario-based Q&As grounded in the blog content:\n\n"
        "TYPE 5 — REAL-WORLD SCENARIOS\n"
        "'What happens when a customer calls after hours?' / 'What should I do if an agent misses a call?'\n"
        "'How does Convin handle [situation]?' / 'What if a customer is unhappy?'\n"
        "→ Category: 'Real-World Scenarios'\n\n"
        "TYPE 6 — BUSINESS USE CASES\n"
        "'How can a plumbing company use Convin for [goal]?' / 'What results can an electrician expect?'\n"
        "'Which home service businesses benefit most from X?'\n"
        "→ Category: 'Business Use Cases'\n\n"
        "TYPE 7 — BEST PRACTICES & TIPS\n"
        "'What is the best way to handle overflow calls?' / 'Top tips for after-hours call management'\n"
        "'What mistakes to avoid when setting up call tracking?'\n"
        "→ Category: 'Best Practices & Tips'\n\n"
        "TYPE 8 — TROUBLESHOOTING & EDGE CASES\n"
        "'What if the AI misses a booking?' / 'How to handle angry customer calls?'\n"
        "'What to do when call volume spikes unexpectedly?'\n"
        "→ Category: 'Troubleshooting & Edge Cases'\n\n"
        "Rules:\n"
        "• Scenarios must come from actual blog content — no inventions\n"
        "• Answers: 2–5 sentences, actionable and specific\n"
        "• Return ONLY raw JSON: [{\"category\":\"...\",\"question\":\"...\",\"answer\":\"...\"},...]\n"
        "Extract MAXIMUM scenario Q&A pairs.\n\n"
        "BLOGS:\n" + ctx
    )
    print(f"    → {len(fb)} scenarios")
    all_new.extend(fb)

print(f"\n📊 Blog extraction: {len(all_new)} new Q&As from {len(pages)} articles")

# ── Load existing KB + merge ───────────────────────────────────────
with open("kb_store.json") as f:
    kb = json.load(f)

# Add blog pages to kb_links (skip duplicates)
existing_urls = {l.get("url","") for l in kb.get("kb_links",[])}
added = 0
for p in pages:
    if p["url"] not in existing_urls:
        kb.setdefault("kb_links",[]).append({
            "url": p["url"], "title": p["title"],
            "content": p["content"],
            "added_at": "2026-04-17T00:00:00",
            "size": p["size"],
        })
        added += 1
print(f"📄 Added {added} new blog pages to KB links")

# Merge + deduplicate FAQs
combined = kb.get("kb_faqs",[]) + all_new
seen, deduped = set(), []
for item in combined:
    k = item["question"].lower().strip()
    if k and k not in seen:
        seen.add(k); deduped.append(item)

print(f"✅ Final: {len(deduped)} unique Q&As across "
      f"{len(set(i['category'] for i in deduped))} categories\n")

# Print category breakdown
cats = {}
for i in deduped: cats[i["category"]] = cats.get(i["category"],0)+1
for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"   {n:>4}  {cat}")

kb["kb_faqs"] = deduped
with open("kb_store.json","w") as f:
    json.dump(kb, f, ensure_ascii=False, indent=2)
print("\n💾 Saved to kb_store.json — restart the app to see results.")
