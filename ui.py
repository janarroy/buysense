import streamlit as st
from logic import *

# --------------------------
# Page Config
# --------------------------
st.set_page_config(page_title="BuySense", layout="centered")

# --------------------------
# Custom Styling (Cream UI)
# --------------------------
st.markdown("""
    <style>
    body {
        background-color: #F7F3EE;
    }
    .main {
        background-color: #F7F3EE;
    }
    .stTextArea textarea {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 12px;
        font-size: 16px;
    }
    .stButton button {
        background-color: #E8DED1;
        color: black;
        border-radius: 10px;
        padding: 10px 20px;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# --------------------------
# Header
# --------------------------
st.markdown("<h1 style='text-align: center;'>BuySense</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: gray;'>Your AI shopping assistant</h3>", unsafe_allow_html=True)

st.write("")
st.write("")

# --------------------------
# Input Section
# --------------------------
example = "Nike Air Force 1, worn twice, $150"

user_input = st.text_area(
    "Paste a product listing",
    value=example
)

# --------------------------
# Analyze Button
# --------------------------
if st.button("Analyze Deal"):

    # NLP Pipeline
    tokens = tokenize(user_input)
    price = extract_price(user_input)
    condition = extract_condition(user_input)
    product = extract_product(user_input)

    if price is None:
        st.error("No price found in listing.")
    else:
        result, reasoning = evaluate(product, condition, price, user_input)

        st.write("")

        # --------------------------
        # Result Display
        # --------------------------
        if result == "Overpriced":
            st.markdown("### Overpriced")
        elif result == "Good Deal":
            st.markdown("### Good Deal")
        else:
            st.markdown("### ⚖️ Fair")

        # Reasoning
        st.write(reasoning)

        st.write("")

        # --------------------------
        # Details Section
        # --------------------------
        st.markdown("#### Details")
        st.write(f"Product: {product}")
        st.write(f"Condition: {condition}")
        st.write(f"Price: ${price}")

        # --------------------------
        # NLP Transparency
        # --------------------------
        with st.expander("See NLP breakdown"):
            st.write(tokens)