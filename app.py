from flask import Flask, request, jsonify
from data import pricing_db
import re

app = Flask(__name__)

# ---------------------------
# 1. Tokenization
# ---------------------------
def tokenize(text):
    return text.lower().split()

# ---------------------------
# 2. Extract Price
# ---------------------------
def extract_price(text):
    match = re.search(r"\$(\d+)", text)
    if match:
        return int(match.group(1))
    return None

# ---------------------------
# 3. Extract Condition
# ---------------------------
def extract_condition(text):
    text = text.lower()
    if "new" in text:
        return "new"
    elif "worn" in text or "used" in text:
        return "used"
    return "unknown"

# ---------------------------
# 4. Extract Product
# ---------------------------
def extract_product(text):
    text = text.lower()

    brands = ["nike", "adidas", "jordan", "new balance", "yeezy", "asics"]

    detected_brand = None
    for brand in brands:
        if brand in text:
            detected_brand = brand
            break

    # Extract model (simple heuristic: words after brand)
    if detected_brand:
        words = text.split()
        try:
            idx = words.index(detected_brand)
            model = " ".join(words[idx:idx+3])  # grab next 2-3 words
            return model
        except:
            return detected_brand

    return "unknown"

# ---------------------------
# 5. Evaluate Deal
# ---------------------------

def evaluate(product, condition, price, text):
    brand = None

    for b in pricing_db:
        if b in product:
            brand = b
            break

    if not brand:
        return "Unknown", "We couldn't identify the brand, so we can't evaluate this listing yet."

    category = detect_category(text)

    if category not in pricing_db[brand]:
        return "Unknown", "We don't have enough data for this type of product."

    min_price, max_price = pricing_db[brand][category][condition]

    if price > max_price:
        return (
            "Overpriced",
            f"This {condition} {brand} sneaker is listed at \\${price}, "
            f"which is above the typical resale range of \\${min_price}–\\${max_price} "
            f"for similar {category} shoes. Buyers are likely paying a premium."
        )

    elif price < min_price:
        return (
            "Good Deal",
            f"This {condition} {brand} sneaker is listed at \\${price}, "
            f"which is below the typical resale range of \\${min_price}–\\${max_price}. "
            f"This appears to be a strong deal."
        )

    else:
        return (
            "Fair",
            f"This {condition} {brand} sneaker is priced at \\${price}, "
            f"which falls within the expected market range of \\${min_price}–\\${max_price} "
            f"for {category} shoes."
        )

# ---------------------------
# API Route
# ---------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")

    tokens = tokenize(text)
    price = extract_price(text)
    condition = extract_condition(text)
    product = extract_product(text)

    if price is None:
        return jsonify({"error": "No price found"})

    result, reasoning = evaluate(product, condition, price, text)

    return jsonify({
        "tokens": tokens,
        "product": product,
        "condition": condition,
        "price": price,
        "result": result,
        "reasoning": reasoning
    })

def detect_category(text):
    text = text.lower()

    hype_keywords = ["travis", "off-white", "limited", "collab", "rare"]
    mid_keywords = ["retro", "boost", "990", "2002r", "gel"]

    if any(word in text for word in hype_keywords):
        return "hype"
    elif any(word in text for word in mid_keywords):
        return "mid"
    else:
        return "basic"

# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)