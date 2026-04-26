from data import pricing_db
import re

def tokenize(text):
    return text.lower().split()

def extract_price(text):
    match = re.search(r"\$(\d+)", text)
    return int(match.group(1)) if match else None

def extract_condition(text):
    text = text.lower()
    if "new" in text:
        return "new"
    elif "worn" in text or "used" in text:
        return "used"
    return "unknown"

def extract_product(text):
    text = text.lower()
    brands = ["nike", "adidas", "jordan", "new balance", "yeezy", "asics"]
    for b in brands:
        if b in text:
            return b
    return "unknown"

def detect_category(text):
    text = text.lower()
    if "retro" in text or "boost" in text:
        return "mid"
    return "basic"

def evaluate(product, condition, price, text):
    if product not in pricing_db:
        return "Unknown", "Brand not recognized."

    category = detect_category(text)
    min_price, max_price = pricing_db[product][category][condition]

    if price > max_price:
        return (
            "Overpriced",
            f"This {condition} {product} sneaker is listed at ${price}, which is above the typical resale range of ${min_price}–${max_price}."
        )
    elif price < min_price:
        return (
            "Good Deal",
            f"This {condition} {product} sneaker is listed at ${price}, which is below the typical resale range of ${min_price}–${max_price}."
        )
    else:
        return (
            "Fair",
            f"This {condition} {product} sneaker is priced within the expected range (${min_price}–${max_price})."
        )