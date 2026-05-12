import json
import os
import re

from data import pricing_db

BRANDS = ["nike", "jordan", "adidas", "new balance", "yeezy", "asics"]

HYPE_KEYWORDS = ["travis", "off-white", "limited", "collab", "rare", "fragment", "dior"]
MID_KEYWORDS = ["retro", "boost", "990", "2002r", "gel", "dunk", "sb"]

# Model keywords → brand, for when the brand name isn't mentioned
MODEL_TO_BRAND = {
    # Nike
    "air force 1": "nike", "air force": "nike", "af1": "nike",
    "air max": "nike", "blazer": "nike", "cortez": "nike",
    "pegasus": "nike", "vaporfly": "nike", "react": "nike",
    # Jordan
    "air jordan": "jordan", "jordan 1": "jordan", "jordan 3": "jordan",
    "jordan 4": "jordan", "jordan 5": "jordan", "jordan 11": "jordan",
    "aj1": "jordan", "aj4": "jordan",
    # Adidas
    "ultraboost": "adidas", "ultra boost": "adidas",
    "yeezy": "adidas", "stan smith": "adidas", "superstar": "adidas",
    "nmd": "adidas", "gazelle": "adidas", "samba": "adidas",
    "forum": "adidas", "campus": "adidas",
    # New Balance
    "990": "new balance", "992": "new balance", "993": "new balance",
    "2002r": "new balance", "574": "new balance", "550": "new balance",
    "530": "new balance", "327": "new balance",
    # Asics
    "gel-kayano": "asics", "gel-nimbus": "asics", "gel-lyte": "asics",
    "gel kayano": "asics", "gel nimbus": "asics",
    # Converse
    "chuck taylor": "converse", "chuck 70": "converse",
    "all star": "converse", "one star": "converse",
    # Reebok
    "club c": "reebok", "classic leather": "reebok", "freestyle": "reebok",
    # Vans
    "old skool": "vans", "sk8-hi": "vans", "sk8 hi": "vans",
    "slip-on": "vans", "authentic": "vans",
    # Puma
    "suede classic": "puma", "rs-x": "puma", "clyde": "puma",
}

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data.py")


# ── Extraction helpers ────────────────────────────────────────────────────────

def tokenize(text):
    return text.lower().split()


def extract_price(text):
    # Prefer $-prefixed prices so "Boost 350 ... $220" picks $220, not the model number.
    match = re.search(r"\$\s*(\d{1,5})(?:\.\d{1,2})?", text)
    if match:
        return int(match.group(1))
    match = re.search(r"(?:price|asking|for)\s*\$?\s*(\d{1,5})", text, re.IGNORECASE)
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
    all_brands = list(dict.fromkeys(BRANDS + list(pricing_db.keys())))
    # Try to anchor on a brand word first
    for brand in all_brands:
        if brand in t:
            words = t.split()
            try:
                idx = next(i for i, w in enumerate(words) if w == brand.split()[0])
                return " ".join(words[idx:idx + 4])
            except StopIteration:
                return brand
    # Fall back to model keyword — grab that phrase + surrounding words
    for model in MODEL_TO_BRAND:
        if model in t:
            idx = t.index(model)
            snippet = t[max(0, idx - 0):idx + len(model) + 20].split(",")[0].strip()
            return snippet
    return "unknown"


def extract_brand(product_or_text):
    t = product_or_text.lower()
    all_brands = list(dict.fromkeys(BRANDS + list(pricing_db.keys())))
    # Direct brand name match
    for b in all_brands:
        if b in t:
            return b
    # Model keyword fallback — handles "Air Force 1" without "Nike" etc.
    for model, brand in MODEL_TO_BRAND.items():
        if model in t:
            return brand
    return None


def detect_category(text):
    t = text.lower()
    if any(k in t for k in HYPE_KEYWORDS):
        return "hype"
    if any(k in t for k in MID_KEYWORDS):
        return "mid"
    return "basic"


