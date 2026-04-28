"""
Generate a standalone HTML one-pager with all FAQs + QNAs
formatted as a support-agent quick-reference sheet.
Run: python3 generate_onepager.py
Output: onepager.html
"""

import json, re, html, os

SRC  = os.path.join(os.path.dirname(__file__), "kb_store.json")
DEST = os.path.join(os.path.dirname(__file__), "onepager.html")

with open(SRC) as f:
    data = json.load(f)

faqs: list[dict] = data.get("kb_faqs", [])

# ── Group by category, preserving insertion order by count ───────────────────
cat_groups: dict[str, list[dict]] = {}
for item in faqs:
    cat = item.get("category", "General")
    cat_groups.setdefault(cat, []).append(item)

cat_order = sorted(cat_groups.keys(), key=lambda c: (
    0 if not c.startswith(("WhatsApp:", "Client Learnings:")) else
    1 if not c.startswith("Client Learnings:") else 2,
    -len(cat_groups[c])
))

SECTION_LABELS = {
    "general": "Product & General",
    "whatsapp": "WhatsApp",
    "learnings": "Client Learnings",
}


def section_of(cat: str) -> str:
    if cat.startswith("WhatsApp:"):
        return "whatsapp"
    if cat.startswith("Client Learnings:"):
        return "learnings"
    return "general"


def short_cat(cat: str) -> str:
    return cat.replace("WhatsApp: ", "").replace("Client Learnings: ", "")


def cat_id(cat: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", cat.lower()).strip("-")


def answer_html(raw: str) -> str:
    """Render numbered-step answers as a step list, otherwise as paragraphs."""
    raw = raw.strip()
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    if not lines:
        return ""
    step_re = re.compile(r"^\d+[\.\)]\s+(.+)$")
    if len(lines) > 1 and all(step_re.match(l) for l in lines):
        items = "".join(
            f'<li>{html.escape(step_re.match(l).group(1))}</li>'
            for l in lines
        )
        return f"<ol>{items}</ol>"
    bullet_re = re.compile(r"^[\-\•\*]\s+(.+)$")
    if len(lines) > 1 and all(bullet_re.match(l) for l in lines):
        items = "".join(
            f'<li>{html.escape(bullet_re.match(l).group(1))}</li>'
            for l in lines
        )
        return f"<ul>{items}</ul>"
    paras = "".join(f"<p>{html.escape(l)}</p>" for l in lines)
    return paras


# ── Build TOC entries ─────────────────────────────────────────────────────────
toc_html_parts = []
prev_section = None
for cat in cat_order:
    sec = section_of(cat)
    if sec != prev_section:
        label = SECTION_LABELS[sec]
        toc_html_parts.append(f'<div class="toc-section-label">{html.escape(label)}</div>')
        prev_section = sec
    cid = cat_id(cat)
    count = len(cat_groups[cat])
    sc = short_cat(cat)
    toc_html_parts.append(
        f'<a href="#{cid}" class="toc-link" data-cat="{html.escape(cid)}">'
        f'{html.escape(sc)}'
        f'<span class="toc-count">{count}</span>'
        f'</a>'
    )

toc_html = "\n".join(toc_html_parts)

# ── Build QA cards ───────────────────────────────────────────────────────────
cards_html_parts = []
for cat in cat_order:
    sec = section_of(cat)
    cid = cat_id(cat)
    sc = short_cat(cat)
    count = len(cat_groups[cat])

    sec_badge_map = {
        "whatsapp": '<span class="sec-badge badge-wa">WhatsApp</span>',
        "learnings": '<span class="sec-badge badge-cl">Client</span>',
        "general": '<span class="sec-badge badge-gen">Product</span>',
    }
    badge = sec_badge_map[sec]

    cards_html_parts.append(
        f'<section id="{cid}" class="cat-section" data-cat="{cid}">'
        f'<div class="cat-header">'
        f'{badge}'
        f'<h2 class="cat-title">{html.escape(sc)}</h2>'
        f'<span class="cat-count">{count} Q&amp;As</span>'
        f'</div>'
        f'<div class="qa-grid">'
    )
    for item in cat_groups[cat]:
        q = item.get("question", "").strip()
        a = item.get("answer", "").strip()
        if not q:
            continue
        a_body = answer_html(a) if a else "<p><em>No answer recorded.</em></p>"
        cards_html_parts.append(
            f'<div class="qa-card" data-q="{html.escape(q.lower())}" data-a="{html.escape(a.lower())}">'
            f'<div class="qa-q">{html.escape(q)}</div>'
            f'<div class="qa-a">{a_body}</div>'
            f'</div>'
        )
    cards_html_parts.append('</div></section>')

cards_html = "\n".join(cards_html_parts)

total_cats = len(cat_order)
total_faqs = len(faqs)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Convin Sense — Support Q&amp;A One-Pager</title>
<style>
/* ═══════════════════════════════════════════════════
   BASE
═══════════════════════════════════════════════════ */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --bg:        #0B0F1A;
  --surf1:     #111827;
  --surf2:     #1A2035;
  --surf3:     #0D1117;
  --accent:    #6366F1;
  --accent-lt: #818CF8;
  --cyan:      #22D3EE;
  --green:     #10B981;
  --amber:     #F59E0B;
  --pink:      #EC4899;
  --txt1:      #E5E7EB;
  --txt2:      #94A3B8;
  --txt3:      #475569;
  --border:    rgba(255,255,255,0.06);
  --border-acc:rgba(99,102,241,0.22);
  --nav-h:     56px;
  --sidebar-w: 260px;
}}

