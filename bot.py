import requests
from bs4 import BeautifulSoup
import time
import logging
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
CACHE_FILE = "lottery_data.json"
CACHE_TTL = 6 * 3600

URL = "https://www.lotteryextreme.com/russia-gosloto-7x49/"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ================= CACHE =================
def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    if time.time() - os.path.getmtime(CACHE_FILE) > CACHE_TTL:
        return None
    with open(CACHE_FILE, "r") as f:
        return json.load(f)

def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

# ================= FETCH =================
def fetch_results():
    cache = load_cache()
    if cache:
        return cache

    try:
        res = requests.get(URL, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        draws = []
        for row in soup.select("table tr"):
            nums = [int(n) for n in row.text.split() if n.isdigit()]
            if len(nums) == DRAW_SIZE and len(set(nums)) == DRAW_SIZE:
                draws.append(sorted(nums))

        draws = draws[:HISTORY_LIMIT]
        save_cache(draws)
        return draws

    except Exception as e:
        logging.error(f"Scrape failed: {e}")
        return []

# ================= ANALYSIS =================
def analyze(history):
    flat = [n for d in history for n in d]
    freq = Counter(flat)

    recency = Counter()
    for i, draw in enumerate(reversed(history)):
        weight = (len(history) - i) / len(history)
        for n in draw:
            recency[n] += weight

    return freq, recency

# ================= GFX =================
def gfx(last):
    neighbors, cross = set(), set()
    for n in last:
        for d in [-2, -1, 1, 2]:
            if 1 <= n + d <= MAX_NUMBER:
                neighbors.add(n + d)
        if n + 7 <= MAX_NUMBER:
            cross.add(n + 7)
        if n - 7 >= 1:
            cross.add(n - 7)
    return neighbors, cross

# ================= DELTA =================
def delta_patterns(history):
    deltas = Counter()
    for draw in history:
        for i in range(len(draw)-1):
            deltas[draw[i+1] - draw[i]] += 1
    return deltas.most_common(10)  # FIXED

# ================= PAIRS/TRIPLETS =================
def pair_triplet(history):
    pairs, triplets = Counter(), Counter()
    for d in history:
        for p in combinations(d, 2):
            pairs[p] += 1
        for t in combinations(d, 3):
            triplets[t] += 1

    return pairs.most_common(50), triplets.most_common(30)  # FIXED

# ================= ML ADAPTIVE WEIGHTS =================
def adaptive_weights(freq):
    avg = sum(freq.values()) / len(freq) if freq else 1
    return {
        "freq": 2 if avg < 10 else 1.5,
        "recency": 3,
        "neighbor": 6,
        "cross": 5
    }

# ================= SCORING =================
def score_numbers(history):
    freq, recency = analyze(history)
    top_deltas = [d for d, _ in delta_patterns(history)]
    top_pairs, top_triplets = pair_triplet(history)

    weights = adaptive_weights(freq)

    last = history[-1]
    neighbors, cross = gfx(last)

    scores = {}

    for n in range(1, MAX_NUMBER + 1):
        score = 0

        score += freq.get(n, 0) * weights["freq"]
        score += recency.get(n, 0) * weights["recency"]

        if n in neighbors:
            score += weights["neighbor"]
        if n in cross:
            score += weights["cross"]

        # FIXED DELTA
        for d in top_deltas:
            if any(abs(n - x) == d for x in last):
                score += 2

        # FIXED PAIRS
        for p, c in top_pairs:
            if n in p:
                score += c * 0.2

        # FIXED TRIPLETS
        for t, c in top_triplets:
            if n in t:
                score += c * 0.1

        scores[n] = score

    return scores

# ================= POOL =================
def build_pool(scores):
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Adaptive pool size
    pool_size = BASE_POOL_SIZE + random.choice([0, 1])
    return sorted([n for n, _ in ranked[:pool_size]])

# ================= FILTER =================
def valid(ticket):
    odds = sum(n % 2 for n in ticket)
    if odds < 2 or odds > 5:
        return False
    if not (120 <= sum(ticket) <= 260):
        return False
    return True

# ================= DIVERSITY =================
def is_diverse(ticket, existing):
    for t in existing:
        if len(set(t) & set(ticket)) >= 6:
            return False
    return True

# ================= TICKETS =================
def generate(pool):
    tickets = []

    for combo in combinations(pool, DRAW_SIZE):
        t = sorted(combo)
        if valid(t) and is_diverse(t, tickets):
            tickets.append(t)
        if len(tickets) >= MAX_TICKETS:
            break

    # fallback
    while len(tickets) < MAX_TICKETS:
        t = sorted(random.sample(pool, DRAW_SIZE))
        if valid(t) and is_diverse(t, tickets):
            tickets.append(t)

    return tickets

# ================= CONFIDENCE =================
def confidence(ticket, scores):
    total = sum(scores[n] for n in ticket)
    max_score = sum(sorted(scores.values(), reverse=True)[:DRAW_SIZE])
    return round((total / max_score) * 100, 2) if max_score else 0

# ================= REAL-TIME DETECTION =================
def is_new_draw(history):
    cache = load_cache()
    return cache != history

# ================= MAIN =================
def run():
    history = fetch_results()

    if not history:
        logging.error("No data")
        return

    if is_new_draw(history):
        logging.info("🎯 New draw detected!")

    scores = score_numbers(history)
    pool = build_pool(scores)
    tickets = generate(pool)

    print("\n🎯 POOL:", pool)
    for i, t in enumerate(tickets, 1):
        print(f"{i}: {t} 🔥 {confidence(t, scores)}%")

# ================= SAFE LOOP =================
        if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Runtime error: {e}")
