import streamlit as st
import requests
import numpy as np
import random

# -------------------------------
# CONFIG
# -------------------------------
API_KEY = "2ccb99a8008f49f18faea5aabab70d9e"   # 🔴 Put your API key here

categories = [
    "technology",
    "sports",
    "business",
    "politics",
    "entertainment",
    "health",
    "science",
    "world"
]
n = len(categories)

# -------------------------------
# SESSION STATE
# -------------------------------
if "counts" not in st.session_state:
    st.session_state.counts = np.zeros(n)

if "q_values" not in st.session_state:
    st.session_state.q_values = np.zeros(n)

if "history" not in st.session_state:
    st.session_state.history = []

# 🔥 NEW: refresh counter
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

epsilon = 0.6

# -------------------------------
# RL FUNCTIONS
# -------------------------------
def select_category():
    # if no learning yet → random category
    if np.sum(st.session_state.counts) == 0:
        return random.randint(0, n - 1)

    if random.random() < epsilon:
        return random.randint(0, n - 1)

    return int(np.argmax(st.session_state.q_values))


def update(category_idx, reward):
    st.session_state.counts[category_idx] += 1
    c = st.session_state.counts[category_idx]
    v = st.session_state.q_values[category_idx]
    st.session_state.q_values[category_idx] += (reward - v) / c


# -------------------------------
# CATEGORY DETECTION
# -------------------------------
def detect_category(title):
    title = title.lower()

    if any(word in title for word in ["tech", "ai", "software", "google", "apple"]):
        return "technology"

    elif any(word in title for word in ["cricket", "football", "sports", "match"]):
        return "sports"

    elif any(word in title for word in ["stock", "market", "business", "economy", "bank"]):
        return "business"

    elif any(word in title for word in ["election", "government", "minister", "politics"]):
        return "politics"

    elif any(word in title for word in ["movie", "film", "actor", "celebrity", "bollywood"]):
        return "entertainment"

    elif any(word in title for word in ["health", "hospital", "disease", "covid", "medicine"]):
        return "health"

    elif any(word in title for word in ["science", "research", "space", "nasa"]):
        return "science"

    elif any(word in title for word in ["war", "global", "international", "country"]):
        return "world"

    else:
        return random.choice(categories)  # 🔥 important for balance


# -------------------------------
# FETCH NEWS (WITH PAGINATION)
# -------------------------------
def fetch_news():
    page = (st.session_state.refresh_count % 10) + 1

    url = f"https://newsapi.org/v2/everything?q=india&pageSize=10&page={page}&language=en&sortBy=publishedAt&apiKey={API_KEY}"
    
    res = requests.get(url)
    data = res.json()

    # 🔥 HANDLE LIMIT ERROR SILENTLY
    if data.get("status") != "ok":
        # reset refresh count
        st.session_state.refresh_count = 0

        # fetch again from page 1
        url = f"https://newsapi.org/v2/everything?q=india&pageSize=10&page=1&language=en&sortBy=publishedAt&apiKey={API_KEY}"
        res = requests.get(url)
        data = res.json()

    articles = data.get("articles", [])

    # add category
    for article in articles:
        title = article.get("title", "")
        article["category"] = detect_category(title)

    return articles

# -------------------------------
# UI
# -------------------------------
st.title("📰 Smart News Recommendation System")
st.write("👉 Click 👍 on news you like. System will learn your interests!")

# -------------------------------
# REFRESH BUTTON (FIXED)
# -------------------------------
if st.button("🔄 Refresh News"):
    st.session_state.refresh_count += 1
    st.rerun()

# show refresh count (optional)
# st.caption(f"Refresh count: {st.session_state.refresh_count}")

# -------------------------------
# FETCH ARTICLES
# -------------------------------
all_articles = fetch_news()

# -------------------------------
# RL CATEGORY SELECTION
# -------------------------------
cat_idx = select_category()
selected_category = categories[cat_idx]

st.subheader(f"📌 Recommended Category: {selected_category.upper()}")

# -------------------------------
# SMART DISPLAY (PRIORITIZE CATEGORY)
# -------------------------------
preferred = [a for a in all_articles if a["category"] == selected_category]
others = [a for a in all_articles if a["category"] != selected_category]

articles = (preferred + others)[:5]

# -------------------------------
# FALLBACK
# -------------------------------
if not articles:
    st.error("❌ No articles coming from API")

    articles = [
        {"title": "AI is transforming the world", "url": "#", "category": "technology"},
        {"title": "India wins cricket match", "url": "#", "category": "sports"},
        {"title": "Stock market rises today", "url": "#", "category": "business"}
    ]

# -------------------------------
# DISPLAY ARTICLES
# -------------------------------
for i, article in enumerate(articles):
    st.write(f"### {article.get('title', 'No Title')}")

    st.write(f"**Category:** {article.get('category', 'unknown')}")

    if article.get("url"):
        st.write(f"[Read full article]({article['url']})")

    col1, col2 = st.columns(2)

    article_category = article.get("category", "technology")
    category_idx = categories.index(article_category)

    with col1:
        if st.button("👍 Like", key=f"like_{i}_{st.session_state.refresh_count}"):
            update(category_idx, 1)
            st.session_state.history.append(article_category)
            st.success("Preference updated!")

    with col2:
        if st.button("👎 Skip", key=f"skip_{i}_{st.session_state.refresh_count}"):
            update(category_idx, 0)
# -------------------------------
# LEARNING STATUS
# -------------------------------
st.write("---")
st.subheader("📊 Learning Status")

for i in range(n):
    st.write(
        f"{categories[i]} -> score: {st.session_state.q_values[i]:.2f}, "
        f"chosen: {int(st.session_state.counts[i])} times"
    )

# -------------------------------
# USER HISTORY
# -------------------------------
st.write("---")
st.subheader("🧠 Your Interest History")
st.write(st.session_state.history)