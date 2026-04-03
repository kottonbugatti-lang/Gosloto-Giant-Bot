import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import json
import os
from collections import Counter
from itertools import combinations
import random

# ================= CONFIG =================
MAX_NUMBER = 49
DRAW_SIZE = 7
HISTORY_LIMIT = 100
BASE_POOL_SIZE = 9
MAX_TICKETS = 15
URL = "https://www.lotteryextreme.com/russia-gosloto-7x49/"

# ================= FETCH (Streamlit Optimized) =================
@st.cache_data(ttl=3600)  # Caches data for 1 hour to prevent IP bans
def fetch_results():
    try:
        # Added headers to mimic a real browser
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        res = requests.get(URL, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        draws = []
        for row in soup.select("table tr"):
            nums = [int(n) for n in row.text.split() if n.isdigit()]
            if len(nums) == DRAW_SIZE and len(set(nums)) == DRAW_SIZE:
                draws.append(sorted(nums))
        
        return draws[:HISTORY_LIMIT]
    except Exception as e:
        st.error(f"Scrape failed: {e}")
        return []

# ================= ANALYSIS LOGIC =================
def analyze(history):
    flat = [n for d in history for n in d]
    freq = Counter(flat)
    recency = Counter()
    for i, draw in enumerate(reversed(history)):
        weight = (len(history) - i) / len(history)
        for n in draw:
            recency[n] += weight
    return freq, recency

def gfx(last):
    neighbors, cross = set(), set()
    for n in last:
        for d in [-2, -1, 1, 2]:
            if 1 <= n + d <= MAX_NUMBER: neighbors.add(n + d)
        if n + 7 <= MAX_NUMBER: cross.add(n + 7)
        if n - 7 >= 1: cross.add(n - 7)
    return neighbors, cross

def delta_patterns(history):
    deltas = Counter()
    for draw in history:
        for i in range(len(draw)-1):
            deltas[draw[i+1] - draw[i]] += 1
    return [d for d, _ in deltas.most_common(10)]

def pair_triplet(history):
    pairs, triplets = Counter(), Counter()
    for d in history:
        for p in combinations(d, 2): pairs[p] += 1
        for t in combinations(d, 3): triplets[t] += 1
    return pairs.most_common(50), triplets.most_common(30)

def score_numbers(history):
    freq, recency = analyze(history)
    top_deltas = delta_patterns(history)
    top_pairs, top_triplets = pair_triplet(history)
    last = history[0] # The most recent draw
    neighbors, cross = gfx(last)
    
    scores = {}
    for n in range(1, MAX_NUMBER + 1):
        score = (freq.get(n, 0) * 1.5) + (recency.get(n, 0) * 3)
        if n in neighbors: score += 6
        if n in cross: score += 5
        if any(abs(n - x) in top_deltas for x in last): score += 2
        for p, c in top_pairs: 
            if n in p: score += c * 0.2
        scores[n] = score
    return scores

# ================= GENERATION LOGIC =================
def build_pool(scores):
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    pool_size = BASE_POOL_SIZE + random.choice([0, 1])
    return sorted([n for n, _ in ranked[:pool_size]])

def valid(ticket):
    odds = sum(n % 2 for n in ticket)
    if odds < 2 or odds > 5: return False
    if not (120 <= sum(ticket) <= 260): return False
    return True

def generate_tickets(pool, scores):
    tickets = []
    attempts = 0
    while len(tickets) < MAX_TICKETS and attempts < 1000:
        t = sorted(random.sample(pool, DRAW_SIZE))
        if valid(t) and t not in tickets:
            tickets.append(t)
        attempts += 1
    return tickets

def get_confidence(ticket, scores):
    total = sum(scores[n] for n in ticket)
    max_possible = sum(sorted(scores.values(), reverse=True)[:DRAW_SIZE])
    return round((total / max_possible) * 100, 2)

# ================= STREAMLIT UI =================
def main():
    st.set_page_config(page_title="Gosloto Giant Bot", layout="wide")
    
    st.title("🎯 Gosloto 7x49 Giant Bot")
    st.sidebar.header("Settings")
    history_count = st.sidebar.slider("History Depth", 10, 100, 50)
    
    if st.button("🚀 Analyze & Generate Tickets"):
        with st.spinner("Analyzing patterns..."):
            history = fetch_results()
            
            if history:
                history = history[:history_count]
                scores = score_numbers(history)
                pool = build_pool(scores)
                tickets = generate_tickets(pool, scores)
                
                # Layout
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader("📊 Top Pool")
                    st.info(f"The algorithm selected these {len(pool)} numbers as the strongest candidates.")
                    st.write(pool)
                    
                    st.subheader("🕒 Last Draw")
                    st.code(history[0])

                with col2:
                    st.subheader("🔥 Recommended Tickets")
                    for i, t in enumerate(tickets):
                        conf = get_confidence(t, scores)
                        st.success(f"**Ticket {i+1}:** `{t}` | Confidence: **{conf}%**")
            else:
                st.error("Could not retrieve data. The site might be down or blocking the request.")

if __name__ == "__main__":
    main()