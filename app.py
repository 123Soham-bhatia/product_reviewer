# app.py
import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import os  # For file/env checks

# ------------------------------
# 1️⃣ Configure Generative AI API
# ------------------------------
# Paths where Streamlit looks for secrets.toml (app dir takes priority)
app_secrets_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
global_secrets_path = os.path.expanduser("~/.streamlit/secrets.toml")

API_KEY = None

# Priority 1: App secrets.toml (if exists)
if os.path.exists(app_secrets_path):
    API_KEY = st.secrets["GEMINI_API_KEY"]
    st.success("✅ Loaded API key from secrets.toml")  # Optional: Confirm it's working

# Priority 2: Global secrets.toml (if exists and app one missing)
elif os.path.exists(global_secrets_path):
    API_KEY = st.secrets["GEMINI_API_KEY"]
    st.success("✅ Loaded API key from global secrets.toml")  # Optional

# Priority 3: Environment variable (silent fallback)
if not API_KEY:
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if API_KEY:
        st.success("✅ Loaded API key from environment variable")  # Optional

# Priority 4: Hardcoded (local testing only, no warning)
if not API_KEY:
    API_KEY = "AIzaSyDYRwLCkX6tUn_-Vj2LXKx9J91h1RjKSBE"
    # No st.warning() here—clean UI for local use
    # Uncomment below if you want a subtle note (e.g., in sidebar)
    # with st.sidebar:
    #     st.info("🔑 Using local API key (set GEMINI_API_KEY env var for security)")

genai.configure(api_key=API_KEY)

# ------------------------------
# 2️⃣ Streamlit App UI
# ------------------------------
st.title("🛍️ Myntra Product Review Analyzer & Summarizer")
st.write("Upload your CSV file with columns like: product_name, review/review_text, rating")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"Loaded {len(df)} reviews")
    
    # ✅ New: Show actual columns for debugging
    st.subheader("Detected CSV Columns:")
    st.write(list(df.columns))
    
    # ✅ Detect review column dynamically
    review_col = None
    possible_review_cols = ['review', 'review_text', 'text', 'comment']
    for col in possible_review_cols:
        if col in df.columns:
            review_col = col
            break
    
    if review_col is None:
        st.error(f"❌ No review column found. Available columns: {list(df.columns)}. Rename your CSV column to 'review' or 'review_text'.")
    else:
        st.success(f"✅ Using review column: '{review_col}'")
        st.dataframe(df.head())

        # ------------------------------
        # 3️⃣ Analyze Reviews Button
        # ------------------------------
        if st.button("Analyze Reviews"):
            st.info("🔹 Starting analysis. Please wait...")

            results = []
            model = genai.GenerativeModel("gemini-2.5-flash")  # Supported Gemini model

            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, row in df.iterrows():
                prompt = f"""
                Analyze this Myntra product review:
                Review: "{row[review_col]}"  # ✅ Dynamic column
                Rating: {row['rating']}

                Provide a concise analysis in this exact format:
                1. Sentiment: (Positive / Negative / Neutral)
                2. Key points: (Bullet list of 2-3 main pros/cons)
                3. Recommendation: (Yes / No / Maybe) - Brief reason
                """

                try:
                    response = model.generate_content(prompt)
                    analysis_text = response.text.strip()
                except Exception as e:
                    analysis_text = f"Error: Could not analyze review. ({str(e)})"

                results.append({
                    "product_name": row["product_name"],
                    "review": row[review_col],  # ✅ Dynamic for output too
                    "rating": row["rating"],
                    "analysis": analysis_text
                })

                # Update progress
                progress = (i + 1) / len(df)
                progress_bar.progress(progress)
                status_text.text(f"✅ Processed review {i+1}/{len(df)}")

                # Delay to respect rate limits
                time.sleep(0.5)

            result_df = pd.DataFrame(results)

            # ------------------------------
            # 4️⃣ Show results in Streamlit
            # ------------------------------
            st.success("🎉 Analysis Completed!")
            st.dataframe(result_df)

            # ------------------------------
            # 5️⃣ Allow CSV download
            # ------------------------------
            csv = result_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Analysis CSV",
                data=csv,
                file_name="myntra_review_analysis.csv",
                mime="text/csv"
            )