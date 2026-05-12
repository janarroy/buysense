# BuySense

AI-powered deal intelligence layer. Paste a product listing and BuySense
returns a deal score, market range, and a suggested action so you can
decide whether to buy, negotiate, or walk away.

## Features

- NLP extraction (product, brand, condition, price)
- Deal Score (0–100) computed against a market range
- Verdict: Good Deal / Fair / Overpriced
- Suggested action and confidence level
- Compare Mode — evaluate multiple listings side-by-side

## Run locally

```bash
pip install -r requirements.txt
streamlit run ui.py
```

Then open http://localhost:8501. To use it from another device on the
same wifi (e.g. your phone), open the **Network URL** that Streamlit
prints in the terminal.

## Files

- `ui.py` — Streamlit app (Analyze + Compare tabs)
- `logic.py` — extraction pipeline and scoring engine
- `data.py` — static pricing benchmarks by brand × category × condition
