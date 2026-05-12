import pandas as pd
import streamlit as st

from logic import analyze_listing, ai_reasoning

st.set_page_config(page_title="BuySense", layout="centered")

st.markdown("""
<style>
/* ── Background with purple glow ── */
html, body { background-color: #0D0E1C !important; }
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] > .main > .block-container {
    background: transparent !important;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse at 80% 100%, rgba(139,92,246,0.22) 0%, transparent 55%),
        radial-gradient(ellipse at 20% 95%,  rgba(59,130,246,0.10) 0%, transparent 45%),
        #0D0E1C !important;
    min-height: 100vh;
}
.block-container { padding-top: 3rem !important; max-width: 780px !important; }

/* ── Inputs ── */
.stTextArea textarea {
    background-color: #13152B !important;
    color: #E8EAF6 !important;
    border: 2px solid #3B5BDB !important;
    border-radius: 16px !important;
    font-size: 15px !important;
    padding: 16px !important;
    box-shadow: 0 0 18px rgba(59,91,219,0.35) !important;
    min-height: 100px !important;
    transition: border-color .2s, box-shadow .2s !important;
}
.stTextArea textarea:focus {
    border-color: #60A5FA !important;
    box-shadow: 0 0 26px rgba(96,165,250,0.45) !important;
}
.stTextInput input {
    background-color: #13152B !important;
    color: #E8EAF6 !important;
    border: 2px solid #1E2147 !important;
    border-radius: 16px !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
    transition: border-color .2s, box-shadow .2s !important;
}
.stTextInput input:focus {
    border-color: #3B5BDB !important;
    box-shadow: 0 0 18px rgba(59,91,219,0.3) !important;
}

/* ── Labels ── */
label, .stTextArea label, .stTextInput label {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    letter-spacing: 0.01em !important;
}
p { color: #C7D2FE; }

/* ── Buttons ── */
.stButton button {
    background-color: #13152B !important;
    color: #818CF8 !important;
    border: 1.5px solid #2A2D52 !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 12px 24px !important;
    transition: background .2s, border-color .2s, color .2s !important;
    width: 100%;
}
.stButton button:hover {
    background-color: #1E2147 !important;
    border-color: #3B5BDB !important;
    color: #A5B4FC !important;
}

/* ── Verdict badges ── */
.verdict-badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 14px;
}
.verdict-good { background-color: #052E16; color: #4ADE80; border: 1px solid #166534; }
.verdict-fair { background-color: #1C1700; color: #FCD34D; border: 1px solid #92400E; }
.verdict-bad  { background-color: #1F0A0A; color: #F87171; border: 1px solid #991B1B; }

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background-color: #13152B !important;
    border: 1.5px solid #1E2147 !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
}
[data-testid="stMetricValue"] { color: #E8EAF6 !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #6B7280 !important; font-size: 12px !important; }

/* ── Alerts / info boxes ── */
[data-testid="stAlert"] {
    background-color: #13152B !important;
    border-radius: 12px !important;
    border-left-color: #3B5BDB !important;
    color: #C7D2FE !important;
}

/* ── Expander ── */
details, [data-testid="stExpander"] {
    background-color: #13152B !important;
    border: 1px solid #1E2147 !important;
    border-radius: 12px !important;
}
summary, [data-testid="stExpander"] summary { color: #818CF8 !important; }

/* ── Divider ── */
hr { border-color: #1E2147 !important; margin: 1.5rem 0 !important; }

/* ── Caption / small text ── */
[data-testid="stCaptionContainer"], small { color: #4B5280 !important; }

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div { background-color: #1E2147 !important; }
[data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg, #3B5BDB, #60A5FA) !important; }

/* ── Summary table ── */
.summary-table { color: #E8EAF6 !important; }
.summary-table th { border-bottom: 2px solid #1E2147 !important; color: #6B7280 !important; }
.summary-table td { border-bottom: 1px solid #13152B !important; }
.summary-table tr.best-row td { background-color: #052E16 !important; }
.summary-table a { color: #93C5FD !important; }
.summary-table a:hover { color: #BFDBFE !important; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='"
    "text-align:center;"
    "background:linear-gradient(135deg,#818CF8 0%,#60A5FA 50%,#A78BFA 100%);"
    "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
    "background-clip:text;"
    "font-size:3.4rem;font-weight:800;letter-spacing:-0.02em;"
    "margin-bottom:6px;margin-top:1rem;"
    "'>BuySense</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#6B7280;font-size:1.05rem;margin-top:0;margin-bottom:2rem'>"
    "Is this actually a good deal?</p>",
    unsafe_allow_html=True,
)
st.write("")


def verdict_badge_html(verdict):
    cls = {
        "Good Deal": "verdict-good",
        "Fair":      "verdict-fair",
        "Overpriced":"verdict-bad",
    }.get(verdict, "verdict-fair")
    return f"<span class='verdict-badge {cls}'>{verdict}</span>"


def render_result(result):
    # AI-only path: no benchmark data but we can still show AI reasoning
    ai_only = result.get("error") and result.get("price") is not None
    if result.get("error") and not ai_only:
        st.error(result["error"])
        return

    if not ai_only:
        score = result["deal_score"]
        verdict = result["verdict"]
        lo, hi = result["market_range"]

        col_score, col_verdict = st.columns([1, 2])
        with col_score:
            st.metric("Deal Score", f"{score}/100")
        with col_verdict:
            st.write("")
            st.markdown(verdict_badge_html(verdict), unsafe_allow_html=True)
            st.caption(f"Confidence: {result['confidence_label']} ({result['confidence']:.2f})")

        st.progress(score / 100)

        m1, m2, m3 = st.columns(3)
        m1.metric("Listing Price", f"${result['price']}")
        m2.metric("Market Range", f"${lo}–${hi}")
        m3.metric("Category", result["category"].capitalize())

        st.info(f"**Suggested action:** {result['action']}")

    # AI reasoning (shown for all results when API key is set)
    ai_text = result.get("ai_reasoning")
    if ai_text:
        st.markdown("**AI Analysis**")
        st.write(ai_text)
    elif not ai_only and result.get("reasoning"):
        st.write(result["reasoning"].replace("$", r"\$"))

    if ai_only:
        st.caption("No benchmark data found — AI analysis based on general market knowledge.")

    if result.get("ai_data_fetched"):
        st.caption("New brand — AI looked up market data and saved it to the database.")

    if not ai_only:
        with st.expander("Extraction details"):
            st.write(f"**Product:** {result['product']}")
            st.write(f"**Brand:** {result['brand']}")
            st.write(f"**Condition:** {result['condition']}")


# ── Session state ────────────────────────────────────────────────────────────

if "listings" not in st.session_state:
    st.session_state.listings = [{"desc": "", "price": "", "result": None}]


def add_item():
    st.session_state.listings.append({"desc": "", "price": "", "result": None})


# ── Input forms ──────────────────────────────────────────────────────────────

for i, item in enumerate(st.session_state.listings):
    label = f"Product {i + 1}" if len(st.session_state.listings) > 1 else "Product"
    st.markdown(f"**{label}**")

    col_desc, col_price = st.columns([3, 1])
    with col_desc:
        item["desc"] = st.text_area(
            "Description",
            value=item["desc"],
            placeholder="e.g. Nike Air Force 1, worn twice",
            label_visibility="collapsed",
            key=f"desc_{i}",
            height=80,
        )
    with col_price:
        item["price"] = st.text_input(
            "Price ($)",
            value=item["price"],
            placeholder="e.g. 150",
            key=f"price_{i}",
        )

    if len(st.session_state.listings) > 1:
        st.write("")

st.write("")

col_analyze, col_add = st.columns([2, 1])
with col_analyze:
    analyze_clicked = st.button("Analyze", use_container_width=True)
with col_add:
    st.button("+ Add another product", on_click=add_item, use_container_width=True)

# ── Run analysis ─────────────────────────────────────────────────────────────

if analyze_clicked:
    active = [
        item for item in st.session_state.listings
        if item["desc"].strip() or item["price"].strip()
    ]
    with st.spinner("Analyzing..."):
        for item in active:
            combined = f"{item['desc'].strip()}, ${item['price'].strip()}" if item["price"].strip() else item["desc"].strip()
            result = analyze_listing(combined)
            ai_text, used_ai = ai_reasoning(combined, result)
            if used_ai:
                result["ai_reasoning"] = ai_text
            item["result"] = result
    for item in st.session_state.listings:
        if item not in active:
            item["result"] = None

# ── Results ──────────────────────────────────────────────────────────────────

results_to_show = [item for item in st.session_state.listings if item.get("result")]
if results_to_show:
    st.write("")
    st.markdown("---")

    # ── Summary table at the top (multi-product only) ─────────────────────────
    if len(results_to_show) > 1:
        scored_rows = []
        for i, item in enumerate(results_to_show):
            r = item["result"]
            if r.get("error") or r.get("deal_score") is None:
                continue
            scored_rows.append({
                "num": i + 1,
                "product": r.get("product") or "—",
                "price": f"${r['price']}",
                "range": f"${r['market_range'][0]}–${r['market_range'][1]}",
                "score": r["deal_score"],
                "verdict": r["verdict"],
            })

        if scored_rows:
            best_score = max(row["score"] for row in scored_rows)
            best_row = max(scored_rows, key=lambda r: r["score"])

            st.markdown("#### Summary")
            st.success(
                f"Best deal: #{best_row['num']} — {best_row['product']} "
                f"({best_row['score']}/100)"
            )

            # HTML table with anchor links on product names
            verdict_colors = {"Good Deal": "#4ADE80", "Fair": "#FCD34D", "Overpriced": "#F87171"}
            verdict_bg = {"Good Deal": "#0D3320", "Fair": "#2D2008", "Overpriced": "#2D0A0A"}

            parts = [
"<style>"
".summary-table{width:100%;border-collapse:collapse;font-size:14px;margin-bottom:12px}"
".summary-table th{text-align:left;padding:8px 12px;border-bottom:2px solid #E8DED1;color:gray;font-weight:500}"
".summary-table td{padding:8px 12px;border-bottom:1px solid #F0EBE3}"
".summary-table tr.best-row td{background-color:#D4EBD0}"
".summary-table a{color:#1a1a1a;text-decoration:underline;cursor:pointer}"
"</style>"
'<table class="summary-table">'
"<thead><tr>"
"<th>#</th><th>Product</th><th>Price</th><th>Market Range</th><th>Deal Score</th><th>Verdict</th>"
"</tr></thead><tbody>"
            ]
            for row in scored_rows:
                is_best = row["score"] == best_score
                row_class = ' class="best-row"' if is_best else ""
                vcolor = verdict_colors.get(row["verdict"], "#333")
                vbg = verdict_bg.get(row["verdict"], "#eee")
                parts.append(
                    f'<tr{row_class}>'
                    f'<td>{row["num"]}</td>'
                    f'<td><a href="#product-{row["num"]}">{row["product"]}</a></td>'
                    f'<td>{row["price"]}</td>'
                    f'<td>{row["range"]}</td>'
                    f'<td><strong>{row["score"]}/100</strong></td>'
                    f'<td><span style="background:{vbg};color:{vcolor};padding:3px 10px;'
                    f'border-radius:999px;font-weight:600">{row["verdict"]}</span></td>'
                    f'</tr>'
                )
            parts.append("</tbody></table>")
            st.markdown("".join(parts), unsafe_allow_html=True)
            st.markdown("---")

    # ── Individual product analyses ───────────────────────────────────────────
    for i, item in enumerate(results_to_show):
        r = item["result"]
        header = item["desc"][:60] + ("…" if len(item["desc"]) > 60 else "")

        if len(results_to_show) > 1:
            # Anchor sits 80px above the heading so the scroll lands with breathing room
            st.markdown(
                f'<div id="product-{i + 1}" style="position:relative;top:-80px;visibility:hidden;pointer-events:none;"></div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"#### Product {i + 1}: {header}")

        render_result(r)

        if i < len(results_to_show) - 1:
            st.markdown("---")