html {{ scroll-behavior: smooth; }}
body {{
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--txt1);
  font-size: 14px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}}

a {{ color: inherit; text-decoration: none; }}

/* ═══════════════════════════════════════════════════
   TOP NAV
═══════════════════════════════════════════════════ */
.topnav {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: var(--nav-h);
  background: rgba(11,15,26,0.92);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  gap: 16px;
}}
.topnav-brand {{
  display: flex; align-items: center; gap: 10px; white-space: nowrap;
}}
.topnav-brand .logo {{
  width: 28px; height: 28px; border-radius: 8px;
  background: linear-gradient(135deg, var(--accent), #8B5CF6);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 800; color: #fff;
}}
.topnav-brand .name {{
  font-size: 1rem; font-weight: 700; color: var(--txt1);
}}
.topnav-brand .badge {{
  font-size: 0.68rem; font-weight: 600; color: var(--accent-lt);
  background: rgba(99,102,241,0.12); border: 1px solid var(--border-acc);
  padding: 2px 8px; border-radius: 20px;
}}
.topnav-search {{
  flex: 1; max-width: 480px;
  position: relative;
}}
.topnav-search input {{
  width: 100%; height: 36px; padding: 0 12px 0 36px;
  background: var(--surf2); border: 1px solid var(--border);
  border-radius: 8px; color: var(--txt1); font-size: 0.85rem;
  outline: none; transition: border-color .15s;
}}
.topnav-search input::placeholder {{ color: var(--txt3); }}
.topnav-search input:focus {{ border-color: var(--accent-lt); }}
.topnav-search .icon {{
  position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
  color: var(--txt3); font-size: 15px; pointer-events: none;
}}
.topnav-right {{
  display: flex; gap: 12px; align-items: center; white-space: nowrap;
}}
.topnav-stats {{
  display: flex; gap: 10px; align-items: center;
}}
.stat-chip {{
  font-size: 0.72rem; color: var(--txt2);
  background: var(--surf2); border: 1px solid var(--border);
  padding: 4px 10px; border-radius: 20px;
}}
.stat-chip b {{ color: var(--accent-lt); }}

.dl-btn {{
  display: flex; align-items: center; gap: 6px;
  height: 34px; padding: 0 14px;
  background: linear-gradient(135deg, var(--accent), #8B5CF6);
  color: #fff; font-size: 0.78rem; font-weight: 600;
  border: none; border-radius: 8px; cursor: pointer;
  text-decoration: none; white-space: nowrap;
  transition: opacity .15s, transform .1s;
}}
.dl-btn:hover {{ opacity: .88; transform: translateY(-1px); }}
.dl-btn:active {{ transform: translateY(0); opacity: 1; }}

/* ═══════════════════════════════════════════════════
   LAYOUT
═══════════════════════════════════════════════════ */
.layout {{
  display: flex;
  margin-top: var(--nav-h);
  min-height: calc(100vh - var(--nav-h));
}}

/* ═══════════════════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════════════════ */
.sidebar {{
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  position: sticky; top: var(--nav-h);
  height: calc(100vh - var(--nav-h));
  overflow-y: auto; overflow-x: hidden;
  background: var(--surf1);
  border-right: 1px solid var(--border);
  padding: 16px 0 32px;
  scrollbar-width: thin;
  scrollbar-color: var(--surf2) transparent;
}}
.sidebar::-webkit-scrollbar {{ width: 4px; }}
.sidebar::-webkit-scrollbar-thumb {{ background: var(--surf2); border-radius: 4px; }}

.toc-section-label {{
  font-size: 0.63rem; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--txt3);
  padding: 14px 16px 4px;
}}
.toc-link {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 16px;
  font-size: 0.78rem; color: var(--txt2);
  border-left: 2px solid transparent;
  transition: all .12s; cursor: pointer; gap: 6px;
}}
.toc-link:hover {{ color: var(--txt1); background: var(--surf2); }}
.toc-link.active {{
  color: var(--accent-lt);
  border-left-color: var(--accent);
  background: rgba(99,102,241,0.08);
  font-weight: 500;
}}
.toc-count {{
  font-size: 0.68rem; color: var(--txt3);
  background: var(--surf2); border-radius: 10px; padding: 1px 6px;
  flex-shrink: 0;
}}