# Product type keywords — used for non-sneaker brands so Gucci bags ≠ Gucci shoes
PRODUCT_TYPE_KEYWORDS = {
    "sneakers": ["sneaker", "shoe", "trainer", "runner", "kicks",
                 "loafer", "heel", "stiletto", "pump", "wedge", "mule",
                 "sandal", "slide", "slipper", "boot", "bootie", "oxford",
                 "derby", "monk strap", "platform", "flat",
                 "air force", "air max", "dunk", "jordan", "yeezy", "ultraboost",
                 "chuck taylor", "old skool", "club c"],
    "bags":        ["bag", "purse", "handbag", "tote", "backpack", "clutch", "wallet",
                    "satchel", "crossbody", "duffle", "pouch"],
    "clothing":    ["shirt", "hoodie", "jacket", "pants", "jeans", "dress", "coat",
                    "tee", "sweater", "shorts", "cardigan", "sweatshirt", "blazer"],
    "electronics": ["iphone", "phone", "laptop", "headphone", "airpod", "earbud",
                    "watch", "camera", "tv", "ipad", "tablet", "console", "macbook"],
    "accessories": ["belt", "hat", "cap", "sunglasses", "glasses", "ring",
                    "necklace", "bracelet", "scarf", "gloves"],
    "watches":     ["watch", "timepiece", "rolex", "omega", "ap", "audemars"],
}

def detect_product_type(text):
    t = text.lower()
    for ptype, keywords in PRODUCT_TYPE_KEYWORDS.items():
        if any(k in t for k in keywords):
            return ptype
    return "general"


# Specific model keywords within a product type
# e.g. "ipad" inside "electronics" → stored as "electronics:ipad"
MODEL_TYPE_KEYWORDS = {
    "electronics": {
        "iphone":      ["iphone"],
        "ipad":        ["ipad"],
        "macbook":     ["macbook", "mac book"],
        "imac":        ["imac"],
        "airpods":     ["airpods", "airpod", "air pods"],
        "apple watch": ["apple watch"],
        "ps5":         ["ps5", "playstation 5"],
        "ps4":         ["ps4", "playstation 4"],
        "xbox":        ["xbox series", "xbox one"],
        "switch":      ["nintendo switch"],
        "galaxy":      ["galaxy s", "galaxy z", "galaxy a"],
        "pixel":       ["pixel phone", "google pixel"],
        "laptop":      ["laptop", "notebook"],
        "headphones":  ["headphones", "headphone", "over-ear", "on-ear"],
        "earbuds":     ["earbuds", "earbud", "in-ear", "galaxy buds"],
    },
    "sneakers": {
        # Specific sneaker models
        "air force 1":  ["air force 1", "af1"],
        "air max":      ["air max"],
        "dunk":         ["dunk low", "dunk high", "sb dunk"],
        "jordan 1":     ["jordan 1", "aj1"],
        "jordan 4":     ["jordan 4", "aj4"],
        "yeezy 350":    ["yeezy 350", "zebra", "beluga"],
        "yeezy 700":    ["yeezy 700"],
        "ultraboost":   ["ultraboost", "ultra boost"],
        "990":          ["990v3", "990v4", "990v5", "990v6"],
        # Footwear sub-types (for luxury/fashion brands)
        "sneaker":      ["sneaker", "trainer", "runner"],
        "heel":         ["heel", "stiletto", "pump"],
        "loafer":       ["loafer", "moccasin"],
        "boot":         ["boot", "bootie", "ankle boot"],
        "sandal":       ["sandal", "slide", "slipper", "mule"],
        "wedge":        ["wedge"],
        "platform":     ["platform shoe", "platform sneaker"],
        "oxford":       ["oxford", "derby", "monk strap"],
        "flat":         ["flat shoe", "ballet flat", "ballerina"],
    },
    "bags": {
        "tote":      ["tote bag", "tote"],
        "backpack":  ["backpack", "rucksack"],
        "crossbody": ["crossbody", "shoulder bag"],
        "clutch":    ["clutch"],
        "wallet":    ["wallet", "cardholder", "card holder"],
        "duffle":    ["duffle", "duffel"],
    },
    "clothing": {
        "hoodie":   ["hoodie", "hooded"],
        "jacket":   ["jacket", "coat", "parka", "bomber"],
        "jeans":    ["jeans", "denim"],
        "t-shirt":  ["t-shirt", "tee", "tshirt"],
        "shorts":   ["shorts"],
        "sweater":  ["sweater", "sweatshirt", "crewneck", "cardigan"],
    },
    "watches": {
        "submariner": ["submariner"],
        "datejust":   ["datejust"],
        "daytona":    ["daytona"],
        "speedmaster":["speedmaster"],
        "seamaster":  ["seamaster"],
        "royal oak":  ["royal oak"],
    },
}


