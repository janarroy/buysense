import streamlit as st
import requests

# --------------------------
# Page Config
# --------------------------
st.set_page_config(page_title="BuySense", layout="centered")


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
# Input
# --------------------------
example = "Nike Air Force 1, worn twice, $150"

user_input = st.text_area(
    "Paste a product listing",
    value=example
)

# --------------------------
# Button
# --------------------------
if st.button("Analyze Deal"):
    response = requests.post(
        "http://127.0.0.1:5000/analyze",
        json={"text": user_input}
    )

    if response.status_code != 200:
        st.error("Backend error. Check server.")
    else:
        data = response.json()

        if "error" in data:
            st.error(data["error"])
        else:
            st.write("")

            if data["result"] == "Overpriced":
                st.markdown(f"### {data['result']}")
            elif data["result"] == "Good Deal":
                st.markdown(f"### {data['result']}")
            else:
                st.markdown(f"### {data['result']}")

            # Reasoning (MAIN VALUE)
            st.write(data["reasoning"])

            st.write("")

            # Details
            st.markdown("#### Details")
            st.write(f"Product: {data['product']}")
            st.write(f"Condition: {data['condition']}")
            st.write(f"Price: ${data['price']}")

            # Optional NLP transparency
            with st.expander("See NLP breakdown"):
                st.write(data["tokens"])