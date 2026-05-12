import json
import os
import re

from data import pricing_db

BRANDS = ["nike", "jordan", "adidas", "new balance", "yeezy", "asics"]

HYPE_KEYWORDS = ["travis", "off-white", "limited", "collab", "rare", "fragment", "dior"]
MID_KEYWORDS = ["retro", "boost", "990", "2002r", "gel", "dunk", "sb"]

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data.py")


# ── Extraction helpers ────────────────────────────────────────────────────────

def tokenize(text):
    return text.lower().split()


def extract_price(text):
    # Prefer $-prefixed prices so "Boost 350 ... $220" picks $220, not the model number.
    match = re.search(r"\$\s*(\d{2,5})(?:\.\d{1,2})?", text)
    if match:
        return int(match.group(1))
    match = re.search(r"(?:price|asking|for)\s*\$?\s*(\d{2,5})", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def extract_condition(text):
    t = text.lower()
    if any(k in t for k in ["brand new", "bnib", "deadstock", "ds "]):
        return "new"
    if "new" in t and "like new" not in t:
        return "new"
    if any(k in t for k in ["worn", "used", "pre-owned", "preowned", "like new", "gently"]):
        return "used"
    return "unknown"


def extract_product(text):
    t = text.lower()
    # Check both hardcoded list and anything AI has already added to pricing_db
    all_brands = list(dict.fromkeys(BRANDS + list(pricing_db.keys())))
    for brand in all_brands:
        if brand in t:
            words = t.split()
            try:
                idx = next(i for i, w in enumerate(words) if w == brand.split()[0])
                model = " ".join(words[idx:idx + 4])
                return model
            except StopIteration:
                return brand
    return "unknown"


def extract_brand(product_or_text):
    t = product_or_text.lower()
    # Also check brands AI has already added to pricing_db
    all_brands = list(dict.fromkeys(BRANDS + list(pricing_db.keys())))
    for b in all_brands:
        if b in t:
            return b
    return None


def detect_category(text):
    t = text.lower()
    if any(k in t for k in HYPE_KEYWORDS):
        return "hype"
    if any(k in t for k in MID_KEYWORDS):
        return "mid"
    return "basic"


def get_market_range(brand, category, condition):
    if not brand or brand not in pricing_db:
        return None
    if category not in pricing_db[brand]:
        return None
    cond = condition if condition in ("new", "used") else "used"
    return pricing_db[brand][category].get(cond)


# ── Scoring ───────────────────────────────────────────────────────────────────

def compute_deal_score(price, market_range):
    lo, hi = market_range
    mid = (lo + hi) / 2
    spread = max(hi - lo, 1)
    delta = (price - mid) / spread
    score = 50 - (delta * 50 / 1.5)
    return int(max(0, min(100, round(score))))


def classify(score):
    if score >= 70:
        return "Good Deal"
    if score >= 40:
        return "Fair"
    return "Overpriced"


def suggested_action(score, price, market_range):
    lo, hi = market_range
    mid = round((lo + hi) / 2)
    if score >= 70:
        return "Buy — priced below the typical market range."
    if score >= 40:
        return f"Reasonable. Buy if you want it, or negotiate toward ~${lo}."
    return f"Walk away or negotiate down to ~${mid}."


def confidence(brand, category_known, condition):
    score = 0.0
    if brand:
        score += 0.5
    if category_known:
        score += 0.3
    if condition in ("new", "used"):
        score += 0.2
    return round(score, 2)


def confidence_label(c):
    if c >= 0.8:
        return "High"
    if c >= 0.5:
        return "Medium"
    return "Low"


# ── OpenAI helpers ────────────────────────────────────────────────────────────

def _get_openai_client():
    api_key = ""

    # 1. Streamlit Cloud secrets (used when deployed)
    try:
        import streamlit as st
        api_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        pass

    # 2. Local .env file (used when running locally)
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
        except ImportError:
            pass
        api_key = os.getenv("OPENAI_API_KEY", "").strip().strip('"')

    if not api_key or api_key == "paste-your-key-here":
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except ImportError:
        return None


def _write_pricing_db():
    """Rewrite data.py from the current in-memory pricing_db."""
    lines = ["# data.py\n", "\n", "pricing_db = {\n"]
    for brand, categories in pricing_db.items():
        lines.append(f'    "{brand}": {{\n')
        for cat, conditions in categories.items():
            lines.append(f'        "{cat}": {{\n')
            for cond, prices in conditions.items():
                lo, hi = prices
                lines.append(f'            "{cond}": ({lo}, {hi}),\n')
            lines.append("        },\n")
        lines.append("    },\n")
    lines.append("}\n")
    with open(_DATA_PATH, "w") as f:
        f.writelines(lines)


def ai_fetch_pricing(listing_text):
    """
    Ask GPT-4o to identify the brand and provide resale price ranges for all
    categories/conditions. Saves the result directly into data.py and updates
    pricing_db in memory so the normal scoring pipeline can use it immediately.
    Returns (brand, category, market_range) or (None, None, None) on failure.
    """
    client = _get_openai_client()
    if client is None:
        return None, None, None

    prompt = (
        "You are a resale market pricing expert. Given this product listing, "
        "identify the brand and provide realistic current USD resale price ranges.\n\n"
        f"Listing: {listing_text}\n\n"
        "Reply with ONLY a JSON object — no extra text — in this exact format:\n"
        "{\n"
        '  "brand": "brand_name_lowercase",\n'
        '  "detected_category": "basic|mid|hype",\n'
        '  "pricing": {\n'
        '    "basic": {"new": [min, max], "used": [min, max]},\n'
        '    "mid":   {"new": [min, max], "used": [min, max]},\n'
        '    "hype":  {"new": [min, max], "used": [min, max]}\n'
        "  }\n"
        "}\n\n"
        "Rules:\n"
        "- basic = standard/common models\n"
        "- mid = popular/sought-after models\n"
        "- hype = limited/collab/rare models\n"
        "- All prices in whole USD integers\n"
        "- Use current secondhand/resale market prices, not retail"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)

        brand = data["brand"].lower().strip()
        detected_category = data.get("detected_category", "basic")
        raw_pricing = data["pricing"]

        # Convert lists → tuples and store in pricing_db
        pricing_entry = {
            cat: {cond: tuple(prices) for cond, prices in conditions.items()}
            for cat, conditions in raw_pricing.items()
        }
        pricing_db[brand] = pricing_entry

        # Persist to data.py so it's available on next run
        _write_pricing_db()

        # Return the specific range for this listing
        condition_key = "used"  # will be refined by caller
        market_range = pricing_entry.get(detected_category, {}).get(condition_key)
        return brand, detected_category, market_range

    except Exception:
        return None, None, None


def ai_reasoning(listing_text, result):
    """
    GPT-4o explanation on top of the scored result. Falls back to the
    rule-based reasoning if the API key is missing or the call fails.
    """
    client = _get_openai_client()
    if client is None:
        return result.get("reasoning"), False

    if result.get("deal_score") is not None:
        lo, hi = result["market_range"]
        context = (
            f"Listing: {listing_text}\n"
            f"Brand: {result['brand']}, condition: {result['condition']}, "
            f"price: ${result['price']}\n"
            f"Market benchmark range: ${lo}–${hi} ({result['category']} category)\n"
            f"Deal score: {result['deal_score']}/100  |  Verdict: {result['verdict']}\n"
            f"Suggested action: {result['action']}"
        )
    else:
        context = (
            f"Listing: {listing_text}\n"
            f"No benchmark data available. Price: ${result.get('price')}. "
            "Use your knowledge of current resale market prices to evaluate this."
        )

    prompt = (
        "You are BuySense, a deal intelligence assistant for resale marketplaces. "
        "Given the listing info below, write a concise 2-3 sentence explanation of "
        "whether this is a good deal. Be specific: mention the price, why it is or "
        "isn't a good value, and what a buyer should do. Do not use dollar sign ($) "
        "symbols — write prices as e.g. 'USD 150' instead. "
        "Keep it conversational and direct.\n\n"
        + context
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip(), True
    except Exception:
        return result.get("reasoning"), False


# ── Main pipeline ─────────────────────────────────────────────────────────────

def analyze_listing(text):
    tokens = tokenize(text)
    price = extract_price(text)
    condition = extract_condition(text)
    product = extract_product(text)
    brand = extract_brand(product) or extract_brand(text)
    category = detect_category(text)

    result = {
        "tokens": tokens,
        "raw_text": text,
        "product": product,
        "brand": brand,
        "category": category,
        "condition": condition,
        "price": price,
        "market_range": None,
        "deal_score": None,
        "verdict": None,
        "reasoning": None,
        "ai_reasoning": None,
        "action": None,
        "confidence": None,
        "confidence_label": None,
        "error": None,
        "ai_data_fetched": False,
    }

    if price is None:
        result["error"] = "Could not find a price in the listing."
        return result

    market_range = get_market_range(brand, category, condition)

    # Unknown brand/product — ask AI to fetch price data and write it to data.py
    if market_range is None:
        ai_brand, ai_category, _ = ai_fetch_pricing(text)
        if ai_brand:
            # Re-run extraction with the newly stored brand data
            brand = ai_brand
            category = ai_category or category
            product = extract_product(text)
            market_range = get_market_range(brand, category, condition)
            result["brand"] = brand
            result["category"] = category
            result["product"] = product
            result["ai_data_fetched"] = True

    category_known = market_range is not None
    conf = confidence(brand, category_known, condition)
    result["confidence"] = conf
    result["confidence_label"] = confidence_label(conf)

    if market_range is None:
        result["error"] = "Could not determine market pricing for this item."
        return result

    lo, hi = market_range
    score = compute_deal_score(price, market_range)
    verdict = classify(score)
    action = suggested_action(score, price, market_range)

    reasoning = (
        f"This {condition} {brand} listing at ${price} compares to a typical "
        f"{category} resale range of ${lo}–${hi}. "
    )
    if price > hi:
        reasoning += "It's above the upper end of the range."
    elif price < lo:
        reasoning += "It's below the lower end of the range."
    else:
        reasoning += "It falls inside the expected market range."

    result.update({
        "market_range": market_range,
        "deal_score": score,
        "verdict": verdict,
        "reasoning": reasoning,
        "action": action,
    })
    return result