def detect_model_type(text, product_type):
    """
    Return a specific model within a product type.
    First tries hardcoded keywords (fast, no API call).
    Falls back to GPT for anything not in the keyword table.
    """
    t = text.lower()
    models = MODEL_TYPE_KEYWORDS.get(product_type, {})
    for model, keywords in models.items():
        if any(k in t for k in keywords):
            return model
    # Fallback: ask GPT to classify the model type
    return _ai_detect_model_type(text, product_type)


def _ai_detect_model_type(text, product_type):
    """Ask GPT to extract the specific model/sub-type from the listing."""
    client = _get_openai_client()
    if client is None:
        return None

    prompt = (
        f"Given this product listing, identify the specific sub-type of the {product_type}.\n\n"
        f"Listing: {text}\n\n"
        "Reply with ONLY a JSON object:\n"
        '{"model_type": "the specific sub-type in 1-3 words lowercase"}\n\n'
        "Examples for sneakers: sneaker, heel, loafer, boot, sandal, slide, mule\n"
        "Examples for electronics: iphone, ipad, macbook, airpods, headphones\n"
        "Examples for bags: tote, backpack, crossbody, clutch, wallet\n"
        "Examples for clothing: hoodie, jacket, jeans, t-shirt, dress\n"
        "If you can't determine a meaningful sub-type, return null."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=30,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        model = data.get("model_type", "").strip().lower()
        return model if model and model not in ("null", "none", "unknown") else None
    except Exception:
        return None


def get_market_range(brand, category, condition, product_type=None, model_type=None):
    """
    Lookup order (most → least specific):
    1. brand → "product_type:model_type" compound key  (e.g. "electronics:iphone")
    2. brand → product_type key                        (e.g. "electronics")
    3. brand → sneaker tier key                        (e.g. "basic", "mid", "hype")
    4. brand → "sneakers" fallback for sneaker/general queries
    """
    if not brand or brand not in pricing_db:
        return None
    cond = condition if condition in ("new", "used") else "new"
    brand_data = pricing_db[brand]

    # 1. Most specific: product_type:model_type compound key
    if product_type and model_type:
        compound = f"{product_type}:{model_type}"
        if compound in brand_data:
            return brand_data[compound].get(cond)

    # 2. Product type key (e.g. "bags", "electronics")
    if product_type and product_type in brand_data:
        return brand_data[product_type].get(cond)

    # 3. Sneaker tier key — only valid for sneakers/general queries
    if category in brand_data:
        if product_type and product_type not in ("sneakers", "general", None):
            return None
        return brand_data[category].get(cond)

    # 4. Sneaker tier → "sneakers" key fallback
    if category in ("basic", "mid", "hype") and "sneakers" in brand_data:
        if product_type in (None, "sneakers", "general"):
            return brand_data["sneakers"].get(cond)

    return None


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


def ai_extract_attributes(text):
    """
    When normal NLP extraction fails, ask GPT to parse the listing and return
    structured attributes. Returns a dict with brand, model, condition, price
    or None if the call fails.
    """
    client = _get_openai_client()
    if client is None:
        return None

    prompt = (
        "You are a product listing parser. Extract structured attributes from this listing.\n\n"
        f"Listing: {text}\n\n"
        "Reply with ONLY a JSON object — no extra text:\n"
        "{\n"
        '  "brand": "brand name lowercase (e.g. nike, sony, levi\'s)",\n'
        '  "model": "specific model name (e.g. air force 1, iphone 13 pro)",\n'
        '  "condition": "new or used",\n'
        '  "price": 123\n'
        "}\n\n"
        "Rules:\n"
        "- brand must be a real brand name, never 'unknown'\n"
        "- condition is 'new' if mint/deadstock/brand new, otherwise 'used'\n"
        "- price is an integer in USD, or null if not found"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        brand = data.get("brand", "").lower().strip()
        if not brand or brand in ("unknown", "n/a", "none"):
            return None
        return {
            "brand": brand,
            "model": data.get("model", "").lower().strip(),
            "condition": data.get("condition", "unknown").lower().strip(),
            "price": data.get("price"),
        }
    except Exception:
        return None


def ai_fetch_pricing(listing_text, product_type="general", model_type=None):
    """
    Fetch resale price ranges for a SPECIFIC brand + product_type + model_type.
    e.g. apple/electronics/iphone and apple/electronics/ipad are stored separately.
    Stored as pricing_db[brand]["product_type:model_type"] when model is known,
    or pricing_db[brand]["product_type"] otherwise.
    """
    client = _get_openai_client()
    if client is None:
        return None, None, None

    specificity = f"{product_type} — {model_type}" if model_type else product_type
    prompt = (
        "You are a resale market pricing expert. Given this product listing, "
        "provide realistic current USD resale price ranges.\n\n"
        f"Listing: {listing_text}\n"
        f"Product type: {specificity}\n\n"
        "Reply with ONLY a JSON object — no extra text:\n"
        "{\n"
        '  "brand": "brand_name_lowercase",\n'
        '  "pricing": {\n'
        '    "new":  [min_price, max_price],\n'
        '    "used": [min_price, max_price]\n'
        "  }\n"
        "}\n\n"
        "Rules:\n"
        "- brand must be the real brand name, never 'unknown'\n"
        "- Prices are whole USD integers for the RESALE/secondhand market\n"
        f"- Price ONLY {specificity} items — not other models or categories"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)

        brand = data["brand"].lower().strip()
        if not brand or brand in ("unknown", "n/a", "none", "other"):
            return None, None, None

        raw = data["pricing"]
        pricing_entry = {
            "new":  tuple(raw["new"]),
            "used": tuple(raw["used"]),
        }

        # Compound key when model is known: "electronics:iphone"
        storage_key = f"{product_type}:{model_type}" if model_type else product_type

        if brand not in pricing_db:
            pricing_db[brand] = {}
        pricing_db[brand][storage_key] = pricing_entry
        _write_pricing_db()

        return brand, storage_key, pricing_entry.get("used")

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

_CONDITION_FILLER = {
    "new", "used", "worn", "brand", "like", "gently", "deadstock",
    "bnib", "ds", "pre-owned", "preowned", "mint", "condition",
}

def _has_meaningful_product(product: str, brand: str) -> bool:
    """True if `product` contains more than just the brand name, condition words, and price tokens."""
    remaining = product.lower().replace(brand.lower(), "").strip(" ,-")
    words = {w.strip("$,-./") for w in remaining.split()}
    # Drop price tokens (pure digits or originally dollar-prefixed) and empty strings
    words = {w for w in words if w and not w.isdigit()}
    return bool(words - _CONDITION_FILLER)


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

    # ── AI extraction fallback ────────────────────────────────────────────────
    # If brand is still unknown after NLP, ask GPT to parse the listing text
    if not brand or brand == "unknown":
        parsed = ai_extract_attributes(text)
        if parsed:
            brand    = parsed["brand"]
            condition = parsed["condition"] if parsed["condition"] != "unknown" else condition
            price    = parsed["price"] if parsed["price"] else price
            product  = f"{brand} {parsed['model']}".strip() if parsed.get("model") else brand
            category = detect_category(f"{brand} {parsed.get('model', '')}")
            result.update({
                "brand": brand, "condition": condition,
                "price": price, "product": product, "category": category,
            })

    # After NLP + AI extraction, require both a brand and a meaningful product description
    if not brand or not _has_meaningful_product(product or "", brand or ""):
        result["error"] = "Not enough information — please include the brand and product name (e.g. 'Gucci bag' or 'Nike Air Force 1')."
        return result

    product_type = detect_product_type(text)
    model_type = detect_model_type(text, product_type)
    result["product_type"] = product_type
    result["model_type"] = model_type

    market_range = get_market_range(brand, category, condition, product_type, model_type)

    # Unknown brand/product — ask AI to fetch price data and write it to data.py
    if market_range is None:
        ai_brand, ai_category, _ = ai_fetch_pricing(text, product_type, model_type)
        if ai_brand:
            brand = ai_brand
            category = ai_category or category
            market_range = get_market_range(brand, category, condition, product_type, model_type)
            # Keep existing product name if it's already good; only re-extract if needed
            re_extracted = extract_product(text)
            if re_extracted != "unknown":
                product = re_extracted
            elif result.get("product") in (None, "unknown"):
                product = f"{brand} {text.split(',')[0].strip()}".strip()
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
