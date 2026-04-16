"""
Standalone extraction runner — reads kb_store.json, calls Claude,
writes FAQs back to kb_store.json. Run once; results appear in the app.
"""
import json, re, os, sys

# ── Load secrets ──────────────────────────────────────────────────
secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
api_key = ""
try:
    with open(secrets_path) as f:
        for line in f:
            if "ANTHROPIC_API_KEY" in line:
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
except Exception as e:
    sys.exit(f"Could not read secrets.toml: {e}")

if not api_key:
    sys.exit("ANTHROPIC_API_KEY not found in secrets.toml")

import anthropic
client = anthropic.Anthropic(api_key=api_key)

# ── Load KB ───────────────────────────────────────────────────────
with open("kb_store.json") as f:
    kb = json.load(f)

MAX_CTX = 580_000

def _faq_call(prompt: str) -> list[dict]:
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
    except json.JSONDecodeError:
        pairs = re.findall(r'"question"\s*:\s*"([^"]+)"[^}]*"answer"\s*:\s*"([^"]+)"', raw)
        return [{"category": "General", "question": q, "answer": a} for q, a in pairs]
    return [
        {
            "category": str(i.get("category", "General")),
            "question":  str(i.get("question", i.get("q", ""))),
            "answer":    str(i.get("answer",   i.get("a", ""))),
        }
        for i in items if isinstance(i, dict) and i.get("question")
    ]

BASE_RULES = (
    "Rules:\n"
    "• Only facts from the content — no inventions.\n"
    "• EXHAUSTIVE — cover every topic, feature, process, policy, edge case, decision, and fact.\n"
    "• Each answer: 2–6 clear sentences or a short bullet list.\n"
    "• Group into specific, descriptive categories.\n"
    "• Return ONLY a raw JSON array (no markdown, no extra text):\n"
    '[\n  {"category":"Category Name","question":"Q?","answer":"A."},\n  ...\n]\n'
    "Extract the MAXIMUM possible Q&A pairs.\n\n"
)

all_faqs = []

# ── Pass 1: Documents ─────────────────────────────────────────────
docs = kb.get("kb_documents", [])
if docs:
    ctx = "\n\n".join(
        f"=== DOCUMENT: {d['name']} ===\n{d['content']}" for d in docs
    )[:MAX_CTX]
    print(f"📄 Processing {len(docs)} document(s)…")
    faqs = _faq_call(
        "You are extracting the maximum possible Q&As from uploaded documents.\n"
        "Read every sentence. Extract every question a user could ever ask.\n\n"
        + BASE_RULES + "DOCUMENTS:\n" + ctx
    )
    print(f"   → {len(faqs)} Q&As extracted")
    all_faqs.extend(faqs)

# ── Pass 2: Web links + crawled ───────────────────────────────────
web = kb.get("kb_links", []) + kb.get("kb_crawled", [])
if web:
    ctx = "\n\n".join(
        f"=== PAGE: {p.get('title', p.get('url',''))} ===\n{p['content']}"
        for p in web
    )[:MAX_CTX]
    print(f"🌐 Processing {len(web)} web page(s)…")
    faqs = _faq_call(
        f"You are extracting the maximum possible Q&As from {len(web)} web page(s).\n"
        "Read every sentence. Extract every question a user could ever ask.\n\n"
        + BASE_RULES + "WEB PAGES:\n" + ctx
    )
    print(f"   → {len(faqs)} Q&As extracted")
    all_faqs.extend(faqs)

# ── Pass 3: WhatsApp — only real WA exports ───────────────────────
_WA_PATTERNS = [
    re.compile(r"^\[(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\]\s+([^:]+):\s*(.*)"),
    re.compile(r"^(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s*[-–]\s*([^:]+):\s*(.*)"),
]

def _is_real_wa(content: str) -> bool:
    count = sum(
        1 for ln in content.split("\n")
        if any(p.match(ln.strip()) for p in _WA_PATTERNS)
    )
    return count >= 5

def _wa_meta(content: str) -> dict:
    msgs = []
    for ln in content.split("\n"):
        for pat in _WA_PATTERNS:
            m = pat.match(ln.strip())
            if m:
                msgs.append({"date": m.group(1), "time": m.group(2), "sender": m.group(3).strip()})
                break
    if not msgs:
        return {}
    participants = list(dict.fromkeys(m["sender"] for m in msgs))
    return {
        "participants": participants,
        "total": len(msgs),
        "date_range": f"{msgs[0]['date']} → {msgs[-1]['date']}",
    }

