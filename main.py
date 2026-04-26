import streamlit as st
import re

# --------------------------
# Pricing DB
# --------------------------
pricing_db = {
    "nike": {
        "basic": {"new": (90, 140), "used": (70, 120)},
        "mid": {"new": (120, 200), "used": (90, 170)},
        "hype": {"new": (200, 400), "used": (150, 350)}
    },
    "adidas": {
        "basic": {"new": (80, 130), "used": (60, 110)},
        "mid": {"new": (120, 200), "used": (90, 170)}
    }
}

# --------------------------
# NLP Functions
# --------------------------
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
    brands = ["nike", "adidas"]
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
            f"This {condition} {product} sneaker is listed at ${price}, which is above the typical resale range of ${min_price}–${max_price}. Buyers are likely paying a premium."
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

# --------------------------
# UI
# --------------------------
st.set_page_config(page_title="BuySense", layout="centered")

st.markdown("<h1 style='text-align:center;'>BuySense</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;color:gray;'>Your AI shopping assistant</h3>", unsafe_allow_html=True)

user_input = st.text_area("Paste a product listing", "Nike Air Force 1, worn twice, $150")

if st.button("Analyze Deal"):
    tokens = tokenize(user_input)
    price = extract_price(user_input)
    condition = extract_condition(user_input)
    product = extract_product(user_input)

    result, reasoning = evaluate(product, condition, price, user_input)

    st.markdown(f"### {result}")
    st.write(reasoning)

    st.markdown("#### Details")
    st.write(f"Product: {product}")
    st.write(f"Condition: {condition}")
    st.write(f"Price: ${price}")

    with st.expander("See NLP breakdown"):
        st.write(tokens)