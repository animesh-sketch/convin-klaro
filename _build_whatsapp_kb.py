"""
Parse Convin_Pilots_Chat.html → extract text + build KB Q&As → kb_store.json
"""
import json, re, os, sys, time
from datetime import datetime
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

client_ai = anthropic.Anthropic(api_key=api_key)

HTML_PATH = os.path.expanduser("~/Downloads/Convin_Pilots_Chat.html")
KB_PATH   = os.path.join(os.path.dirname(__file__), "kb_store.json")

# ── Parse HTML → messages ─────────────────────────────────────────
print("Parsing HTML chat…")
with open(HTML_PATH, encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

messages = []
current_date = ""

for el in soup.select(".date-divider, .msg-row"):
    classes = el.get("class", [])
    if "date-divider" in classes:
        span = el.find("span")
        if span:
            current_date = span.get_text(strip=True)
    elif "msg-row" in classes:
        sender_el = el.find(class_="sender")
        time_el   = el.find(class_="time")
        text_el   = el.find(class_="text")
        if not (sender_el and text_el):
            continue
        sender = sender_el.get_text(strip=True)
        time_  = time_el.get_text(strip=True) if time_el else ""
        text   = text_el.get_text(" ", strip=True)
        if not text or len(text) < 3:
            continue
        messages.append({"date": current_date, "time": time_, "sender": sender, "text": text})

print(f"Parsed {len(messages):,} messages from {current_date and messages[0]['date']} → {current_date}")

# ── Build WA-format text + meta ───────────────────────────────────
lines = [f"[{m['date']} {m['time']}] {m['sender']}: {m['text']}" for m in messages]
chat_text = "\n".join(lines)

participants = list(dict.fromkeys(m["sender"] for m in messages))
counts = {}
for m in messages:
    counts[m["sender"]] = counts.get(m["sender"], 0) + 1

meta = {
    "valid": True,
    "total": len(messages),
    "participants": participants,
    "msg_counts": counts,
    "first_date": messages[0]["date"] if messages else "",
    "last_date":  messages[-1]["date"] if messages else "",
    "date_range": f"{messages[0]['date']} → {messages[-1]['date']}" if messages else "",
}
print(f"Participants: {len(participants)} | Date range: {meta['date_range']}")

# ── Claude Q&A extraction ─────────────────────────────────────────
RULES = (
    "Rules:\n"
    "• ONLY facts from the messages — no inventions.\n"
    "• Focus on actionable insights: metrics, issues resolved, config decisions, client learnings.\n"
    "• Answers: 2–4 clear sentences.\n"
    "• Use SPECIFIC categories: 'Pilot Clients & Metrics', 'Product Issues & Bugs',\n"
    "  'Setup & Configuration', 'Client Objections & Responses', 'Feature Requests',\n"
    "  'Sales Process', 'Onboarding Learnings', 'Bot Performance'.\n"
    "• SKIP: greetings, scheduling, 'okay'/'noted', media omitted, trivial one-liners.\n"
    "• Return ONLY raw JSON: [{\"category\":\"...\",\"question\":\"...\",\"answer\":\"...\"},...]\n"
    "Extract the MAXIMUM number of useful Q&A pairs.\n\n"
)

def _extract(prompt: str) -> list[dict]:
    r = client_ai.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt, "cache_control": {"type": "ephemeral"}}
        ]}],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )
    raw = re.sub(r"^```[a-z]*\n?", "", r.content[0].text.strip())
    raw = re.sub(r"\n?```$", "", raw)
    try:
        items = json.loads(raw)
    except Exception:
        pairs = re.findall(r'"question"\s*:\s*"([^"]+)"[^}]*"answer"\s*:\s*"([^"]+)"', raw)
        return [{"category": "Pilot Clients & Metrics", "question": q, "answer": a} for q, a in pairs]
    return [
        {
            "category": str(i.get("category", "Pilot Clients & Metrics")),
            "question":  str(i.get("question", i.get("q", ""))),
            "answer":    str(i.get("answer",   i.get("a", ""))),
        }
        for i in items if isinstance(i, dict) and i.get("question")
    ]

CHUNK = 500
chunks = [lines[i:i+CHUNK] for i in range(0, len(lines), CHUNK)]
print(f"\nExtracting Q&As — {len(chunks)} chunks of ~{CHUNK} messages…")

all_new = []
for ci, chunk in enumerate(chunks):
    ctx = "\n".join(chunk)
    print(f"  Chunk {ci+1}/{len(chunks)} ({len(chunk)} msgs)…", end=" ", flush=True)
    qas = _extract(
        "You are building a knowledge base from Convin Sense internal pilot WhatsApp group messages.\n"
        "These are real conversations between Convin's sales, onboarding, and implementation teams\n"
        "about AI voice bot (Convin Sense) pilots at various clients.\n\n"
        "EXTRACT ALL of:\n"
        "• Client-specific pilot metrics (connectivity %, qualification %, conversion %)\n"
        "• Bugs, hallucination issues, and their resolutions\n"
        "• Bot configuration decisions and rationale\n"
        "• Client objections and how they were handled\n"
        "• What features/approaches worked well vs poorly\n"
        "• Onboarding and setup learnings per client\n"
        "• Feature requests and workarounds discovered\n"
        "• ROI discussions and business case data\n\n"
        + RULES + "MESSAGES:\n" + ctx
    )
    print(f"{len(qas)} Q&As")
    all_new.extend(qas)
    time.sleep(0.4)

print(f"\n📊 Total extracted: {len(all_new)} Q&As")

# ── Merge into kb_store.json ──────────────────────────────────────
with open(KB_PATH) as f:
    kb = json.load(f)

# Update kb_whatsapp — replace old entry for this file
wa_list = [w for w in kb.get("kb_whatsapp", []) if w.get("name") != "KB- WA"]
wa_list.append({
    "name":     "KB- WA",
    "content":  chat_text,
    "added_at": datetime.now().isoformat(),
    "size":     len(chat_text),
    "meta":     meta,
})
kb["kb_whatsapp"] = wa_list
print(f"💬 kb_whatsapp updated — {len(messages):,} messages, {len(chat_text):,} chars")

# Merge + deduplicate kb_faqs
combined = kb.get("kb_faqs", []) + all_new
seen, deduped = set(), []
for item in combined:
    k = item.get("question", "").lower().strip()
    if k and k not in seen:
        seen.add(k)
        deduped.append(item)

cats = {}
for i in deduped:
    cats[i["category"]] = cats.get(i["category"], 0) + 1

print(f"\n✅ Final KB: {len(deduped)} unique Q&As across {len(cats)} categories")
for cat, n in sorted(cats.items(), key=lambda x: -x[1])[:25]:
    print(f"   {n:>4}  {cat}")

kb["kb_faqs"] = deduped
with open(KB_PATH, "w") as f:
    json.dump(kb, f, ensure_ascii=False, indent=2)
print("\n💾 Saved to kb_store.json")