CITE_RULE = (
    "CITATION RULE — every answer MUST end with one of:\n"
    "  • '💬 [Name] on [Date] at [Time]'\n"
    "  • '💬 [Name1] asked, [Name2] replied on [Date]'\n"
    "  • '💬 Discussed by [Name1], [Name2] on [Date]'\n\n"
)

for chat in kb.get("kb_whatsapp", []):
    content = chat.get("content", "").strip()
    if not content or not _is_real_wa(content):
        print(f"⚠️  Skipping '{chat['name']}' — not a real WhatsApp export")
        continue

    meta = _wa_meta(content)
    plist = ", ".join(meta.get("participants", []))
    drange = meta.get("date_range", "")
    total_m = meta.get("total", 0)

    HEADER = (
        f"WhatsApp chat: {chat['name']}\n"
        f"Participants: {plist}\n"
        f"Date range: {drange}  |  Messages: {total_m}\n"
        "Each line: [DD/MM/YY HH:MM] Sender: Message\n\n"
    )

    print(f"💬 Chat '{chat['name']}' — Pass A (Q&As, decisions, actions)…")
    faqs_a = _faq_call(
        "You are a knowledge analyst deeply reading a WhatsApp conversation.\n\n"
        + HEADER + CITE_RULE
        + "EXTRACT (be exhaustive):\n\n"
        "TYPE 1 — QUESTIONS & ANSWERS\n"
        "Find every explicit question and its response. Also find implied questions "
        "(topic raised that others responded to).\n"
        "→ Category: 'WhatsApp: Questions & Answers'\n\n"
        "TYPE 2 — DECISIONS & AGREEMENTS\n"
        "Find everything agreed, confirmed, or decided. "
        "Look for: agreed/decided/confirmed/let's go with/we'll/done/sorted.\n"
        "→ Category: 'WhatsApp: Decisions & Agreements'\n\n"
        "TYPE 3 — ACTION ITEMS & TASKS\n"
        "Find every task assigned, promise made, next step, deadline. "
        "Look for: will do/I'll/please/can you/by [date]/follow up.\n"
        "→ Category: 'WhatsApp: Action Items & Tasks'\n\n"
        "Return ONLY raw JSON array.\n"
        "Extract the MAXIMUM Q&A pairs.\n\n"
        "CHAT:\n" + content[:MAX_CTX]
    )
    print(f"   → {len(faqs_a)} Q&As")
    all_faqs.extend(faqs_a)

    print(f"💬 Chat '{chat['name']}' — Pass B (knowledge, issues, insights)…")
    faqs_b = _faq_call(
        "You are a knowledge analyst deeply reading a WhatsApp conversation.\n\n"
        + HEADER + CITE_RULE
        + "EXTRACT (be exhaustive):\n\n"
        "TYPE 4 — INFORMATION & KNOWLEDGE SHARED\n"
        "Every fact, figure, process, instruction, contact, data point shared.\n"
        "→ Category: 'WhatsApp: Information & Knowledge'\n\n"
        "TYPE 5 — PROBLEMS & RESOLUTIONS\n"
        "Every issue, complaint, confusion raised and how it was resolved.\n"
        "→ Category: 'WhatsApp: Issues & Resolutions'\n\n"
        "TYPE 6 — BUSINESS & PRODUCT INSIGHTS\n"
        "Anything about clients, products, features, pricing, timelines, deals, strategy.\n"
        "→ Category: 'WhatsApp: Business & Product Insights'\n\n"
        "TYPE 7 — CONTEXT & BACKGROUND\n"
        "Background context, history, or explanations given about the situation or topic.\n"
        "→ Category: 'WhatsApp: Context & Background'\n\n"
        "Return ONLY raw JSON array.\n"
        "Extract the MAXIMUM Q&A pairs.\n\n"
        "CHAT:\n" + content[:MAX_CTX]
    )
    print(f"   → {len(faqs_b)} Q&As")
    all_faqs.extend(faqs_b)

# ── Deduplicate ───────────────────────────────────────────────────
seen = set()
deduped = []
for f in all_faqs:
    k = f["question"].lower().strip()
    if k and k not in seen:
        seen.add(k)
        deduped.append(f)

print(f"\n✅ Total: {len(deduped)} unique Q&As across "
      f"{len(set(f['category'] for f in deduped))} categories")

# ── Save back ─────────────────────────────────────────────────────
kb["kb_faqs"] = deduped
with open("kb_store.json", "w") as f:
    json.dump(kb, f, ensure_ascii=False, indent=2)

print("💾 Saved to kb_store.json — reload the app to see results.")
