import streamlit as st
import pandas as pd
from datetime import datetime

# 👉 Import your bot functions
from bot import run, fetch_results, score_numbers, build_pool, generate, confidence

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="🎯 Gosloto AI Predictor",
    page_icon="🎯",
    layout="wide"
)

# ================= CUSTOM STYLE =================
st.markdown("""
<style>
body {
    background-color: #0f172a;
}
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
}
.card {
    background: #1e293b;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 0 15px rgba(0,0,0,0.4);
    margin-bottom: 15px;
}
.pool-number {
    display: inline-block;
    background: #2563eb;
    padding: 10px;
    margin: 5px;
    border-radius: 10px;
    font-weight: bold;
}
.ticket {
    background: #111827;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.title("🎯 ELITE GOSLOTO 7/49 AI BOT")
st.caption("Hybrid AI + Pattern System | GOD MODE")

# ================= SIDEBAR =================
st.sidebar.header("⚙️ Controls")

run_button = st.sidebar.button("🚀 Generate Prediction")

show_history = st.sidebar.checkbox("📊 Show Draw History")
show_scores = st.sidebar.checkbox("🧠 Show AI Scores")

# ================= MAIN =================
if run_button:

    st.subheader("🔄 Running Prediction Engine...")

    history = fetch_results()

    if not history:
        st.error("❌ Failed to fetch data")
        st.stop()

    scores = score_numbers(history)
    pool = build_pool(scores)
    tickets = generate(pool)

    # ================= POOL =================
    st.subheader("🎯 Selected Number Pool")

    pool_html = ""
    for n in pool:
        pool_html += f'<span class="pool-number">{n}</span>'

    st.markdown(pool_html, unsafe_allow_html=True)

    # ================= TICKETS =================
    st.subheader("🎟️ Generated Tickets")

    for i, t in enumerate(tickets, 1):
        conf = confidence(t, scores)

        st.markdown(f"""
        <div class="ticket">
            <b>Ticket {i}</b><br>
            {t}<br>
            🔥 Confidence: {conf}%
        </div>
        """, unsafe_allow_html=True)

    # ================= STATS =================
    st.subheader("📊 Stats")

    col1, col2, col3 = st.columns(3)

    col1.metric("Pool Size", len(pool))
    col2.metric("Tickets", len(tickets))
    col3.metric("Last Update", datetime.now().strftime("%H:%M:%S"))

    # ================= OPTIONAL =================
    if show_history:
        st.subheader("📜 Draw History")

        df = pd.DataFrame(history, columns=[f"N{i}" for i in range(1, 8)])
        st.dataframe(df)

    if show_scores:
        st.subheader("🧠 AI Score Ranking")

        df_scores = pd.DataFrame(
            sorted(scores.items(), key=lambda x: x[1], reverse=True),
            columns=["Number", "Score"]
        )

        st.dataframe(df_scores)

# ================= FOOTER =================
st.markdown("---")
st.caption("⚡ Powered by Hybrid AI + GFX + Delta + Genetic Logic")