/* ═══════════════════════════════════════════════════
   MAIN CONTENT
═══════════════════════════════════════════════════ */
.main {{
  flex: 1; min-width: 0;
  padding: 32px 28px;
  max-width: 960px;
}}

/* ── Hero ── */
.hero {{
  margin-bottom: 32px;
  padding: 28px 28px 24px;
  background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.07));
  border: 1px solid var(--border-acc);
  border-radius: 16px;
}}
.hero-eyebrow {{
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--accent-lt); margin-bottom: 8px;
}}
.hero-title {{
  font-size: 1.75rem; font-weight: 800; color: var(--txt1);
  line-height: 1.2; margin-bottom: 8px;
}}
.hero-title span {{ color: var(--accent-lt); }}
.hero-sub {{
  font-size: 0.88rem; color: var(--txt2); margin-bottom: 16px; max-width: 600px;
}}
.hero-pills {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.pill {{
  font-size: 0.72rem; font-weight: 600; padding: 4px 12px; border-radius: 20px;
  border: 1px solid;
}}
.pill-v {{ color: #A78BFA; background: rgba(139,92,246,0.12); border-color: rgba(139,92,246,0.3); }}
.pill-c {{ color: #67E8F9; background: rgba(34,211,238,0.1);  border-color: rgba(34,211,238,0.25); }}
.pill-g {{ color: #6EE7B7; background: rgba(16,185,129,0.1);  border-color: rgba(16,185,129,0.25); }}
.pill-p {{ color: #F9A8D4; background: rgba(236,72,153,0.1);  border-color: rgba(236,72,153,0.25); }}

/* ── No results ── */
#no-results {{
  display: none; padding: 48px 0; text-align: center;
  color: var(--txt2); font-size: 0.9rem;
}}

/* ── Category section ── */
.cat-section {{ margin-bottom: 40px; }}
.cat-section.hidden {{ display: none; }}

.cat-header {{
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 14px; padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}}
.cat-title {{
  font-size: 1rem; font-weight: 700; color: var(--txt1);
  flex: 1;
}}
.cat-count {{
  font-size: 0.72rem; color: var(--txt3);
  background: var(--surf2); padding: 2px 8px; border-radius: 10px;
}}

.sec-badge {{
  font-size: 0.62rem; font-weight: 700; letter-spacing: 0.05em;
  text-transform: uppercase; padding: 2px 7px; border-radius: 4px;
  flex-shrink: 0;
}}
.badge-wa  {{ background: rgba(16,185,129,0.15); color: #6EE7B7; border: 1px solid rgba(16,185,129,0.3); }}
.badge-cl  {{ background: rgba(236,72,153,0.12); color: #F9A8D4; border: 1px solid rgba(236,72,153,0.25); }}
.badge-gen {{ background: rgba(99,102,241,0.12); color: #A78BFA; border: 1px solid rgba(99,102,241,0.25); }}

/* ── Q&A grid ── */
.qa-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 12px;
}}
.qa-card {{
  background: var(--surf1);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  transition: border-color .15s;
}}
.qa-card:hover {{ border-color: var(--border-acc); }}
.qa-card.hidden {{ display: none; }}

.qa-q {{
  font-size: 0.82rem; font-weight: 600; color: var(--accent-lt);
  margin-bottom: 8px; line-height: 1.4;
}}
.qa-a {{
  font-size: 0.8rem; color: var(--txt2); line-height: 1.6;
}}
.qa-a p {{ margin-bottom: 4px; }}
.qa-a p:last-child {{ margin-bottom: 0; }}
.qa-a ol, .qa-a ul {{
  padding-left: 18px; margin: 0;
}}
.qa-a li {{ margin-bottom: 3px; }}
.qa-a ol li {{ list-style: decimal; }}
.qa-a ul li {{ list-style: disc; }}

mark {{
  background: rgba(124,58,237,0.3);
  border-radius: 3px;
  padding: 0 2px;
  color: #EEF0FA;
}}

/* ═══════════════════════════════════════════════════
   PRINT
═══════════════════════════════════════════════════ */
@media print {{
  .topnav, .sidebar {{ display: none !important; }}
  .layout {{ display: block; }}
  .main {{ padding: 16px; max-width: 100%; }}
  .qa-grid {{ grid-template-columns: 1fr 1fr; }}
  .qa-card {{ break-inside: avoid; }}
  body {{ background: #fff; color: #111; }}
  .qa-q {{ color: #3730a3; }}
  .qa-a {{ color: #374151; }}
}}

/* ═══════════════════════════════════════════════════
   SCROLLBAR
═══════════════════════════════════════════════════ */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--surf2); border-radius: 4px; }}
</style>
</head>
<body>

<!-- ═══ TOP NAV ═══════════════════════════════════════ -->
<nav class="topnav">
  <div class="topnav-brand">
    <div class="logo">K</div>
    <span class="name">Convin Klaro</span>
    <span class="badge">Support Q&amp;A</span>
  </div>
  <div class="topnav-search">
    <span class="icon">&#128269;</span>
    <input type="search" id="search" placeholder="Search questions and answers…" autocomplete="off">
  </div>
  <div class="topnav-right">
    <div class="topnav-stats">
      <div class="stat-chip"><b>{total_faqs:,}</b> Q&amp;As</div>
      <div class="stat-chip"><b>{total_cats}</b> categories</div>
    </div>
    <button class="dl-btn" id="dl-btn" onclick="downloadPage()">
      &#8595; Download
    </button>
  </div>
</nav>

<!-- ═══ LAYOUT ═════════════════════════════════════════ -->
<div class="layout">

  <!-- SIDEBAR -->
  <aside class="sidebar" id="sidebar">
{toc_html}
  </aside>

  <!-- MAIN -->
  <div class="main">

    <!-- Hero -->
    <div class="hero">
      <div class="hero-eyebrow">&#10022; Convin Sense &nbsp;&middot;&nbsp; Support Intelligence</div>
      <div class="hero-title">Support <span>Q&amp;A</span> One-Pager</div>
      <div class="hero-sub">Every question a support agent needs — FAQs, client learnings, WhatsApp use cases, and product knowledge, all in one searchable sheet.</div>
      <div class="hero-pills">
        <span class="pill pill-v">&#10022; {total_faqs:,} Q&amp;As</span>
        <span class="pill pill-p">&#128193; {total_cats} Categories</span>
        <span class="pill pill-c">&#9889; Instant Search</span>
        <span class="pill pill-g">&#10003; Support-Agent Ready</span>
      </div>
    </div>

    <!-- No results -->
    <div id="no-results">No Q&amp;As match your search.</div>

    <!-- Q&A sections -->
{cards_html}

  </div><!-- .main -->
</div><!-- .layout -->

<script>
(function() {{
  const searchEl = document.getElementById('search');
  const sections = Array.from(document.querySelectorAll('.cat-section'));
  const cards    = Array.from(document.querySelectorAll('.qa-card'));
  const tocLinks = Array.from(document.querySelectorAll('.toc-link'));
  const noRes    = document.getElementById('no-results');

  function highlight(text, term) {{
    if (!term) return text;
    const esc = term.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
    return text.replace(new RegExp('(' + esc + ')', 'gi'), '<mark>$1</mark>');
  }}

  function renderSearch(term) {{
    const t = term.toLowerCase().trim();
    let visibleSections = 0;

    sections.forEach(sec => {{
      const sCards = sec.querySelectorAll('.qa-card');
      let visCount = 0;

      sCards.forEach(card => {{
        const q = card.dataset.q || '';
        const a = card.dataset.a || '';
        const match = !t || q.includes(t) || a.includes(t);

        if (match) {{
          card.classList.remove('hidden');
          if (t) {{
            card.querySelector('.qa-q').innerHTML = highlight(
              card.querySelector('.qa-q').textContent, t);
            card.querySelector('.qa-a').innerHTML = highlight(
              card.querySelector('.qa-a').textContent, t);
          }}
          visCount++;
        }} else {{
          card.classList.add('hidden');
          if (!t) {{
            card.querySelector('.qa-q').innerHTML = card.dataset.qOrig || card.querySelector('.qa-q').textContent;
            card.querySelector('.qa-a').innerHTML = card.dataset.aOrig || card.querySelector('.qa-a').textContent;
          }}
        }}
      }});

      if (visCount > 0) {{
        sec.classList.remove('hidden');
        visibleSections++;
      }} else {{
        sec.classList.add('hidden');
      }}
    }});

    noRes.style.display = visibleSections === 0 ? 'block' : 'none';
  }}

  // Cache original HTML for highlight restore
  cards.forEach(card => {{
    card.dataset.qOrig = card.querySelector('.qa-q').innerHTML;
    card.dataset.aOrig = card.querySelector('.qa-a').innerHTML;
  }});

  searchEl.addEventListener('input', function() {{
    renderSearch(this.value);
  }});

  // Active TOC highlight on scroll
  const observer = new IntersectionObserver((entries) => {{
    entries.forEach(entry => {{
      const id = entry.target.id;
      const link = document.querySelector(`.toc-link[data-cat="${{id}}"]`);
      if (!link) return;
      if (entry.isIntersecting) {{
        tocLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        link.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
      }}
    }});
  }}, {{ rootMargin: '-15% 0px -75% 0px' }});

  sections.forEach(sec => observer.observe(sec));

  // TOC click
  tocLinks.forEach(link => {{
    link.addEventListener('click', function(e) {{
      e.preventDefault();
      const target = document.getElementById(this.dataset.cat);
      if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }});
  }});
}})();

function downloadPage() {{
  const btn = document.getElementById('dl-btn');
  btn.textContent = 'Preparing…';
  btn.style.opacity = '0.7';

  // Capture full page HTML with all current state
  const html = '<!DOCTYPE html>\\n' + document.documentElement.outerHTML;
  const blob = new Blob([html], {{ type: 'text/html;charset=utf-8' }});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = 'convin-support-qna.html';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  setTimeout(() => {{
    btn.innerHTML = '&#8595; Download';
    btn.style.opacity = '1';
  }}, 1200);
}}
</script>
</body>
</html>"""

with open(DEST, "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"✅  Written {len(faqs):,} Q&As across {len(cat_order)} categories → {DEST}")
print(f"    File size: {os.path.getsize(DEST) / 1024:.0f} KB")
